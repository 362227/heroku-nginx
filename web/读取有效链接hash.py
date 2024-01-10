import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


# 代理
proxy = {'http': 'http://127.0.0.1:1086', 'https': 'http://127.0.0.1:1086'}


urls = [
    "https://kacey1--doyathing9.无效2023-05-18.co",
    "https://myphp-1.vercel.app",
    "https://myphp-2.vercel.app",
    "https://myphp-3.vercel.app",
    "https://myphp-4.vercel.app",
    "https://myphp-5.vercel.app",
    "https://myphp-6.vercel.app",
    "https://myphp-7.vercel.app",
    "https://myphp-8.vercel.app",
    "https://myphp-9.vercel.app",
    "https://myphp-10.vercel.app",
    "https://myphp-11.vercel.app",
    "https://myphp-12.vercel.app",
    "https://myphp-13.vercel.app",
    "https://myphp-14.vercel.app",
    "https://myphp-15.vercel.app",
    "https://myphp-16.vercel.app",
    "https://myphp-17.vercel.app",
    "https://myphp-18.vercel.app",
    "https://myphp-19.vercel.app",
    "https://myphp-20.vercel.app",
    "https://myphp-21.vercel.app",
    "https://myphp-22.vercel.app",
    "https://myphp-23.vercel.app",
    "https://myphp-24.vercel.app",
    "https://myphp-25.vercel.app",
    "https://myphp-26.vercel.app",
    "https://myphp-27.vercel.app",
    "https://myphp-28.vercel.app",
    "https://myphp-29.vercel.app",
    "https://myphp-30.vercel.app",
    "https://myphp-31.vercel.app",
    "https://myphp-32.vercel.app",
    "https://myphp-33.vercel.app",
    "https://myphp-34.vercel.app",
    "https://myphp-35.vercel.app",
    "https://myphp-36.vercel.app",
    "https://myphp-37.vercel.app",
    "https://myphp-38.vercel.app",
    "https://myphp-39.vercel.app",
    "https://myphp-40.vercel.app",
    "https://myphp-41.vercel.app",
    "https://myphp-42.vercel.app",
    "https://myphp-43.vercel.app",
    "https://myphp-44.vercel.app",
    "https://myphp-45.vercel.app",
    "https://myphp-46.vercel.app",
    "https://myphp-47.vercel.app",
    "https://myphp-48.vercel.app",
    "https://myphp-49.vercel.app",
    "https://myphp-50.vercel.app",
    "https://myphp-51.vercel.app",
    "https://myphp-52.vercel.app",
    "https://myphp-53.vercel.app",
    "https://myphp-54.vercel.app",
    "https://myphp-55.vercel.app",
    "https://myphp-56.vercel.app",
    "https://myphp-57.vercel.app",
    "https://myphp-58.vercel.app",
    "https://myphp-59.vercel.app",
    "https://myphp-60.vercel.app",
] 


while True:
    # 记录成功的链接
    successful_urls = []

    def request_url(url):
        retry = 0
        while True:
            try:
                new_url = f"{url}/vimeo.php?link=http://vimeo.com/api/oembed.json?url=https%3A//vimeo.com/780837850"
                response = requests.get(new_url, timeout=8)
                if response.status_code == 200 and '780837850' in response.text:
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
