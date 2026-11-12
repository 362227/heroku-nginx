#!/usr/bin/env python3
# baidu-upload.py: 百度网盘开放平台 (xpan + access_token) 上传。
# 分片、并发、重名策略、速度显示与之前的 Go 版一致；不用 BDUSS。
#
# 基本用法:
#   python3 baidu-upload.py -file ./a.zip -dest /备份/ -parallel 40 -norapid
#   python3 baidu-upload.py -file '/content/gofile-dl/bd/*.*' -dest /备份/
#
# 文件过滤 (语法同 rclone, 先用 -n 预览再上传):
#   python3 baidu-upload.py -file './*' -exclude '*.tmp' -exclude '*.part' -n
#   python3 baidu-upload.py -file './*' -include '*.{zip,7z,img}' -min-size 10M -max-age 7d
#   python3 baidu-upload.py -file ./data/ -R -exclude 'node_modules/' -exclude '.git/**' -dest /备份/data/
#   python3 baidu-upload.py -file ./data -R -filter-from rules.txt -ignore-case -v -n
#   python3 baidu-upload.py -files-from list.txt -dest /备份/
#
#   规则按命令行出现顺序匹配, 第一条命中的生效; 有 include 规则时末尾隐含 '- **'。
#   * 不跨 /, ** 跨 /, ? 单字符, [a-z] [!a-z], {a,b}, {{正则}};
#   开头 / 锚定到根(否则任意层级匹配), 结尾 / 只匹配目录。
#   -include/-exclude/-filter/-include-from/-exclude-from/-filter-from/-files-from
#   -min-size -max-size -min-age -max-age -ignore-case -R -max-depth -exclude-if-present -n -v
#
# 默认只上传文件: 目录被跳过, 不递归。加 -R 才进入目录;
#   目录以 / 结尾 (./data/) 只传内容, 否则保留目录名 (./data -> /备份/data/...)。
# 通配符建议加引号由脚本展开; *.* 只匹配带点的文件名, 隐藏文件需 Python 3.11+ 才会被通配符命中。
# -dest 默认 /，一律当作网盘目录，自动接上本地文件名。
# 重名策略，默认 size:
#   size      同名且大小相同则跳过，大小不同则覆盖
#   skip      只要同名就跳过
#   overwrite 一律覆盖
#   rsync     与 size 相同
# 分片: <8GB 用 4MB，>=8GB 用 16MB，>=32GB 用 64MB。默认只用 d.pcs.baidu.com。

import argparse
import glob
import hashlib
import json
import os
import posixpath
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

KB = 1 << 10
MB = 1 << 20
GB = 1 << 30

MIN_BLOCK = 4 * MB
MID_BLOCK = 16 * MB
MAX_BLOCK = 64 * MB
MID_THRESHOLD = 8 * GB
MAX_THRESHOLD = 32 * GB
RECOMMENDED = 32 * GB
MAX_SIZE = 128 * GB
SLICE_MD5 = 256 * KB
EMPTY_MD5 = "d41d8cd98f00b204e9800998ecf8427e"

SKIP, OVERWRITE, RSYNC, SIZE = "skip", "overwrite", "rsync", "size"
UA = "pan.baidu.com"
FIXED_HOST = "https://d.pcs.baidu.com"
SLICE_RETRY = 8
QUIET = False  # 多文件并发时关闭每个文件各自的 \r 进度行
G_DONE = [0]  # 全局已上传字节数 (所有文件)
G_LOCK = threading.Lock()


EXPIRED_CODES = (-6, 110, 111, 20016)  # token 无效/过期 (20016: nas access token expired)


class TokenExpired(RuntimeError):
    pass


class ApiError(Exception):
    def __init__(self, code, body):
        self.code = code
        self.body = body
        super().__init__("百度接口错误 errno=%s: %s" % (code, body))


def convert_size(n, prec=6):
    n = int(n or 0)
    if n < 0:
        return "0B"
    if n < KB:
        return "%dB" % n
    if n < MB:
        return "%.*fKB" % (prec, n / KB)
    if n < GB:
        return "%.*fMB" % (prec, n / MB)
    if n < KB * GB:
        return "%.*fGB" % (prec, n / GB)
    if n < MB * GB:
        return "%.*fTB" % (prec, n / (MB * GB))
    return "%.*fPB" % (prec, n / (GB * GB))


def policy_rtype(policy):
    return "2" if policy == SKIP else "3"


def same_size_policy(policy):
    return policy in (SIZE, RSYNC)


def block_size_of(size):
    if size >= MAX_THRESHOLD:
        return MAX_BLOCK
    if size >= MID_THRESHOLD:
        return MID_BLOCK
    return MIN_BLOCK


def block_count(size, block):
    if size <= 0 or block <= 0:
        return 1
    n = size // block + (1 if size % block else 0)
    return max(1, n)


def resolve_remote(dest, local_file):
    name = os.path.basename(local_file)
    clean = posixpath.normpath("/" + dest.lstrip("/"))
    if dest.endswith("/") or posixpath.basename(clean) != name:
        return posixpath.join(clean, name)
    return clean


def path_legal(name):
    return bool(name) and name not in (".", "..") and not any(c in name for c in ':"?<>|')


def truncate(b, n=200):
    if isinstance(b, bytes):
        b = b.decode("utf-8", "replace")
    s = (b or "").strip()
    if not s:
        return "空响应"
    return s if len(s) <= n else s[:n] + "..."


def parse_api_code(body):
    try:
        data = json.loads(body)
    except Exception:
        return None, False
    code = int(data.get("errno") or 0)
    if code == 0 and data.get("error_code"):
        code = int(data["error_code"])
    return code, True


class Client:
    def __init__(self, cfg_path, parallel=4, rotate_host=False, norefresh=False):
        self.cfg_path = cfg_path
        self.parallel = parallel if parallel > 0 else 20
        self.rotate_host = rotate_host
        self.norefresh = norefresh
        self.lock = threading.Lock()
        self.refreshed_at = 0.0
        self.dir_lock = threading.Lock()
        self.dirs_done = set()
        with open(cfg_path, "r", encoding="utf-8") as f:
            self.cfg = json.load(f)
        need = ("access_token",) if norefresh else ("client_id", "client_secret", "refresh_token")
        for k in need:
            if not self.cfg.get(k):
                raise SystemExit("config 中 %s 不能为空" % " / ".join(need))

    def save(self):
        tmp = self.cfg_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.cfg_path)

    def _request(self, method, url, data=None, headers=None, timeout=60):
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        req.add_header("User-Agent", UA)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def refresh(self):
        q = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": self.cfg["refresh_token"],
            "client_id": self.cfg["client_id"],
            "client_secret": self.cfg["client_secret"],
        })
        _, body = self._request("GET", "https://openapi.baidu.com/oauth/2.0/token?" + q)
        try:
            r = json.loads(body)
        except Exception:
            raise RuntimeError("刷新 token 返回无法解析: %s" % truncate(body))
        if r.get("error") or not r.get("access_token"):
            raise RuntimeError("刷新 token 失败: %s %s" % (r.get("error"), r.get("error_description")))
        self.cfg["access_token"] = r["access_token"]
        if r.get("refresh_token"):
            self.cfg["refresh_token"] = r["refresh_token"]
        self.cfg["expires_at"] = int(time.time()) + int(r.get("expires_in") or 0)
        self.refreshed_at = time.time()
        self.save()
        print("[token] 已用 refresh_token 刷新 access_token, 并写回 %s" % self.cfg_path, file=sys.stderr)

    def ensure_token(self, force=False):
        with self.lock:
            if self.norefresh:  # 只用 config 里的 access_token, 绝不刷新
                return
            # 并发时别的线程刚刷新过, 就直接用新 token, 避免 refresh_token 被重复消耗
            if force and self.cfg.get("access_token") and time.time() - self.refreshed_at < 10:
                return
            if force or not self.cfg.get("access_token") or time.time() > int(self.cfg.get("expires_at") or 0) - 300:
                self.refresh()

    def with_auth(self, do):
        last = b""
        for attempt in range(2):
            self.ensure_token(attempt > 0)
            body = do(self.cfg["access_token"])
            last = body
            code, ok = parse_api_code(body)
            if not ok:
                raise RuntimeError("百度接口返回无法解析: %s" % truncate(body))
            if self.norefresh and code in EXPIRED_CODES:
                raise TokenExpired("access_token 无效或已过期 (errno=%s), 已启用 -norefresh 不会刷新, 请更新 config 里的 access_token" % code)
            if attempt == 0 and code in EXPIRED_CODES:
                continue
            if code != 0:
                raise ApiError(code, body.decode("utf-8", "replace"))
            return body
        raise RuntimeError("鉴权失败")

    def post_form(self, token, method, form):
        url = "https://pan.baidu.com/rest/2.0/xpan/file?method=%s&access_token=%s" % (
            method, urllib.parse.quote(token, safe=""))
        data = urllib.parse.urlencode(form).encode()
        _, body = self._request("POST", url, data, {"Content-Type": "application/x-www-form-urlencoded"})
        return body

    def get_api(self, url):
        _, body = self._request("GET", url)
        return body

    def whoami(self):
        def do(token):
            q = urllib.parse.urlencode({"method": "uinfo", "access_token": token})
            return self.get_api("https://pan.baidu.com/rest/2.0/xpan/nas?" + q)
        r = json.loads(self.with_auth(do))
        return r.get("baidu_name") or r.get("netdisk_name") or "?", r.get("uk")

    def list_dir(self, directory):
        all_items = []
        start = 0
        while True:
            def do(token, start=start):
                q = urllib.parse.urlencode({
                    "method": "list", "access_token": token, "dir": directory,
                    "start": str(start), "limit": "1000", "order": "name",
                })
                return self.get_api("https://pan.baidu.com/rest/2.0/xpan/file?" + q)
            body = self.with_auth(do)
            try:
                items = json.loads(body).get("list") or []
            except Exception:
                raise RuntimeError("解析目录列表失败: %s" % truncate(body))
            all_items.extend(items)
            if len(items) < 1000:
                break
            start += 1000
        return all_items

    def check_exist(self, remote, content_md5=""):
        directory, name = posixpath.dirname(remote), posixpath.basename(remote)
        try:
            listing = self.list_dir(directory)
        except ApiError as e:
            if e.code in (-9, 31066):
                return "none", 0
            raise
        for e in listing:
            if e.get("server_filename") != name:
                continue
            if int(e.get("isdir") or 0) == 1:
                return "dir", 0
            if content_md5 and str(e.get("md5") or "").lower() == content_md5.lower():
                return "same", int(e.get("size") or 0)
            return "file", int(e.get("size") or 0)
        return "none", 0

    def mkdirp(self, remote_file):
        directory = posixpath.dirname(remote_file)
        if directory in ("/", ".", ""):
            return
        parts = []
        d = directory
        while d not in ("/", ".", ""):
            parts.append(d)
            d = posixpath.dirname(d)
        with self.dir_lock:  # 多文件并发时避免同时建同一个目录
            for p in reversed(parts):
                if p in self.dirs_done:
                    continue
                try:
                    self.with_auth(lambda token, p=p: self.post_form(token, "create", {
                        "path": p, "isdir": "1", "rtype": "0", "size": "0",
                    }))
                except ApiError as e:
                    if e.code not in (-8, -7, 31061):  # 已存在
                        raise
                self.dirs_done.add(p)

    def precreate(self, remote, sums, policy, rapid):
        form = {
            "path": remote,
            "size": str(sums["size"]),
            "isdir": "0",
            "autoinit": "1",
            "rtype": policy_rtype(policy),
            "block_list": json.dumps(sums["blocks"]),
            "local_mtime": str(sums["mtime"]),
            "local_ctime": str(sums["mtime"]),
        }
        if rapid:
            form["content-md5"] = sums["content"]
            form["slice-md5"] = sums["slice"]
        body = self.with_auth(lambda token: self.post_form(token, "precreate", form))
        try:
            r = json.loads(body)
        except Exception:
            raise RuntimeError("precreate 返回异常: %s" % truncate(body))
        if not r.get("uploadid") and r.get("return_type") != 2:
            raise RuntimeError("precreate 返回异常: %s" % truncate(body))
        return r

    def locate_upload(self, remote, upload_id):
        def do(token):
            q = urllib.parse.urlencode({
                "method": "locateupload", "appid": "250528", "access_token": token,
                "path": remote, "uploadid": upload_id, "upload_version": "2.0",
            })
            return self.get_api("https://d.pcs.baidu.com/rest/2.0/pcs/file?" + q)
        body = self.with_auth(do)
        try:
            r = json.loads(body)
        except Exception:
            raise RuntimeError("locateupload 返回异常: %s" % truncate(body))
        seen, hosts = set(), []

        def add(raw):
            raw = (raw or "").strip()
            if not raw:
                return
            if not raw.startswith("http"):
                raw = "https://" + raw
            u = urllib.parse.urlparse(raw)
            if not u.hostname:
                return
            scheme = "https" if u.scheme == "http" else (u.scheme or "https")
            h = "%s://%s" % (scheme, u.hostname)
            if h not in seen:
                seen.add(h)
                hosts.append(h)

        for s in r.get("servers") or []:
            add(s.get("server"))
        add(r.get("host"))
        for s in r.get("bak_servers") or []:
            add(s.get("server"))
        return hosts or [FIXED_HOST]

    def post_slice(self, host, remote, upload_id, seq, data, counter):
        q = urllib.parse.urlencode({
            "method": "upload", "access_token": self.cfg["access_token"],
            "type": "tmpfile", "path": remote, "uploadid": upload_id, "partseq": str(seq),
        })
        boundary = "----baidu%s" % hashlib.md5(os.urandom(8)).hexdigest()
        head = ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"file\"\r\n"
                "Content-Type: application/octet-stream\r\n\r\n" % boundary).encode()
        tail = ("\r\n--%s--\r\n" % boundary).encode()
        body = head + data + tail
        counter[0] += len(data)
        url = host.rstrip("/") + "/rest/2.0/pcs/superfile2?" + q
        status, resp = self._request("POST", url, body, {
            "Content-Type": "multipart/form-data; boundary=%s" % boundary,
            "Content-Length": str(len(body)),
        }, timeout=None)
        if status >= 400 and not resp:
            raise RuntimeError("HTTP %d 空响应" % status)
        code, ok = parse_api_code(resp)
        if not ok:
            raise RuntimeError("百度接口返回无法解析: HTTP %d %s" % (status, truncate(resp)))
        if code != 0:
            raise ApiError(code, resp.decode("utf-8", "replace"))
        return resp

    def upload_slice(self, remote, upload_id, seq, data, counter, hosts):
        hosts = hosts or [FIXED_HOST]
        last = None
        for i in range(SLICE_RETRY):
            if i > 0 and isinstance(last, ApiError) and last.code in EXPIRED_CODES:
                self.ensure_token(True)
            else:
                self.ensure_token(False)
            try:
                body = self.post_slice(hosts[i % len(hosts)], remote, upload_id, seq, data, counter)
                md5 = ""
                try:
                    md5 = json.loads(body).get("md5") or ""
                except Exception:
                    pass
                return md5 or hashlib.md5(data).hexdigest()
            except Exception as e:
                last = e
                if isinstance(e, ApiError) and (e.code in (400, 413, 31024, 31364) or (self.norefresh and e.code in EXPIRED_CODES)):
                    raise
                time.sleep((i + 1) * 2)
        raise last

    def create(self, remote, upload_id, sums, policy, block_md5):
        self.with_auth(lambda token: self.post_form(token, "create", {
            "path": remote,
            "size": str(sums["size"]),
            "isdir": "0",
            "uploadid": upload_id,
            "block_list": json.dumps(block_md5),
            "rtype": policy_rtype(policy),
            "local_mtime": str(sums["mtime"]),
        }))

    def verify_remote(self, fid, remote, expect):
        directory, name = posixpath.dirname(remote), posixpath.basename(remote)
        print("[%s] 校验目标目录 %s: 同名 %s, 期望大小 %s" % (fid, directory, name, convert_size(expect, 2)))
        last = None
        for i in range(5):
            if i:
                time.sleep(2)
            try:
                listing = self.list_dir(directory)
            except Exception as e:
                last = e
                continue
            for e in listing:
                if e.get("server_filename") != name or int(e.get("isdir") or 0) == 1:
                    continue
                size = int(e.get("size") or 0)
                if size == expect:
                    print("[%s] 校验通过: %s 存在, 大小 %s" % (fid, remote, convert_size(size, 2)))
                    return
                raise RuntimeError("校验失败: %s 同名但大小不一致, 网盘 %s, 本地 %s" % (
                    remote, convert_size(size, 2), convert_size(expect, 2)))
            last = RuntimeError("校验失败: 目标目录 %s 没有同名文件 %s" % (directory, name))
        raise last

    def upload_blocks(self, fid, local, remote, upload_id, sums, need, policy):
        blocks = list(sums["blocks"])
        if not need:
            need = list(range(len(blocks)))
        host_lock = threading.Lock()
        host_list = [FIXED_HOST]
        host_at = 0.0
        counter = [0]
        counter_lock = threading.Lock()
        stop = threading.Event()
        err_box = [None]

        def pick_host(seq):
            nonlocal host_list, host_at
            if not self.rotate_host:
                return [FIXED_HOST]
            with host_lock:
                if time.time() - host_at > 30 or not host_list or host_at == 0:
                    try:
                        fresh = self.locate_upload(remote, upload_id)
                        if fresh:
                            host_list = fresh
                            host_at = time.time()
                    except Exception:
                        pass
                n = len(host_list)
                return [host_list[(seq + i) % n] for i in range(n)] or [FIXED_HOST]

        def worker(seq):
            if stop.is_set():
                return
            data = read_slice(local, seq, sums["block"], sums["size"])
            try:
                md5 = self.upload_slice(remote, upload_id, seq, data, counter, pick_host(seq))
            except Exception as e:
                if err_box[0] is None:
                    err_box[0] = RuntimeError("分片 %d 上传失败: %s" % (seq, e))
                    stop.set()
                return
            blocks[seq] = md5
            with counter_lock:
                counter[0]  # counted during send
            done[0] += len(data)
            with G_LOCK:
                G_DONE[0] += len(data)

        done = [0]
        start = time.time()

        def printer():
            last = start
            last_n = 0
            while not stop.is_set():
                time.sleep(3)
                now = time.time()
                n = done[0]
                speed = int((n - last_n) / max(now - last, 0.001))
                elapsed = time.time() - start
                sys.stdout.write("\r[%s] ↑ %s/%s %s/s in %s ............" % (
                    fid, convert_size(n, 2), convert_size(sums["size"], 2),
                    convert_size(speed, 2), fmt_elapsed(elapsed)))
                sys.stdout.flush()
                last, last_n = now, n

        t = threading.Thread(target=printer, daemon=True)
        if not QUIET:
            t.start()
        with ThreadPoolExecutor(max_workers=self.parallel) as pool:
            futs = [pool.submit(worker, seq) for seq in need if 0 <= seq < len(blocks)]
            for fut in as_completed(futs):
                fut.result()
        stop.set()
        if not QUIET:
            t.join(timeout=1)
            uploaded = sums["size"] if err_box[0] is None else done[0]
            sys.stdout.write("\r[%s] ↑ %s/%s %s/s in %s ............\n" % (
                fid, convert_size(uploaded, 2), convert_size(sums["size"], 2),
                convert_size(0, 2), fmt_elapsed(time.time() - start)))
        if err_box[0]:
            raise err_box[0]
        self.create(remote, upload_id, sums, policy, blocks)

    def upload(self, fid, local, remote, policy, rapid, scan_md5):
        print("[%s] 准备上传: %s" % (fid, local))
        try:
            st = os.stat(local)
        except OSError as e:
            print("[%s] 文件不可读, 错误信息: %s, 跳过..." % (fid, e))
            raise
        size = st.st_size
        if size > MAX_SIZE:
            print("[%s] 文件大小超过128G, 无法上传, 跳过..." % fid)
            raise RuntimeError("文件 %s 大小超过128G" % local)
        if size >= RECOMMENDED:
            print("[%s] 文件超过32GB, 上传有可能失败, 建议分割文件..." % fid)

        block = block_size_of(size)
        try:
            state, remote_size = self.check_exist(remote)
        except ApiError:
            state, remote_size = "none", 0
        if state == "dir":
            raise RuntimeError("保存路径不可以覆盖目录")
        if state == "file":
            if policy == SKIP:
                print("[%s] 目标文件, %s, 已存在, 跳过..." % (fid, remote))
                return 0, True
            if same_size_policy(policy) and remote_size == size:
                print("[%s] 目标文件 %s 同名且大小相同 (%s), 跳过..." % (fid, remote, convert_size(size, 2)))
                return 0, True
            if same_size_policy(policy) and remote_size != size:
                print("[%s] 目标文件 %s 同名但大小不同, 网盘 %s, 本地 %s, 覆盖上传" % (
                    fid, remote, convert_size(remote_size, 2), convert_size(size, 2)))

        if not scan_md5:
            rapid = False
        if scan_md5:
            print("[%s] 开始计算文件元信息, 请稍候..." % fid)
            print("[%s] 开始计算文件分块md5, 请稍候..." % fid)
            sums = sum_file(local, block, True, fid)
            if state == "none":
                try:
                    again, _ = self.check_exist(remote, sums["content"])
                except ApiError:
                    again = "none"
                if again == "same" and policy != OVERWRITE:
                    print("[%s] 目标文件, %s, 已存在, 跳过..." % (fid, remote))
                    return 0, True
        else:
            print("[%s] 已跳过 MD5 预扫描，直接上传" % fid)
            sums = sums_no_scan(size, st.st_mtime, block)

        self.mkdirp(remote)
        try:
            pre = self.precreate(remote, sums, policy, rapid)
        except ApiError as e:
            if e.code in (114514, 31061, -8) and policy == SKIP:
                print("[%s] %s 目标已存在, 跳过" % (fid, remote))
                return 0, True
            raise
        if pre.get("return_type") == 2:
            print("[%s] 秒传成功, 保存到网盘路径: %s" % (fid, remote))
            self.verify_remote(fid, remote, sums["size"])
            print()
            return sums["size"], False

        print("[%s] 开始上传文件...\n" % fid)
        need = pre.get("block_list") or []
        if not scan_md5:
            need = []
        self.upload_blocks(fid, local, remote, pre["uploadid"], sums, need, policy)
        self.verify_remote(fid, remote, sums["size"])
        print("[%s] 上传文件成功, 保存到网盘路径: %s" % (fid, remote))
        return sums["size"], False


def fmt_elapsed(sec):
    sec = int(sec)
    return "%dm%d.%ds" % (sec // 60, sec % 60, 0) if sec >= 60 else "%.1fs" % sec


def read_slice(local, seq, block, size):
    offset = seq * block
    n = min(block, max(0, size - offset))
    with open(local, "rb") as f:
        f.seek(offset)
        data = f.read(n)
    if len(data) != n:
        raise RuntimeError("读取分片 %d 失败" % seq)
    return data


def sums_no_scan(size, mtime, block):
    n = block_count(size, block)
    blocks = [hashlib.md5(("block:%d" % i).encode()).hexdigest() for i in range(n)]
    if size == 0:
        blocks = [EMPTY_MD5]
    return {"size": size, "content": "", "slice": "", "blocks": blocks, "block": block, "mtime": int(mtime)}


def sum_file(local, block, with_content, fid):
    st = os.stat(local)
    sums = {"size": st.st_size, "content": "", "slice": "", "blocks": [], "block": block, "mtime": int(st.st_mtime)}
    if st.st_size == 0:
        sums["blocks"] = [EMPTY_MD5]
        if with_content:
            sums["content"] = sums["slice"] = EMPTY_MD5
        return sums
    content = hashlib.md5()
    slice_hash = hashlib.md5()
    block_hash = hashlib.md5()
    filled = in_block = read = 0
    last = start = time.time()
    with open(local, "rb") as f:
        while True:
            buf = f.read(MB)
            if not buf:
                break
            read += len(buf)
            if with_content:
                content.update(buf)
            off = 0
            while off < len(buf):
                take = min(len(buf) - off, block - in_block)
                block_hash.update(buf[off:off + take])
                if with_content and filled < SLICE_MD5:
                    m = min(take, SLICE_MD5 - filled)
                    slice_hash.update(buf[off:off + m])
                    filled += m
                in_block += take
                off += take
                if in_block == block:
                    sums["blocks"].append(block_hash.hexdigest())
                    block_hash = hashlib.md5()
                    in_block = 0
            if fid and not QUIET and time.time() - last >= 3:
                speed = int(read / max(time.time() - start, 0.001))
                sys.stdout.write("\r[%s] 扫描 MD5 %s/%s %s/s" % (
                    fid, convert_size(read, 2), convert_size(st.st_size, 2), convert_size(speed, 2)))
                sys.stdout.flush()
                last = time.time()
    if in_block:
        sums["blocks"].append(block_hash.hexdigest())
    if with_content:
        sums["content"] = content.hexdigest()
        sums["slice"] = sums["content"] if st.st_size <= SLICE_MD5 else slice_hash.hexdigest()
    if fid and not QUIET:
        print("\r[%s] 扫描 MD5 %s/%s 完成" % (fid, convert_size(st.st_size, 2), convert_size(st.st_size, 2)))
    return sums


def bool_arg(v):
    if str(v).lower() in ("1", "true", "yes", "on"):
        return True
    if str(v).lower() in ("0", "false", "no", "off"):
        return False
    raise argparse.ArgumentTypeError(v)


DIR_HELP_NOTE = "目录默认跳过，加 -R 才进入目录"

DURATIONS = {"ms": 0.001, "s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "M": 2592000, "y": 31536000}


def parse_size(s):
    """rclone 风格: 12345 默认 KiB; 支持 b k M G T P, 可带 i/iB, 全按 1024。"""
    m = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*([bkmgtpBKMGTP]?)(?:[iI]?[bB])?\s*", str(s))
    if not m:
        raise ValueError("无法解析大小: %r (例: 100k 10M 1G 500b)" % s)
    unit = (m.group(2) or "k").lower()
    mult = {"b": 1, "k": KB, "m": MB, "g": GB, "t": GB * KB, "p": GB * MB}[unit]
    return int(float(m.group(1)) * mult)


def parse_cutoff(s, now):
    """返回时间戳。'1h30m' / '7d' / '2w' => now-相对时间; '2024-01-02' 等 => 绝对时间。"""
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).timestamp()
        except ValueError:
            pass
    tokens = re.findall(r"([0-9]+(?:\.[0-9]+)?)(ms|s|m|h|d|w|M|y)", s)
    if not tokens or "".join(a + b for a, b in tokens) != s:
        raise ValueError("无法解析时间: %r (例: 30m 12h 7d 2w 6M 1y 1h30m 2024-01-31)" % s)
    return now - sum(float(a) * DURATIONS[b] for a, b in tokens)


def _glob_body(p):
    out, i, n = [], 0, len(p)
    while i < n:
        c = p[i]
        if c == "\\" and i + 1 < n:
            out.append(re.escape(p[i + 1]))
            i += 2
        elif c == "*":
            if p.startswith("**/", i):
                out.append("(?:.*/)?")
                i += 3
            elif p.startswith("**", i):
                out.append(".*")
                i += 2
            else:
                out.append("[^/]*")
                i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        elif c == "[":
            j = i + 1
            if j < n and p[j] in "!^":
                j += 1
            if j < n and p[j] == "]":
                j += 1
            while j < n and p[j] != "]":
                j += 1
            if j >= n:
                out.append(re.escape(c))
                i += 1
            else:
                cls = p[i + 1:j]
                neg = cls[:1] in ("!", "^")
                if neg:
                    cls = cls[1:]
                cls = cls.replace("\\", "\\\\").replace("[", "\\[")
                out.append("[" + ("^" if neg else "") + cls + "]")
                i = j + 1
        elif c == "{":
            if p.startswith("{{", i):
                j = p.find("}}", i + 2)
                if j >= 0:
                    out.append("(?:" + p[i + 2:j] + ")")
                    i = j + 2
                    continue
            depth, j, cur, parts = 1, i + 1, i + 1, []
            while j < n and depth:
                ch = p[j]
                if ch == "\\":
                    j += 2
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                elif ch == "," and depth == 1:
                    parts.append(p[cur:j])
                    cur = j + 1
                j += 1
            if depth:
                out.append(re.escape(c))
                i += 1
            else:
                parts.append(p[cur:j - 1])
                out.append("(?:" + "|".join(_glob_body(x) for x in parts) + ")")
                i = j
        else:
            out.append(re.escape(c))
            i += 1
    return "".join(out)


def glob_to_regex(pat, ignore_case=False):
    anchored = pat.startswith("/")
    if anchored:
        pat = pat[1:]
    prefix = "^" if anchored else "(?:^|/)"
    return re.compile(prefix + _glob_body(pat) + "$", re.I if ignore_case else 0)


class Rule:
    def __init__(self, include, pattern, ignore_case):
        self.include = include
        self.pattern = pattern
        self.re = glob_to_regex(pattern, ignore_case)
        self.dir_only = pattern.endswith("/")
        dp = None
        if pattern.endswith("/"):
            dp = pattern
        elif pattern.endswith("/**"):
            dp = pattern[:-3] + "/"
        self.dir_re = glob_to_regex(dp, ignore_case) if dp else None

    def text(self):
        return ("+ " if self.include else "- ") + self.pattern


class Filter:
    def __init__(self, rules, ignore_case, min_size, max_size, newer_than, older_than):
        merged = []
        for op, pat in rules:
            if op == "!":
                merged = []
            else:
                merged.append((op == "+", pat))
        self.rules = [Rule(inc, pat, ignore_case) for inc, pat in merged]
        self.has_include = any(r.include for r in self.rules)
        self.min_size, self.max_size = min_size, max_size
        self.newer_than, self.older_than = newer_than, older_than

    def check_name(self, rel):
        for r in self.rules:
            if not r.dir_only and r.re.search(rel):
                return r.include, ("命中 " + r.text())
        if self.has_include:
            return False, "没命中任何 include 规则 (有 include 时隐含 '- **')"
        return True, ""

    def dir_excluded(self, rel_dir):
        s = rel_dir.rstrip("/") + "/"
        for r in self.rules:
            if r.dir_re and r.dir_re.search(s):
                return not r.include
        return False

    def check_meta(self, st):
        if self.min_size is not None and st.st_size < self.min_size:
            return False, "小于 min-size"
        if self.max_size is not None and st.st_size > self.max_size:
            return False, "大于 max-size"
        if self.older_than is not None and st.st_mtime > self.older_than:
            return False, "不满足 min-age (太新)"
        if self.newer_than is not None and st.st_mtime < self.newer_than:
            return False, "不满足 max-age (太旧)"
        return True, ""


def read_lines(path):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith(("#", ";")):
                out.append(line)
    return out


def parse_filter_lines(lines):
    out = []
    for line in lines:
        line = line.strip()
        if line == "!":
            out.append(("!", ""))
        elif line.startswith("+ "):
            out.append(("+", line[2:].strip()))
        elif line.startswith("- "):
            out.append(("-", line[2:].strip()))
        else:
            raise ValueError("filter 规则必须以 '+ ' 或 '- ' 开头, 或者是单独的 '!': %r" % line)
    return out


class RuleAction(argparse.Action):
    """--include/--exclude/--filter 及 *-from 按命令行出现顺序追加到同一个规则列表。"""

    def __call__(self, parser, ns, values, option_string=None):
        rules = list(getattr(ns, "rules", None) or [])
        opt = (option_string or "").lstrip("-")
        try:
            if opt == "include":
                rules.append(("+", values))
            elif opt == "exclude":
                rules.append(("-", values))
            elif opt == "filter":
                rules.extend(parse_filter_lines([values]))
            elif opt == "include-from":
                rules.extend(("+", x) for x in read_lines(values))
            elif opt == "exclude-from":
                rules.extend(("-", x) for x in read_lines(values))
            elif opt == "filter-from":
                rules.extend(parse_filter_lines(read_lines(values)))
        except (OSError, ValueError) as e:
            parser.error(str(e))
        ns.rules = rules


def walk_dir(root, recursive, max_depth, marker, filt):
    def rec(d, prefix, depth):
        if marker and os.path.exists(os.path.join(d, marker)):
            return
        try:
            with os.scandir(d) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError as e:
            print("读取目录失败 %s: %s" % (d, e), file=sys.stderr)
            return
        for e in entries:
            rel = prefix + e.name
            try:
                if e.is_dir(follow_symlinks=False):
                    if recursive and (not max_depth or depth < max_depth) and not filt.dir_excluded(rel):
                        yield from rec(e.path, rel + "/", depth + 1)
                elif e.is_file():
                    yield e.path, rel
            except OSError:
                continue
    yield from rec(root, "", 1)


def gather(args, filt, files_from):
    """返回 [(本地路径, 用于匹配规则的相对路径, 网盘相对路径, 是否绕过名字规则)], 被跳过的目录数。"""
    seen, cands, dirs_skipped = set(), [], 0

    def add(path, rel, remote_rel, bypass):
        ap = os.path.abspath(path)
        if ap in seen:
            return
        seen.add(ap)
        cands.append((path, rel, remote_rel, bypass))

    for pat in args.file:
        if any(c in pat for c in "*?["):
            try:
                hits = sorted(glob.glob(pat, recursive=args.recursive, include_hidden=True))
            except TypeError:  # Python < 3.11
                hits = sorted(glob.glob(pat, recursive=args.recursive))
        else:
            hits = [pat]
        if not hits:
            print("没有匹配: %s" % pat, file=sys.stderr)
            continue
        for h in hits:
            if os.path.isdir(h):
                if not args.recursive:
                    dirs_skipped += 1
                    continue
                name = os.path.basename(os.path.abspath(h))
                contents_only = h.endswith(("/", os.sep)) or not name
                for path, rel in walk_dir(h, True, args.max_depth, args.exclude_if_present, filt):
                    add(path, rel, rel if contents_only else posixpath.join(name, rel), False)
            elif os.path.isfile(h):
                b = os.path.basename(h)
                add(h, b, b, False)
            else:
                print("文件不存在: %s" % h, file=sys.stderr)
    for path in files_from:
        if os.path.isfile(path):
            b = os.path.basename(path)
            add(path, b, b, True)
        else:
            print("files-from 中的文件不存在: %s" % path, file=sys.stderr)
    return cands, dirs_skipped


def main():
    p = argparse.ArgumentParser(add_help=True, allow_abbrev=False,
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog="过滤规则语法同 rclone: 第一条命中的规则生效; 有 include 规则时末尾隐含 '- **'; "
                                       "* 不跨目录, ** 跨目录, ? 单字符, [a-z] [!a-z] {a,b} {{regex}}; "
                                       "开头 / 表示锚定到根, 结尾 / 只匹配目录。")
    p.add_argument("-config", "--config", default="config.json")
    p.add_argument("-file", "--file", dest="file", nargs="+", default=[],
                   help="本地文件/通配符/目录, 可多个。" + DIR_HELP_NOTE + "; 目录以 / 结尾只传内容, 否则保留目录名")
    p.add_argument("-dest", "--dest", dest="dest", default="/", help="网盘目录, 默认 /")
    p.add_argument("-policy", "--policy", default=SIZE)
    p.add_argument("-parallel", "--parallel", type=int, default=20, help="单个文件的分片并发数, 默认 20")
    p.add_argument("-transfers", "--transfers", type=int, default=4, help="同时上传的文件数, 默认 4 (同时分片请求数约为 transfers x parallel)")
    p.add_argument("-norapid", "--norapid", action="store_true")
    p.add_argument("-md5", "--md5", type=bool_arg, default=True)
    p.add_argument("-rotatehost", "--rotatehost", action="store_true")
    p.add_argument("-norefresh", "--norefresh", action="store_true", help="只用 config 里的 access_token, 绝不刷新 (过期直接报错); 此时不要求 client_id/secret/refresh_token")

    g = p.add_argument_group("文件过滤 (rclone 风格)")
    p.set_defaults(rules=[])
    g.add_argument("-include", "--include", action=RuleAction, dest="rules", metavar="PAT", help="包含 (可重复)")
    g.add_argument("-exclude", "--exclude", action=RuleAction, dest="rules", metavar="PAT", help="排除 (可重复)")
    g.add_argument("-filter", "--filter", action=RuleAction, dest="rules", metavar="RULE", help="'+ PAT' / '- PAT' / '!' (清空之前的规则)")
    g.add_argument("-include-from", "--include-from", action=RuleAction, dest="rules", metavar="FILE", help="每行一个 include 规则, # ; 开头为注释")
    g.add_argument("-exclude-from", "--exclude-from", action=RuleAction, dest="rules", metavar="FILE", help="每行一个 exclude 规则")
    g.add_argument("-filter-from", "--filter-from", action=RuleAction, dest="rules", metavar="FILE", help="每行一条 '+ PAT' / '- PAT'")
    g.add_argument("-files-from", "--files-from", dest="files_from", metavar="FILE", help="文件内每行一个本地文件路径, 绕过名字规则, 仍受大小/时间限制")
    g.add_argument("-ignore-case", "--ignore-case", action="store_true", help="规则不区分大小写")
    g.add_argument("-min-size", "--min-size", metavar="SIZE", help="最小大小, 如 100k 10M 1G, 无后缀默认 KiB, 用 b 表示字节")
    g.add_argument("-max-size", "--max-size", metavar="SIZE", help="最大大小")
    g.add_argument("-min-age", "--min-age", metavar="AGE", help="只要比这更旧的文件, 如 30m 12h 7d 2w 6M 1y 1h30m 2024-01-31")
    g.add_argument("-max-age", "--max-age", metavar="AGE", help="只要比这更新的文件")
    g.add_argument("-R", "--recursive", action="store_true", help="进入目录并递归 (默认不进入目录)")
    g.add_argument("-max-depth", "--max-depth", type=int, default=0, metavar="N", help="递归深度, 1 = 只有目录下一层文件, 0 = 不限; 大于 1 自动开启递归")
    g.add_argument("-exclude-if-present", "--exclude-if-present", metavar="NAME", help="目录里存在该文件名则整个目录跳过 (递归时有效)")
    g.add_argument("-n", "--dry-run", action="store_true", help="只列出将要上传的文件, 不连接网盘")
    g.add_argument("-v", "--verbose", action="store_true", help="显示被排除的文件及原因")
    args = p.parse_args()

    if args.policy not in (SIZE, SKIP, OVERWRITE, RSYNC):
        print("未知重名策略 %r，可选 size | skip | overwrite | rsync" % args.policy, file=sys.stderr)
        return 2
    if (not args.file and not args.files_from) or not args.dest.startswith("/"):
        print("用法: python3 baidu-upload.py -file 本地文件或通配符 [-dest /网盘目录/] [-exclude PAT] [-include PAT] "
              "[-min-size 1M] [-R] [-n] ...  (-h 查看全部)", file=sys.stderr)
        return 2
    if args.max_depth > 1:
        args.recursive = True
    if args.transfers < 1:
        print("-transfers 必须 >= 1", file=sys.stderr)
        return 2

    now = time.time()
    try:
        min_size = parse_size(args.min_size) if args.min_size else None
        max_size = parse_size(args.max_size) if args.max_size else None
        older_than = parse_cutoff(args.min_age, now) if args.min_age else None
        newer_than = parse_cutoff(args.max_age, now) if args.max_age else None
        files_from = read_lines(args.files_from) if args.files_from else []
        filt = Filter(args.rules, args.ignore_case, min_size, max_size, newer_than, older_than)
    except (ValueError, OSError, re.error) as e:
        print("参数错误: %s" % e, file=sys.stderr)
        return 2

    cands, dirs_skipped = gather(args, filt, files_from)
    picked, excluded = [], 0
    for path, rel, remote_rel, bypass in cands:
        ok, why = True, ""
        if not bypass:
            ok, why = filt.check_name(rel)
        if ok:
            try:
                ok, why = filt.check_meta(os.stat(path))
            except OSError as e:
                ok, why = False, str(e)
        if ok:
            picked.append((path, remote_rel))
        else:
            excluded += 1
            if args.verbose:
                print("[排除] %s  (%s)" % (rel, why))
    if dirs_skipped:
        print("已跳过 %d 个目录 (加 -R 可进入目录)" % dirs_skipped)
    print("匹配 %d 个文件, 排除 %d 个" % (len(picked), excluded))

    base = posixpath.normpath("/" + args.dest.lstrip("/"))
    if args.dry_run:
        total = 0
        for path, remote_rel in picked:
            size = os.path.getsize(path)
            total += size
            print("[dry-run] %s -> %s (%s)" % (path, posixpath.join(base, remote_rel), convert_size(size, 2)))
        print("[dry-run] 合计 %s, 未上传" % convert_size(total, 2))
        return 0
    if not picked:
        print("未检测到上传的文件", file=sys.stderr)
        return 1

    global QUIET
    client = Client(args.config, args.parallel, args.rotatehost, args.norefresh)
    try:
        name, uk = client.whoami()
        print("[0] 当前账号: %s (uk=%s)%s" % (name, uk, ", -norefresh: 不会刷新 token" if args.norefresh else ""))
    except TokenExpired as e:
        print("[0] %s" % e, file=sys.stderr)
        return 1
    except Exception as e:
        print("[0] 获取当前账号信息失败: %s" % e, file=sys.stderr)
    transfers = min(args.transfers, len(picked))
    QUIET = transfers > 1
    print()
    print("[0] 提示: 共 %d 个文件, 单个文件最大并发量为: %d, 最大同时上传文件数为: %d" % (len(picked), client.parallel, transfers))

    ok_ids, skip_ids, bad_ids = set(), set(), set()
    total = 0
    started = time.time()
    checks = []
    scan = args.md5 and not args.norapid

    def job(fid, path, remote_rel):
        print("[%s] 加入上传队列: %s" % (fid, path))
        try:
            for part in remote_rel.split("/"):
                if not path_legal(part):
                    raise RuntimeError("%s 路径含有非法字符" % path)
            remote = posixpath.join(base, remote_rel)
            n, skipped = client.upload(fid, path, remote, args.policy, scan, scan)
            return fid, "skip" if skipped else "ok", remote, os.path.getsize(path), n, None
        except Exception as e:
            return fid, "bad", None, 0, 0, e

    finished = [0]
    stop_progress = threading.Event()

    def global_progress():
        last_t, last_n = time.time(), G_DONE[0]
        while not stop_progress.wait(5):
            now, n = time.time(), G_DONE[0]
            speed = int((n - last_n) / max(now - last_t, 0.001))
            print("[进度] 已完成 %d/%d 个文件, 已上传 %s, %s/s, 用时 %s" % (
                finished[0], len(picked), convert_size(n, 2), convert_size(speed, 2), fmt_elapsed(now - started)))
            last_t, last_n = now, n

    if QUIET:
        threading.Thread(target=global_progress, daemon=True).start()
    with ThreadPoolExecutor(max_workers=transfers) as pool:
        futs = [pool.submit(job, str(i), path, rel) for i, (path, rel) in enumerate(picked, 1)]
        for fut in as_completed(futs):
            fid, status, remote, size, n, err = fut.result()
            finished[0] += 1
            if status == "bad":
                print("[%s] 上传文件失败, %s" % (fid, err), file=sys.stderr)
                bad_ids.add(fid)
                continue
            total += n
            checks.append((fid, remote, size))
            (skip_ids if status == "skip" else ok_ids).add(fid)
    stop_progress.set()
    checks.sort(key=lambda x: int(x[0]))

    elapsed = time.time() - started
    print("\n上传结束, 时间: %s, 总大小: %s" % (fmt_elapsed(elapsed), convert_size(total)))
    if checks:
        print("开始核对目标目录同名文件及大小...")
        for fid, remote, size in checks:
            try:
                client.verify_remote(fid, remote, size)
            except Exception as e:
                print("[%s] %s" % (fid, e), file=sys.stderr)
                ok_ids.discard(fid)
                skip_ids.discard(fid)
                bad_ids.add(fid)
    sys.stderr.flush()
    print("%d个文件上传成功  %d个跳过  %d个失败" % (len(ok_ids), len(skip_ids), len(bad_ids)))
    return 1 if bad_ids else 0


if __name__ == "__main__":
    sys.exit(main())
