import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 代理
proxy = {'http': 'http://127.0.0.1:1086', 'https': 'http://127.0.0.1:1086'}

# 需要尝试的链接列表
urls = [
    "https://vimeo362227.onrender.com",
    "https://vimeo362227-1.onrender.com",
    "https://vimeo362227-2.onrender.com",
    "https://vimeo362227-3.onrender.com",
    "https://vimeo362227-4.onrender.com",
    "https://vimeo362227-5.onrender.com",
    "https://vimeo362227-6.onrender.com",
    "https://vimeo362227-7.onrender.com",
    "https://vimeo362227-8.onrender.com",
    "https://vimeo362227-9.onrender.com",
    "https://vimeo362227-10.onrender.com",
    "https://vimeo362227-11.onrender.com",
    "https://vimeo362227-12.onrender.com",
    "https://vimeo362227-13.onrender.com",
    "https://vimeo362227-14.onrender.com",
    "https://vimeo362227-15.onrender.com",
    "https://vimeo362227-16.onrender.com",
    "https://vimeo362227-17.onrender.com",
    "https://vimeo362227-18.onrender.com",
    "https://vimeo362227-19-7hgu.onrender.com",
    "https://vimeo362227-20.onrender.com",
    "https://vimeo362227-21.onrender.com",
    "https://vimeo362227-22.onrender.com",
    "https://vimeo362227-23.onrender.com",
    "https://vimeo362227-24.onrender.com",
    "https://vimeo362227-25.onrender.com",
    "https://vimeo362227-26.onrender.com",
    "https://vimeo362227-27.onrender.com",
    "https://vimeo362227-28.onrender.com",
    "https://vimeo362227-29.onrender.com",
    "https://ellie001.onrender.com",
    "https://ellie002.onrender.com",
    "https://ellie003.onrender.com",
    "https://ellie004.onrender.com",
    "https://ellie006.onrender.com",
    "https://ellie005.onrender.com",
    "https://ellie010.onrender.com",
    "https://ellie007.onrender.com",
    "https://ellie008.onrender.com",
    "https://ellie009.onrender.com",
    "https://kai005.onrender.com",
    "https://kai006.onrender.com"
]


while True:
    # 记录成功的链接
    successful_urls = []

    def request_url(url):
        retry = 0
        while True:
            try:
                response = requests.get(url, timeout=20)
                #response = requests.get(url, proxies=proxy, timeout=20)
                if response.status_code == 200:
                    print(f'{url} returned 200')
                    successful_urls.append(url)
                    return None  # 返回None表示成功
                else:
                    print(f'{url} returned {response.status_code}')
            except requests.exceptions.RequestException as e:
                if isinstance(e, requests.exceptions.Timeout) and retry < 10:
                    retry += 1
                    print(f'{url} timed out, retrying {retry}/10')
                else:
                    print(f'{url} failed: {e}')
                    break
            time.sleep(1)  # 等待1秒后重试

    # 使用线程池并发请求
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(request_url, url) for url in urls]
        # 等待所有请求完成
        for _ in as_completed(futures):
            pass

    # 将成功的链接写入文件
    with open('/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/urls.txt', 'w') as f:
        for url in successful_urls:
            f.write(url + '\n')

    # 休眠一段时间后再次尝试
    print("一轮结束")
    time.sleep(10)

