import sys
import asyncio
import aiohttp
import re
import os
import argparse
import time

# 限制最大并发数
semaphore = asyncio.Semaphore(300)

# 提取链接中的最后连续数字作为文件名
def extract_filename_from_url(url):
    match = re.search(r'(\d+)(?!.*\d)', url)
    return match.group(1) if match else 'unknown'

# 异步下载函数
async def download_link(session, url, referer, download_dir):
    async with semaphore:  # 限制并发
        filename = extract_filename_from_url(url)
        file_path = os.path.join(download_dir, filename)
        os.makedirs(download_dir, exist_ok=True)  # 创建下载目录

        retry_count = 0
        max_retries = 15  # 最大重试次数
        retry_delay = 1  # 初始重试延迟(秒)
        max_delay = 60  # 最大重试延迟(秒)

        while retry_count <= max_retries:
            try:
                headers = {'Referer': referer}
                async with session.get(url, headers=headers, timeout=30) as response:
                    # 根据状态码做出处理
                    if response.status == 200:
                        content = await response.read()
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        print(f"Downloaded {file_path}")
                        return  # 成功下载，跳出函数
                    elif response.status == 403:
                        print(f"403 Forbidden: {url}, retrying {retry_count + 1}/{max_retries}")
                        retry_count += 1
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, max_delay)  # 指数退避
                    elif response.status in [404, 429]:
                        print(f"Skipping {url} due to status {response.status}")
                        return  # 跳过此文件
                    elif response.status in [500, 503]:
                        print(f"Server error {response.status} on {url}, retrying {retry_count + 1}/{max_retries}")
                        retry_count += 1
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, max_delay)  # 指数退避
                    else:
                        print(f"Failed to download {url} with status {response.status}")
                        return  # 其他状态码直接跳出
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"Error downloading {url}: {e}, retrying {retry_count + 1}/{max_retries}")
                retry_count += 1
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)  # 指数退避
            except Exception as e:
                print(f"Fatal error downloading {url}: {e}")
                return  # 遇到非网络/服务器错误时直接跳出

        # 如果重试超过最大次数依然失败
        print(f"Failed to download {url} after {max_retries} retries.")

# 读取链接并进行异步下载
async def main(file_path, download_dir, referer):
    with open(file_path, 'r') as f:
        urls = [line.strip() for line in f if line.startswith('http')]

    if not urls:
        print("No valid URLs found in the file.")
        return

    async with aiohttp.ClientSession() as session:
        tasks = [download_link(session, url, referer, download_dir) for url in urls]
        await asyncio.gather(*tasks)

# 解析命令行参数并运行异步任务
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download files with custom referer and paths.")
    parser.add_argument("-i", "--input", required=True, help="Path to the file containing URLs.")
    parser.add_argument("-d", "--download_dir", required=True, help="Directory to save downloaded files.")
    parser.add_argument("-r", "--referer", required=True, help="Referer URL for HTTP headers.")

    args = parser.parse_args()

    # 启动异步下载
    asyncio.run(main(args.input, args.download_dir, args.referer))
