import requests
import time
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# 代理
proxy = {'http': 'http://127.0.0.1:1086', 'https': 'http://127.0.0.1:1086'}

# 需要尝试的链接列表

urls_text = """
https://kacey1--doyathing9.无效2023-05-18.co
https://various-colorful-epoxy.glitch.me
https://marked-tin-organ.glitch.me
https://jazzy-vivid-scallion.glitch.me
https://classy-fuzzy-turkey.glitch.me
https://confirmed-stone-chef.glitch.me
https://mellow-shell-lip.glitch.me
https://gelatinous-subdued-holiday.glitch.me
https://lightning-marmalade-straw.glitch.me
https://pouncing-expensive-fern.glitch.me
https://versed-fresh-soldier.glitch.me
https://cloudy-soft-thought.glitch.me
https://octagonal-upbeat-strand.glitch.me
https://sharp-remarkable-stoat.glitch.me
https://coffee-serious-menu.glitch.me
https://gregarious-crawling-egg.glitch.me
https://meadow-early-town.glitch.me
https://false-guiltless-echinacea.glitch.me
https://candy-laced-vacuum.glitch.me
https://intriguing-various-echinacea.glitch.me
https://unique-turquoise-acoustic.glitch.me
https://heather-chartreuse-forsythia.glitch.me
https://teal-agreeable-wrench.glitch.me
https://bald-caterwauling-leo.glitch.me
https://sphenoid-gleaming-terrier.glitch.me
https://curved-phrygian-pillow.glitch.me
https://sugared-magical-rudbeckia.glitch.me
https://foamy-probable-viper.glitch.me
https://sophisticated-industrious-silkworm.glitch.me
https://private-stream-baboon.glitch.me
https://snow-pineapple-powder.glitch.me
https://beneficial-mature-beard.glitch.me
https://ambiguous-sore-red.glitch.me
https://adventurous-neon-galaxy.glitch.me
https://developing-scarlet-glockenspiel.glitch.me
https://aware-cyclic-snail.glitch.me
https://omniscient-heliotrope-ornament.glitch.me
https://midnight-maple-thimbleberry.glitch.me
https://ripe-chambray-literature.glitch.me
https://fate-puzzling-tree.glitch.me
https://observant-three-tempo.glitch.me
https://precious-indigo-uncle.glitch.me
https://treasure-entertaining-vase.glitch.me
https://frill-plucky-textbook.glitch.me
https://daffodil-equatorial-stew.glitch.me
https://friendly-frequent-xylophone.glitch.me
https://basalt-prickle-health.glitch.me
https://antique-everlasting-headphones.glitch.me
https://jolly-scarce-angora.glitch.me
https://sunny-troubled-splash.glitch.me
https://short-lying-teacher.glitch.me
https://sage-extreme-help.glitch.me
https://rural-regular-iridium.glitch.me
https://dark-brassy-hawk.glitch.me
https://ordinary-verbose-iron.glitch.me
https://cherry-trusted-acapella.glitch.me
https://dandelion-obsidian-torta.glitch.me
https://resolute-tropical-guava.glitch.me
https://typhoon-pickled-crayfish.glitch.me
"""

# Split the multi-line string into individual hash values
urls = urls_text.strip().split("\n")

# Define the pattern for the URLs
pattern = r"(https://\S+\.glitch\.me)"

# Define the replacement string
#replacement = r"\1/vimeo.php?stream=\1"
replacement = r"\1/"

# Apply the regex substitution to each URL
urls = [re.sub(pattern, replacement, url) for url in urls]









while True:
    # 记录成功的链接
    successful_urls = []

    def request_url(url):
        retry = 0
        while True:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f'{url} returned 200')
                    successful_urls.append(url)
                    return None  # 返回None表示成功
                else:
                    print(f'{url} returned {response.status_code}')
                    if retry < 5:
                        retry += 1
                        print(f'{url} retrying {retry}/5')
                    else:
                        break
            except requests.exceptions.RequestException as e:
                print(f'{url} failed: {e}')
                if retry < 3:
                    retry += 1
                    print(f'{url} retrying {retry}/3')
                else:
                    break
            time.sleep(1)  # 等待1秒后重试

    # 使用线程池并发请求
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(request_url, url) for url in urls]
        # 等待所有请求完成
        for _ in as_completed(futures):
            pass

    # 将成功的链接写入文件
    if len(successful_urls) >= 50:
        with open('/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/urls.txt', 'w') as f:
            for url in successful_urls:
                f.write(url + '\n')
    else:
        print('Successful URLs less than 40, skipped writing to file.')

    # 如果所有链接都成功，则退出循环
    if set(successful_urls) == set(urls):
        print("All URLs succeeded!")
        break

    # 休眠一段时间后再次尝试
    print("一轮结束")
    print(len(successful_urls))
    time.sleep(5)
    os.system('clear')
