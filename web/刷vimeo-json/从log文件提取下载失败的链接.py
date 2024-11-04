import re
import glob
path = "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据-刷json/合并*log"
for filename in glob.glob(path):
    with open(filename, encoding='gbk', errors='ignore') as f:

# 读入文件
#with open('合并637000000-637999999.html', encoding='gbk', errors='ignore') as f:
      file = f.read()

    # 使用正则表达式匹配相应的内容, 使用findall匹配，返回列表类型，但是属于字符数组
      file = re.findall(r'       0B.*\/([0-9]{6,10}).*', file)  #提取下载速度为0的链接，即有验证码或者网络错误造成失败的链接
 

#for item in file:
for item in file:
   # print(item)
    #filename = m.group(1) + filename2
    print('https://vimeo.com/api/oembed.json?url=https%3A%2F%2Fvimeo.com%2F' + item + '\n        out=' + item)

    
