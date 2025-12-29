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
    
    def get_upload_speed(self, interval=5):
        """监控上传速度，每interval秒显示一次"""
        while self.speed_monitor_running:
            try:
                net_io_before = psutil.net_io_counters(pernic=True)
                bytes_sent_before = 0
                for iface, stats in net_io_before.items():
                    if iface != 'lo':  # 排除本地回环接口
                        bytes_sent_before += stats.bytes_sent
                
                time.sleep(interval)
                
                net_io_after = psutil.net_io_counters(pernic=True)
                bytes_sent_after = 0
                for iface, stats in net_io_after.items():
                    if iface != 'lo':  # 排除本地回环接口
                        bytes_sent_after += stats.bytes_sent
                
                bytes_per_sec = (bytes_sent_after - bytes_sent_before) / interval
                mb_per_sec = bytes_per_sec / (1024 * 1024)
                
                print(f"上传速度: {mb_per_sec:.2f} MB/s")
                
            except Exception as e:
                print(f"速度监控出错: {e}")
                break
    
    def start_speed_monitor(self):
        """启动速度监控线程"""
        self.speed_monitor_running = True
        self.upload_speed_thread = threading.Thread(
            target=self.get_upload_speed,
            args=(5,)  # 每5秒显示一次
        )
        self.upload_speed_thread.daemon = True
        self.upload_speed_thread.start()
        print("速度监控已启动，每5秒显示一次上传速度")
    
    def stop_speed_monitor(self):
        """停止速度监控"""
        self.speed_monitor_running = False
        if self.upload_speed_thread:
            self.upload_speed_thread.join(timeout=2)
    
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
        """监控rclone输出，检查是否成功"""
        if not self.rclone_process:
            return False
        
        output_lines = []
        
        # 实时读取输出
        for line in iter(self.rclone_process.stdout.readline, ''):
            line = line.strip()
            if line:
                output_lines.append(line)
                print(f"rclone: {line}")
        
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
            
            # 强制刷新目标目录
            print("\n强制刷新目标目录...")
            self.refresh_target_directory()
            print("目标目录刷新完成\n")
            
            # 启动速度监控
            self.start_speed_monitor()
            
            # 启动rclone进程
            print("启动rclone上传...")
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
