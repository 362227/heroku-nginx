<?php
header("content-type:text/html;charset=utf-8");
$file = $_GET['file'];

$file_path = $file ;
if ( file_exists ( $file_path )){
$file_arr = file( $file_path );
for ( $i =0; $i < count ( $file_arr ); $i ++){ //逐行读取文件内容
echo $file_arr [ $i ]. "<br />" ;
}
/*
foreach($file_arr as $value){
echo $value."<br />";
}*/
}
?>

