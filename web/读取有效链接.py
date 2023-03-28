import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 代理
proxy = {'http': 'http://127.0.0.1:1086', 'https': 'http://127.0.0.1:1086'}

# 需要尝试的链接列表
'''
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
'''

urls = [
    "https://vimeo362227-0001.onrender.com",
    "https://vimeo362227-0002.onrender.com",
    "https://vimeo362227-0003.onrender.com",
    "https://vimeo362227-0004.onrender.com",
    "https://vimeo362227-0005.onrender.com",
    "https://vimeo362227-0006.onrender.com",
    "https://vimeo362227-0007.onrender.com",
    "https://vimeo362227-0008.onrender.com",
    "https://vimeo362227-0009.onrender.com",
    "https://vimeo362227-0010.onrender.com",
    "https://vimeo362227-0011.onrender.com",
    "https://vimeo362227-0012.onrender.com",
    "https://vimeo362227-0013.onrender.com",
    "https://vimeo362227-0014.onrender.com",
    "https://vimeo362227-0015.onrender.com",
    "https://vimeo362227-0016.onrender.com",
    "https://vimeo362227-0017.onrender.com",
    "https://vimeo362227-0018.onrender.com",
    "https://vimeo362227-0019.onrender.com",
    "https://vimeo362227-0020.onrender.com",
    "https://vimeo362227-0021.onrender.com",
    "https://vimeo362227-0022.onrender.com",
    "https://vimeo362227-0023.onrender.com",
    "https://vimeo362227-0024.onrender.com",
    "https://vimeo362227-0025.onrender.com",
    "https://vimeo362227-0026.onrender.com",
    "https://vimeo362227-0027.onrender.com",
    "https://vimeo362227-0028.onrender.com",
    "https://vimeo362227-0029.onrender.com",
    
    "https://vimeo362227-30.onrender.com",
    "https://vimeo362227-31.onrender.com",
    "https://vimeo362227-32.onrender.com",
    "https://vimeo362227-33.onrender.com",
    "https://vimeo362227-34.onrender.com",
    "https://vimeo362227-35.onrender.com",
    "https://vimeo362227-36.onrender.com",
    "https://vimeo362227-37.onrender.com",
    "https://vimeo362227-38.onrender.com",
    "https://vimeo362227-39.onrender.com",
    "https://vimeo362227-40.onrender.com",
    "https://vimeo362227-41.onrender.com",
    "https://vimeo362227-42.onrender.com",
    "https://vimeo362227-43.onrender.com",
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
                if isinstance(e, requests.exceptions.Timeout) and retry < 6:
                    retry += 1
                    print(f'{url} timed out, retrying {retry}/6')
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

