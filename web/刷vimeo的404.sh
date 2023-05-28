#!/bin/bash
num=$1

python3 /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接.py -n $num -t /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接.txt
ulimit -n 2048

#python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/替换为onrender链接.py /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接01.txt
#python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/替换为onrender链接.py /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接02.txt


FILE_PATH="/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接.txt"
LINES_PER_BATCH=$(($(wc -l < $FILE_PATH)/4 + 1))  # 计算每部分的行数
TOTAL_LINES=$(wc -l < $FILE_PATH)
BATCHES=$((TOTAL_LINES/LINES_PER_BATCH))

for ((i=0;i<$BATCHES;i++)); do
    start=$((i*LINES_PER_BATCH+1))
    end=$(((i+1)*LINES_PER_BATCH))
    sed -n "$start,${end}p" $FILE_PATH > batch_$i.txt
    aria2c --check-certificate=false --referer=http://friendlondon.tv -i batch_$i.txt --file-allocation=none --max-concurrent-downloads=720 --disk-cache=0 --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01 --max-download-result=20000000 | tee -a /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999.log"
    rm batch_$i.txt
done

# Download the remaining lines
if [ $((BATCHES*LINES_PER_BATCH)) -lt $TOTAL_LINES ]; then
    start=$((BATCHES*LINES_PER_BATCH+1))
    end=$TOTAL_LINES
    sed -n "$start,${end}p" $FILE_PATH > batch_$BATCHES.txt
    aria2c --check-certificate=false --referer=http://friendlondon.tv -i batch_$BATCHES.txt --file-allocation=none --max-concurrent-downloads=720 --disk-cache=0 --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01 --max-download-result=20000000 | tee -a /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999.log" 
    rm batch_$BATCHES.txt
fi




#python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/从log文件提取有ref的链接.py > /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/有ref的链接.txt
#IP=( "https://trimediting.com/"  "https://somesuch.co/ " "https://www.petgorilla.com/"  "http://malloybrothers.com/" "http://alexanderhammer.com/"  "http://ways-means.co" "http://www.romanwhite.com" ); IP1=( "http://loucloutercasting.com/" "https://www.themill.com/"  "https://www.ntropic.com/"  "http://coffeeand.tv" "http://believemedia.com" "http://modernpost.com" "http://www.treyfanjoy.com/" ) ; for i in "${IP[@]}";do aria2c  --referer=$i -i "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/有ref的链接.txt" --file-allocation=none --max-concurrent-downloads=500 --disk-cache=0 --check-certificate=false --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/ref; done & for i1 in "${IP1[@]}";do aria2c  --referer=$i1 -i "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/有ref的链接.txt" --file-allocation=none --max-concurrent-downloads=494 --disk-cache=0 --check-certificate=false --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/ref; done  &


#echo 下载失败的链接
#python3 /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/从log文件提取下载失败的链接.py > /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/遗漏文件链接合并.txt
#aria2c - --referer=http://friendlondon.tv --check-certificate=false -i "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/遗漏文件链接合并.txt" --file-allocation=none --max-concurrent-downloads=200 --disk-cache=0 --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/遗漏文件 --max-download-result=1000




echo 删除重复小文件
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01"  -type f -name "*.*" -delete
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/02"  -type f -name "*.*" -delete
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/ref"  -type f -name "*.*" -delete
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/遗漏文件"  -type f -name "*.*" -delete

echo 合并为大文件
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01"  -type f -name "*" | xargs sed 'a\' > /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999"
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/02"  -type f -name "*" | xargs sed 'a\' >> /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999"
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/ref"  -type f -name "*" | xargs sed 'a\' >> /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999"
find "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/遗漏文件"  -type f -name "*" | xargs sed 'a\' >> /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999"

echo 提取hash链接
#egrep -i '[0-9]{5,11}:[a-z0-9]{8,11}' 合并$num"000000"-$num"999999" > /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并hash链接$num"000000"-$num"999999"

#echo 提取大文件有效信息（egrep命令，提取有avc_url的行）
#egrep -i '\"avc_url\"'  /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999"temp > /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999"

#rm -rf /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999"temp

#echo 进一步删除无效信息（sed命令）
#sed -i s/.*video\"\:\{\"id\"//g  /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999"

#echo 整理好数据，进一步精简
#python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/正则预处理.py -t /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999"

echo 提取404
egrep -i 'out=|oembed'  /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999" > /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/oembed链接合并$num"000000"-$num"999999".log.404.txt


txt=$(curl  -F file=@/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999".log.404.txt  https://api.anonfiles.com/upload  | grep  '"full"' | sed 's/\\//g' | sed -nE 's/.*"full": "([^"]*)".*/\1/p' )
curl https://362227.top/rss/file.php?text=$txt 

sudo bash 刷vimeo的hash.sh $num
