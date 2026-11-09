#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""115 网盘上传工具，Python 单文件版。

命令行尽量兼容 orzogc/fake115uploader，并增加：
  -j 并发上传流数量
  文件夹 / 多文件 / 通配符（*.mp4、123*、*.*，请在 shell 里给通配符加引号）
  --max N 每个通配符参数最多取 N 个文件，--max-order 选取顺序（默认最新修改优先）
  --prefix 给网盘上的文件名加前缀（只改发给 115 的名字，本地文件不动）
  1 秒滑动窗口的实时网速（不再只用全程平均速度）

依赖:
  pip install requests cryptography lz4

仅用于协议研究。Cookie 只放在本机配置文件或 -k 参数里，不要提交到仓库。
"""

from __future__ import annotations

import argparse
import base64
import glob
import hashlib
import hmac
import json
import os
import re
import shutil
import signal
import sys
import threading
import time
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from email.utils import formatdate

APP_VER = "30.5.1"
UA = "Mozilla/5.0 115disk/" + APP_VER
ALI_UA = "aliyun-sdk-android/2.9.1"
MD5_SALT = "Qclm8MGWUv59TnrR0XPg"
END_STRING = "000000"
TARGET_PREFIX = "U_1_"
CRC_SALT = b"^j>WD3Kr?J2gLFjD4W2y@"
P224_LEN = 28
MAX_PARTS = 10000
OSS_MIN_PART = 100 * 1024
OSS_MAX_PART = 5 * 1024 * 1024 * 1024
MAX_FILE = 115 * 1024 * 1024 * 1024
SIMPLE_LIMIT = 5 * 1024 * 1024 * 1024
GB = 1024 * 1024 * 1024

INFO_URL = "https://proapi.115.com/app/uploadinfo"
INIT_URL = "https://uplb.115.com/4.0/initupload.php?k_ec=%s"
GETINFO_URL = "https://uplb.115.com/3.0/getuploadinfo.php"
CREATE_DIR_URL = "https://webapi.115.com/files/add"
ORDER_URL = "https://webapi.115.com/files/order"
SEARCH_URL = "https://webapi.115.com/files/search?offset=0&limit=100000&aid=1&cid=%d&format=json"
LIST_DIR_URL = (
    "https://webapi.115.com/files?aid=1&cid=%d&o=user_ptime&asc=0"
    "&offset=0&show_dir=1&limit=100000&natsort=1&format=json"
)
LIST_RECENT_URL = (
    "https://webapi.115.com/files?aid=1&cid=%d&o=user_ptime&asc=0"
    "&offset=0&show_dir=0&limit=%d&natsort=1&format=json"
)

REMOTE_PUB = bytes((
    0x57, 0xA2, 0x92, 0x57, 0xCD, 0x23, 0x20, 0xE5, 0xD6, 0xD1, 0x43, 0x32,
    0x2F, 0xA4, 0xBB, 0x8A, 0x3C, 0xF9, 0xD3, 0xCC, 0x62, 0x3E, 0xF5, 0xED,
    0xAC, 0x62, 0xB7, 0x67, 0x8A, 0x89, 0xC9, 0x1A, 0x83, 0xBA, 0x80, 0x0D,
    0x61, 0x29, 0xF5, 0x22, 0xD0, 0x34, 0xC8, 0x95, 0xDD, 0x24, 0x65, 0x24,
    0x3A, 0xDD, 0xC2, 0x50, 0x95, 0x3B, 0xEE, 0xBA,
))

requests = None
lz4_block = None
Cipher = algorithms = modes = sympadding = ec = None
DEPS_ERR = ""

STOP = threading.Event()
PRINT_LOCK = threading.Lock()
_CANCEL = threading.local()


def halted():
    """全局暂停，或当前线程正在上传的那个文件被单独暂停。"""
    if STOP.is_set():
        return True
    ev = getattr(_CANCEL, "ev", None)
    return ev is not None and ev.is_set()


def load_deps():
    global requests, lz4_block, Cipher, algorithms, modes, sympadding, ec, DEPS_ERR
    if requests is not None:
        return True
    try:
        import requests as _requests
        import lz4.block as _lz4_block
        from cryptography.hazmat.primitives.ciphers import Cipher as _Cipher
        from cryptography.hazmat.primitives.ciphers import algorithms as _algorithms
        from cryptography.hazmat.primitives.ciphers import modes as _modes
        from cryptography.hazmat.primitives import padding as _sympadding
        from cryptography.hazmat.primitives.asymmetric import ec as _ec
    except ImportError as exc:
        DEPS_ERR = str(exc)
        return False
    requests = _requests
    lz4_block = _lz4_block
    Cipher, algorithms, modes, sympadding, ec = (
        _Cipher, _algorithms, _modes, _sympadding, _ec,
    )
    return True


def log(msg):
    ui = GLOBAL_UI
    if ui is not None and ui.started:
        ui.log(msg)
    else:
        with PRINT_LOCK:
            print(msg, file=sys.stderr, flush=True)


GLOBAL_UI = None


def fmt_size(n):
    n = max(0, int(n))
    val = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if val < 1024 or unit == "TB":
            if unit == "B":
                return "%d B" % int(val)
            return "%.2f %s" % (val, unit)
        val /= 1024
    return "%d B" % n


def fmt_rate(bps):
    bps = max(0.0, float(bps))
    if bps >= 1024 * 1024:
        return "%.2f MB/s" % (bps / 1024 / 1024)
    if bps >= 1024:
        return "%.1f KB/s" % (bps / 1024)
    return "%.0f B/s" % bps


def fmt_eta(seconds):
    if seconds is None or seconds < 0 or seconds > 99 * 86400:
        return "--:--"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return "%d:%02d:%02d" % (h, m, s)
    return "%02d:%02d" % (m, s)


def disp_width(text):
    width = 0
    for ch in text:
        width += 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
    return width


def clip_text(text, cols):
    if cols <= 1:
        return ""
    out = []
    used = 0
    for ch in text:
        cw = 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
        if used + cw > cols - 1:
            out.append("…")
            break
        out.append(ch)
        used += cw
    return "".join(out)


def window_rate(samples, now, window=1.0):
    """最近 window 秒内的实际上传速度：字节 / 这些字节真实占用的时间，不用全程平均。"""
    total = 0
    oldest = None
    cut = now - window
    for ts, nbytes in samples:
        if ts < cut or nbytes <= 0:
            continue
        total += nbytes
        if oldest is None or ts < oldest:
            oldest = ts
    if total <= 0 or oldest is None:
        return 0.0
    span = now - oldest
    if span < 0.25:
        span = 0.25
    return total / span


class EcdhCipher:
    """与 fake115uploader/cipher.EcdhCipher 对齐的 P-224 通道。"""

    def __init__(self):
        if ec is None:
            raise RuntimeError("缺少 cryptography")
        x = int.from_bytes(REMOTE_PUB[:P224_LEN], "big")
        y = int.from_bytes(REMOTE_PUB[P224_LEN:], "big")
        peer = ec.EllipticCurvePublicNumbers(x, y, ec.SECP224R1()).public_key()
        self.private = ec.generate_private_key(ec.SECP224R1())
        secret = self.private.exchange(ec.ECDH(), peer)
        # Go 的 big.Int.Bytes() 会去掉前导 0
        secret = secret.lstrip(b"\x00") or b"\x00"
        if len(secret) < 16:
            raise RuntimeError("ECDH 共享密钥过短")
        self.key = secret[:16]
        self.iv = secret[-16:]
        nums = self.private.public_key().public_numbers()
        xb = nums.x.to_bytes(P224_LEN, "big")
        flag = 0x03 if (nums.y & 1) else 0x02
        self.pub = bytes([P224_LEN + 1, flag]) + xb

    def encode_token(self, timestamp):
        r1 = int.from_bytes(os.urandom(1), "big")
        r2 = int.from_bytes(os.urandom(1), "big")
        tbytes = (int(timestamp) & 0xFFFFFFFF).to_bytes(4, "big")
        tmp = bytearray()
        for i in range(15):
            tmp.append(self.pub[i] ^ r1)
        tmp.append(r1)
        tmp.append(0x73 ^ r1)
        tmp.extend((r1, r1, r1))
        for i in range(4):
            tmp.append(r1 ^ tbytes[3 - i])
        for i in range(15, len(self.pub)):
            tmp.append(self.pub[i] ^ r2)
        tmp.append(r2)
        tmp.append(0x01 ^ r2)
        tmp.extend((r2, r2, r2))
        crc = zlib.crc32(CRC_SALT + bytes(tmp)) & 0xFFFFFFFF
        tmp.extend(crc.to_bytes(4, "little"))
        return base64.b64encode(bytes(tmp)).decode("ascii")

    def encrypt(self, plain):
        padder = sympadding.PKCS7(128).padder()
        data = padder.update(plain) + padder.finalize()
        xor_key = bytearray(self.iv)
        out = bytearray()
        block = bytearray()
        ecb = Cipher(algorithms.AES(self.key), modes.ECB()).encryptor()
        for i, b in enumerate(data):
            block.append(b ^ xor_key[i % 16])
            if i % 16 == 15:
                xor_key = bytearray(ecb.update(bytes(block)))
                out.extend(xor_key)
                block.clear()
        return bytes(out)

    def decrypt(self, data):
        if not data:
            raise ValueError("空响应")
        n = len(data) - (len(data) % 16)
        if n <= 0:
            raise ValueError("密文过短")
        dec = Cipher(algorithms.AES(self.key), modes.CBC(self.iv)).decryptor()
        plain = dec.update(data[:n]) + dec.finalize()
        if len(plain) < 2:
            raise ValueError("明文过短")
        length = plain[0] + (plain[1] << 8)
        blob = plain[2:2 + length]
        if len(blob) != length:
            raise ValueError("lz4 长度不匹配")
        return lz4_block.decompress(blob, uncompressed_size=1024 * 1024)


def sha1_file(path, on_bytes=None):
    h = hashlib.sha1()
    done = 0
    with open(path, "rb") as f:
        while True:
            if halted():
                raise InterruptedError("已中断")
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            done += len(chunk)
            if on_bytes:
                on_bytes(len(chunk))
    return h.hexdigest().upper()


def sha1_range(path, spec):
    try:
        a, b = spec.split("-", 1)
        start, end = int(a), int(b)
    except Exception as exc:
        raise ValueError("sign_check 范围错误: %s" % spec) from exc
    if start < 0 or end < start:
        raise ValueError("sign_check 范围错误: %s" % spec)
    h = hashlib.sha1()
    left = end - start + 1
    with open(path, "rb") as f:
        f.seek(start)
        while left > 0:
            chunk = f.read(min(1024 * 1024, left))
            if not chunk:
                break
            h.update(chunk)
            left -= len(chunk)
    if left:
        raise ValueError("sign_check 超出文件长度: %s" % spec)
    return h.hexdigest().upper()


def plan_parts(size, parts_num):
    if size <= 0:
        return []
    if parts_num:
        n = int(parts_num)
    elif size > 9 * GB:
        n = MAX_PARTS
    else:
        n = MAX_PARTS
        for i in range(1, 10):
            if size < i * GB:
                n = i * 1000
                break
    n = max(1, min(MAX_PARTS, n))
    part_size = (size + n - 1) // n
    if part_size < OSS_MIN_PART:
        part_size = OSS_MIN_PART
    if part_size > OSS_MAX_PART:
        part_size = OSS_MAX_PART
    parts = []
    offset = 0
    number = 1
    while offset < size:
        if number > MAX_PARTS:
            raise RuntimeError("分片数量超过 %d" % MAX_PARTS)
        sz = min(part_size, size - offset)
        parts.append({"number": number, "offset": offset, "size": sz})
        offset += sz
        number += 1
    return parts


class LimitedReader:
    def __init__(self, raw, limit, on_abs):
        self.raw = raw
        self.left = int(limit)
        self.sent = 0
        self.on_abs = on_abs

    def __len__(self):
        return self.sent + self.left

    def read(self, amt=-1):
        if halted():
            raise InterruptedError("已中断")
        if self.left <= 0:
            return b""
        if amt is None or amt < 0 or amt > 64 * 1024:
            amt = 64 * 1024
        amt = min(amt, self.left)
        data = self.raw.read(amt)
        if not data:
            return b""
        self.left -= len(data)
        self.sent += len(data)
        if self.on_abs:
            self.on_abs(self.sent)
        return data


def gmt_date():
    return formatdate(timeval=None, localtime=False, usegmt=True)


def oss_string_to_sign(method, bucket, key, headers, params):
    h = {k.lower(): str(v).strip() for k, v in headers.items()}
    content_md5 = h.get("content-md5", "")
    content_type = h.get("content-type", "")
    date = h.get("x-oss-date") or h.get("date") or ""
    canon = []
    for name in sorted(k for k in h if k.startswith("x-oss-")):
        canon.append("%s:%s" % (name, h[name]))
    headers_string = ("\n".join(canon) + "\n") if canon else ""
    resource = "/%s/%s" % (bucket, key)
    sub = []
    for pk, pv in params.items():
        sub.append((pk, "" if pv is None else str(pv)))
    sub.sort(key=lambda item: item[0])
    if sub:
        bits = []
        for pk, pv in sub:
            bits.append(pk if pv == "" else "%s=%s" % (pk, pv))
        resource += "?" + "&".join(bits)
    return "\n".join([method, content_md5, content_type, date, headers_string + resource])


def oss_sign(method, bucket, key, headers, params, key_id, key_secret):
    sts = oss_string_to_sign(method, bucket, key, headers, params)
    digest = hmac.new(key_secret.encode("utf-8"), sts.encode("utf-8"), hashlib.sha1).digest()
    headers["Authorization"] = "OSS %s:%s" % (key_id, base64.b64encode(digest).decode("ascii"))
    return sts


def xml_text(payload, tag):
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        m = re.search(r"<%s>([^<]+)</%s>" % (tag, tag), payload.decode("utf-8", "replace"))
        return m.group(1) if m else ""
    for el in root.iter():
        if el.tag.split("}")[-1] == tag and el.text:
            return el.text.strip()
    return ""


def checkpoint_path(save_dir, file_path):
    base = os.path.basename(file_path)
    safe = re.sub(r"[^\w.\-]+", "_", base, flags=re.UNICODE)[:80] or "file"
    digest = hashlib.md5(os.path.abspath(file_path).encode("utf-8")).hexdigest()[:10]
    return os.path.join(save_dir, "%s.%s.json" % (safe, digest))


def atomic_write_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_target(value):
    """-c / 配置里的 cid：纯数字当 cid，其余当网盘路径（/ 表示根目录）。返回 int 或规范化后的 /a/b。"""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return 0
    if text.isdigit():
        return int(text)
    parts = [seg for seg in re.split(r"[\\/]+", text) if seg]
    if not parts:
        return 0
    return "/" + "/".join(parts)


def default_config():
    return {
        "cookies": "",
        "cid": 0,
        "resultDir": "",
        "httpRetry": 0,
        "httpProxy": "",
        "ossProxy": "",
        "partsNum": 0,
    }


class Api115:
    def __init__(self, cookies, http_retry, proxy, verbose):
        self.cookies = cookies.strip()
        self.http_retry = max(0, int(http_retry))
        self.proxy = proxy.strip()
        self.verbose = verbose
        self._local = threading.local()
        self.user_id = ""
        self.user_key = ""
        self._init_lock = threading.Lock()
        self._last_init = 0.0

    def session(self):
        sess = getattr(self._local, "s", None)
        if sess is None:
            sess = requests.Session()
            sess.headers.update({"User-Agent": UA, "Cookie": self.cookies})
            if self.proxy:
                sess.proxies.update({"http": self.proxy, "https": self.proxy})
                sess.trust_env = False
            self._local.s = sess
        return sess

    def request(self, method, url, data=None, headers=None, timeout=30):
        last = None
        for _ in range(self.http_retry + 1):
            try:
                resp = self.session().request(
                    method, url, data=data, headers=headers, timeout=timeout,
                )
                if resp.status_code >= 500:
                    raise RuntimeError("HTTP %s" % resp.status_code)
                return resp
            except Exception as exc:
                last = exc
                if self.verbose:
                    log("http 请求出现错误：%s" % exc)
        raise RuntimeError("http 请求出现错误：%s" % last)

    def get_json(self, url):
        resp = self.request("GET", url)
        if not resp.content:
            raise RuntimeError("响应为空: %s" % url)
        return resp.json()

    def post_json(self, url, form):
        if isinstance(form, dict):
            body = urllib.parse.urlencode(sorted(form.items()))
        else:
            body = form
        resp = self.request(
            "POST", url, data=body.encode("utf-8") if isinstance(body, str) else body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if not resp.content:
            raise RuntimeError("响应为空: %s" % url)
        return resp.json()

    def login(self):
        data = self.get_json(INFO_URL)
        uid = data.get("user_id", 0)
        self.user_id = str(uid)
        self.user_key = str(data.get("userkey") or data.get("user_key") or "")
        if self.user_id in ("", "0") or not self.user_key:
            raise RuntimeError("获取 userkey 出错，请确定 cookies 是否设置好（每次网页登录都要更新）")
        if self.verbose:
            log("userID 和 userKey：%s %s" % (self.user_id, self.user_key))

    def order(self, cid):
        try:
            body = "user_order=user_ptime&file_id=%d&user_asc=0&fc_mix=0" % int(cid)
            self.post_json(ORDER_URL, body)
        except Exception as exc:
            if self.verbose:
                log("设置排序失败（可忽略）：%s" % exc)

    def _items(self, payload):
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("list", "data"):
                if isinstance(data.get(key), list):
                    return data[key]
        return []

    def _find_dir(self, payload, pid, name):
        for item in self._items(payload):
            if not isinstance(item, dict):
                continue
            if item.get("fid"):
                continue
            try:
                parent = int(item.get("pid"))
                cid = int(item.get("cid"))
            except (TypeError, ValueError):
                continue
            if parent == int(pid) and item.get("n") == name:
                return cid
        return None

    def find_dir(self, pid, name):
        """在 pid 下找名为 name 的子文件夹，找不到返回 None（不创建）。"""
        query = urllib.parse.urlencode({"search_value": name})
        try:
            found = self._find_dir(self.get_json(SEARCH_URL % int(pid) + "&" + query), pid, name)
            if found is not None:
                return found
        except Exception as exc:
            if self.verbose:
                log("搜索文件夹失败，改为直接列出：%s" % exc)
        return self._find_dir(self.get_json(LIST_DIR_URL % int(pid)), pid, name)

    def resolve_path(self, path, create=True):
        """把 /a/b/c 逐级解析成 cid。create=True 时缺的层级会创建（像 mkdir -p）。"""
        cid = 0
        walked = ""
        for name in [seg for seg in re.split(r"[\\/]+", path) if seg]:
            if name in (".", ".."):
                raise RuntimeError("路径里不能有 . 或 ..：%s" % path)
            walked += "/" + name
            nxt = self.find_dir(cid, name)
            if nxt is None:
                if not create:
                    raise RuntimeError("网盘里找不到文件夹 %s" % walked)
                nxt = self.create_dir(cid, name)
                log("已在网盘创建文件夹 %s（cid=%d）" % (walked, nxt))
            cid = nxt
        return cid

    def create_dir(self, pid, name):
        time.sleep(0.4)
        payload = self.post_json(CREATE_DIR_URL, {"pid": str(int(pid)), "cname": name})
        if payload.get("state"):
            cid = int(payload.get("cid"))
            if self.verbose:
                log("创建文件夹 %s ，cid=%d" % (name, cid))
            self.order(cid)
            return cid
        errno = int(payload.get("errno") or 0)
        if errno != 20004:
            raise RuntimeError("创建文件夹 %s 失败：%s" % (name, payload.get("error") or payload))
        query = urllib.parse.urlencode({"search_value": name})
        search_url = SEARCH_URL % int(pid) + "&" + query
        try:
            found = self._find_dir(self.get_json(search_url), pid, name)
            if found is not None:
                self.order(found)
                return found
        except Exception as exc:
            if self.verbose:
                log("搜索文件夹失败，改为直接列出：%s" % exc)
        found = self._find_dir(self.get_json(LIST_DIR_URL % int(pid)), pid, name)
        if found is None:
            raise RuntimeError("创建文件夹 %s 失败，且未能在父目录中找到同名文件夹" % name)
        self.order(found)
        return found

    def upload_sha1(self, cipher, filename, file_size, file_sha1, sign_key, sign_val, cid):
        file_id = file_sha1.upper()
        target = TARGET_PREFIX + str(int(cid))
        h1 = hashlib.sha1((self.user_id + file_id + target + "0").encode("utf-8")).hexdigest()
        sig = hashlib.sha1((self.user_key + h1 + END_STRING).encode("utf-8")).hexdigest().upper()
        now = int(time.time())
        uid_md5 = hashlib.md5(self.user_id.encode("utf-8")).hexdigest()
        token = hashlib.md5(
            (MD5_SALT + file_id + str(file_size) + sign_key + sign_val + self.user_id
             + str(now) + uid_md5 + APP_VER).encode("utf-8")
        ).hexdigest()
        k_ec = cipher.encode_token(now)
        form = {
            "appid": "0",
            "appversion": APP_VER,
            "userid": self.user_id,
            "filename": filename,
            "filesize": str(file_size),
            "fileid": file_id,
            "target": target,
            "sig": sig,
            "t": str(now),
            "token": token,
        }
        if sign_key and sign_val:
            form["sign_key"] = sign_key
            form["sign_val"] = sign_val
        body = cipher.encrypt(urllib.parse.urlencode(sorted(form.items())).encode("utf-8"))
        url = INIT_URL % k_ec
        if self.verbose:
            log("initupload sig=%s token=%s" % (sig, token))
        with self._init_lock:
            gap = time.monotonic() - self._last_init
            if gap < 0.3:
                time.sleep(0.3 - gap)
            resp = self.request(
                "POST", url, data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )
            self._last_init = time.monotonic()
        raw = resp.content
        try:
            decrypted = cipher.decrypt(raw)
        except Exception as exc:
            if self.verbose:
                log("解密响应失败，改用原文：%s" % exc)
            decrypted = raw
        if self.verbose:
            log("init 响应: %s" % decrypted[:1500])
        try:
            return json.loads(decrypted.decode("utf-8"))
        except Exception as exc:
            raise RuntimeError("无法解析 initupload 响应: %s" % decrypted[:300]) from exc

    def fast_or_token(self, cipher, path, cid, on_hash=None, name=None):
        file_sha1 = sha1_file(path, on_hash)
        filename = name or os.path.basename(path)
        size = os.path.getsize(path)
        payload = self.upload_sha1(cipher, filename, size, file_sha1, "", "", cid)
        status = int(payload.get("status") or 0)
        code = int(payload.get("statuscode") or 0) if "statuscode" in payload else None
        if status == 7 and code == 701:
            sign_key = str(payload.get("sign_key") or "")
            sign_check = str(payload.get("sign_check") or "")
            sign_val = sha1_range(path, sign_check)
            payload = self.upload_sha1(
                cipher, filename, size, file_sha1, sign_key, sign_val, cid,
            )
            status = int(payload.get("status") or 0)
            code = int(payload.get("statuscode") or 0) if "statuscode" in payload else None
        payload["_sha1"] = file_sha1
        payload["_size"] = size
        payload["_name"] = filename
        if status == 2 and code == 0:
            return "fast", payload
        if status == 1 and code == 0:
            return "token", payload
        msg = payload.get("statusmsg") or payload.get("message") or payload
        raise RuntimeError("秒传/初始化失败：%s" % msg)

    def verify(self, cid, file_sha1, filename, size):
        sha = file_sha1.upper()
        last_err = ""
        for attempt in range(6):
            if attempt:
                time.sleep(1.0 + attempt * 0.4)
            for url in (
                LIST_RECENT_URL % (int(cid), 50),
                (SEARCH_URL % int(cid)) + "&" + urllib.parse.urlencode({"search_value": filename}),
                LIST_DIR_URL % int(cid),
            ):
                try:
                    payload = self.get_json(url)
                except Exception as exc:
                    last_err = str(exc)
                    continue
                if isinstance(payload, dict) and payload.get("state") is False:
                    last_err = str(payload.get("error") or payload.get("message") or payload)[:300]
                    continue
                if self._match(payload, sha, filename, size):
                    return True, ""
        return False, last_err or "列表和搜索都没有匹配到这个文件"

    def _match(self, payload, sha, filename, size):
        for item in self._items(payload):
            if not isinstance(item, dict):
                continue
            item_sha = str(item.get("sha") or item.get("sha1") or "").upper()
            item_name = item.get("n") or item.get("name") or ""
            try:
                item_size = int(item.get("s") or item.get("size") or -1)
            except (TypeError, ValueError):
                item_size = -1
            if item_sha and item_sha == sha:
                return True
            if item_name == filename and item_size == int(size):
                return True
        return False


class OssClient:
    def __init__(self, api, internal, proxy, verbose):
        self.api = api
        self.internal = internal
        self.proxy = proxy.strip()
        self.verbose = verbose
        self._local = threading.local()
        self._token = None
        self._token_at = 0.0
        self._lock = threading.Lock()
        self.endpoint_scheme = "https"
        self.endpoint_host = ""

    def session(self):
        sess = getattr(self._local, "s", None)
        if sess is None:
            sess = requests.Session()
            sess.headers.update({"User-Agent": ALI_UA})
            if self.proxy:
                sess.proxies.update({"http": self.proxy, "https": self.proxy})
                sess.trust_env = False
            self._local.s = sess
        return sess

    def refresh(self, force=False):
        with self._lock:
            if self._token and not force and (time.monotonic() - self._token_at) < 50 * 60:
                return self._token
            info = self.api.get_json(GETINFO_URL)
            endpoint = str(info.get("endpoint") or info.get("Endpoint") or "")
            token_url = str(info.get("gettokenurl") or info.get("getTokenUrl") or info.get("GetTokenURL") or "")
            if not endpoint or not token_url:
                raise RuntimeError("getuploadinfo 缺少 endpoint/gettokenurl: %s" % info)
            if self.internal and ".aliyuncs.com" in endpoint and "-internal" not in endpoint:
                endpoint = endpoint.replace(".aliyuncs.com", "-internal.aliyuncs.com", 1)
            if "://" not in endpoint:
                endpoint = "https://" + endpoint
            parsed = urllib.parse.urlparse(endpoint)
            self.endpoint_scheme = parsed.scheme or "https"
            self.endpoint_host = parsed.netloc
            resp = self.api.request("GET", token_url, timeout=30)
            token = resp.json()
            key_id = token.get("AccessKeyId") or token.get("accessKeyId")
            secret = token.get("AccessKeySecret") or token.get("accessKeySecret")
            security = token.get("SecurityToken") or token.get("securityToken")
            if not key_id or not secret or not security:
                raise RuntimeError("OSS token 无效: %s" % token)
            self._token = {
                "id": key_id,
                "secret": secret,
                "token": security,
            }
            self._token_at = time.monotonic()
            if self.verbose:
                log("OSS endpoint=%s://%s" % (self.endpoint_scheme, self.endpoint_host))
            return self._token

    def _url(self, bucket, key, params):
        quoted = urllib.parse.quote(key, safe="/")
        base = "%s://%s.%s/%s" % (self.endpoint_scheme, bucket, self.endpoint_host, quoted)
        if not params:
            return base
        pairs = []
        for pk, pv in params.items():
            if pv is None or pv == "":
                pairs.append(urllib.parse.quote(pk, safe=""))
            else:
                pairs.append("%s=%s" % (
                    urllib.parse.quote(pk, safe=""),
                    urllib.parse.quote(str(pv), safe=""),
                ))
        return base + "?" + "&".join(pairs)

    def call(self, method, bucket, key, params, headers, data=None, timeout=(30, None)):
        replayable = data is None or isinstance(data, (bytes, bytearray))

        def once(cred):
            hdrs = {
                "Date": gmt_date(),
                "x-oss-security-token": cred["token"],
                "User-Agent": ALI_UA,
            }
            hdrs.update(headers or {})
            oss_sign(method, bucket, key, hdrs, params or {}, cred["id"], cred["secret"])
            return self.session().request(
                method, self._url(bucket, key, params or {}),
                data=data, headers=hdrs, timeout=timeout,
            )

        resp = once(self.refresh())
        # 流式 body 只能读一次，403 交给分片重试重新打开文件
        if replayable and resp.status_code == 403 and b"SecurityToken" in resp.content:
            resp = once(self.refresh(force=True))
        return resp

    def put_object(self, bucket, key, reader, size, extra_headers, on_abs):
        def progress(n):
            on_abs(n)
        body = LimitedReader(reader, size, progress) if not isinstance(reader, (bytes, bytearray)) else reader
        if isinstance(body, (bytes, bytearray)):
            data = body
        else:
            data = body
        headers = {"Content-Length": str(size), "Content-Type": "application/octet-stream"}
        headers.update(extra_headers or {})
        return self.call("PUT", bucket, key, {}, headers, data=data)

    def initiate(self, bucket, key):
        # 115 回调按顺序分片校验整文件。合并时不能再带 x-oss-hash-sha1。
        variants = (
            {"uploads": "", "sequential": "", "x-oss-enable-sha1": ""},
            {"uploads": "", "sequential": ""},
        )
        last = b""
        status = 0
        for params in variants:
            resp = self.call("POST", bucket, key, params, {"Content-Type": "application/xml"})
            status = resp.status_code
            last = resp.content
            if status // 100 != 2:
                continue
            upload_id = xml_text(resp.content, "UploadId")
            if upload_id:
                return upload_id
        raise RuntimeError("初始化分片失败 HTTP %s %s" % (status, last[:300]))

    def upload_part(self, bucket, key, upload_id, number, reader, size, on_abs):
        body = LimitedReader(reader, size, on_abs)
        headers = {"Content-Length": str(size), "Content-Type": "application/octet-stream"}
        params = {"partNumber": str(number), "uploadId": upload_id}
        resp = self.call("PUT", bucket, key, params, headers, data=body)
        if resp.status_code // 100 != 2:
            if resp.status_code == 403:
                self.refresh(force=True)
            raise RuntimeError("分片 %s 失败 HTTP %s %s" % (
                number, resp.status_code, resp.content[:300],
            ))
        etag = resp.headers.get("ETag") or resp.headers.get("Etag")
        if not etag:
            raise RuntimeError("分片 %s 没有 ETag" % number)
        return etag

    def complete(self, bucket, key, upload_id, parts, sha1, callback, callback_var):
        parts = sorted(parts, key=lambda item: item["number"])
        xml = ["<CompleteMultipartUpload>"]
        for part in parts:
            etag = part["etag"]
            xml.append("<Part><PartNumber>%d</PartNumber><ETag>%s</ETag></Part>" % (
                int(part["number"]), etag,
            ))
        xml.append("</CompleteMultipartUpload>")
        body = "".join(xml).encode("utf-8")
        headers = {
            "Content-Type": "application/xml",
            "Content-Length": str(len(body)),
        }
        if callback:
            headers["x-oss-callback"] = oss_callback_header(callback)
        if callback_var:
            headers["x-oss-callback-var"] = oss_callback_header(callback_var)
        resp = self.call("POST", bucket, key, {"uploadId": upload_id}, headers, data=body)
        text = resp.content.decode("utf-8", "replace")
        if self.verbose:
            log("complete HTTP %s %s" % (resp.status_code, text[:800]))
        if resp.status_code == 203 or b"CallbackFailed" in resp.content:
            raise RuntimeError("上传回调失败 HTTP %s %s" % (resp.status_code, text[:800]))
        if resp.status_code == 404 or xml_text(resp.content, "Code") == "NoSuchUpload":
            return {"result": "missing", "body": text, "status": resp.status_code}
        if resp.status_code != 200:
            code = xml_text(resp.content, "Code")
            raise RuntimeError("合并分片失败 HTTP %s %s %s" % (resp.status_code, code, text[:800]))
        if callback_succeeded(text):
            return {"result": "callback", "body": text, "status": 200}
        return {"result": "uploaded", "body": text, "status": 200}


class FileProgress:
    def __init__(self, path, size, cid):
        self.path = path
        self.size = size
        self.cid = cid
        self.phase = "等待"
        self.done = 0
        self.phase_start = None
        self.samples = deque()
        self.error = ""
        self.cancel = threading.Event()

    def set_phase(self, phase, reset=True):
        ui = GLOBAL_UI
        if ui is None:
            self.phase = phase
            if reset:
                self.done = 0
                self.samples.clear()
                self.phase_start = time.monotonic()
            return
        with ui.lock:
            self.phase = phase
            if reset:
                self.done = 0
                self.samples.clear()
                self.phase_start = time.monotonic()

    def finish(self):
        ui = GLOBAL_UI
        if ui is None:
            self.phase = "完成"
            self.done = self.size
            return
        with ui.lock:
            self.phase = "完成"
            self.done = self.size

    def add(self, nbytes, upload, ui):
        if nbytes <= 0:
            return
        now = time.monotonic()
        self.done += nbytes
        self.samples.append((now, nbytes))
        cut = now - 5
        while self.samples and self.samples[0][0] < cut:
            self.samples.popleft()
        if self.phase_start is None:
            self.phase_start = now
        if upload and ui is not None:
            ui.add_upload(nbytes, now)

    def rate(self, now):
        return window_rate(self.samples, now, 1.0)

    def average(self, now):
        if not self.phase_start or self.done <= 0:
            return 0.0
        return self.done / max(now - self.phase_start, 0.25)


class ProgressUI:
    def __init__(self, jobs, mode_name):
        self.jobs = jobs
        self.mode_name = mode_name
        self.files = []
        self.logs = deque(maxlen=5)
        self.lock = threading.RLock()
        self.started = False
        self.alive = False
        self.thread = None
        self.tty = sys.stdout.isatty()
        self.prev_lines = 0
        self.up_samples = deque()
        self.up_total = 0
        self.up_start = None
        self.done_n = 0
        self.fail_n = 0
        self.save_n = 0

    def add_file(self, item):
        with self.lock:
            self.files.append(item)

    def add_upload(self, nbytes, now):
        self.up_total += nbytes
        self.up_samples.append((now, nbytes))
        if self.up_start is None:
            self.up_start = now
        cut = now - 5
        while self.up_samples and self.up_samples[0][0] < cut:
            self.up_samples.popleft()

    def mark_done(self, kind):
        with self.lock:
            if kind == "success":
                self.done_n += 1
            elif kind == "failed":
                self.fail_n += 1
            elif kind == "saved":
                self.save_n += 1

    def log(self, msg):
        with self.lock:
            self.logs.append(str(msg))
        if not self.tty:
            with PRINT_LOCK:
                print(msg, file=sys.stderr, flush=True)

    def start(self):
        self.started = True
        self.alive = True
        self.thread = threading.Thread(target=self._loop, name="progress", daemon=True)
        self.thread.start()

    def stop(self):
        self.alive = False
        if self.thread:
            self.thread.join(timeout=1.5)
        if self.tty:
            self._render()
            with PRINT_LOCK:
                sys.stdout.write("\n")
                sys.stdout.flush()
            self.prev_lines = 0

    def _loop(self):
        last_plain = 0.0
        while self.alive:
            if self.tty:
                self._render()
            else:
                now = time.monotonic()
                if now - last_plain >= 1.0:
                    last_plain = now
                    with PRINT_LOCK:
                        print(self._oneline(now), file=sys.stderr, flush=True)
            time.sleep(0.2)

    def _stats(self, now):
        with self.lock:
            rows = []
            total_size = 0
            progressed = 0
            for item in self.files:
                total_size += item.size
                phase = item.phase
                done = item.size if phase == "完成" else item.done
                if phase == "完成":
                    progressed += item.size
                elif phase == "上传":
                    progressed += min(item.done, item.size)
                rows.append({
                    "path": item.path,
                    "size": item.size,
                    "phase": phase,
                    "done": done,
                    "error": item.error,
                    "rate": item.rate(now),
                })
            logs = list(self.logs)
            up_samples = list(self.up_samples)
            done_n, fail_n, save_n = self.done_n, self.fail_n, self.save_n
        instant = window_rate(up_samples, now, 1.0)
        remain = max(0, total_size - progressed)
        eta = (remain / instant) if instant > 0 else None
        return {
            "rows": rows,
            "logs": logs,
            "total_size": total_size,
            "progressed": progressed,
            "instant": instant,
            "eta": eta,
            "done_n": done_n,
            "fail_n": fail_n,
            "save_n": save_n,
        }

    def _oneline(self, now):
        st = self._stats(now)
        pct = (100.0 * st["progressed"] / st["total_size"]) if st["total_size"] else 0
        active = [item for item in st["rows"] if item["phase"] in ("哈希", "秒传", "上传")]
        bits = []
        for item in active[:3]:
            pct_f = (100.0 * item["done"] / item["size"]) if item["size"] else 0
            bits.append("%s %s %.0f%% %s" % (
                os.path.basename(item["path"]), item["phase"], pct_f, fmt_rate(item["rate"]),
            ))
        return "总 %.1f%% 实时 %s | %s" % (
            pct, fmt_rate(st["instant"]),
            " ; ".join(bits) if bits else "等待中",
        )

    def _compose(self):
        now = time.monotonic()
        st = self._stats(now)
        cols = shutil.get_terminal_size((100, 24)).columns
        lines = list(st["logs"])
        pct = (st["progressed"] / st["total_size"]) if st["total_size"] else 0
        lines.append(
            "115上传  %s  并发 %d  完成 %d  失败 %d  已存档 %d  Ctrl+C 暂停" % (
                self.mode_name, self.jobs, st["done_n"], st["fail_n"], st["save_n"],
            )
        )
        lines.append(
            "总进度 %5.1f%%  %s / %s   实时 %s   ETA %s" % (
                pct * 100,
                fmt_size(st["progressed"]),
                fmt_size(st["total_size"]),
                fmt_rate(st["instant"]),
                fmt_eta(st["eta"]),
            )
        )
        lines.append("─" * min(max(cols - 1, 10), 72))
        rows = st["rows"]
        active = [item for item in rows if item["phase"] in ("哈希", "秒传", "上传")]
        if len(rows) <= 16:
            show = rows
            extra = ""
        else:
            show = active[:10]
            if len(show) < 8:
                for item in rows:
                    if item not in show and item["phase"] != "完成":
                        show.append(item)
                    if len(show) >= 10:
                        break
            waiting = sum(1 for item in rows if item["phase"] == "等待")
            extra = "其余 等待 %d  完成 %d  失败 %d" % (waiting, st["done_n"], st["fail_n"])
        bar_w = 16 if cols >= 110 else 10
        for item in show:
            ratio = (item["done"] / item["size"]) if item["size"] else (1.0 if item["phase"] == "完成" else 0.0)
            ratio = max(0.0, min(1.0, ratio))
            filled = int(round(ratio * bar_w))
            bar = "█" * filled + "░" * (bar_w - filled)
            base = os.path.basename(item["path"])
            name = base
            if sum(1 for other in rows if os.path.basename(other["path"]) == base) > 1:
                name = os.path.join(os.path.basename(os.path.dirname(item["path"])) or ".", base)
            eta = None
            if item["phase"] in ("哈希", "上传") and item["size"] and item["rate"] > 0:
                eta = max(0, item["size"] - item["done"]) / item["rate"]
            shown = item["size"] if item["phase"] == "完成" else min(item["done"], item["size"])
            line = "%s  %-4s %3.0f%% %s  实时 %-12s %s/%s  ETA %s" % (
                name, item["phase"], ratio * 100, bar,
                fmt_rate(item["rate"]),
                fmt_size(shown),
                fmt_size(item["size"]),
                fmt_eta(eta) if item["phase"] != "完成" else "00:00",
            )
            if item["phase"] == "失败" and item["error"]:
                line += "  " + item["error"]
            lines.append(line)
        if extra:
            lines.append(extra)
        return [clip_text(line, cols) for line in lines]

    def _render(self):
        lines = self._compose()
        buf = []
        if self.prev_lines:
            buf.append("\x1b[%dA" % self.prev_lines)
        for line in lines:
            buf.append("\x1b[2K%s\n" % line)
        extra = self.prev_lines - len(lines)
        if extra > 0:
            for _ in range(extra):
                buf.append("\x1b[2K\n")
            buf.append("\x1b[%dA" % extra)
        with PRINT_LOCK:
            sys.stdout.write("".join(buf))
            sys.stdout.flush()
        self.prev_lines = len(lines)


def callback_is_encoded(value):
    try:
        decoded = base64.b64decode(value, validate=True)
    except Exception:
        return False
    stripped = decoded.lstrip()
    return stripped.startswith(b"{") or stripped.startswith(b"[")


def oss_callback_header(value):
    if not value:
        return ""
    raw = value.strip()
    if callback_is_encoded(raw):
        return raw
    return base64.b64encode(raw.encode("utf-8")).decode("ascii")


def callback_succeeded(text):
    text = (text or "").strip()
    if not text or text[0] not in "{[":
        return False
    try:
        data = json.loads(text)
    except Exception:
        return False
    if not isinstance(data, dict):
        return False
    if data.get("state") is True:
        return True
    if data.get("pickcode") or data.get("pick_code"):
        return True
    inner = data.get("data")
    if isinstance(inner, dict) and any(inner.get(k) for k in ("pick_code", "pickcode", "file_id", "id")):
        return True
    status = data.get("status")
    if status in (1, 2, "1", "2") and not data.get("statusmsg") and data.get("statuscode") in (0, "0", None):
        return True
    return False


def callback_pair(token):
    cb = token.get("callback") or {}
    if isinstance(cb, str):
        return cb, ""
    callback = cb.get("callback") or ""
    callback_var = cb.get("callback_var") or ""
    if not isinstance(callback, str):
        callback = json.dumps(callback, ensure_ascii=False, separators=(",", ":"))
    if not isinstance(callback_var, str):
        callback_var = json.dumps(callback_var, ensure_ascii=False, separators=(",", ":"))
    return callback, callback_var


def oss_headers_for_callback(callback, callback_var):
    headers = {}
    encoded = oss_callback_header(callback)
    encoded_var = oss_callback_header(callback_var)
    if encoded:
        headers["x-oss-callback"] = encoded
    if encoded_var:
        headers["x-oss-callback-var"] = encoded_var
    return headers


class App:
    def __init__(self, args, config, api):
        self.args = args
        self.config = config
        self.api = api
        self.oss = OssClient(api, args.a, config.get("_oss_proxy") or "", args.v)
        self.mode = "f" if args.f else ("u" if args.u else "m")
        self.jobs = max(1, args.jobs)
        self.save_dir = args.d
        self.remove_file = args.e
        self.parts_num = int(config.get("partsNum") or 0)
        self.result = {"success": [], "failed": [], "saved": [], "notes": []}
        self.result_lock = threading.Lock()
        self.net = threading.Semaphore(self.jobs)
        self.put_pool = ThreadPoolExecutor(max_workers=self.jobs, thread_name_prefix="put")
        self.cipher_local = threading.local()

    def cipher(self):
        c = getattr(self.cipher_local, "c", None)
        if c is None:
            c = EcdhCipher()
            self.cipher_local.c = c
        return c

    def record(self, kind, path, cid, error=""):
        with self.result_lock:
            if kind == "success":
                self.result["success"].append(path)
            elif kind == "failed":
                self.result["failed"].append({"path": path, "cid": cid, "error": error})
            else:
                self.result["saved"].append(path)
        if GLOBAL_UI:
            GLOBAL_UI.mark_done(kind)

    def note(self, msg):
        log(msg)
        with self.result_lock:
            self.result["notes"].append(str(msg))

    def _remove_local(self, path):
        os.remove(path)
        log("已删除本地文件 %s" % path)

    def upload_file(self, task):
        path, cid, prog = task
        prev_cancel = getattr(_CANCEL, "ev", None)
        _CANCEL.ev = getattr(prog, "cancel", None)
        try:
            if halted():
                prog.phase = "暂停"
                return
            cp_file = checkpoint_path(self.save_dir, path) if self.mode == "m" else ""
            cp = None
            if cp_file and os.path.isfile(cp_file):
                try:
                    cp = load_json(cp_file)
                except Exception as exc:
                    log("读取存档失败，将重新上传 %s ：%s" % (path, exc))
                    cp = None
            if cp and cp.get("upload_id") and cp.get("mode") != "sequential-sha1":
                log("旧存档不是顺序分片，115 无法校验，将重新上传 %s" % path)
                try:
                    os.remove(cp_file)
                except OSError:
                    pass
                cp = None
            if cp and cp.get("upload_id"):
                log("继续断点续传 %s" % path)
                self._multipart(path, cid, prog, cp, cp_file, resume=True)
                return
            prog.set_phase("哈希")

            def on_hash(n):
                prog.add(n, False, GLOBAL_UI)

            remote_name = (self.args.prefix + os.path.basename(path)) if self.args.prefix else None
            try:
                kind, token = self.api.fast_or_token(self.cipher(), path, cid, on_hash, remote_name)
            except InterruptedError:
                prog.set_phase("暂停", reset=False)
                return
            if kind == "fast":
                prog.finish()
                log("秒传成功 %s" % path)
                if self.remove_file:
                    self._remove_local(path)
                if cp_file and os.path.isfile(cp_file):
                    os.remove(cp_file)
                self.record("success", path, cid)
                return
            if self.mode == "f":
                raise RuntimeError("秒传失败，-f 不会改用普通上传")
            size = int(token.get("_size") or os.path.getsize(path))
            if self.mode == "u":
                if size > SIMPLE_LIMIT:
                    raise RuntimeError("超过 5GB，普通模式 -u 不支持，请改用 -m")
                log("秒传未命中，普通上传 %s" % path)
                self._simple(path, cid, prog, token)
                return
            if size <= 1024:
                log("%s 小于等于 1KB，改用普通上传" % path)
                self._simple(path, cid, prog, token)
                return
            if size > MAX_FILE:
                raise RuntimeError("超过 115GB，取消上传")
            log("秒传未命中，断点续传 %s" % path)
            self._multipart(path, cid, prog, self._new_cp(path, cid, token), cp_file, resume=False)
        except InterruptedError:
            prog.set_phase("暂停", reset=False)
        except Exception as exc:
            with GLOBAL_UI.lock:
                prog.phase = "失败"
                prog.error = str(exc)
            log("上传失败 %s ：%s" % (path, exc))
            self.record("failed", path, cid, str(exc))
        finally:
            _CANCEL.ev = prev_cancel

    def _new_cp(self, path, cid, token):
        callback, callback_var = callback_pair(token)
        return {
            "version": 1,
            "path": os.path.abspath(path),
            "size": int(token["_size"]),
            "sha1": token["_sha1"],
            "name": token.get("_name") or os.path.basename(path),
            "cid": int(cid),
            "bucket": token.get("bucket") or "",
            "object": token.get("object") or "",
            "upload_id": "",
            "mode": "sequential-sha1",
            "callback": callback,
            "callback_var": callback_var,
            "parts": [],
            "done": [],
        }

    def _simple(self, path, cid, prog, token):
        bucket = token.get("bucket") or ""
        key = token.get("object") or ""
        sha1 = token["_sha1"]
        size = int(token["_size"])
        remote_name = token.get("_name") or os.path.basename(path)
        if not bucket or not key:
            raise RuntimeError("初始化响应缺少 bucket/object")
        callback, callback_var = callback_pair(token)
        prog.set_phase("上传")
        self.oss.refresh()
        state = {"n": 0}
        headers = oss_headers_for_callback(callback, callback_var)
        resp = None
        last = None
        for attempt in range(3):
            if halted():
                raise InterruptedError("已中断")
            prog.set_phase("上传")
            state["n"] = 0

            def on_abs(n, st=state):
                delta = n - st["n"]
                st["n"] = n
                if delta > 0:
                    prog.add(delta, True, GLOBAL_UI)

            try:
                with self.net:
                    with open(path, "rb") as f:
                        resp = self.oss.put_object(bucket, key, f, size, headers, on_abs)
                if resp.status_code // 100 == 2:
                    break
                if resp.status_code == 403:
                    self.oss.refresh(force=True)
                last = RuntimeError("普通上传失败 HTTP %s %s" % (resp.status_code, resp.content[:300]))
            except InterruptedError:
                raise
            except Exception as exc:
                last = exc
            log("普通上传失败（第 %d 次）：%s" % (attempt + 1, last))
            if attempt < 2:
                time.sleep(1 + attempt)
        else:
            raise last
        if not self.api.verify(cid, sha1, remote_name, size)[0]:
            raise RuntimeError("OSS 返回成功，但在 115 文件列表中未确认，请稍后到网盘查看")
        prog.finish()
        log("普通上传成功 %s" % path)
        if self.remove_file:
            self._remove_local(path)
        self.record("success", path, cid)

    def _multipart(self, path, cid, prog, cp, cp_file, resume):
        bucket = cp.get("bucket") or ""
        key = cp.get("object") or ""
        sha1 = cp["sha1"]
        size = int(cp["size"])
        remote_name = cp.get("name") or os.path.basename(path)
        if not bucket or not key:
            raise RuntimeError("存档缺少 bucket/object")
        self.oss.refresh()
        if not cp.get("parts"):
            cp["parts"] = plan_parts(size, self.parts_num)
        if not cp.get("upload_id"):
            cp["upload_id"] = self.oss.initiate(bucket, key)
            cp["done"] = []
            atomic_write_json(cp_file, cp)
        done_map = {int(item["number"]): item for item in cp.get("done") or []}
        pending = [part for part in cp["parts"] if int(part["number"]) not in done_map]
        pending.sort(key=lambda part: int(part["number"]))
        prog.set_phase("上传")
        already = sum(int(part["size"]) for part in cp["parts"] if int(part["number"]) in done_map)
        if already:
            if GLOBAL_UI is not None:
                with GLOBAL_UI.lock:
                    prog.done += already
            else:
                prog.done += already
        inflight = {}
        lock = threading.Lock()

        def report(number, absolute):
            with lock:
                prev = inflight.get(number, 0)
                inflight[number] = absolute
                delta = absolute - prev
            if delta > 0:
                prog.add(delta, True, GLOBAL_UI)

        def one(part):
            number = int(part["number"])
            if halted():
                raise InterruptedError("已中断")
            last_err = None
            for attempt in range(3):
                if halted():
                    raise InterruptedError("已中断")
                if attempt and time.monotonic() - self.oss._token_at > 50 * 60:
                    self.oss.refresh(force=True)
                try:
                    with lock:
                        inflight[number] = 0
                    with self.net:
                        with open(path, "rb") as f:
                            f.seek(int(part["offset"]))
                            etag = self.oss.upload_part(
                                bucket, key, cp["upload_id"], number, f, int(part["size"]),
                                lambda n, num=number: report(num, n),
                            )
                    with lock:
                        prev = inflight.pop(number, 0)
                    gap = int(part["size"]) - prev
                    if gap > 0:
                        prog.add(gap, True, GLOBAL_UI)
                    return {"number": number, "etag": etag}
                except InterruptedError:
                    raise
                except Exception as exc:
                    with lock:
                        prev = inflight.pop(number, 0)
                    if prev:
                        if GLOBAL_UI is not None:
                            with GLOBAL_UI.lock:
                                prog.done = max(0, prog.done - prev)
                        else:
                            prog.done = max(0, prog.done - prev)
                    if halted():
                        raise InterruptedError("已中断")
                    last_err = exc
                    log("分片 %d 上传失败（第 %d 次）：%s" % (number, attempt + 1, exc))
                    if attempt < 2:
                        time.sleep(1 + attempt)
            raise RuntimeError("分片 %d 连续失败：%s" % (number, last_err))

        futures = []
        error = None
        # 顺序分片不能并发，后一片必须等前一片完成。-j 只并发不同文件。
        for part in pending:
            if halted() or error:
                break
            try:
                item = one(part)
            except Exception as exc:
                error = exc
                if not isinstance(exc, InterruptedError):
                    log("分片失败：%s" % exc)
                continue
            if item:
                done_map[int(item["number"])] = item
                cp["done"] = sorted(done_map.values(), key=lambda x: int(x["number"]))
                atomic_write_json(cp_file, cp)
        if error or halted() or len(done_map) < len(cp["parts"]):
            cp["done"] = sorted(done_map.values(), key=lambda x: int(x["number"]))
            atomic_write_json(cp_file, cp)
            prog.set_phase("暂停", reset=False)
            log("已保存进度 %s" % cp_file)
            self.record("saved", path, cid)
            return
        callback = cp.get("callback") or ""
        callback_var = cp.get("callback_var") or ""
        if not callback:
            log("存档里没有 callback，115 可能不会登记这个文件")
        try:
            result = self.oss.complete(
                bucket, key, cp["upload_id"], list(done_map.values()),
                sha1, callback, callback_var,
            )
        except Exception as exc:
            atomic_write_json(cp_file, cp)
            prog.set_phase("暂停", reset=False)
            log("合并失败，进度已保存 %s ：%s" % (cp_file, exc))
            self.note(str(exc))
            self.record("saved", path, cid)
            return
        confirmed = result.get("result") == "callback"
        reason = ""
        if result.get("result") == "missing":
            confirmed, reason = self.api.verify(cid, sha1, remote_name, size)
            if not confirmed:
                if os.path.isfile(cp_file):
                    os.remove(cp_file)
                detail = (result.get("body") or "").replace("\n", " ")[:500]
                self.note("断点 uploadId 已失效，存档已删除。请再执行一次重新上传。列表：%s 响应：%s" % (reason, detail))
                self.record("failed", path, cid, "uploadId 已失效，请再运行一次")
                prog.set_phase("失败", reset=False)
                return
        if not confirmed:
            confirmed, reason = self.api.verify(cid, sha1, remote_name, size)
        if not confirmed:
            atomic_write_json(cp_file, cp)
            prog.set_phase("暂停", reset=False)
            detail = (result.get("body") or "").replace("\n", " ")[:500]
            message = "115 还没确认这个文件。合并响应 HTTP %s %s 。列表：%s 。进度已保存在 %s" % (
                result.get("status"), detail, reason, cp_file,
            )
            self.note(message)
            self.record("saved", path, cid)
            return
        prog.finish()
        if os.path.isfile(cp_file):
            os.remove(cp_file)
        log("断点续传成功 %s" % path)
        if self.remove_file:
            self._remove_local(path)
        self.record("success", path, cid)


MAX_ORDER_LABEL = {"mtime": "最新修改优先", "size": "最大优先", "name": "文件名升序"}


def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def _size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def order_files(paths, order):
    """按 order 排序：mtime 最新在前，size 最大在前，name 文件名升序。值相同按路径排序。"""
    if order == "mtime":
        return sorted(paths, key=lambda p: (-_mtime(p), p))
    if order == "size":
        return sorted(paths, key=lambda p: (-_size(p), p))
    return sorted(paths)


def expand_inputs(patterns, max_per=0, order="mtime"):
    """展开参数。max_per > 0 时，每个通配符参数最多取 max_per 个文件（只取文件，不进文件夹）。
    普通文件、普通文件夹参数不受 max_per 影响。"""
    found = []
    seen = set()
    missing = []
    for pattern in patterns:
        limited = False
        if glob.has_magic(pattern):
            matches = sorted(glob.glob(pattern, recursive=True))
            if max_per > 0:
                # 限量模式：只要文件，目录不展开，也不占名额
                matches = order_files([m for m in matches if os.path.isfile(m)], order)
                limited = True
            if not matches:
                missing.append(pattern)
                continue
            items = matches
        else:
            items = [pattern]
        taken = 0
        total_new = 0
        for item in items:
            path = os.path.abspath(item)
            if path in seen:
                continue
            total_new += 1
            if limited and taken >= max_per:
                continue
            seen.add(path)
            found.append(path)
            taken += 1
            if not os.path.exists(path):
                missing.append(item)
        if limited and total_new > taken:
            log("%s 匹配 %d 个文件，按 --max 取前 %d 个（%s）" % (
                pattern, total_new, taken, MAX_ORDER_LABEL.get(order, order),
            ))
    return found, missing


def collect_files(paths, recursive, root_cid, api):
    files = []
    for path in paths:
        if not os.path.exists(path):
            log("找不到 %s" % path)
            continue
        if os.path.isdir(path):
            if not recursive:
                log("%s 是文件夹，上传文件夹需要 --recursive" % path)
                continue
            base = os.path.basename(path.rstrip(os.sep)) or path
            try:
                top = api.create_dir(root_cid, base)
            except Exception as exc:
                log("创建远程文件夹失败，跳过 %s ：%s" % (path, exc))
                continue
            cid_map = {path: top}
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames.sort()
                filenames.sort()
                if dirpath not in cid_map:
                    parent = cid_map.get(os.path.dirname(dirpath))
                    if parent is None:
                        log("跳过 %s ，父目录没有创建成功" % dirpath)
                        dirnames[:] = []
                        continue
                    try:
                        cid_map[dirpath] = api.create_dir(parent, os.path.basename(dirpath))
                    except Exception as exc:
                        log("创建远程文件夹失败，跳过 %s ：%s" % (dirpath, exc))
                        dirnames[:] = []
                        continue
                parent_cid = cid_map[dirpath]
                for name in filenames:
                    fp = os.path.join(dirpath, name)
                    if os.path.isfile(fp):
                        files.append((fp, parent_cid))
        elif os.path.isfile(path):
            files.append((path, root_cid))
        else:
            log("跳过非常规文件 %s" % path)
    uniq = []
    seen = set()
    for path, cid in files:
        if path in seen:
            continue
        seen.add(path)
        uniq.append((path, cid))
    return uniq


def script_dir():
    return os.path.dirname(os.path.abspath(__file__))


def ensure_config(path):
    if os.path.isfile(path):
        return False
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(default_config(), f, ensure_ascii=False, indent=4)
        f.write("\n")
    return True


def load_config(path):
    cfg = default_config()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeError("设置文件不是 json 对象")
    cfg.update(data)
    cfg["cid"] = parse_target(cfg.get("cid"))
    cfg["httpRetry"] = int(cfg.get("httpRetry") or 0)
    cfg["partsNum"] = int(cfg.get("partsNum") or 0)
    return cfg


def build_parser():
    parser = argparse.ArgumentParser(
        prog="fake115uploader.py",
        formatter_class=argparse.RawTextHelpFormatter,
        description="模拟 115 客户端上传（Python 单文件版）",
        epilog=(
            "示例:\n"
            "  python fake115uploader.py -f \"*.mp4\" \"123*\"\n"
            "  python fake115uploader.py -u -j 4 \"0.ZIP\" \"1.ZIP\"\n"
            "  python fake115uploader.py -m --recursive -j 3 /data/videos\n"
            "  python fake115uploader.py -m -c 123456 --parts-num 2000 huge.iso\n"
            "  python fake115uploader.py -m -j 3 --max 5 \"/content/*.txt\" \"/content/*.jpg\"\n"
            "  python fake115uploader.py -m --prefix 2024_ \"/content/*.jpg\"\n"
            "  python fake115uploader.py -m -c /Photos/2024 \"/content/*.jpg\"\n"
            "\n"
            "通配符请加引号，否则会被 shell 提前展开。\n"
            "-j 是同时上传的文件数。单个文件的分片必须按顺序传，不能并发。\n"
            "--max N 对每个通配符参数分别限量，默认按最新修改时间选取，可用 --max-order 改成 size / name。\n"
            "网速「实时」是最近 1 秒内实际上传的速度，不是从开始算的平均速度。"
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("-f", action="store_true", help="秒传模式")
    mode.add_argument("-u", action="store_true", help="先秒传，失败后普通上传（不支持超过 5GB）")
    mode.add_argument("-m", action="store_true", help="先秒传，失败后断点续传")
    parser.add_argument("-l", default="", metavar="文件", help="设置文件，默认是脚本目录下的 fake115uploader.json")
    parser.add_argument("-d", default="", metavar="文件夹", help="断点续传存档目录，默认是脚本目录")
    parser.add_argument("-k", default="", metavar="Cookie", help="115 网页 Cookie")
    parser.add_argument("-c", default=None, metavar="cid或路径",
                        help="目标文件夹：纯数字是 cid，其余按 115 网盘路径处理（如 /Photos/2024，不存在会创建）；\n"
                             "默认取配置文件，否则 0（根目录）。名字是纯数字的文件夹请写成 /2024")
    parser.add_argument("--no-create", dest="no_create", action="store_true",
                        help="-c 给的路径在网盘里不存在时直接报错，不自动创建")
    parser.add_argument("-r", default="", metavar="文件夹", help="把上传结果写到这个目录")
    parser.add_argument("-n", action="store_true", help="不读取设置文件，必须同时用 -k")
    parser.add_argument("-a", action="store_true", help="走阿里云内网（在对应地域的阿里云机器上使用）")
    parser.add_argument("-e", action="store_true", help="上传成功后删除本地文件")
    parser.add_argument("-http-proxy", "--http-proxy", dest="http_proxy", default="", metavar="代理", help="115 API 代理，如 http://127.0.0.1:7890")
    parser.add_argument("-oss-proxy", "--oss-proxy", dest="oss_proxy", default="", metavar="代理", help="OSS 上传代理")
    parser.add_argument("-http-retry", "--http-retry", dest="http_retry", type=int, default=None, metavar="次数", help="HTTP 失败重试次数，默认 0")
    parser.add_argument("-recursive", "--recursive", dest="recursive", action="store_true", help="递归上传文件夹，并在网盘创建同名目录")
    parser.add_argument("-parts-num", "--parts-num", dest="parts_num", type=int, default=None, metavar="数量", help="断点续传分片数，1 到 10000，仅 -m")
    parser.add_argument("-j", "--jobs", type=int, default=3, metavar="N", help="并发上传数量，默认 3")
    parser.add_argument("--max", dest="max_per", type=int, default=0, metavar="N",
                        help="每个通配符参数最多取 N 个文件（只取文件，不进文件夹，选取顺序见 --max-order），0 为不限制")
    parser.add_argument("--max-order", dest="max_order", choices=("mtime", "size", "name"),
                        default="mtime",
                        help="配合 --max 选文件的顺序：mtime=最新修改优先（默认），size=最大优先，name=文件名升序")
    parser.add_argument("--prefix", default="", metavar="前缀",
                        help="给上传到 115 的文件名加前缀，只改网盘上的名字，本地文件不动；不影响文件夹名")
    parser.add_argument("-v", action="store_true", help="打印调试信息")
    parser.add_argument("--self-test", action="store_true", help="运行不联网的自检")
    parser.add_argument("files", nargs="*", help="文件、文件夹或通配符")
    return parser


def print_result(config, result):
    if not result["success"] and not result["failed"] and not result["saved"]:
        log("本次没有上传文件")
        return
    result_dir = config.get("resultDir") or ""
    if result_dir:
        os.makedirs(result_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        path = os.path.join(result_dir, stamp + " result.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        log("上传结果已写入 %s" % path)
    if result.get("notes"):
        print("详细信息：")
        for line in result["notes"]:
            print(line)
    print("上传成功（%d）：" % len(result["success"]))
    for item in result["success"]:
        print(item)
    print("上传失败（%d）：" % len(result["failed"]))
    for item in result["failed"]:
        print("  文件：%s ，cid：%s ，%s" % (item.get("path"), item.get("cid"), item.get("error") or ""))
    print("已保存进度（%d）：" % len(result["saved"]))
    for item in result["saved"]:
        print(item)


def install_signal():
    def handle(signum, frame):
        if STOP.is_set():
            raise SystemExit(130)
        STOP.set()
        log("收到中断，正在停止。再次 Ctrl+C 立即退出。断点续传会保存已完成分片。")
    signal.signal(signal.SIGINT, handle)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle)


def run_upload(args):
    if not load_deps():
        sys.exit("缺少依赖（%s）。请执行: pip install requests cryptography lz4" % DEPS_ERR)
    base = script_dir()
    config_path = args.l or os.path.join(base, "fake115uploader.json")
    if not args.d:
        args.d = base
    created = False
    if args.n:
        config = default_config()
    else:
        created = ensure_config(config_path)
        config = load_config(config_path)
        if created:
            log("已生成设置文件 %s" % config_path)
    if args.k:
        config["cookies"] = args.k
    if args.c is not None:
        config["cid"] = parse_target(args.c)
    if args.r:
        config["resultDir"] = args.r
    if args.http_retry is not None:
        config["httpRetry"] = int(args.http_retry)
    if args.parts_num is not None:
        config["partsNum"] = int(args.parts_num)
    http_proxy = (args.http_proxy or config.get("httpProxy") or "").strip()
    oss_proxy = (args.oss_proxy or config.get("ossProxy") or os.environ.get("http_proxy")
                 or os.environ.get("https_proxy") or "").strip()
    config["_http_proxy"] = http_proxy
    config["_oss_proxy"] = oss_proxy
    if not (args.f or args.u or args.m):
        if created and not args.files:
            log("请把 115 网页 Cookie 填进设置文件的 cookies，或用 -k 传入。")
        build_parser().print_help()
        sys.exit(1)
    if not args.files:
        log("请在参数最后指定文件、文件夹或通配符")
        sys.exit(1)
    if not config.get("cookies"):
        log("cookies 为空。请编辑 %s 或使用 -k" % config_path)
        sys.exit(1)
    if config["partsNum"] and not args.m:
        log("-parts-num 只能和 -m 一起用")
        sys.exit(1)
    if not (0 <= int(config["partsNum"]) <= MAX_PARTS):
        log("分片数量必须在 0 到 %d 之间" % MAX_PARTS)
        sys.exit(1)
    if args.jobs < 1:
        log("-j 至少为 1")
        sys.exit(1)
    if args.max_per < 0:
        log("--max 不能小于 0")
        sys.exit(1)
    if args.prefix and (any(c in args.prefix for c in "/\\") or any(ord(c) < 32 for c in args.prefix)):
        log("--prefix 不能包含 / \\ 或控制字符")
        sys.exit(1)
    if config.get("resultDir"):
        if not os.path.isdir(config["resultDir"]):
            log("结果目录不存在：%s" % config["resultDir"])
            sys.exit(1)
    os.makedirs(args.d, exist_ok=True)
    paths, missing = expand_inputs(args.files, args.max_per, args.max_order)
    for pattern in missing:
        if glob.has_magic(pattern) or not os.path.exists(pattern):
            log("没有匹配到：%s" % pattern)
    mode_name = {"f": "秒传", "u": "普通", "m": "断点续传"}["m" if args.m else ("u" if args.u else "f")]
    global GLOBAL_UI
    GLOBAL_UI = ProgressUI(args.jobs, mode_name)
    install_signal()
    api = Api115(config["cookies"], config["httpRetry"], http_proxy, args.v)
    try:
        api.login()
    except Exception as exc:
        log("登录失败：%s" % exc)
        sys.exit(1)
    if isinstance(config["cid"], str):
        target = config["cid"]
        try:
            config["cid"] = api.resolve_path(target, create=not args.no_create)
        except Exception as exc:
            log("解析目标文件夹 %s 失败：%s" % (target, exc))
            sys.exit(1)
        log("目标文件夹 %s → cid=%d" % (target, config["cid"]))
    if args.u or args.m:
        api.order(config["cid"])
    try:
        pairs = collect_files(paths, args.recursive, int(config["cid"]), api)
    except Exception as exc:
        log("整理文件列表失败：%s" % exc)
        sys.exit(1)
    if not pairs:
        log("没有可上传的文件")
        sys.exit(1)
    log("共 %d 个文件，并发 %d" % (len(pairs), args.jobs))
    app = App(args, config, api)
    tasks = []
    for path, cid in pairs:
        try:
            size = os.path.getsize(path)
        except OSError as exc:
            log("无法读取 %s ：%s" % (path, exc))
            app.record("failed", path, cid, str(exc))
            continue
        prog = FileProgress(path, size, cid)
        GLOBAL_UI.add_file(prog)
        tasks.append((path, cid, prog))
    GLOBAL_UI.start()
    file_pool = ThreadPoolExecutor(max_workers=args.jobs, thread_name_prefix="file")
    try:
        futures = [file_pool.submit(app.upload_file, task) for task in tasks]
        for fut in as_completed(futures):
            fut.result()
    except KeyboardInterrupt:
        STOP.set()
    finally:
        file_pool.shutdown(wait=True, cancel_futures=True)
        app.put_pool.shutdown(wait=True, cancel_futures=True)
        GLOBAL_UI.stop()
    print_result(config, app.result)
    if app.result["failed"]:
        sys.exit(1)


def run_self_tests():
    if not load_deps():
        sys.exit("自检需要依赖: pip install requests cryptography lz4 （%s）" % DEPS_ERR)
    cipher = EcdhCipher()
    assert len(cipher.pub) == 30, len(cipher.pub)
    assert len(cipher.key) == 16 and len(cipher.iv) == 16
    token = cipher.encode_token(1_700_000_000)
    raw = base64.b64decode(token)
    assert len(raw) == 48, len(raw)
    blob = cipher.encrypt(b"a=1&b=2")
    assert len(blob) % 16 == 0 and len(blob) >= 16
    # PKCS7 全块填充
    assert len(cipher.encrypt(b"")) == 16
    parts = plan_parts(2500 * 1024, 0)
    assert sum(p["size"] for p in parts) == 2500 * 1024
    assert parts[0]["size"] >= OSS_MIN_PART or len(parts) == 1
    big = plan_parts(10 * GB + 10, 1)
    assert all(p["size"] <= OSS_MAX_PART for p in big)
    assert sum(p["size"] for p in big) == 10 * GB + 10
    sts = oss_string_to_sign(
        "PUT", "bucket", "object",
        {"Date": "DATE", "Content-Type": "application/octet-stream", "x-oss-security-token": "TOK"},
        {"partNumber": "2", "uploadId": "UP"},
    )
    assert sts.split("\n")[0] == "PUT"
    assert "x-oss-security-token:TOK" in sts
    assert sts.endswith("/bucket/object?partNumber=2&uploadId=UP"), sts
    empty = oss_string_to_sign("POST", "b", "k", {"Date": "D"}, {"uploads": ""})
    assert empty.endswith("/b/k?uploads"), empty
    # 实时速度：只看最近 1 秒里这些字节真实花了多久，30 秒前的大块不能把速度拉低
    samples = deque()
    now = 1000.0
    samples.append((now - 30, 100 * 1024 * 1024))
    samples.append((now - 0.2, 2 * 1024 * 1024))
    rate = window_rate(samples, now, 1.0)
    assert rate == 2 * 1024 * 1024 / 0.25, rate
    samples.append((now - 0.8, 1024 * 1024))
    rate = window_rate(samples, now, 1.0)
    assert abs(rate - (3 * 1024 * 1024) / 0.8) < 1, rate
    # 通配符
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "123abc.mp4"), "wb").close()
        open(os.path.join(tmp, "note.txt"), "wb").close()
        open(os.path.join(tmp, "0.ZIP"), "wb").close()
        os.makedirs(os.path.join(tmp, "sub"))
        found, missing = expand_inputs([
            os.path.join(tmp, "*.mp4"),
            os.path.join(tmp, "123*"),
            os.path.join(tmp, "0.ZIP"),
            os.path.join(tmp, "*.nope"),
        ])
        names = sorted(os.path.basename(p) for p in found if os.path.basename(p) != "sub")
        assert "123abc.mp4" in names and "0.ZIP" in names and "note.txt" not in names
        assert missing and missing[0].endswith("*.nope")
        cp = checkpoint_path(tmp, os.path.join(tmp, "0.ZIP"))
        atomic_write_json(cp, {"upload_id": "x", "done": []})
        assert load_json(cp)["upload_id"] == "x"
    # --max / --max-order：每个通配符各取 N 个，只取文件，不进文件夹
    with tempfile.TemporaryDirectory() as tmp2:
        for i in range(4):
            for ext in ("jpg", "txt"):
                p = os.path.join(tmp2, "p%d.%s" % (i, ext))
                with open(p, "wb") as f:
                    f.write(b"x" * (i + 1) * (10 if ext == "jpg" else 1))
                stamp = 1_000_000 + i * 100  # p3 最新
                os.utime(p, (stamp, stamp))
        os.makedirs(os.path.join(tmp2, "dir.jpg"))  # 名字匹配 *.jpg 的文件夹，不能占名额
        os.utime(os.path.join(tmp2, "dir.jpg"), (2_000_000, 2_000_000))
        pats = [os.path.join(tmp2, "*.jpg"), os.path.join(tmp2, "*.txt")]
        found, _ = expand_inputs(pats, 2)  # 默认 mtime
        names = [os.path.basename(p) for p in found]
        assert names == ["p3.jpg", "p2.jpg", "p3.txt", "p2.txt"], names
        found, _ = expand_inputs(pats, 2, "name")
        names = [os.path.basename(p) for p in found]
        assert names == ["p0.jpg", "p1.jpg", "p0.txt", "p1.txt"], names
        found, _ = expand_inputs(pats, 2, "size")
        names = [os.path.basename(p) for p in found]
        assert names == ["p3.jpg", "p2.jpg", "p3.txt", "p2.txt"], names
        assert not any(os.path.basename(p) == "dir.jpg" for p in found)
        # 不设 --max 时保持旧行为：全部匹配，目录也保留
        found, _ = expand_inputs([os.path.join(tmp2, "*.jpg")])
        assert len(found) == 5, found
        # 两个通配符重叠：重叠文件只算在先出现的参数里
        found, _ = expand_inputs([os.path.join(tmp2, "p3.*"), os.path.join(tmp2, "*.txt")], 2)
        names = [os.path.basename(p) for p in found]
        assert names[:2] == ["p3.jpg", "p3.txt"] or names[:2] == ["p3.txt", "p3.jpg"], names
        assert len(names) == 4 and len(set(names)) == 4, names
    # --prefix：发给 115 的 filename 带前缀，本地文件名不变
    with tempfile.TemporaryDirectory() as tmp3:
        fp = os.path.join(tmp3, "x.bin")
        with open(fp, "wb") as f:
            f.write(b"hello")
        api = Api115("c=1", 0, "", False)
        seen = {}

        def fake_init(cipher, filename, size, sha1, sign_key, sign_val, cid):
            seen["name"] = filename
            return {"status": 2, "statuscode": 0}

        api.upload_sha1 = fake_init
        kind, payload = api.fast_or_token(None, fp, 0, None, "pre_" + os.path.basename(fp))
        assert kind == "fast" and seen["name"] == "pre_x.bin" and payload["_name"] == "pre_x.bin"
        kind, payload = api.fast_or_token(None, fp, 0, None)
        assert seen["name"] == "x.bin" and payload["_name"] == "x.bin"
        assert os.path.isfile(fp)
    # -c 路径：parse_target 与逐级解析
    assert parse_target(None) == 0 and parse_target("") == 0 and parse_target("/") == 0
    assert parse_target("123") == 123 and parse_target(456) == 456 and parse_target("2024") == 2024
    assert parse_target("/a/b/") == "/a/b" and parse_target("a\\b") == "/a/b" and parse_target("//a//b") == "/a/b"
    api = Api115("c=1", 0, "", False)
    tree = {(0, "a"): 11, (11, "b"): 22}
    made = []

    def fake_create(pid, name):
        cid = 100 + len(made)
        made.append((pid, name))
        tree[(pid, name)] = cid
        return cid

    api.find_dir = lambda pid, name: tree.get((pid, name))
    api.create_dir = fake_create
    assert api.resolve_path("/a/b") == 22 and not made
    assert api.resolve_path("/a/c/d") == 101 and made == [(11, "c"), (100, "d")], made
    assert api.resolve_path("/") == 0
    made.clear()
    try:
        api.resolve_path("/a/zzz", create=False)
        raise AssertionError("应该报错")
    except RuntimeError:
        pass
    assert not made
    parser = build_parser()
    ns = parser.parse_args(["-m", "-j", "4", "-c", "0", "-http-proxy", "http://127.0.0.1:1", "-recursive", "a.zip"])
    assert ns.m and ns.jobs == 4 and ns.c == "0" and ns.http_proxy.startswith("http") and ns.recursive
    assert ns.max_per == 0 and ns.max_order == "mtime"
    ns = parser.parse_args(["-m", "--max", "5", "--max-order", "size", "a.zip"])
    assert ns.max_per == 5 and ns.max_order == "size"
    ns = parser.parse_args(["-m", "-c", "/Photos/2024", "--no-create", "x.zip"])
    assert ns.c == "/Photos/2024" and ns.no_create
    assert parser.parse_args(["-m", "x.zip"]).c is None
    ns = parser.parse_args(["-m", "--prefix", "a_", "x.zip"])
    assert ns.prefix == "a_" and parser.parse_args(["-m", "x.zip"]).prefix == ""
    reader = LimitedReader(open(os.devnull, "rb"), 0, None)
    assert reader.read() == b""
    print("self-test ok")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        run_self_tests()
        return
    if not args.files and not (args.f or args.u or args.m) and not args.n:
        # 首次运行生成配置，和原版一样先落一个 json
        path = args.l or os.path.join(script_dir(), "fake115uploader.json")
        if not os.path.isfile(path):
            ensure_config(path)
            print("已生成设置文件 %s" % path, file=sys.stderr)
            print("请把网页版 115 的 Cookie 填进 cookies，或运行时用 -k 传入。", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    run_upload(args)


if __name__ == "__main__":
    main()
