import re
import glob
import sys

filename = sys.argv[1]

# 读入文件
with open(filename, encoding='gbk', errors='ignore') as f:
    file = f.read()

# 使用正则表达式匹配相应的内容, 使用findall匹配，返回列表类型，但是属于字符数组
file = re.findall(r'.*errorCode\=3 .+?player\.vimeo\.com\/video\/(.*)', file)  #提取有404的链接

for item in file:
    print('https://vimeo.com/api/oembed.json?url=https://vimeo.com/' + item + '\n        out=' + item)
