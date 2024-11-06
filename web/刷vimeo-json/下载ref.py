import sys
import asyncio
import aiohttp
import re
import os

# 文件路径
file_path = 'links.txt'
# 下载目录的绝对路径
download_dir = "C:/downloads"
# 限制最大并发数
semaphore = asyncio.Semaphore(200)

# 提取链接中的最后连续数字作为文件名
def extract_filename_from_url(url):
    match = re.search(r'(\d+)(?!.*\d)', url)
    return match.group(1) if match else 'unknown'

# 异步下载函数
async def download_link(session, url, referer):
    async with semaphore:  # 限制并发
        filename = extract_filename_from_url(url)
        file_path = os.path.join(download_dir, filename)
        os.makedirs(download_dir, exist_ok=True)  # 创建下载目录

        try:
            headers = {'Referer': referer}
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    print(f"Downloaded {file_path}")
                else:
                    print(f"Failed to download {url} with status {response.status}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")

# 读取链接并进行异步下载
async def main(referer):
    with open(file_path, 'r') as f:
        urls = [line.strip() for line in f if line.startswith('http')]

    if not urls:
        print("No valid URLs found in the file.")
        return

    async with aiohttp.ClientSession() as session:
        tasks = [download_link(session, url, referer) for url in urls]
        await asyncio.gather(*tasks)

# 运行异步任务
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a referer URL as a command-line argument.")
        sys.exit(1)

    referer = sys.argv[1]
    asyncio.run(main(referer))
