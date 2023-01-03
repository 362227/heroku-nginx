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



$file_path = "remote上传百度网盘日志.txt" ;
if ( file_exists ( $file_path )){
echo '<a href="查看UTF8完整版日志.php?file='.$file_path.'" target="_blank"><h3>上传百度网盘进度</h3></a>';
$file_arr = file( $file_path );
for ( $i =0; $i < count ( $file_arr ); $i ++){ //逐行读取文件内容
$resault = $file_arr [ $i ]. "<br />" ;

}

if (preg_match_all('/上传结束/', file_get_contents('remote上传百度网盘日志.txt', $url), $links)){
    

echo '<font color="#F12A0B">'.preg_replace('/[\s\S]*(上传结束.*)/','$1', file_get_contents('remote上传百度网盘日志.txt')).'</font>';

    }

else {
for ( $i =0; $i < count ( $file_arr ); $i ++){ //逐行读取文件内容
$file_arr [ $i ] = str_replace("............","............<br>",$file_arr [ $i ]);
echo "<font size=2>".$file_arr [ $i ]. "</font><br />" ;}
}
}
