#!/bin/bash

# Set the maximum number of workers
MAX_WORKERS=$1

# Define a function to upload a file
function upload_file {
    file=$1
    $2 fake115uploader -e --oss-proxy http://127.0.0.1:1083 -c 2596786305585036490 -u "$file" || $2 fake115uploader -e --oss-proxy http://127.0.0.1:1083 -c 2596786305585036490  -parts-num 37 -m "$file"
    fake115uploader -e  -c 2596786305585036490 -u "$file" || fake115uploader -e -c 2596786305585036490  -parts-num 37 -m "$file"
}

# Export the upload_file function so that it can be used by xargs
export -f upload_file

# Define a signal handler function to catch CTRL+C signal
function sigint_handler {
    echo "Interrupt signal received. Stopping the script."
    # terminate xargs and any running fake115uploader processes
    pkill -P $$
    exit 1
}

# Trap the CTRL+C signal and call the sigint_handler function
trap sigint_handler INT

# Use find to locate all files in /var/www/html/tx/
# Pass each file to xargs to upload
find /var/www/html/tx/ -type f -print0 | \
    xargs -r -0 -P $MAX_WORKERS -I {} bash -c 'upload_file "$@"' _ {}

echo "All commands have completed."
