import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# 代理
proxy = {'http': 'http://127.0.0.1:1086', 'https': 'http://127.0.0.1:1086'}

# 需要尝试的链接列表


urls = [
    "https://github.c/qodnh/?这是无效链接，让这个代码能无限循环", 
    "https://dc328d28-ef61-4e36-9b6d-040bb1384e09-00-3bjxvzmdvu0yu.sisko.replit.dev",
    "https://0c92fe09-72ff-45c1-9fa4-e5b4e51ad53c-00-11vqtgma08u4p.pike.replit.dev",
    "https://109ef66c-c2f0-4345-8d15-47333a179e2e-00-1q1wc7w4fmtnq.sisko.replit.dev",
    "https://1616325f-23ff-469e-ba6a-1227e6bc9155-00-14uiu4b8ug72l.sisko.replit.dev",
    "https://b2a7c1ca-37cc-4f02-9656-8bd00e662f3f-00-39r5sxr4czym3.pike.replit.dev",
    "https://b9dc0bd1-a377-4b49-b51f-0ee53c458d30-00-3cko837imdl1x.pike.replit.dev", #006
    "https://418d13b4-66ab-447d-bc84-2f55955eb0a0-00-1ansofx0xaop3.pike.replit.dev",
    "https://0cd68126-a42c-4462-98f0-0772bdf5a633-00-3evk3tcly5ul6.pike.replit.dev",
    "https://690a829d-6ec1-4398-9135-74d6a47797fb-00-erbdketagsxu.sisko.replit.dev",
    "https://08dfa419-1e33-4304-8090-34b45898e918-00-2o5pwozmgmibl.sisko.replit.dev",#010

    #rgttta@hotmail.com
    "https://27a01819-dbc5-4bd3-8af4-86c227ba0e36-00-2h7tnbhr7ijub.kirk.replit.dev", #001
    "https://31a3a53d-2421-4a52-a3be-5dc7a46a8489-00-1j81lajxerd0n.kirk.replit.dev",
    "https://f822e367-500f-49de-8a3f-6f10a05799b7-00-2s73nnxsieubn.worf.replit.dev",
    "https://1e16f377-3769-41ec-a08c-e9d0fcd8209b-00-3d1n7rthu0xw.spock.replit.dev",
    "https://5d9b9b13-e024-4a5d-b903-0550152c670c-00-2e18itco2z3af.kirk.replit.dev",#005
    "https://3e90728b-899e-49e3-8771-8af5e984cb12-00-2mzs0vh65m0cd.picard.replit.dev",
    "https://613fa021-f42a-4951-9dcb-d5a1e95204f0-00-iyamzl49wkys.kirk.replit.dev",
    "https://c392e103-b1b5-42ed-853f-2c36877b6dfd-00-d57wjynhoa0t.riker.replit.dev",
    "https://baa350c4-f211-403a-b9b7-2324a3e633a8-00-y2b4n59p5vm6.kirk.replit.dev",
    "https://544cfef0-0123-4989-aa2f-038afa0ceb78-00-qp5ysznr8te7.kirk.replit.dev",

    #pizvjdeewlfzt@hotmail.com
    "https://95ba45ed-1939-442f-93bc-c5267c0de320-00-1u9jmnq7kdpmr.worf.replit.dev",
    "https://215d2ca8-cfcd-4839-8b07-b8ef6ab56493-00-2x68rh8htefn1.picard.replit.dev",
    "https://ae7d2c78-8cb3-4666-a485-feb2263697d2-00-kjvkp6yl7vws.worf.replit.dev",
    "https://d40547c6-043e-4b30-ac97-2685d4bf1d13-00-1lwg41prwc0sl.kirk.replit.dev",
    "https://e24f0172-82a3-45b2-88e9-7d3f49cfea6a-00-36keftxll3h66.worf.replit.dev",#5
    "https://1e52d4ba-2224-4b07-a512-2900c75389fd-00-17rkamgufgafo.spock.replit.dev",
    "https://13db71ee-3d92-4fab-9edd-242e1c4e83d3-00-2kkfxsqcief8e.picard.replit.dev",
    "https://1f9fc906-b151-48ea-b2a3-6f60e8410618-00-3euraaw2tz1zm.janeway.replit.dev",
    "https://c7605d2f-e5e1-44b8-88d3-4533e6d4a41a-00-2nle1ckc67358.worf.replit.dev",
    "https://66f0929d-0d27-4acd-b2e1-ca55113816cd-00-38xjxwqruff4d.worf.replit.dev",

    #lzywgycaew@hotmail.com
    "https://992b88f7-448a-40dd-8edb-046daf62a172-00-bocw5tm8ihqj.kirk.replit.dev",
    "https://7e6162f1-6dc8-40ac-a9d8-cf1b96e55f6b-00-1sm8wncgr4exb.worf.replit.dev",
    "https://48765636-6863-4060-8a4e-4c1e27ca854c-00-nspvgig715ah.picard.replit.dev",
    "https://1cbcae3c-bced-45c8-9748-dc2d4177bddb-00-30amd4ifl2s5k.janeway.replit.dev",
    "https://7a024403-b62b-4c0c-8ab0-a25dec4930eb-00-n30alnzyv0lh.spock.replit.dev",#5
    "https://6f195e37-2ec0-4e74-96af-7ab526678c8a-00-3p58xlsbehz8f.kirk.replit.dev",
    "https://f5e9888a-f148-4393-b227-a000deb762e8-00-3gyx1jukys308.spock.replit.dev",
    "https://85b7dd15-7ccc-4d66-92c2-34cfb6aecd38-00-wx411c8gq7tg.worf.replit.dev",
    "https://9e23479a-749b-4997-8b50-29dc4e5dc67c-00-1sw5o080h0ypx.worf.replit.dev",
    "https://2555c905-f039-4fc5-973f-5b8b5b420ab9-00-1w2maf8vk8i7u.spock.replit.dev",
   
]





'''
#偶数
urls = [
    "https://github.c/qodnh/?这是无效链接，让这个代码能无限循环", 
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
    "https://vimeo362227-64.onrender.com",
    "https://vimeo362227-66.onrender.com",
    "https://vimeo362227-68.onrender.com",
    "https://vimeo362227-70.onrender.com",
    "https://vimeo362227-72.onrender.com",
    "https://vimeo10362227-2.onrender.com",  
    "https://vimeo10362227-4.onrender.com",  
    "https://vimeo10362227-6.onrender.com",  
    "https://vimeo10362227-8.onrender.com",
    "https://vimeo10362227-10.onrender.com",  
    "https://vimeo10362227-12.onrender.com", 
    "https://vimeo10362227-14.onrender.com",  
    "https://vimeo10362227-16.onrender.com",  
    "https://vimeo10362227-18.onrender.com",  
    "https://vimeo10362227-20.onrender.com",  
    "https://vimeo10362227-22.onrender.com", 
    "https://vimeo10362227-24.onrender.com",  
    "https://vimeo10362227-26.onrender.com",  
    "https://vimeo10362227-28.onrender.com",  
    "https://vimeo10362227-30.onrender.com",  
    "https://vimeo10362227-32.onrender.com", 
    "https://vimeo10362227-34.onrender.com",  
    "https://vimeo10362227-36.onrender.com",  
    "https://vimeo10362227-38.onrender.com",  
    "https://vimeo10362227-40.onrender.com",  
    "https://vimeo10362227-42.onrender.com", 
    "https://vimeo10362227-44.onrender.com",  
    "https://vimeo10362227-46.onrender.com",  
    "https://vimeo10362227-48.onrender.com",  
    "https://vimeo10362227-50.onrender.com",  
    "https://vimeo10362227-52.onrender.com", 
    "https://vimeo10362227-54.onrender.com",  
    "https://vimeo10362227-56.onrender.com",  
    "https://vimeo10362227-58.onrender.com",  
    "https://vimeo10362227-60.onrender.com",  
    "https://vimeo10362227-62.onrender.com",  
    "https://vimeo10362227-64.onrender.com",  
    "https://vimeo10362227-66.onrender.com",  
    "https://vimeo10362227-68.onrender.com",  
    "https://vimeo10362227-70.onrender.com",
    "https://vimeo10362227-72.onrender.com",
    "https://vimeo10362227-74.onrender.com",

    
    "https://ellie002.onrender.com",
    "https://ellie004.onrender.com",
    "https://ellie006.onrender.com",
    "https://ellie008.onrender.com",
    "https://ellie010.onrender.com",
    "https://ellie012.onrender.com",
    "https://ellie014.onrender.com",
    "https://ellie016.onrender.com",
    "https://ellie018.onrender.com",
    "https://ellie020.onrender.com",
    "https://ellie022.onrender.com",
    "https://ellie024.onrender.com",
    "https://ellie026.onrender.com",
    "https://ellie028.onrender.com",
    "https://ellie030.onrender.com",
    "https://ellie032.onrender.com",
    "https://ellie034.onrender.com",
    "https://ellie036.onrender.com",
    "https://ellie038.onrender.com",
    "https://ellie040.onrender.com",
    "https://ellie042.onrender.com",
    "https://ellie044.onrender.com",
    "https://ellie046.onrender.com",
    "https://ellie048.onrender.com",
    "https://ellie050.onrender.com",
    "https://ellie052.onrender.com",
    "https://ellie054.onrender.com",
    "https://ellie056.onrender.com",
    "https://ellie058.onrender.com",
    "https://ellie060.onrender.com",
    "https://ellie062.onrender.com",
    "https://ellie064.onrender.com",
    "https://ellie066.onrender.com",
    "https://ellie068.onrender.com",
    "https://ellie070.onrender.com",
    "https://ellie072.onrender.com",
    "https://ellie074.onrender.com",
    "https://ellie076.onrender.com",  
    "https://ellie078.onrender.com",  
    "https://ellie080.onrender.com",  
    "https://ellie082.onrender.com",  
    "https://ellie084.onrender.com",  
    "https://ellie086.onrender.com",  
    "https://ellie088.onrender.com",  
    "https://ellie090.onrender.com",  
    "https://ellie092.onrender.com",  
    "https://ellie094.onrender.com",  
    "https://ellie096.onrender.com",  
    "https://ellie098.onrender.com",  
    "https://ellie100.onrender.com",  
    "https://ellie102.onrender.com",
    "https://ellie104.onrender.com",
    "https://kai006.onrender.com",
]
'''


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
                response = requests.get(url, timeout=15)
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
