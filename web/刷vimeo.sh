#!/bin/bash
num=$1

python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接.py -n $num -t /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接01.txt
python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接.py -n $num -t /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接02.txt

aria2c  --check-certificate=false --referer=http://friendlondon.tv -i "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接01.txt" --file-allocation=none --max-concurrent-downloads=770 --disk-cache=0 --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01 --max-download-result=1000 | tee /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999.log"
aria2c  --check-certificate=false --referer=http://friendlondon.tv -i "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/链接02.txt" --file-allocation=none --max-concurrent-downloads=770 --disk-cache=0 --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/02 --max-download-result=1000 | tee -a /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/合并$num"000000"-$num"999999.log"
python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/从log文件提取有ref的链接.py > /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/有ref的链接.txt

IP=( "https://visualcreatures.com/ " "https://www.gwenghelid.com" "http://www.colorcollective.com" "http://www.treyfanjoy.com/" "http://www.pulsefilms.com" "http://boyinthecastle.com" "http://www.mathieuplainfosse.com" "http://www.lutimedia.com" "http://moxiepictures.com" "http://www.els.tv" "http://sesler.com" "http://contrast.tv" "http://www.finalcut-edit.com" "http://the-quarry.co.uk" "http://therapystudios.com" "http://www.chrisroebuck.tv" "http://blackdogfilms.com" "http://malloybrothers.com/" "http://www.305films.com" "http://www.company3.com"   ); IP1=( "http://electrictheatre.tv" "http://www.benzene.paris/" "http://www.tenthree.co.uk" "http://alexanderhammer.com/" "http://samuelbayer.com/" "http://www.davidbaumeditor.com" "http://ways-means.co" "http://http://trimediting.com" "http://makemakeentertainment.com" "http://www.jonasakerlund.com" "http://www.romanwhite.com" "http://www.pulsefilms.com" "http://www.kaisaul.com" "http://coffeeand.tv/" "http://visionfilmco.com" "http://www.schemeengine.com" "http://believemedia.com" "http://www.resetcontent.com" "http://modernpost.com/" "http://www.lane-casting.com"  ) ; for i in "${IP[@]}";do aria2c  --referer=$i -i "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/有ref的链接.txt" --file-allocation=none --max-concurrent-downloads=500 --disk-cache=0 --check-certificate=false --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/ref; done & for i1 in "${IP1[@]}";do aria2c  --referer=$i1 -i "/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/有ref的链接.txt" --file-allocation=none --max-concurrent-downloads=494 --disk-cache=0 --check-certificate=false --dir=/mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/ref; done  & python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/正则预处理小文件.py -p /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/01 &&  python /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/正则预处理小文件.py -p /mnt/d/常用/vimeo/传统方法刷-下载后再处理数据/temp/02  
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

 
