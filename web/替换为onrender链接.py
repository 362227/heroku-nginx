import fileinput
import re
import random
import sys

# 定义要替换的链接和替换后的链接列表
old_link = "https://crowncloud.362227.top/rss/刷vimeo跳转地址.php"
new_links = [
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
]
input_file = sys.argv[1]

# 替换链接并更新文件
for line in fileinput.input(input_file, inplace=True):
    print(re.sub(f"{old_link}\?url=(https:\/\/player\.vimeo\.com\/video\/\d+)", lambda x: f"{new_links[random.randint(0, len(new_links)-1)]}/oldvimeo.php?url={x.group(1)}&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa", line), end='')
