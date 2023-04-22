import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 代理
proxy = {'http': 'http://127.0.0.1:1086', 'https': 'http://127.0.0.1:1086'}

# 需要尝试的链接列表
urls = [
    "https://replitt1.15651618096.无效.co",
    "https://replitt1.15651618096.repl.co",
    "https://replitt2.15651618096.repl.co",
    "https://replitt3.15651618096.repl.co",
    "https://replitt4.15651618096.repl.co",
    "https://replitt5.15651618096.repl.co",
    "https://replitt6.15651618096.repl.co",
    "https://hoola1.hellyahoola.repl.co",
    "https://hoola2.hellyahoola.repl.co",
    "https://hoola3.hellyahoola.repl.co",
    "https://hoola4.hellyahoola.repl.co",
    "https://hoola5.hellyahoola.repl.co",
    "https://hoola6.hellyahoola.repl.co",
    "https://kevin1.hoolahellya.repl.co",
    "https://kevin2.hoolahellya.repl.co",
    "https://kevin3.hoolahellya.repl.co",
    "https://kevin4.hoolahellya.repl.co",
    "https://kevin5.hoolahellya.repl.co",
    "https://kevin6.hoolahellya.repl.co",
    "https://killer1.hellyakiller.repl.co",
    "https://killer2.hellyakiller.repl.co",
    "https://killer3.hellyakiller.repl.co",
    "https://killer4.hellyakiller.repl.co",
    "https://killer5.hellyakiller.repl.co",
    "https://killer6.hellyakiller.repl.co",
    "https://hooray1.hoorayhuh.repl.co",
    "https://hooray2.hoorayhuh.repl.co",
    "https://hooray3.hoorayhuh.repl.co",
    "https://hooray4.hoorayhuh.repl.co",
    "https://hooray5.hoorayhuh.repl.co",
    "https://hooray6.hoorayhuh.repl.co",
    "https://rendeer1.yagoodyahell.repl.co",
    "https://rendeer2.yagoodyahell.repl.co",
    "https://rendeer3.yagoodyahell.repl.co",
    "https://rendeer4.yagoodyahell.repl.co",
    "https://rendeer5.yagoodyahell.repl.co",
    "https://rendeer6.yagoodyahell.repl.co",
    "https://amazoon1.goodyahellya.repl.co",
    "https://amazoon2.goodyahellya.repl.co",
    "https://amazoon3.goodyahellya.repl.co",
    "https://amazoon4.goodyahellya.repl.co",
    "https://amazoon5.goodyahellya.repl.co",
    "https://amazoon6.goodyahellya.repl.co",
    "https://yaheyyahey1.doyathing3.repl.co",
    "https://yaheyyahey2.doyathing3.repl.co",
    "https://yaheyyahey3.doyathing3.repl.co",
    "https://yaheyyahey4.doyathing3.repl.co",
    "https://yaheyyahey5.doyathing3.repl.co",
    "https://yaheyyahey6.doyathing3.repl.co",
    "https://felly1.goodya5678.repl.co",
    "https://felly2.goodya5678.repl.co",
    "https://felly3.goodya5678.repl.co",
    "https://felly4.goodya5678.repl.co",
    "https://felly5.goodya5678.repl.co",
    "https://felly6.goodya5678.repl.co",
    "https://jelly1.goodya3.repl.co",
    "https://jelly2.goodya3.repl.co",
    "https://jelly3.goodya3.repl.co",
    "https://jelly4.goodya3.repl.co",
    "https://jelly5.goodya3.repl.co",
    "https://jelly6.goodya3.repl.co",
    "https://helly1.doyathing2.repl.co",
    "https://helly2.doyathing2.repl.co",
    "https://helly3.doyathing2.repl.co",
    "https://helly4.doyathing2.repl.co",
    "https://helly5.doyathing2.repl.co",
    "https://helly6.doyathing2.repl.co",
    "https://ulley1.pistolwayne.repl.co",
    "https://ulley2.pistolwayne.repl.co",
    "https://ulley3.pistolwayne.repl.co",
    "https://ulley4.pistolwayne.repl.co",
    "https://ulley5.pistolwayne.repl.co",
    "https://ulley6.pistolwayne.repl.co",
    "https://wulley1.goodya1234.repl.co",
    "https://wulley2.goodya1234.repl.co",
    "https://wulley3.goodya1234.repl.co",
    "https://wulley4.goodya1234.repl.co",
    "https://wulley5.goodya1234.repl.co",
    "https://wulley6.goodya1234.repl.co",
    "https://shelly1.goodya4.repl.co",
    "https://shelly2.goodya4.repl.co",
    "https://shelly3.goodya4.repl.co",
    "https://shelly4.goodya4.repl.co",
    "https://shelly5.goodya4.repl.co",
    "https://shelly6.goodya4.repl.co",
    "https://kelly1.doyathing7.repl.co",
    "https://kelly2.doyathing7.repl.co",
    "https://kelly3.doyathing7.repl.co",
    "https://kelly4.doyathing7.repl.co",
    "https://kelly5.doyathing7.repl.co",
    "https://kelly6.doyathing7.repl.co",
    "https://hikitiki1.doyathing6.repl.co",
    "https://hikitiki2.doyathing6.repl.co",
    "https://hikitiki3.doyathing6.repl.co",
    "https://hikitiki4.doyathing6.repl.co",
    "https://hikitiki5.doyathing6.repl.co",
    "https://hikitiki6.doyathing6.repl.co",
 

    
    "https://google1.iyiyi.repl.co",
    "https://google2.iyiyi.repl.co",
    "https://google3.iyiyi.repl.co",
    "https://google4.iyiyi.repl.co",
    "https://google5.iyiyi.repl.co",
    "https://google6.iyiyi.repl.co",
    "https://362227github1.362227.repl.co",
    "https://362227github2.362227.repl.co",
    "https://362227github3.362227.repl.co",
    "https://362227github4.362227.repl.co",
    "https://362227github5.362227.repl.co",
    "https://362227github6.362227.repl.co",
    "https://10362227github1.10362227.repl.co",
    "https://10362227github2.10362227.repl.co",
    "https://10362227github3.10362227.repl.co",
    "https://10362227github4.10362227.repl.co",
    "https://10362227github5.10362227.repl.co",
    "https://10362227github6.10362227.repl.co",
    "https://gdhdhdh1441414github1.gdhdhdh1441414.repl.co",
    "https://gdhdhdh1441414github2.gdhdhdh1441414.repl.co",
    "https://gdhdhdh1441414github3.gdhdhdh1441414.repl.co",
    "https://gdhdhdh1441414github4.gdhdhdh1441414.repl.co",
    "https://gdhdhdh1441414github5.gdhdhdh1441414.repl.co",
    "https://gdhdhdh1441414github6.gdhdhdh1441414.repl.co",
    "https://tdlguwwlnj-1.tdlguwwlnj.repl.co",
    "https://tdlguwwlnj-2.tdlguwwlnj.repl.co",
    "https://tdlguwwlnj-3.tdlguwwlnj.repl.co",
    "https://tdlguwwlnj-4.tdlguwwlnj.repl.co",
    "https://tdlguwwlnj-5.tdlguwwlnj.repl.co",
    "https://tdlguwwlnj-6.tdlguwwlnj.repl.co",
    "https://ksmggouvixkmp-1.ksmggouvixkmp.repl.co",
    "https://ksmggouvixkmp-2.ksmggouvixkmp.repl.co",
    "https://ksmggouvixkmp-3.ksmggouvixkmp.repl.co",
    "https://ksmggouvixkmp-4.ksmggouvixkmp.repl.co",
    "https://ksmggouvixkmp-5.ksmggouvixkmp.repl.co",
    "https://ksmggouvixkmp-6.ksmggouvixkmp.repl.co",
    "https://ldgukyzubqress-1.ldgukyzubqress.repl.co",
    "https://ldgukyzubqress-2.ldgukyzubqress.repl.co",
    "https://ldgukyzubqress-3.ldgukyzubqress.repl.co",
    "https://ldgukyzubqress-4.ldgukyzubqress.repl.co",
    "https://ldgukyzubqress-5.ldgukyzubqress.repl.co",
    "https://ldgukyzubqress-6.ldgukyzubqress.repl.co",
    "https://vfjfhw-1.vfjfhw.repl.co",
    "https://vfjfhw-2.vfjfhw.repl.co",
    "https://vfjfhw-3.vfjfhw.repl.co",
    "https://vfjfhw-4.vfjfhw.repl.co",
    "https://vfjfhw-5.vfjfhw.repl.co",
    "https://vfjfhw-6.vfjfhw.repl.co",
    "https://zywfttnabp-1.zywfttnabp.repl.co",
    "https://zywfttnabp-2.zywfttnabp.repl.co",
    "https://zywfttnabp-3.zywfttnabp.repl.co",
    "https://zywfttnabp-4.zywfttnabp.repl.co",
    "https://zywfttnabp-5.zywfttnabp.repl.co",
    "https://zywfttnabp-6.zywfttnabp.repl.co",
    "https://bruqtp-1.bruqtp.repl.co",
    "https://bruqtp-2.bruqtp.repl.co",
    "https://bruqtp-3.bruqtp.repl.co",
    "https://bruqtp-4.bruqtp.repl.co",
    "https://bruqtp-5.bruqtp.repl.co",
    "https://bruqtp-6.bruqtp.repl.co",
    "https://nsgnipqrwke-1.nsgnipqrwke.repl.co",
    "https://nsgnipqrwke-2.nsgnipqrwke.repl.co",
    "https://nsgnipqrwke-3.nsgnipqrwke.repl.co",
    "https://nsgnipqrwke-4.nsgnipqrwke.repl.co",
    "https://nsgnipqrwke-5.nsgnipqrwke.repl.co",
    "https://nsgnipqrwke-6.nsgnipqrwke.repl.co",
    "https://sovj2weiosjke-1.sovj2weiosjke.repl.co",
    "https://sovj2weiosjke-2.sovj2weiosjke.repl.co",
    "https://sovj2weiosjke-3.sovj2weiosjke.repl.co",
    "https://sovj2weiosjke-4.sovj2weiosjke.repl.co",
    "https://sovj2weiosjke-5.sovj2weiosjke.repl.co",
    "https://sovj2weiosjke-6.sovj2weiosjke.repl.co",
    "https://sdllguovhw-1.sdllguovhw.repl.co",
    "https://sdllguovhw-2.sdllguovhw.repl.co",
    "https://sdllguovhw-3.sdllguovhw.repl.co",
    "https://sdllguovhw-4.sdllguovhw.repl.co",
    "https://sdllguovhw-5.sdllguovhw.repl.co",
    "https://sdllguovhw-6.sdllguovhw.repl.co",
    "https://otbdylgngzhwxyl-1.otbdylgngzhwxyl.repl.co",
    "https://otbdylgngzhwxyl-2.otbdylgngzhwxyl.repl.co",
    "https://otbdylgngzhwxyl-3.otbdylgngzhwxyl.repl.co",
    "https://otbdylgngzhwxyl-4.otbdylgngzhwxyl.repl.co",
    "https://otbdylgngzhwxyl-5.otbdylgngzhwxyl.repl.co",
    "https://otbdylgngzhwxyl-6.otbdylgngzhwxyl.repl.co",
    
] 

while True:
    # 记录成功的链接和包含“811977669”的链接
    successful_urls = []
    filtered_urls = []

    def request_url(url):
        retry = 0
        while True:
            try:
                response = requests.get(f'{url}/vimeo.php?link=http://vimeo.com/api/oembed.json?url=https%3A//vimeo.com/811977669', timeout=15)
                if response.status_code == 200:
                    print(f'{url} returned 200')
                    successful_urls.append(url)
                    if '811977669' in str(response.content):
                        filtered_urls.append(url)
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
                if retry < 6:
                    retry += 1
                    print(f'{url} retrying {retry}/6')
                else:
                    break
            time.sleep(1)  # 等待1秒后重试

    # 使用线程池并发请求
    with ThreadPoolExecutor(max_workers=80) as executor:
        futures = [executor.submit(request_url, url) for url in urls]
        # 等待所有请求完成
        for _ in as_completed(futures):
            pass

    # 将成功的链接写入文件
    if len(filtered_urls) >120:
        with open('urls.txt', 'a') as f:
            for url in filtered_urls:
                f.write(url + '\n')

    # 如果所有链接都成功，则退出循环
    if set(successful_urls) == set(urls):
        print("All URLs succeeded!")
        break

    # 休眠一段时间后再次尝试
    print("一轮结束")
    print(len(successful_urls))
    time.sleep(4)
