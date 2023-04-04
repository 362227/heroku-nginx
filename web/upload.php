<?php
$upload_folder = './';  // 上传文件保存的目录
$max_size = 1048576000;  // 最大允许上传的文件大小（单位：字节），这里设置为 1000 MB

// 检查是否有文件上传
if (empty($_FILES['file'])) {
    http_response_code(400);
    echo "No file uploaded";
    exit;
}

// 检查上传的文件是否有错误
if ($_FILES['file']['error'] !== UPLOAD_ERR_OK) {
    http_response_code(400);
    echo "Error uploading file: {$_FILES['file']['error']}";
    exit;
}

// 检查上传的文件大小是否超出限制
if ($_FILES['file']['size'] > $max_size) {
    http_response_code(400);
    echo "File size exceeds limit of {$max_size} bytes";
    exit;
}

// 将上传的文件移动到指定的目录
$filename = basename($_FILES['file']['name']);
$filepath = "{$upload_folder}/{$filename}";
if (move_uploaded_file($_FILES['file']['tmp_name'], $filepath)) {
    http_response_code(200);
    echo "File uploaded successfully
    ";
} else {
    http_response_code(500);
    echo "Error moving file to upload folder";
}
