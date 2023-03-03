import re
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('--path', '-p', type=str, default="/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01", help='文件夹')
args = parser.parse_args()
path = args.path
#for i in range(500000):
# txt = "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01/786" + str(i).zfill(6)
 

#path = '/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/02'
files = os.listdir(path)
for i, file in enumerate(files):
 txt = os.path.join(path, file)
 #print (OldFileName)


 

# 创建一个函数来替换文本
 def replacetext(search_text,replace_text):

  # 以读写模式打开文件
  with open(txt,'r+') as f:

    # 读取文件数据并将其存储在文件变量中
    file = f.read()
    
    # 用文件数据中的字符串替换模式

    file = re.sub(search_text, replace_text, file)

    # 设置位置到页面顶部插入数据
    f.seek(0)
    
    # 在文件中写入替换数据
    f.write(file)

    # 截断文件大小
    f.truncate()

  # 返回“文本已替换”字符串
  return "文本已替换" + txt

# 创建一个变量并存储我们要搜索的文本
 search_text = r".+?(\,\"duration\"\:.+?\,)\"thumbs\".+?\"640\"\:\"(.+?)\".+?(\"account\_type\"\:\".+?\")(\,\"name\"\:\")(.+?\").+?\"title\"\:\"(.+?)\"\,\"(share\_url\"\:\".+?\").*"

#创建一个变量并存储我们要更新的文本
 replace_text = r'title>\6 from \5</title><br>\7\1\3\4\5<br><img src="\2?mw=240"  alt="img" /><br>'

# 调用replacetext函数并打印返回的语句
 print(replacetext(search_text,replace_text))
