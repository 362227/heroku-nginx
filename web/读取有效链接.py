import requests
import time
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# 代理
proxy = {'http': 'http://127.0.0.1:1086', 'https': 'http://127.0.0.1:1086'}

# 需要尝试的链接列表

urls_text = """
http://various-colorful-epoxy.glitch.me
http://marked-tin-organ.glitch.me
http://jazzy-vivid-scallion.glitch.me
http://classy-fuzzy-turkey.glitch.me
http://confirmed-stone-chef.glitch.me
http://mellow-shell-lip.glitch.me
http://gelatinous-subdued-holiday.glitch.me
http://lightning-marmalade-straw.glitch.me
http://pouncing-expensive-fern.glitch.me
http://versed-fresh-soldier.glitch.me
http://cloudy-soft-thought.glitch.me
http://octagonal-upbeat-strand.glitch.me
http://sharp-remarkable-stoat.glitch.me
http://coffee-serious-menu.glitch.me
http://gregarious-crawling-egg.glitch.me
http://meadow-early-town.glitch.me
http://false-guiltless-echinacea.glitch.me
http://candy-laced-vacuum.glitch.me
http://intriguing-various-echinacea.glitch.me
http://unique-turquoise-acoustic.glitch.me
http://heather-chartreuse-forsythia.glitch.me
http://teal-agreeable-wrench.glitch.me
http://bald-caterwauling-leo.glitch.me
http://sphenoid-gleaming-terrier.glitch.me
http://curved-phrygian-pillow.glitch.me
http://sugared-magical-rudbeckia.glitch.me
http://foamy-probable-viper.glitch.me
http://sophisticated-industrious-silkworm.glitch.me
http://private-stream-baboon.glitch.me
http://snow-pineapple-powder.glitch.me
http://beneficial-mature-beard.glitch.me
http://ambiguous-sore-red.glitch.me
http://adventurous-neon-galaxy.glitch.me
http://developing-scarlet-glockenspiel.glitch.me
http://aware-cyclic-snail.glitch.me
http://omniscient-heliotrope-ornament.glitch.me
http://midnight-maple-thimbleberry.glitch.me
http://ripe-chambray-literature.glitch.me
http://fate-puzzling-tree.glitch.me
http://observant-three-tempo.glitch.me
http://precious-indigo-uncle.glitch.me
http://treasure-entertaining-vase.glitch.me
http://frill-plucky-textbook.glitch.me
http://daffodil-equatorial-stew.glitch.me
http://friendly-frequent-xylophone.glitch.me
http://basalt-prickle-health.glitch.me
http://antique-everlasting-headphones.glitch.me
http://jolly-scarce-angora.glitch.me
http://sunny-troubled-splash.glitch.me
http://short-lying-teacher.glitch.me
http://sage-extreme-help.glitch.me
http://rural-regular-iridium.glitch.me
http://dark-brassy-hawk.glitch.me
http://ordinary-verbose-iron.glitch.me
http://cherry-trusted-acapella.glitch.me
http://dandelion-obsidian-torta.glitch.me
http://resolute-tropical-guava.glitch.me
http://typhoon-pickled-crayfish.glitch.me
http://cyclic-aged-slip.glitch.me
http://boggy-fog-hosta.glitch.me
http://succinct-efficient-eye.glitch.me
http://thin-congruous-salesman.glitch.me
http://sustaining-platinum-trombone.glitch.me
http://acidic-motley-pail.glitch.me
http://complete-scintillating-silkworm.glitch.me
http://sophisticated-alert-spleen.glitch.me
http://quilled-supreme-soybean.glitch.me
http://selective-attractive-hardhat.glitch.me
http://relieved-granite-panther.glitch.me
http://prairie-furry-help.glitch.me
http://rounded-deserted-alloy.glitch.me
http://amber-mammoth-pot.glitch.me
http://faceted-gamy-pomegranate.glitch.me
http://handy-coffee-vole.glitch.me
http://stupendous-pouncing-chill.glitch.me
http://concrete-maddening-ragdoll.glitch.me
http://bold-different-unicorn.glitch.me
http://kind-orange-contraption.glitch.me
http://indigo-iris-dill.glitch.me
http://lean-steel-behavior.glitch.me
http://jumpy-habitual-twist.glitch.me
http://north-cooked-hardhat.glitch.me
http://mewing-shaded-chard.glitch.me
http://sly-bloom-sphere.glitch.me
http://miniature-atom-mask.glitch.me
http://celestial-blossom-donut.glitch.me
http://tasteful-nettle-shamrock.glitch.me
http://sun-electric-crown.glitch.me
http://plain-quark-mimosa.glitch.me
http://graceful-dorian-bathtub.glitch.me
http://innovative-wandering-whip.glitch.me
http://cumbersome-agreeable-log.glitch.me
http://cuddly-wandering-reward.glitch.me
http://navy-intriguing-mortarboard.glitch.me
http://wirehaired-maddening-mitten.glitch.me
http://ruddy-amazing-conchoraptor.glitch.me
http://amazing-valley-silence.glitch.me
http://beautiful-agate-cayenne.glitch.me
http://snow-glass-rate.glitch.me
http://sapphire-beryl-snapper.glitch.me
http://freckle-fabulous-food.glitch.me
http://puzzled-glacier-cone.glitch.me
http://messy-swift-furniture.glitch.me
http://outstanding-garrulous-flyaway.glitch.me
http://slender-heady-replace.glitch.me
http://vine-ionian-bandicoot.glitch.me
http://thankful-shard-cathedral.glitch.me
http://holistic-quilt-coneflower.glitch.me
http://comfortable-flicker-hamburger.glitch.me
http://adjoining-adaptive-ranunculus.glitch.me
http://unleashed-blossom-knee.glitch.me
http://salty-concise-harrier.glitch.me
http://honeysuckle-purrfect-exception.glitch.me
http://abounding-sudsy-growth.glitch.me
http://tide-roomy-busby.glitch.me
http://hickory-humdrum-hose.glitch.me
http://swamp-piquant-clownfish.glitch.me
http://private-north-bread.glitch.me
http://alkaline-grave-queen.glitch.me
http://glossy-tattered-pawpaw.glitch.me
http://infrequent-dune-handball.glitch.me
http://ribbon-auspicious-trampoline.glitch.me
http://cerulean-sticky-riverbed.glitch.me
http://nimble-bristle-cell.glitch.me
http://heady-opposite-subway.glitch.me
http://distinct-nervous-side.glitch.me
http://quartz-grateful-consonant.glitch.me
http://plucky-lavender-hippopotamus.glitch.me
http://unleashed-brick-thought.glitch.me
http://oasis-stream-vise.glitch.me
http://unmarred-verdant-soybean.glitch.me
http://diligent-fluffy-work.glitch.me
http://protective-obsidian-anemone.glitch.me
http://rebel-majestic-eoraptor.glitch.me
http://southern-season-gecko.glitch.me
http://mirage-massive-tadpole.glitch.me
http://bumpy-crystalline-nation.glitch.me
http://bristle-hickory-macadamia.glitch.me
http://military-parallel-dive.glitch.me
"""

# Split the multi-line string into individual hash values
urls = urls_text.strip().split("\n")










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
