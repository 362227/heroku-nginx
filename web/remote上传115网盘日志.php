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




$file_path = "remote上传115网盘日志.txt";
if(file_exists($file_path)) {echo '<a href="查看UTF8完整版日志.php?file=remote上传115网盘日志.txt" target="_blank"><h3>上传115网盘进度</h3></a>';

$A=strtotime("now");
$B=date(filemtime($file_path));
$C= $A - $B;

if ( $C < 5) { 
    
$content = file_get_contents($file_path);	
$content1 = preg_replace('/[\s\S]*([\s\S]{280}$)/','$1', $content); //读取后面280个字符
echo '<p class="break-all">'.$content1.'</p>';
}               
 
else {
$content = file_get_contents($file_path);	
$content1 = preg_replace('/[\s\S]*([\s\S]{280}$)/','$1', $content); //读取后面280个字符
$content2 = preg_replace('/[\s\S]*上传成功的文件/','上传成功的文件', $content1); //读取后面280个字符
echo '<p class="break-all">'.$content2.'</p>';
 
 
}   
}
?>
