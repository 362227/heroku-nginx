import psutil
import time
import sys
from collections import defaultdict

def get_upload_speed_once(process_name="fake115uploader"):
    """获取当前上传速度（只计算一次）"""
    try:
        # 查找目标进程
        target_pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    target_pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                continue
        
        if not target_pids:
            print("0.00")
            return
        
        # 第一次获取数据
        first_data = {}
        for pid in target_pids:
            try:
                # Linux系统：读取/proc文件系统获取网络统计
                with open(f"/proc/{pid}/net/dev", "r") as f:
                    total_tx = 0
                    for line in f.readlines()[2:]:  # 跳过前两行标题
                        parts = line.strip().split()
                        if len(parts) >= 10:
                            tx_bytes = int(parts[9])  # 发送字节数在第9列
                            total_tx += tx_bytes
                    first_data[pid] = (total_tx, time.time())
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                first_data[pid] = (0, time.time())
        
        # 等待一小段时间
        time.sleep(1)
        
        # 第二次获取数据
        total_speed = 0
        for pid in target_pids:
            try:
                # 获取第二次数据
                with open(f"/proc/{pid}/net/dev", "r") as f:
                    total_tx = 0
                    for line in f.readlines()[2:]:
                        parts = line.strip().split()
                        if len(parts) >= 10:
                            tx_bytes = int(parts[9])
                            total_tx += tx_bytes
                    
                # 计算速度
                if pid in first_data:
                    old_bytes, old_time = first_data[pid]
                    time_diff = time.time() - old_time
                    if time_diff > 0:
                        speed = (total_tx - old_bytes) / time_diff / 1024  # KB/s
                        total_speed += speed
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
        
        print(f"{total_speed:.2f}")
        
    except Exception as e:
        print("0.00")

def get_upload_speed_by_connections_once(process_name="fake115uploader"):
    """通过连接信息获取当前上传速度（只计算一次，跨平台）"""
    try:
        # 查找目标进程
        target_pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    target_pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                continue
        
        if not target_pids:
            print("0.00")
            return
        
        # 方法1：使用psutil的网络连接统计（需要root/admin权限）
        conn_stats = {}
        for pid in target_pids:
            try:
                proc = psutil.Process(pid)
                connections = proc.connections()
                total_bytes = 0
                
                # 获取每个连接的统计信息
                for conn in connections:
                    if hasattr(conn, 'bytes_sent'):
                        total_bytes += conn.bytes_sent
                
                conn_stats[pid] = (total_bytes, time.time())
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                conn_stats[pid] = (0, time.time())
        
        # 等待一小段时间
        time.sleep(1)
        
        # 第二次获取
        total_speed = 0
        for pid in target_pids:
            try:
                proc = psutil.Process(pid)
                connections = proc.connections()
                total_bytes = 0
                
                for conn in connections:
                    if hasattr(conn, 'bytes_sent'):
                        total_bytes += conn.bytes_sent
                
                if pid in conn_stats:
                    old_bytes, old_time = conn_stats[pid]
                    time_diff = time.time() - old_time
                    if time_diff > 0:
                        speed = (total_bytes - old_bytes) / time_diff / 1024  # KB/s
                        total_speed += speed
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                continue
        
        if total_speed <= 0:
            # 尝试使用系统级网络统计
            import platform
            system = platform.system()
            
            if system == "Linux":
                # Linux: 读取系统级网络统计
                with open("/proc/net/dev", "r") as f:
                    lines = f.readlines()
                    tx1 = 0
                    for line in lines[2:]:
                        parts = line.strip().split()
                        if len(parts) >= 10:
                            tx1 += int(parts[9])  # 发送字节
                
                time.sleep(1)
                
                with open("/proc/net/dev", "r") as f:
                    lines = f.readlines()
                    tx2 = 0
                    for line in lines[2:]:
                        parts = line.strip().split()
                        if len(parts) >= 10:
                            tx2 += int(parts[9])
                
                total_speed = (tx2 - tx1) / 1024  # KB/s
            
            elif system == "Darwin":  # macOS
                import subprocess
                # 获取网络统计
                result1 = subprocess.run(["netstat", "-b"], capture_output=True, text=True)
                time.sleep(1)
                result2 = subprocess.run(["netstat", "-b"], capture_output=True, text=True)
                # 这里需要解析netstat输出，实际实现会更复杂
        
        print(f"{total_speed:.2f}")
        
    except Exception as e:
        print("0.00")

def get_upload_speed_simple(process_name="fake115uploader"):
    """简化版本 - 获取当前上传速度（只运行一次）"""
    try:
        # 第一次测量
        net_io1 = psutil.net_io_counters()
        bytes_sent1 = net_io1.bytes_sent
        
        time.sleep(1)  # 等待1秒
        
        # 第二次测量
        net_io2 = psutil.net_io_counters()
        bytes_sent2 = net_io2.bytes_sent
        
        # 计算速度
        speed = (bytes_sent2 - bytes_sent1) / 1024  # KB/s
        print(f"{speed:.2f}")
        
    except Exception as e:
        print("0.00")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_name = sys.argv[1]
    else:
        process_name = "fake115uploader"
    
    # 选择其中一种方法运行（推荐第一种）
    get_upload_speed_once(process_name)