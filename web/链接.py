import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--txt', '-t', type=str, default="链接01.txt", help='txt文件名')
parser.add_argument('--numb', '-n', type=str, default='100', help='要刷的序号（前3位）')
args = parser.parse_args()
txt = args.txt
numb = args.numb

 

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
  return "文本已替换"

# 创建一个变量并存储我们要搜索的文本
search_text = "(?<=out=).*(?=[0-9]{6})|(?<=video/).*(?=[0-9]{6})"

#创建一个变量并存储我们要更新的文本
replace_text = numb

# 调用replacetext函数并打印返回的语句
print(replacetext(search_text,replace_text))