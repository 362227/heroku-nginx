import random
import os

# 定义需要替换的字符串和替换后的四个 URL
search_string = "http://362227.top/rss/刷vimeo跳转地址.php?url="

urls_text = """
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
