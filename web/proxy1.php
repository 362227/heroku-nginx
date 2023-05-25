<?php
// https://*****.onrender.com/vimeo.php， onrender下载这个proxy1.php并重命名为oldvimeo.php
$t1 = microtime(true);


ini_set('display_errors','off');
date_default_timezone_set('PRC');
$link=$_GET["link"]; 
$url=$_GET["url"]; 
$ref=$_GET["ref"]; 
$token=$_GET["token"];
$name=$_GET["name"];
$org=$_GET["org"];


if  (strstr($link, "http")){ 
    
    $res = shell_exec("curl -L \"$link\" ");
    $res = preg_replace('/^$|.*You Have been banned.*/',$_SERVER['HTTP_HOST'].' 抓hash时出错'.$link, $res); 
    echo $res;
    exit;
}







$id = preg_replace('/.+?\/([0-9]{1,9}).*/','$1', $url); 
//echo $id;
//exit;

//如果是hash链接
if (strstr($url, "?h=")){    
      $result = shell_exec("curl $url "); 


$res = preg_replace('/[\s\S]*window.playerConfig \= |    var fullscreenSupported[\s\S]*/','', $result); //删除无效数据，提取json数据
$data = json_decode($res, true);

$title = $data['video']['title'];
$author_name = $data['video']['owner']['name']; 
$account_type = $data['video']['owner']['account_type']; 
$duration = $data['video']['duration']; 
$thumbnail_url = $data['video']['thumbs']['base']; 
$uri = $data['video']['share_url']; 
    
   
   
 if (strstr($result, "avc_url")){
     
     
  echo  'title>'.$title.'  from '.$author_name.'</title><br>"share_url":"'.$uri.'""duration":'.$duration.',"account_type":"'.$account_type.'","name":"'.$author_name.'"<br><img src="'.$thumbnail_url.'?mw=240"  alt="img" >';
}else if (strstr($result, "this video cannot be played here") ){  //如果出现403
 
  $url = preg_replace('/player\.|video\//','', $url);
  $url = preg_replace('/\?h\=/','/', $url);
  echo $url; 
    
}
}











//如果是非hash链接
else {

$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, 'https://player.vimeo.com/video/'.$id);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'GET');

curl_setopt($ch, CURLOPT_ENCODING, 'gzip, deflate');


$headers = array();
$headers[] = 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9';
$headers[] = 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,fr;q=0.6,ru;q=0.5';
$headers[] = 'Cache-Control: max-age=0';
$headers[] = 'Connection: keep-alive';
$headers[] = 'Cookie: vuid=13se&geolocation=US%3BNV; OptanonAlertBoxClosed=2022-06-07T03:09:00.308Z; __cf_bm=hdM6BzJ5ZoUnhu38JlLdGoiOed1XjlOLkOO3D8pz8eU-1654582551-0-AaLvJIF3QJCD1RHRPrCjw7XOeDDwsScCg8Z9XKbm2TngJk=';
$headers[] = 'Sec-Fetch-Dest: document';
$headers[] = 'Sec-Fetch-Mode: navigate';
$headers[] = 'Sec-Fetch-Site: none';
$headers[] = 'Sec-Fetch-User: ?1';
$headers[] = 'Referer:'. $ref;
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

$result = curl_exec($ch);

if ($org == 1 ) {echo $result; exit;} //如果url添加&org=1，则输出原始内容

$res = preg_replace('/[\s\S]*window.playerConfig \= |    var fullscreenSupported[\s\S]*/','', $result); //删除无效数据，提取json数据
$data = json_decode($res, true);

$title = $data['video']['title'];
$author_name = $data['video']['owner']['name']; 
$account_type = $data['video']['owner']['account_type']; 
$duration = $data['video']['duration']; 
$thumbnail_url = $data['video']['thumbs']['base']; 
$uri = $data['video']['share_url']; 







$array = array( 
"https://www.petgorilla.com/"  ,
  "http://malloybrothers.com/"  ); 


$array_chunked = array_chunk($array, ceil(count($array) / 2));

$array1 = $array_chunked[0];
$array2 = $array_chunked[1];






//新方法新方法新方法新方法新方法新方法新方法新方法新方法新方法新方法

 if (strstr($result, "avc_url")){
     
     
  echo  'title>'.$title.'  from '.$author_name.'</title><br>"share_url":"'.$uri.'""duration":'.$duration.',"account_type":"'.$account_type.'","name":"'.$author_name.'"<br><img src="'.$thumbnail_url.'?mw=240"  alt="img" >';
}else if (strstr($result, "this video cannot be played here") ){  //如果出现403
    
    
    


$loop_count = count($array) / 2;
for ($i = 0; $i < $loop_count; $i++) {
  $ref1 = $array1[$i];$ref1 = empty($ref1) ? "无效" : $ref1;
  $ref2 = $array2[$i];$ref2 = empty($ref2) ? "无效" : $ref2;
  $curl_cmd = "curl https://player.vimeo.com/video/$id --referer$ref1 & curl https://player.vimeo.com/video/$id --referer$ref2 ";
 //echo $curl_cmd;
  $result = shell_exec($curl_cmd);
  

    
    
    
    
    
    if (strstr($result, "avc_url")){

$res = preg_replace('/[\s\S]*window.playerConfig \= |    var fullscreenSupported[\s\S]*/','', $result); //删除无效数据，提取json数据
$data = json_decode($res, true);

$title = $data['video']['title'];
$author_name = $data['video']['owner']['name']; 
$account_type = $data['video']['owner']['account_type']; 
$duration = $data['video']['duration']; 
$thumbnail_url = $data['video']['thumbs']['base']; 
$uri = $data['video']['share_url']; 


        echo  'title>'.$title.'  from '.$author_name.'</title><br>"share_url":"'.$uri.'""duration":'.$duration.',"account_type":"'.$account_type.'","name":"'.$author_name.'"<br><img src="'.$thumbnail_url.'?mw=240"  alt="img" >';
      break; 
   
    }
   
}
  if (!strstr($result, "avc_url")){
      echo $id."有ref有ref有ref有ref有ref有ref有ref有ref有ref有ref有ref有ref有ref有ref"; 
     }

 
 
}

 

else if (strstr($result, "This video does not exist.")) {
     echo "https://vimeo.com/api/oembed.json?url=https://vimeo.com/".$id."
     out=".$id;  //404不管三七二十一全部反馈https://vimeo.com/api/oembed.json?url=https://vimeo.com/
}

else

{  //如果不是403，也不包含avc_url，那就是其他的了，比如404、完全隐藏、有密码、真人验证、被封提示等等，这种情况下，验证码和被封提示被替换成空（便于被识别失败的链接），其他则替换成10362227
   
    if (strstr($result, "You Have been banned.")  || strstr($result, "CAPTCHA Challenge") ) { $result = preg_replace('/[\s\S]*/','', $result);}//如果有验证码或者被封，则输出为空
    $result = str_replace($result, '103622271036222710362227103622271036222710362227', $result); //只要出现字符，就全部替换成10362227

    echo $result;}
}


$t2 = microtime(true);
//echo '程序耗时'.round($t2-$t1,3).'秒';

exit;
//新方法新方法新方法新方法新方法新方法新方法新方法新方法新方法新方法





















$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);


$result = preg_replace('/[\s\S]*CAPTCHA Challenge[\s\S]*/','', $result); //如果有验证码，全部清空内容
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
 


$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);








if (strlen($result) > 556)  {
    exit;
    
}



else {

if (strlen($result) > 6 && $content === "this video cannot be played here") {
    
    
foreach ($array as $ref) { 


$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'GET');

curl_setopt($ch, CURLOPT_ENCODING, 'gzip, deflate');

$headers = array();
$headers[] = 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9';
$headers[] = 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,fr;q=0.6,ru;q=0.5';
$headers[] = 'Cache-Control: max-age=0';
$headers[] = 'Connection: keep-alive';
$headers[] = 'Cookie: vuid=13se&geolocation=US%3BNV; OptanonAlertBoxClosed=2022-06-07T03:09:00.308Z; __cf_bm=hdM6BzJ5ZoUnhu38JlLdGoiOed1XjlOLkOO3D8pz8eU-1654582551-0-AaLvJIF3QJCD1RHRPrCjw7XOeDDwsScCg8Z9XKbm2TngJk=';
$headers[] = 'Sec-Fetch-Dest: document';
$headers[] = 'Sec-Fetch-Mode: navigate';
$headers[] = 'Sec-Fetch-Site: none';
$headers[] = 'Sec-Fetch-User: ?1';
$headers[] = 'Referer:'.$ref;
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);
    //echo $result;
    if (strstr($result, "title")){
      echo $result; 
      break; 
   
    }
   
}
  if (!strstr($result, "title")){
      echo "有ref"; 
     }

}




else if  (strlen($result) > 6) {echo $result;}  //如果有数据输出，且没有出现“this video cannot be played here”，即输出最普通的（无ref，可能有，也可能404，带密码，私密等等）

else  {   //上述条件均不满足（即无数据输出，curl_php遇到验证码确实是无数据输出），就是有验证码了

 
 
$name1  = preg_replace('/(.*)[0-9]{3}php$/','$1', $name);

$arr = array(
    'https://'.$name1.'003php.herokuapp.com/proxy.php?url='.$url.'&ref='.$ref.'&name='.$name1.'003php&token=0e8635cf-e01e-4d5d-b778-53bb2ec48453',
    'https://'.$name1.'003php.herokuapp.com/proxy.php?url='.$url.'&ref='.$ref.'&name='.$name1.'003php&token=0e8635cf-e01e-4d5d-b778-53bb2ec48453'
);
$key = array_rand($arr, 1);
//输出随机内容
// echo $arr[$key];
echo file_get_contents ($arr[$key]);







$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, 'https://api.heroku.com/apps/'.$name.'/dynos');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'DELETE');



$headers = array();
$headers[] = 'Content-Type: application/json';
$headers[] = 'Accept: application/vnd.heroku+json; version=3';
$headers[] = 'Authorization: Bearer '.$token;
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

$result = curl_exec($ch);
//file_put_contents(date('Y-m-d H:i:s').'log.txt', $result);




$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'GET');

curl_setopt($ch, CURLOPT_ENCODING, 'gzip, deflate');

$headers = array();
$headers[] = 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9';
$headers[] = 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7,fr;q=0.6,ru;q=0.5';
$headers[] = 'Cache-Control: max-age=0';
$headers[] = 'Connection: keep-alive';
$headers[] = 'Cookie: vuid=13se&geolocation=US%3BNV; OptanonAlertBoxClosed=2022-06-07T03:09:00.308Z; __cf_bm=hdM6BzJ5ZoUnhu38JlLdGoiOed1XjlOLkOO3D8pz8eU-1654582551-0-AaLvJIF3QJCD1RHRPrCjw7XOeDDwsScCg8Z9XKbm2TngJk=';
$headers[] = 'Sec-Fetch-Dest: document';
$headers[] = 'Sec-Fetch-Mode: navigate';
$headers[] = 'Sec-Fetch-Site: none';
$headers[] = 'Sec-Fetch-User: ?1';
$headers[] = 'Referer:'. $ref;
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

$result = curl_exec($ch);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);
echo $result;
}
}
