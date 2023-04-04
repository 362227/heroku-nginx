<?php
$url=$_GET["url"]; 


// 读取所有行
$lines = explode("\n", shell_exec("curl -L https://crowncloud.362227.top/rss/urls.txt"));

// 随机选择一个行号
$random_key = array_rand($lines);

// 取出对应的行内容
$random_line = $lines[$random_key];

// 去除行末的换行符
$host = rtrim($random_line, "\r\n");

$url = $host.'/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa';


header('Location: ' . $url);
