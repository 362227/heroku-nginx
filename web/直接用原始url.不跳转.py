import random
import os

# 定义需要替换的字符串和替换后的四个 URL
search_string = "http://362227.top/rss/刷vimeo跳转地址.php?url="

urls_text = """
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
