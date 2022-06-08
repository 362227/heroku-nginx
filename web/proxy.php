<?php
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
$headers[] = 'Referer:http://www.jonasakerlund.com';
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
$headers[] = 'Referer:https://www.roguefilms.co.uk';
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
$headers[] = 'Referer:http://www.305films.tv';
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
$headers[] = 'Referer:https://www.oneshotmike.com';
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
$headers[] = 'Referer:https://lockteditorial.com';
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
$headers[] = 'Referer:https://editorjon.co.uk';
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
$headers[] = 'Referer:https://www.echoartists.com';
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
echo $result;

}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}
else {
echo $result;
}
}

else {
echo $result;
}

}

else if  (strlen($result) > 6) {echo $result;}

else  {


$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, 'https://api.heroku.com/apps/'.$name.'/dynos');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'DELETE');

    
    
$arr = array(
    'https://phpweb362227mxs.herokuapp.com/proxy.php?url='.$url.'&ref=abcdef&name=phpweb362227mxs&token=f24c45c0-c8fa-4b0f-b63',
    'https://phpweb362227dvi.herokuapp.com/proxy.php?url='.$url.'&ref=abcdef&name=phpweb362227dvi&token=bb328733-d0fd-4dce-bc2',
    'https://phpweb362227toc.herokuapp.com/proxy.php?url='.$url.'&ref=abcdef&name=phpweb362227toc&token=359b6921-a8a0-4c7b-9b6',
    'https://phpweb362227otb.herokuapp.com/proxy.php?url='.$url.'&ref=abcdef&name=phpweb362227otb&token=6e84e952-e8b7-4aba-88f',
    'https://phpweb362227znx.herokuapp.com/proxy.php?url='.$url.'&ref=abcdef&name=phpweb362227znx&token=36057f92-15df-41e8-8f2',
    'https://phpweb362227sdl.herokuapp.com/proxy.php?url='.$url.'&ref=abcdef&name=phpweb362227sdl&token=da9eea96-bd5b-4ca8-999',
    'https://phpweb362227iho.herokuapp.com/proxy.php?url='.$url.'&ref=abcdef&name=phpweb362227iho&token=e97ac6ea-ad31-4684-bf7',
    'https://phpweb362227uqe.herokuapp.com/proxy.php?url='.$url.'&ref=abcdef&name=phpweb362227uqe&token=78fcd56a-0a64-4f49-984',
    'https://phpweb362227kfm.herokuapp.com/proxy.php?url='.$url.'&ref=abcdef&name=phpweb362227kfm&token=06f7a8be-9486-4ba8-983',
    'https://phpweb362227kiy.herokuapp.com/proxy.php?url='.$url.'&ref=abcdef&name=phpweb362227kiy&token=3150e145-5af5-4a0e-89b'
);
$key = array_rand($arr, 1);
echo file_get_contents ($arr[$key]);
    

//重启APP
$headers = array();
$headers[] = 'Content-Type: application/json';
$headers[] = 'Accept: application/vnd.heroku+json; version=3';
$headers[] = 'Authorization: Bearer '.$token;
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

$result = curl_exec($ch);
file_put_contents('log.txt', $result);








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
echo $result;
}

