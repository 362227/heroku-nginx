import re
import glob

path = "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据-刷json/合并*log"

# 遍历匹配的日志文件
for filename in glob.glob(path):
    with open(filename, encoding='gbk', errors='ignore') as f:
        # 读取文件内容
        file = f.read()

        # 使用正则表达式提取 errorCode 为 1, 22 或 29 的数字 ID
        file = re.findall(r'.*errorCode=(1|22|29) .+?([0-9]{6,10})', file)

        # 遍历所有匹配到的项目
        for item in file:
            # 输出格式化后的链接，item[1] 是提取的 ID
            print(f'https://vimeo.com/api/oembed.json?url=https%3A%2F%2Fvimeo.com%2F{item[1]}\n        out={item[1]}')
