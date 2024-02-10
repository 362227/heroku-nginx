import random
import os

# 定义需要替换的字符串和替换后的四个 URL
search_string = "https://362227.top/rss/刷vimeo跳转地址单个ref.php?url="

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
"""

# 构建替换字符串列表
replace_strings = [url.strip() + "/vimeo.php?url=" for url in urls_text.split("\n") if url.strip()]

input_file = "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接.txt"
output_file = "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接.txt"
temp_file = "temp_output.txt"

with open(input_file, "r") as f_in, open(temp_file, "w") as f_out:
    for line in f_in:
        # 从替换字符串数组中随机选择一个替换字符串
        replace_string = random.choice(replace_strings)
        # 替换字符串
        new_line = line.replace(search_string, replace_string)
        # 只在包含 "vimeo.php" 的行的结尾添加 &ref=http://friendlondon.tv，并将结果写入新文件
        if "vimeo.php" in new_line:
            new_line = new_line.strip() + "&ref=http://friendlondon.tv\n"
        else:
            new_line = new_line.strip() + "\n"
        f_out.write(new_line)

# 复制临时文件内容到原始文件
os.replace(temp_file, input_file)
print("替换完成，结果已覆盖原始文件", input_file)
