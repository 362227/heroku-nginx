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
 


$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

//echo $result;

if (strlen($result) > 556)  {
    exit;
    
}

else {

if (strlen($result) > 6 && $content === "this video cannot be played here") {
    
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
$headers[] = 'Referer:https://www.colorcollective.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
    if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://www.treyfanjoy.com/';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
         if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:http://www.pulsefilms.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
  
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
$headers[] = 'Referer:https://boyinthecastle.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {

            
            
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
$headers[] = 'Referer:http://www.mathieuplainfosse.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {          
            
            
            
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
$headers[] = 'Referer:https://www.lane-casting.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {  
            
            
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
$headers[] = 'Referer:http://www.305films.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://www.company3.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://electrictheatre.tv';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://contrast.tv';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://sesler.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://www.els.tv';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://moxiepictures.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://www.lutimedia.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://dugdale.tv';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://the-quarry.co.uk';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://www.finalcut-edit.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://therapystudios.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:http://www.chrisroebuck.tv';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://blackdogfilms.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {

 
 
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
$headers[] = 'Referer:http://malloybrothers.com/';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
 
 
 
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
$headers[] = 'Referer:http://www.benzene.paris/';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
 
 
 
 
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
$headers[] = 'Referer:https://samuelbayer.com/';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {


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
$headers[] = 'Referer:https://alexanderhammer.com/';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
            


      
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
$headers[] = 'Referer:https://www.tenthree.co.uk';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
  
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
$headers[] = 'Referer:https://modernpost.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:http://friendlondon.tv';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {

            


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
$headers[] = 'Referer:http://www.davidbaumeditor.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
  
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
$headers[] = 'Referer:https://ways-means.co';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://foreign-xchange.co';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {

         
            
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
$headers[] = 'Referer:http://trimediting.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://makemakeentertainment.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://nomadedit.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
  
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
$headers[] = 'Referer:http://www.resetcontent.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://believemedia.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://www.schemeengine.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        
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
$headers[] = 'Referer:https://visionfilmco.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
     
         
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
$headers[] = 'Referer:https://coffeeand.tv/';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
         
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
$headers[] = 'Referer:https://www.kaisaul.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
 
            
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
$headers[] = 'Referer:https://www.pulsefilms.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
            
            
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
$headers[] = 'Referer:http://www.romanwhite.com';
$headers[] = 'Upgrade-Insecure-Requests: 1';
$headers[] = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36';
$headers[] = 'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"';
$headers[] = 'Sec-Ch-Ua-Mobile: ?0';
$headers[] = 'Sec-Ch-Ua-Platform: \"Windows\"';
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
$result = curl_exec($ch);
$content= preg_replace('/[\s\S]*this video cannot be played here[\s\S]*/','this video cannot be played here', $result);
        if ($content === "this video cannot be played here") {
        

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
$headers[] = 'Referer:http://www.jonasakerlund.com';
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

echo $result;

}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
////$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);
  
echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);
 
echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;

}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;

}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;


}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;


}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;


}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
 
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
 
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}
else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
}
}

else {
$result = preg_replace('/[\s\S]*(\<title\>.+?\<\/title\>)[\s\S]*\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?thumbs".+?\"\:\"(.+?)\_.+?(\"name\"\:\".+?\").+?(\,\"account\_type\"\:\".+?\")[\s\S]*/','$1<br>$3$2$6$5<br><img src="$4?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.*(\"duration\"\:[0-9]{1,20}\,).*(account_type\"\:\".+?\",\"name\"\:\".+?\").*\"\,\"title\"\:\".+?\"\,(\"share\_url\"\:\".+?\").*/','$1<br>$3$4$5<br><img src="$2?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/.*(title>.+?<\/title>).*thumb\.src \= \"(.+?)\?.+?(account_type\"\:\".+?\",\"name\"\:\".+?\").*(\"share\_url\"\:\".+?\").*(\"duration\"\:[0-9]{1,20}\,).*/','$1<br>$5$3$4<br><img src="$2?mw=240"  alt="img" /><br>', $result);
//$result = preg_replace('/[\s\S]*\"title\"\:\"(.+?)\"\,\"width.*(\"duration\"\:.+?\,).+?(\"share_url\"\:\".+?\").+?(\"name\"\:\".+?\").+?(\"account\_type\"\:\".+?\")\}\,\"spatial.*\"thumbnail\"\:\"(.+?)\"[\s\S]*/','$1<br>$2$5$4$3<br><img src="$6?mw=240"  alt="img" /><br>', $result);
$result = preg_replace('/fallback |<title>|script>/','title>', $result);
$result = preg_replace('/[\s\S]*DOCTYPE html[\s\S]*|[\s\S]*this video cannot be played here[\s\S]*/','00000000000', $result);

echo $result;
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
file_put_contents(date('Y-m-d H:i:s').'log.txt', $result);




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















