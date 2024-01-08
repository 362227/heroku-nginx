import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


# 代理
proxy = {'http': 'http://127.0.0.1:1083', 'https': 'http://127.0.0.1:1083'}

urls = [
    "https://kacey1--doyathing9.无效2023-05-18.co",
    "https://ladymamalade-9-1-ladymamalade9.replit.app",
    "https://ladymamalade-9-2-ladymamalade9.replit.app",
    "https://ladymamalade-9-3-ladymamalade9.replit.app",
    "https://ladymamalade-9-4-ladymamalade9.replit.app",
    "https://ladymamalade-9-5-ladymamalade9.replit.app",
    "https://ladymamalade-9-6-ladymamalade9.replit.app",
    "https://ladymamalade-9-7-ladymamalade9.replit.app",
    "https://ladymamalade-9-8-ladymamalade9.replit.app",
    "https://ladymamalade-9-9-ladymamalade9.replit.app",
    "https://ladymamalade-9-10-ladymamalade9.replit.app",
    "https://ladymamalade-9-11-ladymamalade9.replit.app",
    "https://ladymamalade-9-12-ladymamalade9.replit.app",
    "https://ladymamalade-9-13-ladymamalade9.replit.app",
    "https://ladymamalade-9-14-ladymamalade9.replit.app",
    "https://ladymamalade-9-15-ladymamalade9.replit.app",
    "https://ladymamalade-9-16-ladymamalade9.replit.app",
    "https://ladymamalade-9-17-ladymamalade9.replit.app",
] 



while True:
    # 记录成功的链接
    successful_urls = []

    def request_url(url):
        retry = 0
        while True:
            try:
                new_url = f"{url}/vimeo.php?link=https://player.vimeo.com/video/211"
                response = requests.get(new_url, timeout=8)
                if response.status_code == 200 and 'gutierrez' in response.text:
                    print(f'{new_url} returned 200')
                    successful_urls.append(url)
                    return None  # 返回None表示成功
                else:
                    print(f'{new_url} returned {response.status_code}')
                    if retry < 2:
                        retry += 1
                        print(f'{new_url} retrying {retry}/2')
                    else:
                        break
            except requests.exceptions.RequestException as e:
                print(f'{new_url} failed: {e}')
                if retry < 2:
                    retry += 1
                    print(f'{new_url} retrying {retry}/2')
                else:
                    break
            time.sleep(1)  # 等待1秒后重试

    # 使用线程池并发请求
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(request_url, url) for url in urls]
        # 等待所有请求完成
        for _ in as_completed(futures):
            pass

    # 将成功的链接写入文件
    if len(successful_urls) >= 140:
        with open('/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/urls.txt', 'w') as f:
            for url in successful_urls:
                f.write(url + '\n')
        print("以下链接未成功写入urls.txt:")
        print(set(urls) - set(successful_urls))
    else:
        print('Successful URLs less than 40, skipped writing to file.')

    # 如果所有链接都成功，则退出循环
    if set(successful_urls) == set(urls):
        print("All URLs succeeded!")
        break

    # 休眠一段时间后再次尝试
    print("一轮结束")
    print(len(successful_urls))
    time.sleep(4)
    os.system('clear')
