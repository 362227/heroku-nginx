import re
import glob
import sys

path = sys.argv[1]
for filename in glob.glob(path):
    with open(filename, encoding='gbk', errors='ignore') as f:
        # 读入文件
        file = f.read()

        # 使用正则表达式匹配相应的内容
        pattern = re.compile(r'"\\\/videos\\\/(?P<id>.+?)\:(?P<hash>.+?)\"')
        matches = re.finditer(pattern, file)
        
        for m in matches:
            print('http://362227.top/rss/刷vimeo跳转地址.php?url=https://player.vimeo.com/video/' + m.group('id') + "?h=" + m.group('hash') + '\n        out=' + m.group('id'))
