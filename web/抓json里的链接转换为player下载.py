import requests
import os
import random
import concurrent.futures
from requests.exceptions import RetryError, Timeout, ConnectionError, HTTPError

# 读取链接文件路径
file_path = "links.txt"
# 修改后的链接前缀
prefix = "http://pistolwayne001php.herokuapp.com/%E5%88%B7vimeo%E8%B7%B3%E8%BD%AC%E5%9C%B0%E5%9D%80.php?url=https://player.vimeo.com/video/"
# 下载保存路径
download_path = "downloaded_videos/"
# 代理地址列表 links.txt
proxies = ["http://127.0.0.1:1083", "http://127.0.0.1:1088"]

# 读取链接文件内容
with open(file_path, "r") as f:
    links = [link.strip() for link in f.readlines() if link.startswith("http")]

# 定义下载函数
def download_video(link):
    link = link.strip()  # 去掉行末的换行符
    if random.randint(0, 2) == 0:
        # 不使用代理
        proxy = random.choice(proxies)
        #proxy = None
    else:
        # 随机选择一个代理
        #proxy = None
        proxy = random.choice(proxies)
    retry = 20
    while retry > 0:
        try:
            response = requests.get(link, proxies={"http": proxy, "https": proxy}, verify=True)
            if response.status_code == 200:
                data = response.json()
                uri = data.get("uri", "")
                if uri.startswith("/videos/"):
                    video_id = uri.split(":")[0].split("/")[-1]
                    video_url = prefix + video_id + "?h=" + uri.split(":")[-1]
                    retry_download = 20
                    while retry_download > 0:
                        try:
                            response = requests.get(video_url)
                            if response.status_code == 200:
                                file_name = video_id
                                file_path = os.path.join(download_path, file_name)
                                with open(file_path, "wb") as f:
                                    f.write(response.content)
                                print(f"{video_url} downloaded and saved as {file_path}")
                                break
                            else:
                                print(f"Failed to download {video_url}, status code: {response.status_code}")
                        except (RetryError, Timeout, ConnectionError, HTTPError) as e:
                            retry_download -= 1
                            print(f"Failed to download {video_url}, retrying... ({e})")
                            time.sleep(5)  # 重试间隔统一为5秒
                    if retry_download == 0:
                        print(f"Failed to download {video_url} after 20 retries")
                else:
                    print(f"Invalid uri: {uri}")
                break
            elif response.status_code == 403:
                print(f"Failed to access {link}, status code: {response.status_code}")
                os.system('echo 被ban了')  # 
                retry -= 1
                time.sleep(5)  # 重试间隔统一为5秒
            elif response.status_code == 404:
                print(f"Failed to access {link}, status code: {response.status_code}")
                break
        except (RetryError, Timeout, ConnectionError, HTTPError) as e:
            retry -= 1
            print(f"Failed to access {link}, retrying... ({e})")
            time.sleep(5)  # 重试间隔统一为5秒
    if retry == 0:
        print(f"Failed to access {link} after 20 retries")

# 使用线程池下载视频
with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:
    executor.map(download_video, links)
