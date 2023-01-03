<?php
ini_set('display_errors','off');
$actual_link = 'http://'.$_SERVER['HTTP_HOST']; 
$page = file_get_contents($actual_link.'/encodeexplorer.index.php?m&sort_by=mod&sort_as=desc&dir=backup/');
$page = str_replace("src=\"?img","src=\"/encodeexplorer.index.php?img",$page);
$page = str_replace("<a href=\"?s&amp;dir=backup/\">","<a href=\"/index.php?explorer&path=%2Fusr%2Fshare%2Fnginx%2Fkodexplorer%2Fremote%2Fbackup%2F\" target=\"_blank\">",$page);
$page = str_replace("已离线的文件，每个文件大约1-2小时后删","下载的文件",$page);
echo '<hr /><br>'.$page;






$page = file_get_contents($actual_link.'/encodeexplorer.index.php?m&sort_by=mod&sort_as=desc&dir=remote115mv/');
$page = str_replace("src=\"?img","src=\"/encodeexplorer.index.php?img",$page);
$page = str_replace("<a href=\"?s&amp;dir=remote115mv/\">","<a href=\"/index.php?explorer&path=%2Fusr%2Fshare%2Fnginx%2Fkodexplorer%2Fremote%2Fremote115mv%2F\" target=\"_blank\">",$page);
$page = str_replace("已离线的文件，每个文件大约1-2小时后删","MV，差上传115网盘",$page);
echo '<hr /><br>'.$page;



$page = file_get_contents($actual_link.'/encodeexplorer.index.php?m&sort_by=mod&sort_as=desc&dir=remote115live/');
$page = str_replace("src=\"?img","src=\"/encodeexplorer.index.php?img",$page);
$page = str_replace("<a href=\"?s&amp;dir=remote115live/\">","<a href=\"/index.php?explorer&path=%2Fusr%2Fshare%2Fnginx%2Fkodexplorer%2Fremote%2Fremote115live%2F\" target=\"_blank\">",$page);
$page = str_replace("已离线的文件，每个文件大约1-2小时后删","现场，差上传115网盘",$page);
echo '<hr /><br>'.$page;



$page = file_get_contents($actual_link.'/encodeexplorer.index.php?m&sort_by=mod&sort_as=desc&dir=remote115tx362227/');
$page = str_replace("src=\"?img","src=\"/encodeexplorer.index.php?img",$page);
$page = str_replace("<a href=\"?s&amp;dir=remote115tx362227/\">","<a href=\"/encodeexplorer.index.php?sort_by=mod&sort_as=desc&dir=remote115tx362227/\" target=\"_blank\">",$page);
$page = str_replace("已离线的文件，每个文件大约1-2小时后删","TX，差上传115网盘",$page);
echo '<hr /><br>'.$page;


$page = file_get_contents($actual_link.'/encodeexplorer.index.php?m&sort_by=mod&sort_as=desc&dir=spotify/');
$page = str_replace("src=\"?img","src=\"/encodeexplorer.index.php?img",$page);
$page = str_replace("<a href=\"?s&amp;dir=spotify/\">","<a href=\"/index.php?explorer&path=%2Fusr%2Fshare%2Fnginx%2Fkodexplorer%2Fremote%2Fspotify%2F\" target=\"_blank\">",$page);
$page = str_replace("已离线的文件，每个文件大约1-2小时后删","Spotify下载",$page);
echo '<hr /><br>'.$page;
