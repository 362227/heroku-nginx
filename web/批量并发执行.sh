#!/bin/bash

# Set the maximum number of workers
MAX_WORKERS=3

# Define a function to upload a file
function upload_file {
    file=$1
    fake115uploader -e --oss-proxy http://127.0.0.1:1083 -c 2051423373191282165 -u "$file; fake115uploader -e --oss-proxy http://127.0.0.1:1083 -c 2051423373191282165  -parts-num 37 -m "$file; "
}

# Export the upload_file function so that it can be used by xargs
export -f upload_file

# Use find to locate all files in /var/www/html/tx/
# Pass each file to xargs to upload
find /var/www/html/tx/ -type f -print0 | \
    xargs -0 -P $MAX_WORKERS -I {} bash -c 'upload_file "$@"' _ {}

echo "All commands have completed."
