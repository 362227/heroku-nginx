import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


# 代理
proxy = {'http': 'http://127.0.0.1:1083', 'https': 'http://127.0.0.1:1083'}

urls = [
    "https://kacey1--doyathing9.无效2023-05-18.co",
    "https://vimeo01.up.railway.app",
    "https://vimeo02.up.railway.app",
    "https://vimeo03.up.railway.app",
    "https://vimeo04.up.railway.app",
    "https://vimeo05.up.railway.app",
    "https://vimeo06.up.railway.app",
    "https://vimeo07.up.railway.app",
    "https://vimeo08.up.railway.app",
    "https://vimeo09.up.railway.app",
    "https://vimeo10.up.railway.app",
    "https://vimeo11.up.railway.app",
    "https://vimeo12.up.railway.app",
    "https://vimeo13.up.railway.app",
    "https://vimeo14.up.railway.app",
    "https://vimeo15.up.railway.app",
    "https://vimeo16.up.railway.app",
    "https://vimeo17.up.railway.app",
    "https://vimeo18.up.railway.app",
    "https://vimeo19.up.railway.app",
    "https://vimeo20.up.railway.app",
    "https://vimeo21.up.railway.app",
    "https://vimeo22.up.railway.app",
    "https://vimeo23.up.railway.app",
    "https://vimeo24.up.railway.app",
    "https://vimeo25.up.railway.app",
    "https://vimeo26.up.railway.app",
    "https://vimeo27.up.railway.app",
    "https://vimeo28.up.railway.app",
    "https://vimeo29.up.railway.app",
    "https://vimeo30.up.railway.app",
    "https://vimeo31.up.railway.app",
    "https://vimeo32.up.railway.app",
    "https://vimeo33.up.railway.app",
    "https://vimeo34.up.railway.app",
    "https://vimeo35.up.railway.app",
    "https://vimeo36.up.railway.app",
    "https://vimeo37.up.railway.app",
    "https://vimeo38.up.railway.app",
    "https://vimeo39.up.railway.app",
    "https://vimeo40.up.railway.app",
    "https://vimeo41.up.railway.app",
    "https://vimeo42.up.railway.app",
    "https://vimeo43.up.railway.app",
    "https://vimeo44.up.railway.app",
    "https://vimeo45.up.railway.app",
    "https://vimeo46.up.railway.app",
    "https://vimeo47.up.railway.app",
    "https://vimeo48.up.railway.app",
    "https://vimeo49.up.railway.app",
    "https://vimeo50.up.railway.app",
    "https://vimeo51.up.railway.app",
    "https://vimeo52.up.railway.app",
    "https://vimeo53.up.railway.app",
    "https://vimeo54.up.railway.app",
    "https://vimeo55.up.railway.app",
    "https://vimeo56.up.railway.app",
    "https://vimeo57.up.railway.app",
    "https://vimeo58.up.railway.app",
    "https://vimeo59.up.railway.app",
    "https://vimeo60.up.railway.app",
    "https://vimeo61.up.railway.app",
    "https://vimeo62.up.railway.app",
    "https://vimeo63.up.railway.app",
    "https://vimeo64.up.railway.app",
    "https://vimeo65.up.railway.app",
    "https://vimeo66.up.railway.app",
    "https://vimeo67.up.railway.app",
    "https://vimeo68.up.railway.app",
    "https://vimeo69.up.railway.app",
    "https://vimeo70.up.railway.app",
    "https://vimeo71.up.railway.app",
    "https://vimeo72.up.railway.app",
    "https://vimeo73.up.railway.app",
    "https://vimeo74.up.railway.app",
    "https://vimeo75.up.railway.app",
    "https://vimeo76.up.railway.app",
    "https://vimeo77.up.railway.app",
    "https://vimeo78.up.railway.app",
    "https://vimeo79.up.railway.app",
    "https://vimeo80.up.railway.app",
    "https://vimeo81.up.railway.app",
    "https://vimeo82.up.railway.app",
    "https://vimeo83.up.railway.app",
    "https://vimeo84.up.railway.app",
    "https://vimeo85.up.railway.app",
    "https://vimeo86.up.railway.app",
    "https://vimeo87.up.railway.app",
    "https://vimeo88.up.railway.app",
    "https://vimeo89.up.railway.app",
    "https://vimeo90.up.railway.app",
    "https://vimeo91.up.railway.app",
    "https://vimeo92.up.railway.app",
    "https://vimeo93.up.railway.app",
    "https://vimeo94.up.railway.app",
  
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
