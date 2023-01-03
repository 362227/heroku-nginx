<?php
ini_set('display_errors','off');

echo '
<style>.keep-all {
 word-break: keep-all;
}
.break-all {
 word-break: break-all;
}
.keep-all, .break-all {
 width: 100%; 
 font-size: 16px;
 display: inline-block;
}

#wrap{white-space:normal; width:90%; }
#word-wrap:break-word;
</style>';


$file =file_get_contents('remote上传谷歌网盘日志.txt');
if(file_exists("remote上传谷歌网盘日志.txt")) {echo '<a href="查看UTF8完整版日志.php?file=remote上传谷歌网盘日志.txt'.$file_path.'" target="_blank"><h3>上传谷歌网盘进度</h3></a>';}

$file1 = preg_replace('/[\s\S]*(\* [\s\S]*Elapsed time.*)/','$1', $file); 
$file2 = preg_replace('/\n|[\s\S]*Elapsed time.+?\/ 0 Bytes.*/','<br>', $file1); 
echo '<p class="break-all">'.$file2.'</p>';
?>
