#!/usr/bin/env python3
import os
import json
import time
import psutil
import subprocess
import threading
import sys
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置参数
API_URL = "http://127.0.0.1:5244/api/fs/copy"
SOURCE_DIR = "/var/www/html/tx/"
MAX_CONCURRENT = 5  # 最大并发数
MIN_WAIT_TIME = 30  # 最小等待时间(秒)
LARGE_FILE_THRESHOLD = 20 * 1024 * 1024 * 1024  # 20GB(可以根据需要调整)

class FileUploader:
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.uploaded_files = set()
        self.failed_files = set()
        self.processing_files = set()
        self.lock = threading.Lock()
        self.start_time = time.time()
        
    def get_upload_speed(self, interval=1):
        """监控上传速度"""
        # 获取所有网卡的统计信息(pernic=True)
        net_io_before = psutil.net_io_counters(pernic=True)
        
        # 计算非回环接口的总发送字节数
        bytes_sent_before = 0
        for iface, stats in net_io_before.items():
            # 排除本地回环接口(lo)
            if iface != 'lo':
                bytes_sent_before += stats.bytes_sent
        
        time.sleep(interval)
        
        net_io_after = psutil.net_io_counters(pernic=True)
        bytes_sent_after = 0
        for iface, stats in net_io_after.items():
            # 排除本地回环接口（lo）
            if iface != 'lo':
                bytes_sent_after += stats.bytes_sent
        
        bytes_per_sec = (bytes_sent_after - bytes_sent_before) / interval
        mb_per_sec = bytes_per_sec / (1024 * 1024)
        
        return mb_per_sec
    
    def send_single_copy_command(self, filename):
        """为单个文件发送复制命令"""
        payload = {
            "src_dir": "/tx",
            "dst_dir": f"/bd{self.target_dir}",  # 修正这里：将 /bd 和目标目录拼接
            "names": [filename],
            "overwrite": False,
            "skip_existing": False,
            "merge": False
        }
        
        payload_json = json.dumps(payload, ensure_ascii=False)
        
        # 构建完整的curl命令
        curl_command = [
            "curl", "-s", "-X", "POST", API_URL,
            "-H", "content-type: application/json;charset=UTF-8",
            "--data-raw", payload_json
        ]
        
        try:
            with subprocess.Popen(curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                stdout, stderr = proc.communicate(timeout=30)  # 30秒超时
                
                if proc.returncode == 0:
                    print(f"✓ 文件 {filename} 复制命令已发送")
                    return filename, True, ""
                else:
                    error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "未知错误"
                    print(f"✗ 文件 {filename} 复制命令失败: {error_msg}")
                    return filename, False, error_msg
                    
        except subprocess.TimeoutExpired:
            print(f"✗ 文件 {filename} 复制命令超时")
            return filename, False, "命令执行超时"
        except Exception as e:
            print(f"✗ 文件 {filename} 复制命令异常: {e}")
            return filename, False, str(e)
    
    def get_all_rclone_files(self):
        """获取目标目录下所有文件名列表"""
        rclone_command = [
            "rclone", "ls", f"bd:{self.target_dir}",
            "--config=/usr/local/bin/rclone.conf"
        ]
        
        try:
            with subprocess.Popen(rclone_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                stdout, stderr = proc.communicate(timeout=10)
                
                if proc.returncode == 0:
                    output = stdout.decode('utf-8', errors='ignore')
                    # 从rclone输出中提取文件名
                    files = set()
                    for line in output.split('\n'):
                        if line.strip():
                            # rclone输出格式通常是: 文件大小 文件名
                            # 提取最后一个空格后的部分作为文件名
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                filename = ' '.join(parts[1:])  # 处理文件名中有空格的情况
                                files.add(filename)
                    return files
                else:
                    print(f"rclone列出文件失败: {stderr.decode('utf-8', errors='ignore')}")
                    return set()
                    
        except Exception as e:
            print(f"获取rclone文件列表时出错: {e}")
            return set()
    
    def check_all_files_exist(self, source_files):
        """检查所有源文件是否都已存在于目标目录"""
        # 获取目标目录下的所有文件
        target_files = self.get_all_rclone_files()
        
        # 检查每个源文件是否都在目标目录中
        missing_files = []
        for filename in source_files:
            if filename not in target_files:
                missing_files.append(filename)
        
        return missing_files, target_files
    
    def get_file_size(self, filename):
        """获取文件大小（字节）"""
        filepath = os.path.join(SOURCE_DIR, filename)
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0
    
    def calculate_wait_time(self, files):
        """根据文件大小计算等待时间"""
        if not files:
            return MIN_WAIT_TIME
        
        total_size = 0
        large_files = 0
        
        for filename in files:
            size = self.get_file_size(filename)
            total_size += size
            if size >= LARGE_FILE_THRESHOLD:
                large_files += 1
        
        # 计算基础等待时间
        total_gb = total_size / (1024 * 1024 * 1024)
        
        # 规则：每GB等待10秒，但最小30秒
        # 如果有大文件，增加额外等待时间
        base_wait = max(MIN_WAIT_TIME, total_gb * 10)
        
        # 大文件额外等待
        extra_wait = large_files * 60  # 每个大文件额外1分钟
        
        wait_time = base_wait + extra_wait
        
        # 限制最大等待时间为10分钟
        max_wait = 10 * 60
        wait_time = min(max_wait, wait_time)
        
        print(f"本轮文件总大小: {total_gb:.2f} GB")
        print(f"大文件数量: {large_files}")
        print(f"计算出的等待时间: {wait_time:.0f} 秒")
        
        return wait_time
    
    def upload_batch(self, files):
        """上传一批文件"""
        if not files:
            return
        
        print(f"\n{'='*60}")
        print(f"开始上传第 {len(self.uploaded_files) // MAX_CONCURRENT + 1} 批文件")
        print(f"本次上传 {len(files)} 个文件: {', '.join(files[:5])}" + (f" 等{len(files)}个文件" if len(files) > 5 else ""))
        print(f"{'='*60}")
        
        # 计算预估等待时间
        wait_time = self.calculate_wait_time(files)
        
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
            futures = {executor.submit(self.send_single_copy_command, filename): filename 
                      for filename in files}
            
            for future in as_completed(futures):
                filename = futures[future]
                try:
                    result_filename, success, error_msg = future.result()
                    
                    with self.lock:
                        if success:
                            self.uploaded_files.add(result_filename)
                        else:
                            self.failed_files.add(result_filename)
                            
                except Exception as e:
                    print(f"文件 {filename} 上传异常: {e}")
                    with self.lock:
                        self.failed_files.add(filename)
        
        # 移除处理中的文件
        with self.lock:
            for filename in files:
                if filename in self.processing_files:
                    self.processing_files.remove(filename)
        
        return wait_time
    
    def display_progress(self, all_files, round_num):
        """显示进度信息"""
        with self.lock:
            uploaded = len(self.uploaded_files)
            failed = len(self.failed_files)
            processing = len(self.processing_files)
        
        total_files = len(all_files)
        remaining = total_files - uploaded - failed
        
        elapsed_time = time.time() - self.start_time
        
        print(f"\n{'='*60}")
        print(f"第 {round_num} 轮上传进度")
        print(f"{'='*60}")
        print(f"总文件数: {total_files}")
        print(f"已上传成功: {uploaded} 个")
        print(f"上传失败: {failed} 个")
        print(f"正在处理: {processing} 个")
        print(f"剩余文件: {remaining} 个")
        print(f"已用时: {elapsed_time:.1f} 秒 ({elapsed_time/60:.1f} 分钟)")
        
        # 显示上传速度
        try:
            speed = self.get_upload_speed(interval=2)
            print(f"当前上传速度: {speed:.2f} MB/s")
        except:
            pass
        
        if failed:
            print(f"\n失败文件: {list(self.failed_files)[:10]}")
            if len(self.failed_files) > 10:
                print(f"... 还有 {len(self.failed_files) - 10} 个失败文件")
        
        print(f"{'='*60}\n")
    
    def run(self):
        # 1. 获取源目录所有文件
        all_files = []
        for f in os.listdir(SOURCE_DIR):
            if os.path.isfile(os.path.join(SOURCE_DIR, f)):
                all_files.append(f)
        
        if not all_files:
            print("没有找到文件")
            return
        
        print(f"找到 {len(all_files)} 个文件")
        
        total_files = len(all_files)
        round_num = 1
        consecutive_success_checks = 0  # 连续成功检查次数
        
        # 先检查是否已经有部分文件上传了
        print("正在检查目标目录现有文件...")
        missing_files, target_files = self.check_all_files_exist(all_files)
        
        if not missing_files:
            print("所有文件都已存在于目标目录，无需上传！")
            return
        
        print(f"需要上传 {len(missing_files)} 个文件")
        print(f"目标目录已有 {len(target_files)} 个文件")
        
        # 初始化待上传文件
        remaining_files = missing_files.copy()
        
        # 开始定期检查线程
        stop_checking = False
        check_thread = None
        
        def periodic_check():
            """每10秒检查一次文件状态"""
            check_count = 0
            while not stop_checking:
                try:
                    missing, target = self.check_all_files_exist(all_files)
                    check_count += 1
                    
                    if not missing:
                        print(f"\n[定时检查 {check_count}] ✅ 验证通过：所有文件都已存在于目标目录")
                    else:
                        print(f"\n[定时检查 {check_count}] ⚠️ 仍有 {len(missing)} 个文件缺失")
                        if len(missing) <= 10:
                            for filename in missing:
                                print(f"  ✗ {filename}")
                        else:
                            for filename in missing[:5]:
                                print(f"  ✗ {filename}")
                            print(f"  ... 还有 {len(missing) - 5} 个缺失文件")
                    
                    # 显示实时上传速度
                    try:
                        speed = self.get_upload_speed(interval=1)
                        print(f"[定时检查 {check_count}] 当前上传速度: {speed:.2f} MB/s")
                    except:
                        pass
                        
                except Exception as e:
                    print(f"[定时检查 {check_count}] 检查出错: {e}")
                
                # 等待10秒
                for i in range(10):
                    if stop_checking:
                        break
                    time.sleep(1)
        
        # 启动定时检查线程
        check_thread = threading.Thread(target=periodic_check, daemon=True)
        check_thread.start()
        print("\n已启动定时检查，每10秒检查一次文件上传状态...\n")
        
        try:
            while True:
                # 检查是否所有文件都已上传
                missing_files, target_files = self.check_all_files_exist(all_files)
                
                if not missing_files:
                    consecutive_success_checks += 1
                    print(f"\n✓ 第 {consecutive_success_checks} 次检查通过：所有文件已存在于目标目录")
                    
                    # 连续3次检查都通过才认为真正完成
                    if consecutive_success_checks >= 1:
                        print("\n✅ 所有文件确认已上传到目标目录！")
                        break
                else:
                    consecutive_success_checks = 0  # 重置成功计数
                    remaining_files = missing_files
                
                # 如果没有剩余文件，等待后继续检查
                if not remaining_files:
                    print(f"\n等待 {MIN_WAIT_TIME} 秒后再次检查...")
                    # 等待期间也显示速度
                    for i in range(MIN_WAIT_TIME):
                        time.sleep(1)
                        if i % 5 == 0:  # 每5秒显示一次速度
                            try:
                                speed = self.get_upload_speed(interval=1)
                                print(f"等待中... {MIN_WAIT_TIME-i:.0f}秒后检查 [速度: {speed:.2f} MB/s]")
                            except:
                                print(f"等待中... {MIN_WAIT_TIME-i:.0f}秒后检查")
                    continue
                
                # 选择最多5个文件上传
                with self.lock:
                    batch_files = []
                    for filename in remaining_files:
                        if filename not in self.processing_files and filename not in self.uploaded_files:
                            batch_files.append(filename)
                            if len(batch_files) >= MAX_CONCURRENT:
                                break
                
                if not batch_files:
                    print("\n没有可上传的文件，等待后继续检查...")
                    for i in range(MIN_WAIT_TIME):
                        time.sleep(1)
                        if i % 5 == 0:  # 每5秒显示一次速度
                            try:
                                speed = self.get_upload_speed(interval=1)
                                print(f"等待中... {MIN_WAIT_TIME-i:.0f}秒后检查 [速度: {speed:.2f} MB/s]")
                            except:
                                print(f"等待中... {MIN_WAIT_TIME-i:.0f}秒后检查")
                    continue
                
                # 标记为处理中
                with self.lock:
                    for filename in batch_files:
                        self.processing_files.add(filename)
                
                # 上传这批文件
                wait_time = self.upload_batch(batch_files)
                
                # 显示进度
                self.display_progress(all_files, round_num)
                
                # 等待下一轮
                print(f"\n等待 {wait_time:.0f} 秒后进行下一轮上传或检查...")
                
                # 显示等待倒计时，每5秒显示速度
                for i in range(int(wait_time)):
                    time.sleep(1)
                    remaining = wait_time - i - 1
                    
                    # 每5秒显示一次速度
                    if i % 5 == 0:
                        try:
                            speed = self.get_upload_speed(interval=1)
                            print(f"等待中... {remaining:.0f}秒后继续 [速度: {speed:.2f} MB/s]")
                        except:
                            print(f"等待中... {remaining:.0f}秒后继续")
                
                round_num += 1
                
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
        except Exception as e:
            print(f"\n\n程序发生错误: {e}")
        finally:
            # 停止定时检查线程
            stop_checking = True
            if check_thread and check_thread.is_alive():
                check_thread.join(timeout=2)
        
        # 最终统计
        elapsed_time = time.time() - self.start_time
        
        print(f"\n{'='*60}")
        print(f"上传完成！")
        print(f"{'='*60}")
        print(f"总文件数: {total_files}")
        print(f"成功上传: {len(self.uploaded_files)} 个")
        print(f"上传失败: {len(self.failed_files)} 个")
        print(f"总耗时: {elapsed_time:.1f} 秒 ({elapsed_time/60:.1f} 分钟)")
        
        # 计算总文件大小和平均速度
        total_size = 0
        for filename in all_files:
            total_size += self.get_file_size(filename)
        
        size_gb = total_size / (1024 * 1024 * 1024)
        avg_speed_mb = (size_gb * 1024) / elapsed_time if elapsed_time > 0 else 0
        
        print(f"总大小: {size_gb:.2f} GB")
        print(f"平均速度: {avg_speed_mb:.2f} MB/秒")
        
        # 最终验证
        print("\n最终验证...")
        missing_files, target_files = self.check_all_files_exist(all_files)
        if not missing_files:
            print("✅ 验证通过：所有文件都已存在于目标目录")
        else:
            print(f"⚠️ 验证失败：仍有 {len(missing_files)} 个文件缺失")
            for filename in missing_files[:10]:
                print(f"  ✗ {filename}")
            if len(missing_files) > 10:
                print(f"  ... 还有 {len(missing_files) - 10} 个缺失文件")
        
        print(f"{'='*60}")
        

def main():
    if len(sys.argv) < 2:
        print(f"使用方法: {sys.argv[0]} <目标目录>")
        print(f"例如: {sys.argv[0]} /DC大叔2019/根目录/")
        sys.exit(1)
    
    target_dir = sys.argv[1]
    print(f"源目录: {SOURCE_DIR}")
    print(f"目标目录: {target_dir}")
    
    uploader = FileUploader(target_dir)
    uploader.run()

if __name__ == "__main__":
    main()
