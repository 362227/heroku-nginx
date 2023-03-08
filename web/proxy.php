<?php
// 修改
ini_set('display_errors','off');
date_default_timezone_set('PRC');
$url=$_GET["url"]; 
$ref=$_GET["ref"]; 
$token=$_GET["token"];
$name=$_GET["name"];

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
 


$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);


$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
 

$result = preg_replace('/[\s\S]*CAPTCHA Challenge[\s\S]*/','', $result); //如果有验证码，全部清空内容
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

//echo $result;
//exit;
$array = array( "https://www.colorcollective.com", 
"https://www.treyfanjoy.com/", 
"http://www.pulsefilms.com", 
"https://boyinthecastle.com", 
"http://www.mathieuplainfosse.com", 
"https://www.lutimedia.com", 
"https://moxiepictures.com", 
"https://www.els.tv", 
"https://sesler.com", 
"https://contrast.tv", 
"https://www.finalcut-edit.com", 
"https://the-quarry.co.uk",
"https://therapystudios.com", 
"http://www.chrisroebuck.tv",
"https://blackdogfilms.com",
"http://malloybrothers.com/",
"http://www.305films.com", 
"https://www.company3.com", 
"https://electrictheatre.tv", 
"http://www.benzene.paris/",
"http://friendlondon.tv",
"https://www.tenthree.co.uk",
"https://alexanderhammer.com/",
"https://samuelbayer.com/",
"http://www.davidbaumeditor.com",
"https://ways-means.co",
"https://http://trimediting.com",
"https://makemakeentertainment.com",
"http://www.jonasakerlund.com",
"http://www.romanwhite.com",
"https://www.pulsefilms.com",
"https://www.kaisaul.com",
"https://coffeeand.tv/",
"https://visionfilmco.com",
"https://www.schemeengine.com",
"https://believemedia.com",
"http://www.resetcontent.com",
"https://modernpost.com/", 
"https://www.lane-casting.com" ); 





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
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*CAPTCHA Challenge[\s\S]*/','有验证码', $result);
echo $result;
}
}














