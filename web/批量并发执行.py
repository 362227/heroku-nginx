#列出目录文件绝对路径 ls /mnt/g/LIVE/TX/下载文件夹/CVC/ | sed "s:^:/mnt/g/LIVE/TX/下载文件夹/CVC/:"
import pty
import subprocess
import threading
import os
import time
import shlex

dir = '/var/www/html/tx/'
file_list = os.listdir(dir)


def run_command(command):
    master_fd, slave_fd = pty.openpty()
    process = subprocess.Popen(command, shell=True, stdout=slave_fd, stderr=subprocess.STDOUT)
    while process.poll() is None:
        try:
            output = os.read(master_fd, 1024).decode()
            if output:
                print(f"\r{output.strip()}", end='', flush=True)
        except OSError:
            break
        time.sleep(3)
    os.close(master_fd)
    os.close(slave_fd)


def run_commands(commands):
    threads = []
    for command in commands:
        while threading.active_count() > 5:
            continue
        thread = threading.Thread(target=run_command, args=(command,))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()


def main():
    commands = [
    f"python /usr/local/bin/fake115upload.py -u {shlex.quote(dir + file)} -c 2588129333331541770"
        for file in file_list
    ]
    run_commands(commands)


if __name__ == "__main__":
    main()

