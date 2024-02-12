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
https://cyclic-aged-slip.glitch.me
https://boggy-fog-hosta.glitch.me
https://succinct-efficient-eye.glitch.me
https://thin-congruous-salesman.glitch.me
https://sustaining-platinum-trombone.glitch.me
https://acidic-motley-pail.glitch.me
https://complete-scintillating-silkworm.glitch.me
https://sophisticated-alert-spleen.glitch.me
https://quilled-supreme-soybean.glitch.me
https://selective-attractive-hardhat.glitch.me
https://relieved-granite-panther.glitch.me
https://prairie-furry-help.glitch.me
https://rounded-deserted-alloy.glitch.me
https://amber-mammoth-pot.glitch.me
https://faceted-gamy-pomegranate.glitch.me
https://handy-coffee-vole.glitch.me
https://stupendous-pouncing-chill.glitch.me
https://concrete-maddening-ragdoll.glitch.me
https://bold-different-unicorn.glitch.me
https://kind-orange-contraption.glitch.me
https://indigo-iris-dill.glitch.me
https://lean-steel-behavior.glitch.me
https://jumpy-habitual-twist.glitch.me
https://north-cooked-hardhat.glitch.me
https://mewing-shaded-chard.glitch.me
https://sly-bloom-sphere.glitch.me
https://miniature-atom-mask.glitch.me
https://celestial-blossom-donut.glitch.me
https://tasteful-nettle-shamrock.glitch.me
https://sun-electric-crown.glitch.me
https://plain-quark-mimosa.glitch.me
https://graceful-dorian-bathtub.glitch.me
https://innovative-wandering-whip.glitch.me
https://cumbersome-agreeable-log.glitch.me
https://cuddly-wandering-reward.glitch.me
https://navy-intriguing-mortarboard.glitch.me
https://wirehaired-maddening-mitten.glitch.me
https://ruddy-amazing-conchoraptor.glitch.me
https://amazing-valley-silence.glitch.me
https://beautiful-agate-cayenne.glitch.me
https://snow-glass-rate.glitch.me
https://sapphire-beryl-snapper.glitch.me
https://freckle-fabulous-food.glitch.me
https://puzzled-glacier-cone.glitch.me
https://messy-swift-furniture.glitch.me
https://outstanding-garrulous-flyaway.glitch.me
https://slender-heady-replace.glitch.me
https://vine-ionian-bandicoot.glitch.me
https://thankful-shard-cathedral.glitch.me
https://holistic-quilt-coneflower.glitch.me
https://comfortable-flicker-hamburger.glitch.me
https://adjoining-adaptive-ranunculus.glitch.me
https://unleashed-blossom-knee.glitch.me
https://salty-concise-harrier.glitch.me
https://honeysuckle-purrfect-exception.glitch.me
https://abounding-sudsy-growth.glitch.me
https://tide-roomy-busby.glitch.me
https://hickory-humdrum-hose.glitch.me
https://swamp-piquant-clownfish.glitch.me
https://private-north-bread.glitch.me
https://alkaline-grave-queen.glitch.me
https://glossy-tattered-pawpaw.glitch.me
https://infrequent-dune-handball.glitch.me
https://ribbon-auspicious-trampoline.glitch.me
https://cerulean-sticky-riverbed.glitch.me
https://nimble-bristle-cell.glitch.me
https://heady-opposite-subway.glitch.me
https://distinct-nervous-side.glitch.me
https://quartz-grateful-consonant.glitch.me
https://plucky-lavender-hippopotamus.glitch.me
https://unleashed-brick-thought.glitch.me
https://oasis-stream-vise.glitch.me
https://unmarred-verdant-soybean.glitch.me
https://diligent-fluffy-work.glitch.me
https://protective-obsidian-anemone.glitch.me
https://rebel-majestic-eoraptor.glitch.me
https://southern-season-gecko.glitch.me
https://mirage-massive-tadpole.glitch.me
https://bumpy-crystalline-nation.glitch.me
https://bristle-hickory-macadamia.glitch.me
https://military-parallel-dive.glitch.me
https://glitter-profuse-wrinkle.glitch.me
https://amused-speckle-balance.glitch.me
https://concise-spectacled-pajama.glitch.me
https://wise-apricot-comma.glitch.me
https://believed-ginger-badge.glitch.me
https://meteor-fine-espadrille.glitch.me
https://coal-carnation-taurus.glitch.me
https://young-frequent-aquarius.glitch.me
https://ripe-tree-guardian.glitch.me
https://acidic-rebel-gazelle.glitch.me
https://lucky-deciduous-plane.glitch.me
https://imaginary-pattern-collision.glitch.me
https://ruby-ruby-forgery.glitch.me
https://plausible-obvious-canoe.glitch.me
https://understood-quark-eel.glitch.me
https://gelatinous-locrian-turnip.glitch.me
https://receptive-sophisticated-rayon.glitch.me
https://pinto-palm-hair.glitch.me
https://cypress-fixed-clutch.glitch.me
https://healthy-humane-anaconda.glitch.me
https://tortoiseshell-glamorous-lynx.glitch.me
https://mysterious-thoracic-route.glitch.me
https://water-eight-adapter.glitch.me
https://melodious-young-wholesaler.glitch.me
https://acidic-gabby-slayer.glitch.me
https://pentagonal-tasty-grape.glitch.me
https://acoustic-experienced-arithmetic.glitch.me
https://abrupt-power-nova.glitch.me
https://protective-aboard-macadamia.glitch.me
https://tundra-inexpensive-atlasaurus.glitch.me
https://butter-fantasy-ocarina.glitch.me
https://noble-separate-shield.glitch.me
https://satin-aromatic-motorcycle.glitch.me
https://adhesive-cuboid-recorder.glitch.me
https://repeated-silk-yak.glitch.me
https://clear-separated-chatter.glitch.me
https://colossal-instinctive-amusement.glitch.me
https://brick-political-knuckle.glitch.me
https://tattered-calico-tub.glitch.me
https://snow-abrupt-random.glitch.me
https://typical-coral-skunk.glitch.me
https://typhoon-malleable-plywood.glitch.me
https://zealous-slash-waterlily.glitch.me
https://scientific-pastoral-web.glitch.me
https://courageous-polarized-gorgonzola.glitch.me
https://wax-zany-thimbleberry.glitch.me
https://rural-purrfect-viscountess.glitch.me
https://abaft-tangible-porpoise.glitch.me
https://evergreen-midi-moose.glitch.me
https://unruly-legend-fenugreek.glitch.me
https://lilac-phrygian-bamboo.glitch.me
https://lightning-bloom-teller.glitch.me
https://scratched-humdrum-yew.glitch.me
https://dapper-brash-licorice.glitch.me
https://likeable-luxuriant-bergamot.glitch.me
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
