import random
import os

# 定义需要替换的字符串和替换后的四个 URL
search_string = "http://362227.top/rss/刷vimeo跳转地址.php?url="

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
http://outstanding-garrulous-flyaway.glitch.me
http://vine-ionian-bandicoot.glitch.me
"""

# 构建替换字符串列表
replace_strings = [url.strip() + "/vimeo.php?url=" for url in urls_text.split("\n") if url.strip()]

input_file = "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接.txt"
output_file = input_file  # 使用相同的文件名进行覆盖

# 使用临时文件名
temp_file = "temp_output.txt"

with open(input_file, "r") as f_in, open(temp_file, "w") as f_out:
    for line in f_in:
        # 从替换字符串数组中随机选择一个替换字符串
        replace_string = random.choice(replace_strings)
        # 替换字符串
        new_line = line.replace(search_string, replace_string)

        # 只在包含 "vimeo.php" 的行的结尾添加 &ref=http://friendlondon.tv，并将结果写入新文件
        if "vimeo.php" in new_line and "&ref=http://friendlondon.tv" not in new_line:
            new_line = new_line.strip() + "&ref=http://friendlondon.tv\n"
        else:
            new_line = new_line.strip() + "\n"
            new_line = new_line.replace("out=", "  out=")
        f_out.write(new_line)

# 关闭文件，确保缓冲区被刷新
f_in.close()
f_out.close()

# 使用 os.replace() 函数将临时文件覆盖原始文件
os.replace(temp_file, input_file)

print("替换完成，结果已覆盖原始文件", input_file)
