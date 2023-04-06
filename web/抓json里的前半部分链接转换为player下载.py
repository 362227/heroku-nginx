import requests
import os
import re
import sys
import json
import random
import time
import threading
import subprocess
import concurrent.futures
from requests.exceptions import RetryError, Timeout, ConnectionError, HTTPError






proxies = {
    "http": sys.argv[1]
}



def check_and_delete():
 while True:
    print("检查是否为200")
    response = requests.get('http://vimeo.com/api/oembed.json?url=https%3A//vimeo.com/211', proxies=proxies)
    if response.status_code == 403 or response.status_code == 429 or response.status_code == 503 or response.status_code == 000:
        print("重启 Heroku")
        #curl -n -X DELETE https://api.heroku.com/apps/x362227/dynos -H "Content-Type: application/json" -H "Accept: application/vnd.heroku+json; version=3" -H "Authorization: Bearer 14042630-f7f9-4adf-a33a-892a7c25a075" 
        headers = {'Content-Type': 'application/json', 'Accept': 'application/vnd.heroku+json; version=3', 'Authorization': 'Bearer 0e8635cf-e01e-4d5d-b778-53bb2ec48453'}
        requests.delete('https://api.heroku.com/apps/' + sys.argv[2] + '/dynos', headers=headers)
    time.sleep(10)

# 启动check_and_delete线程
check_thread = threading.Thread(target=check_and_delete)
check_thread.start()





# 读取链接文件路径
file_path = "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/oembed链接合并802000000-802999999.log.404.txt"
# 修改后的链接前缀
prefix = "http://pistolwayne001php.herokuapp.com/%E5%88%B7vimeo%E8%B7%B3%E8%BD%AC%E5%9C%B0%E5%9D%80.php?url=https://player.vimeo.com/video/"
# 下载保存路径
download_path = "downloaded_videos/"
# 代理地址列表 links.txt


# 获取文件总行数
with open(file_path, "r") as f:
    total_lines = len(f.readlines())
# 读取前一半的内容
half_lines = total_lines // 2
with open(file_path, "r") as f:
    links = [link.strip() for i, link in enumerate(f.readlines()) if link.startswith("http") and i < half_lines]




# 定义下载函数
def download_video(link):
    link = link.strip()  # 去掉行末的换行符
    retry = 20
    while retry > 0:
        try:
            response = requests.get(link, proxies={"http": sys.argv[1], "https": sys.argv[1]}, verify=True)
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
                retry -= 1
                time.sleep(15)  # 重试间隔为15秒
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
with concurrent.futures.ThreadPoolExecutor(max_workers=66) as executor:
    executor.map(download_video, links)
