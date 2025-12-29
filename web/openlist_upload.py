import sys
import subprocess
import time
import psutil
import threading
import signal
import os
import re

class RcloneUploader:
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.rclone_process = None
        self.speed_monitor_running = False
        self.upload_speed_thread = None
        self.max_retries = 5
        self.current_retry = 0
        
        # 进度估算相关变量
        self.total_size_bytes = 0  # 总文件大小（字节）
        self.estimated_transferred = 0  # 估算已传输字节数
        self.last_speed_check_time = 0  # 上次速度检查时间
        self.last_bytes_sent = 0  # 上次发送的字节数
        self.upload_start_time = 0  # 上传开始时间
        self.progress_last_display = 0  # 上次显示进度的时间
        
    def refresh_target_directory(self):
        """执行rclone lsd强制刷新目标目录"""
        # 确保目标目录格式正确
        if not self.target_dir.startswith('/'):
            target_path = f"/{self.target_dir}"
        else:
            target_path = self.target_dir
            
        refresh_command = [
            'rclone', 'lsd', f'dav:/bd{target_path}',
            '--config=/usr/local/bin/rclone.conf'
        ]
        
        print(f"正在刷新目标目录: {' '.join(refresh_command)}")
        
        try:
            # 执行刷新命令
            refresh_process = subprocess.Popen(
                refresh_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # 等待命令完成
            stdout, stderr = refresh_process.communicate()
            return_code = refresh_process.returncode
            
            print(f"目录刷新完成，返回码: {return_code}")
            
            # 无论成功还是失败都只打印提示，不中断流程
            if stdout.strip():
                print(f"刷新输出: {stdout.strip()}")
            if stderr.strip():
                print(f"刷新错误: {stderr.strip()}")
                
            print("目标目录刷新完成，继续上传流程...")
            
        except Exception as e:
            print(f"刷新目录时出错: {e}")
            print("继续上传流程...")
    
    def parse_size_string(self, size_str):
        """解析大小字符串为字节数"""
        # 示例: "7 GiB", "500 MiB", "2.5 GB"等
        size_str = size_str.strip().upper()
        
        # 定义单位转换
        units = {
            'B': 1,
            'KB': 1000,
            'MB': 1000 * 1000,
            'GB': 1000 * 1000 * 1000,
            'TB': 1000 * 1000 * 1000 * 1000,
            'KIB': 1024,
            'MIB': 1024 * 1024,
            'GIB': 1024 * 1024 * 1024,
            'TIB': 1024 * 1024 * 1024 * 1024
        }
        
        # 提取数字和单位
        for unit in sorted(units.keys(), key=len, reverse=True):
            if size_str.endswith(unit):
                number = float(size_str[:-len(unit)].strip())
                return int(number * units[unit])
        
        # 如果没有单位，尝试直接解析为数字
        try:
            return int(float(size_str))
        except:
            return 0
    
    def extract_total_size_from_line(self, line):
        """从rclone的输出行中提取总文件大小"""
        # 示例: rclone: Transferred: 0 B / 7 GiB, 0%, 0 B/s, ETA -
        pattern = r'Transferred:\s*[\d\.]+\s*\w*\s*/\s*([\d\.]+\s*\w*)'
        match = re.search(pattern, line)
        
        if match:
            total_size_str = match.group(1)
            return self.parse_size_string(total_size_str)
        
        return 0
    
    def get_upload_speed_and_estimate_progress(self):
        """监控上传速度并估算进度"""
        # 初始化网络统计
        net_io_before = psutil.net_io_counters(pernic=True)
        self.last_bytes_sent = 0
        for iface, stats in net_io_before.items():
            if iface != 'lo':  # 排除本地回环接口
                self.last_bytes_sent += stats.bytes_sent
        
        self.last_speed_check_time = time.time()
        self.upload_start_time = time.time()
        
        while self.speed_monitor_running:
            try:
                # 计算当前速度
                net_io_current = psutil.net_io_counters(pernic=True)
                current_bytes_sent = 0
                for iface, stats in net_io_current.items():
                    if iface != 'lo':
                        current_bytes_sent += stats.bytes_sent
                
                current_time = time.time()
                time_diff = current_time - self.last_speed_check_time
                
                if time_diff > 0:
                    # 计算速度（字节/秒）
                    bytes_diff = current_bytes_sent - self.last_bytes_sent
                    speed_bps = bytes_diff / time_diff
                    speed_mbps = speed_bps / (1024 * 1024)
                    
                    # 更新已传输字节数的估算
                    self.estimated_transferred += bytes_diff
                    
                    # 更新记录
                    self.last_bytes_sent = current_bytes_sent
                    self.last_speed_check_time = current_time
                    
                    # 每5秒显示一次详细进度
                    current_time_for_display = time.time()
                    if current_time_for_display - self.progress_last_display >= 5:
                        self.progress_last_display = current_time_for_display
                        
                        # 显示上传速度
                        print(f"📊 实时上传速度: {speed_mbps:.2f} MB/s")
                        
                        # 显示估算进度
                        if self.total_size_bytes > 0:
                            elapsed_time = current_time_for_display - self.upload_start_time
                            estimated_percentage = (self.estimated_transferred / self.total_size_bytes) * 100
                            
                            # 确保百分比不超过100%
                            if estimated_percentage > 100:
                                estimated_percentage = 100
                            
                            # 计算剩余时间和估算速度
                            if speed_bps > 0:
                                remaining_bytes = self.total_size_bytes - self.estimated_transferred
                                if remaining_bytes > 0:
                                    eta_seconds = remaining_bytes / speed_bps
                                    
                                    # 格式化时间显示
                                    if eta_seconds < 60:
                                        eta_str = f"{int(eta_seconds)}秒"
                                    elif eta_seconds < 3600:
                                        eta_str = f"{int(eta_seconds/60)}分{int(eta_seconds%60)}秒"
                                    else:
                                        hours = int(eta_seconds/3600)
                                        minutes = int((eta_seconds%3600)/60)
                                        eta_str = f"{hours}小时{minutes}分"
                                    
                                    # 格式化已传输和总大小
                                    transferred_mb = self.estimated_transferred / (1024 * 1024)
                                    total_mb = self.total_size_bytes / (1024 * 1024)
                                    
                                    print(f"📈 估算进度: {estimated_percentage:.1f}% ({transferred_mb:.1f} MB / {total_mb:.1f} MB)")
                                    print(f"⏱️  预计剩余时间: {eta_str}")
                                else:
                                    print("✅ 上传完成（估算）")
                            else:
                                transferred_mb = self.estimated_transferred / (1024 * 1024)
                                total_mb = self.total_size_bytes / (1024 * 1024)
                                print(f"📈 估算进度: {estimated_percentage:.1f}% ({transferred_mb:.1f} MB / {total_mb:.1f} MB)")
                        
                        print("-" * 50)
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                print(f"速度监控出错: {e}")
                break
    
    def start_speed_monitor(self):
        """启动速度监控和进度估算线程"""
        self.speed_monitor_running = True
        self.upload_speed_thread = threading.Thread(
            target=self.get_upload_speed_and_estimate_progress
        )
        self.upload_speed_thread.daemon = True
        self.upload_speed_thread.start()
        print("速度监控和进度估算已启动")
    
    def stop_speed_monitor(self):
        """停止速度监控"""
        self.speed_monitor_running = False
        if self.upload_speed_thread:
            self.upload_speed_thread.join(timeout=2)
        
        # 显示最终估算结果
        if self.total_size_bytes > 0:
            elapsed_time = time.time() - self.upload_start_time
            estimated_percentage = (self.estimated_transferred / self.total_size_bytes) * 100
            if estimated_percentage > 100:
                estimated_percentage = 100
            
            transferred_mb = self.estimated_transferred / (1024 * 1024)
            total_mb = self.total_size_bytes / (1024 * 1024)
            
            print(f"\n📊 最终估算结果:")
            print(f"   总用时: {elapsed_time:.1f}秒")
            print(f"   估算总进度: {estimated_percentage:.1f}%")
            print(f"   估算传输量: {transferred_mb:.1f} MB / {total_mb:.1f} MB")
            
            if elapsed_time > 0:
                avg_speed_mbps = self.estimated_transferred / elapsed_time / (1024 * 1024)
                print(f"   平均速度: {avg_speed_mbps:.2f} MB/s")
    
    def run_rclone_command(self):
        """执行rclone命令"""
        # 确保目标目录格式正确
        if not self.target_dir.startswith('/'):
            target_path = f"/{self.target_dir}"
        else:
            target_path = self.target_dir
            
        command = [
            'rclone', 'copy', 'dav:/tx', f'dav:/bd{target_path}',
            '--include=*.*',
            '--config=/usr/local/bin/rclone.conf',
            '--max-depth=1', 
            '-v',  # 详细输出
            '--stats=6s'  # 6秒显示一次统计
        ]
        
        print(f"执行命令: {' '.join(command)}")
        
        try:
            self.rclone_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )
            
            return self.rclone_process
            
        except Exception as e:
            print(f"执行rclone命令失败: {e}")
            return None
    
    def check_if_copied_successful(self, output_lines):
        """检查输出中是否有Copied成功的标志或Checks 100%完成"""
        for line in output_lines:
            # 检查是否包含Copied
            if 'Copied' in line:
                # 提取数字，检查是否复制了文件
                match = re.search(r'Copied:\s*(\d+)', line)
                if match:
                    copied_count = int(match.group(1))
                    if copied_count > 0:
                        print(f"检测到Copied成功: {copied_count}个文件")
                        return True
                else:
                    # 如果没有数字，只要有Copied就认为是成功的尝试
                    print("检测到Copied字样")
                    return True
            
            # 检查是否包含"Checks:"和"100%"在同一行
            # 使用正则表达式确保"Checks:"和"100%"在同一行
            checks_pattern = r'Checks:.*100%'
            if re.search(checks_pattern, line):
                print(f"检测到Checks 100%完成: {line}")
                return True
            

        
        return False
    
    def monitor_rclone_output(self):
        """监控rclone输出，检查是否成功并提取总文件大小"""
        if not self.rclone_process:
            return False
        
        output_lines = []
        total_size_extracted = False
        
        # 实时读取输出
        for line in iter(self.rclone_process.stdout.readline, ''):
            line = line.strip()
            if line:
                output_lines.append(line)
                print(f"rclone: {line}")
                
                # 尝试从Transferred行提取总文件大小
                if not total_size_extracted and 'Transferred:' in line:
                    total_size = self.extract_total_size_from_line(line)
                    if total_size > 0:
                        self.total_size_bytes = total_size
                        total_size_extracted = True
                        total_gb = total_size / (1024 * 1024 * 1024)
                        print(f"📁 检测到总文件大小: {total_gb:.2f} GB ({total_size} 字节)")
        
        # 等待进程结束
        return_code = self.rclone_process.wait()
        print(f"rclone进程结束，返回码: {return_code}")
        
        # 检查是否有Copied成功的标志或Checks 100%完成
        has_copied = self.check_if_copied_successful(output_lines)
        
        if has_copied:
            print("✅ 检测到Copied或Checks 100%，上传成功！")
            return True
        else:
            print("❌ 未检测到Copied或Checks 100%，上传失败！")
            return False
    
    def upload(self):
        """主上传方法，支持重试"""
        while self.current_retry < self.max_retries:
            self.current_retry += 1
            print(f"\n{'='*60}")
            print(f"开始上传尝试 {self.current_retry}/{self.max_retries}")
            print(f"{'='*60}")
            
            # 重置进度估算变量
            self.total_size_bytes = 0
            self.estimated_transferred = 0
            self.progress_last_display = 0
            
            # 强制刷新目标目录
            print("\n强制刷新目标目录...")
            self.refresh_target_directory()
            print("目标目录刷新完成\n")
            
            # 启动速度监控和进度估算
            self.start_speed_monitor()
            
            # 启动rclone进程
            print("启动rclone上传...")
            print("注意：由于特殊配置，rclone显示的速度可能为0，将使用网络监控估算进度")
            process = self.run_rclone_command()
            
            if not process:
                print("❌ rclone进程启动失败")
                self.stop_speed_monitor()
                continue
            
            # 监控输出并检查结果
            success = self.monitor_rclone_output()
            
            # 停止速度监控
            self.stop_speed_monitor()
            
            # 检查结果
            if success:
                print("✅ 文件已上传成功！")
                return True
            else:
                print(f"❌ 上传失败")
                if self.current_retry < self.max_retries:
                    print(f"等待3秒后重试... ({self.current_retry + 1}/{self.max_retries})")
                    time.sleep(3)  # 等待3秒后重试
                else:
                    print(f"已达到最大重试次数({self.max_retries})")
        
        print(f"\n❌ 上传失败，已达到最大重试次数({self.max_retries})")
        return False
    
    def cleanup(self):
        """清理资源"""
        self.stop_speed_monitor()
        if self.rclone_process and self.rclone_process.poll() is None:
            print("终止rclone进程...")
            self.rclone_process.terminate()
            try:
                self.rclone_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.rclone_process.kill()
                self.rclone_process.wait()


def signal_handler(signum, frame):
    """处理中断信号"""
    print("\n收到中断信号，正在清理...")
    if 'uploader' in globals():
        uploader.cleanup()
    sys.exit(0)


def main():
    if len(sys.argv) < 2:
        print(f"使用方法: {sys.argv[0]} <目标目录>")
        print(f"例如: {sys.argv[0]} /DC大叔2019/根目录/")
        sys.exit(1)
    
    target_dir = sys.argv[1]
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建上传器并执行
    global uploader
    uploader = RcloneUploader(target_dir)
    
    try:
        success = uploader.upload()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"上传过程中发生错误: {e}")
        uploader.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
