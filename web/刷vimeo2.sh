#!/bin/bash
num=$1

python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接.py -n $num -t /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接01.txt
python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接.py -n $num -t /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接02.txt

aria2c  --check-certificate=false -i "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接01.txt" --file-allocation=none --max-concurrent-downloads=970 --disk-cache=0 --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01 --max-download-result=1000 | tee /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999.log"
aria2c  --check-certificate=false -i "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接02.txt" --file-allocation=none --max-concurrent-downloads=970 --disk-cache=0 --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/02 --max-download-result=1000 | tee -a /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999.log"
python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/从log文件提取有ref的链接.py > /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/有ref的链接.txt

IP=( "https://www.petgorilla.com/"   ); IP1=( "https://www.ntropic.com/"  ) ; for i in "${IP[@]}";do aria2c  --referer=$i -i "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/有ref的链接.txt" --file-allocation=none --max-concurrent-downloads=500 --disk-cache=0 --check-certificate=false --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/ref; done & for i1 in "${IP1[@]}";do aria2c  --referer=$i1 -i "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/有ref的链接.txt" --file-allocation=none --max-concurrent-downloads=494 --disk-cache=0 --check-certificate=false --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/ref; done  & python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/正则预处理小文件.py -p /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01 &&  python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/正则预处理小文件.py -p /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/02  
wait



find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01"  -type f -name "*.*" -delete
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/02"  -type f -name "*.*" -delete
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/ref"  -type f -name "*.*" -delete

python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/正则预处理小文件.py -p /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/ref

echo 删除5KB以上的小文件
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01"  -size +5k -delete
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/02"  -size +5k -delete
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/ref"  -size +5k -delete

echo 合并为大文件
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01"  -type f -name "*" | xargs sed 'a\' > /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999"
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/02"  -type f -name "*" | xargs sed 'a\' >> /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999"
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/ref"  -type f -name "*" | xargs sed 'a\' >> /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999"


echo 提取最终数据$num"000000"-$num"999999"
python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/正则提取最新.py > /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999".html

 
