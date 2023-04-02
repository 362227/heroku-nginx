import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 代理
proxy = {'http': 'http://127.0.0.1:1086', 'https': 'http://127.0.0.1:1086'}

# 需要尝试的链接列表

urls = [
    "https://vimeo362227.onrender.com/这是无效链接，别删，让这个代码能循环", 
    "https://vimeo362227.onrender.com",
    "https://vimeo362227-2.onrender.com",
    "https://vimeo362227-4.onrender.com",
    "https://vimeo362227-6.onrender.com",
    "https://vimeo362227-8.onrender.com",
    "https://vimeo362227-10.onrender.com",
    "https://vimeo362227-12.onrender.com",
    "https://vimeo362227-14.onrender.com",
    "https://vimeo362227-16.onrender.com",
    "https://vimeo362227-18.onrender.com",
    "https://vimeo362227-20.onrender.com",
    "https://vimeo362227-22.onrender.com",
    "https://vimeo362227-24.onrender.com",
    "https://vimeo362227-26.onrender.com",
    "https://vimeo362227-28.onrender.com",
    "https://vimeo362227-29.onrender.com",
    "https://vimeo362227-30.onrender.com",
    "https://vimeo362227-32.onrender.com",
    "https://vimeo362227-34.onrender.com",
    "https://vimeo362227-36.onrender.com",
    "https://vimeo362227-38.onrender.com",
    "https://vimeo362227-40.onrender.com",
    "https://vimeo362227-42.onrender.com",
    "https://vimeo362227-44.onrender.com",
    "https://vimeo362227-46.onrender.com",
    "https://vimeo362227-48.onrender.com",
    "https://vimeo362227-50.onrender.com",
    "https://vimeo362227-52.onrender.com",
    "https://vimeo362227-54.onrender.com",
    "https://vimeo362227-56.onrender.com",
    "https://vimeo362227-58.onrender.com",
    "https://vimeo362227-60.onrender.com",
    "https://vimeo362227-62.onrender.com",
    
    "https://ellie002.onrender.com",
    "https://ellie004.onrender.com",
    "https://ellie006.onrender.com",
    "https://ellie008.onrender.com",
    "https://ellie010.onrender.com",
    "https://kai006.onrender.com",
]


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
    "https://vimeo362227-44.onrender.com",
    "https://vimeo362227-45.onrender.com",
    "https://vimeo362227-46.onrender.com",
    "https://vimeo362227-47.onrender.com",
    "https://vimeo362227-48.onrender.com",
    "https://vimeo362227-49.onrender.com",
    "https://vimeo362227-50.onrender.com",
    "https://vimeo362227-51.onrender.com",
    "https://vimeo362227-52.onrender.com",
    "https://vimeo362227-53.onrender.com"
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
    
    "https://bcxdxrdqx-manyapps-001.onrender.com",
    "https://bcxdxrdqx-manyapps-002.onrender.com",
    "https://bcxdxrdqx-manyapps-003.onrender.com",
    "https://bcxdxrdqx-manyapps-004.onrender.com",
    "https://bcxdxrdqx-manyapps-005.onrender.com",
    "https://bcxdxrdqx-manyapps-006.onrender.com",
    "https://bcxdxrdqx-manyapps-007.onrender.com",
    "https://bcxdxrdqx-manyapps-008.onrender.com",
    "https://bcxdxrdqx-manyapps-009.onrender.com",
    "https://bcxdxrdqx-manyapps-010.onrender.com",
    "https://bcxdxrdqx-manyapps-011.onrender.com",
    "https://bcxdxrdqx-manyapps-012.onrender.com",
    "https://bcxdxrdqx-manyapps-013.onrender.com",
    "https://bcxdxrdqx-manyapps-014.onrender.com",
    "https://bcxdxrdqx-manyapps-015.onrender.com",
    "https://bcxdxrdqx-manyapps-016.onrender.com",
    "https://bcxdxrdqx-manyapps-017.onrender.com",
    "https://bcxdxrdqx-manyapps-018.onrender.com",
    "https://bcxdxrdqx-manyapps-019.onrender.com",
    "https://bcxdxrdqx-manyapps-020.onrender.com",  
    
    "https://uflulnjoaurhdhk-manyapps-001.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-002.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-003.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-004.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-005.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-006.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-007.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-008.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-009.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-010.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-011.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-012.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-013.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-014.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-015.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-016.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-017.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-018.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-019.onrender.com",
    "https://uflulnjoaurhdhk-manyapps-020.onrender.com",  
    
    "https://kobpiwpwprfnj-manyapps-001.onrender.com",
    "https://kobpiwpwprfnj-manyapps-002.onrender.com",
    "https://kobpiwpwprfnj-manyapps-003.onrender.com",
    "https://kobpiwpwprfnj-manyapps-004.onrender.com",
    "https://kobpiwpwprfnj-manyapps-005.onrender.com",
    "https://kobpiwpwprfnj-manyapps-006.onrender.com",
    "https://kobpiwpwprfnj-manyapps-007.onrender.com",
    "https://kobpiwpwprfnj-manyapps-008.onrender.com",
    "https://kobpiwpwprfnj-manyapps-009.onrender.com",
    
    "https://resignation1-manyapps-001.onrender.com",
    "https://resignation1-manyapps-002.onrender.com",
    "https://resignation1-manyapps-003.onrender.com",
    "https://resignation1-manyapps-004.onrender.com",
    "https://resignation1-manyapps-005.onrender.com",
    "https://resignation1-manyapps-006.onrender.com",
    "https://resignation1-manyapps-007.onrender.com",
    "https://resignation1-manyapps-008.onrender.com",
    "https://resignation1-manyapps-009.onrender.com",
    "https://resignation1-manyapps-010.onrender.com",
    "https://resignation1-manyapps-011.onrender.com",
    "https://resignation1-manyapps-012.onrender.com",
    "https://resignation1-manyapps-013.onrender.com",
    "https://resignation1-manyapps-014.onrender.com",
    "https://resignation1-manyapps-015.onrender.com",
    "https://resignation1-manyapps-016.onrender.com",
    "https://resignation1-manyapps-017.onrender.com",
    "https://resignation1-manyapps-018.onrender.com",
    "https://resignation1-manyapps-019.onrender.com",
    "https://resignation1-manyapps-020.onrender.com",
]
'''

while True:
    # 记录成功的链接
    successful_urls = []

    def request_url(url):
        retry = 0
        while True:
            try:
                response = requests.get(url, timeout=20)
                if response.status_code == 200:
                    print(f'{url} returned 200')
                    successful_urls.append(url)
                    return None  # 返回None表示成功
                else:
                    print(f'{url} returned {response.status_code}')
                    if retry < 6:
                        retry += 1
                        print(f'{url} retrying {retry}/6')
                    else:
                        break
            except requests.exceptions.RequestException as e:
                print(f'{url} failed: {e}')
                if retry < 6:
                    retry += 1
                    print(f'{url} retrying {retry}/6')
                else:
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

    # 如果所有链接都成功，则退出循环
    if set(successful_urls) == set(urls):
        print("All URLs succeeded!")
        break

    # 休眠一段时间后再次尝试
    print("一轮结束")
    time.sleep(10)
    os.system('clear')
