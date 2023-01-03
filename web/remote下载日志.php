<style>
pre{font-size: 16px; font-family: "微软雅黑"; }
</style>



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





$file_path = "remote下载日志.txt" ;


if(file_exists($file_path)) {
echo '<a href="查看UTF8完整版日志.php?file='.$file_path.'" target="_blank"><h3>下载进度</h3></a>';
 
$content = file_get_contents ($file_path);
$content = preg_replace('/[\s\S]* \*\*\*([\s\S]*)/','$1', $content);
$content = str_replace("===============================================================================","",$content);
$content = str_replace("-------------------------------------------------------------------------------","<br>",$content);
$content = str_replace("\n","<br>",$content);
echo "<p class='break-all'><font size=2>".$content."</font></p>";
 
 
$A=strtotime("now");
$B=date(filemtime($file_path));

$C= $A-$B;

if ( $C < 7) { 
if ( file_exists ( $file_path )){
$file_arr = file( $file_path );
for ( $i =0; $i < count ( $content ); $i ++){ //逐行读取文件内容
//echo $file_arr [ $i ]. "<br>" ;
$content = $file_arr [ $i ]. "<br>" ;
$content = preg_replace('/[\s\S]*(gdrivedl.+?00MB)/','$1', $content);
$content= preg_replace('/[\s\S]*(\[download\].*)/','$1', $content);
$content = preg_replace('/[\s\S]*( \*\*\*[\s\S]*)/','$1', $content);
echo '<p class="break-all"><font size=2>'.$content.'</font></p>';
}


}
}

else {   //如果修改时间大于55秒，说明下载中断/完成

if ( file_exists ( $file_path )){
$file_arr = file( $file_path );
for ( $i =0; $i < count ( $file_arr ); $i ++){ //逐行读取文件内容
//echo $file_arr [ $i ]. "<br>" ;
$content = preg_replace('/.*\: Downloading.*/','', $file_arr);
$content = $file_arr [ $i ]. "" ;
$content = preg_replace('/[\s\S]*(\[download\].*)/','$1', $content);
$content = preg_replace('/[\s\S]*(gdrivedl.+?00MB)/','$1', $content);
$content = preg_replace('/.*\: Downloading.*|.*\[redirect\].*/','', $content); //去除Downloading行
$content = preg_replace('/.* ETA\:.*/','', $content); //去除aria2c行
$content = preg_replace('/.*CN\:1 DL.*/','', $content); //去除aria2c行
$content = preg_replace('/(^\[.*)/','<br>$1$2', $content); //保留有用的，在每行的[添加<br>，让页面看起来正常

// echo $content;
                                             }
                  }

}
}
?>
