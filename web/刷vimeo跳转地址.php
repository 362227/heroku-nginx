<?php
$url=$_GET["url"]; 


// 读取所有行
$lines = shell_exec("curl -L https://crowncloud.362227.top/rss/urls.txt");

// 随机选择一个行号
$random_key = array_rand($lines);

// 取出对应的行内容
$random_line = $lines[$random_key];

// 去除行末的换行符
$host = rtrim($random_line, "\r\n");

$url = $host.'/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa';


header('Location: ' . $url);


exit;






$arr = array(
 //   'https://pistolwayne001php.herokuapp.com/proxy.php?url='.$url.'&ref=http://friendlondon.tv&name=pistolwayne003php&token=0e8635cf-e01e-4d5d-b778-53bb2ec48453',
 //   'https://pistolwayne002php.herokuapp.com/proxy.php?url='.$url.'&ref=http://friendlondon.tv&name=pistolwayne002php&token=0e8635cf-e01e-4d5d-b778-53bb2ec48453',
    //'https://pistolwayne003php.herokuapp.com/proxy.php?url='.$url.'&ref=http://friendlondon.tv&name=pistolwayne001php&token=0e8635cf-e01e-4d5d-b778-53bb2ec48453',




/*
'https://crowncloud.362227.top/rss/刷vimeo跳转地址.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
//'http://pistolwayne.byethost22.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://bnmiwztvf.byethost17.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://yishaofang.byethost5.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://10362227.byethost24.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://p1956.byethost17.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',

'http://admin001.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://admin002.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://admin003.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://admin004.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://admin005.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://admin006.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://admin007.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://admin008.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://admin009.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://admin010.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',

'http://kai001.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kai002.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kai003.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kai004.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kai005.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kai006.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kai007.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kai008.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kai009.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kai010.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',


'http://p1956.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://p195601.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://p195602.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://p195603.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://p195604.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://p195605.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://p195606.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://p195607.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://p195608.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://p195609.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',


'http://yishaofang.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',

'http://1036222701.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://1036222702.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://1036222703.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://1036222704.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://1036222705.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://1036222706.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://1036222707.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://1036222708.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',


'http://kel001.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kel002.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kel003.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kel004.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kel005.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'http://kel006.vastserve.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
*/



'https://vimeo362227.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-1.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-2.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-3.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-4.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-5.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-6.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-7.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-8.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-9.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
//'https://vimeo362227-10.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-11.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-12.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-13.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-14.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-15.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-16.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-17.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-18.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-19-7hgu.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-20.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-21.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-22.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-23.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-24.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://vimeo362227-25.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',



//'https://ellie001.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://ellie002.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://ellie003.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://ellie004.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://ellie005.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://ellie006.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
//'https://ellie007.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://ellie008.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
//'https://ellie009.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://ellie010.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',


'https://kai005.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
'https://kai006.onrender.com/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',















//'https://php-in-vercel-xpdv.vercel.app/api/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
//'https://php-in-vercel-na8v.vercel.app/api/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
//'https://php-in-vercel-flame.vercel.app/api/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
//'https://php-in-vercel-jxt5.vercel.app/api/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
//'https://php-in-vercel-feiz.vercel.app/api/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
//'https://php-in-vercel-1nvw.vercel.app/api/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
//'https://php-in-vercel-7c24.vercel.app/api/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
//'https://php-in-vercel.vercel.app/api/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',
//'https://php-in-vercel-wheat.vercel.app/vimeo.php?url='.$url.'&ref=http://friendlondon.tv&name=sovj2weiosjke003php&token=fa54fb92-335d-4f1b-93c7-7c01efce63aa',


    

);
$key = array_rand($arr, 1);

header('Location: ' . $arr[$key]);
