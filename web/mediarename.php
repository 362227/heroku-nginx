<?php

$regex_link = '/.*/';
$regex_tit = '/.*/';


$dir = dirname("/var/www/html/TX/");




$path = "/var/www/html/TX/";

$html = shell_exec("find $path -maxdepth 1 -size +1M -type f ! -name *-Master-* "); //获取文件名
echo $html;
//exit;


$date=date("Y-m-d H");
if (preg_match_all($regex_link, $html, $filenames) ) {
    $size = count($filenames[0]);
    for ($i = 0;$i < $size;$i++) {
        $filename =  $filenames[0][$i];
        $name = preg_replace('/(.*)(\.[\s\S]{2,5}$)/','$1', $filename);
        $name = preg_replace('/\r|\n/','', $name);
        $ext = preg_replace('/(.*)(\.[\s\S]{2,5}$)/','$2', $filename);
        $ext = preg_replace('/\r|\n/','', $ext);
        
        $videoc = shell_exec("cd $path && mediainfo \"--Inform=Video;%Width%x%Height%%ScanType%-%Format%%CodecID%\"  \"$filename\" "); //获取音频编码
        $videoc = preg_replace('/\r|\n/','', $videoc);
        $audioc = shell_exec("cd $path && mediainfo \"--Inform=Audio;%Format%%Format_Profile%\"  \"$filename\" "); //获取音频编码
        $audioc = preg_replace('/\r|\n/','', $audioc);
        $newfilename = $name.' ('.$audioc.'-Master-'.$videoc.'-TX)'.$ext;
        $newfilename = preg_replace('/AVCV\_MPEG4\/ISO\/AVC/','H264', $newfilename);        
        
        




$str1="1280x720";
$str2="720";
$str3="1920x1080";
$str4="1080";
$str5="-AVC27";
$str6="-H264";
$str7="720x480";
$str8="480";
$str9="720x576";
$str10="576";
$str11="Progressive-";
$str12="p-";
$str13="Interlaced-";
$str14="i-";
$str15=",-";
$str16="-";
$str17="MPEG AudioLayer";
$str18="MP";
$str19="MPEG AudioLayer 3";
$str20="MP3";
$str21="MBAFF-";
$str22="i-";
$str25="(PCM-";
$str26="(LPCM-";
$str27="-AVCavc1";
$str28="-H264";
$str29="-VP9V_VP9";
$str30="-VP9";
$str31="ProResapco";
$str32="APCO";
$str33="AV1av01";
$str34="AV1";
$str35="ProResapcn";
$str36="APCN";
$str37="ProResapcs";
$str38="APCS";
$str39="ProResap4h";
$str40="AP4H";
$str41="MPEG Video2";
$str42="MPEG";
$str43="MPEG Video";
$str44="MPEG";
$str45="MPEG-4 Visualmp4v";
$str46="MPEG4";
$str47="-VP9";
$str48="p-VP9";
$str49="Opus-";
$str50="OPUS-";
$str51="AC-3-";
$str52="AC3-";
$str53="HEVChvc1";
$str54="HEVC";
$str55="-HEVC";
$str56="p-HEVC";
$str57="pp-HEVC";
$str58="p-HEVC";
$str59="OPUS-Master-3840x2160p-VP9-TX";
$str60="OPUS-YouTube-3840x2160p-VP9-TX";
$str61="OPUS-Master-1080p-VP9-TX";
$str62="OPUS-YouTube-1080p-VP9-TX";
$str63="MPEG-4 Visual20";
$str64="MPEG-4";
$str65="-JPEGjpeg";
$str66="p-JPEG";
$str67="MP2MP2";
$str68="MP2";
$str69="AVCV_MPEG4/ISO/AVC";
$str70="H264";


        
         $newfilename = str_replace( array("$str1","$str3","$str5","$str7","$str9","$str11","$str13","$str15","$str17","$str19","$str21","$str23","$str25","$str27","$str29","$str31","$str33","$str35","$str37","$str39","$str41","$str43","$str45","$str47","$str49","$str51","$str53","$str55","$str57","$str59","$str61","$str63","$str62"), array("$str2","$str4","$str6","$str8","$str10","$str12","$str14","$str16","$str18","$str20","$str22","$str24","$str26","$str28","$str30","$str32","$str34","$str36","$str38","$str40","$str42","$str44","$str46","$str48","$str50","$str52","$str54","$str56","$str58","$str60","$str62","$str64","$str66"),$newfilename);
        
        
        
        
        
        
        
        shell_exec("cd $path && mv \"$filename\" \"$newfilename\"");
    }
    echo $videoc;

}
else {
  echo $header.'<item> <title>出错，请检查 '.$date.'</title> <link>'.$url.'#'.$date.'</link></item>'.$footer;
}
?>
