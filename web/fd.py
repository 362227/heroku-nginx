#!/usr/bin/env python3
"""fast-down Python 版。多线程下载，参数贴近 aria2c。

示例:
  fd -x16 -d "保存目录" --user-agent="Mozilla/5.0 ..." --referer="https://example.com/" URL
  fd -c -x16 -d "VIDEO_TS" URL
  fd -c URL1 URL2
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import json
import os
import queue
import re
import shutil
import socket
import ssl
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from http.client import HTTPConnection, HTTPSConnection, HTTPException
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

VERSION = "2.8.0"
CTRL_SUFFIX = ".fdctrl"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"
)
BLOCK_CHARS = " ▏▎▍▌▋▊▉█"
IO_LOCK = threading.Lock()
# 这些状态码只代表"这条连接暂时不行", 不应该让整个下载失败
RETRY_STATUS = (403, 429, 500, 502, 503, 504)

ZH = {
    "url-info": "文件名称: {name}\n文件大小: {size} ({size_in_bytes} 字节)\n文件路径: {path}\n并行数量: {concurrent}",
    "etag": "ETag: {etag}",
    "last-modified": "最后修改时间: {last_modified}",
    "resume": "未完成的下载, 继续下载...",
    "progress-line": "已下载 {completed} / {total} ({percentage}%)",
    "already": "文件已下载完成, 跳过",
    "output": "输出路径: {path}",
    "overwrite": "文件已经存在, 是否覆盖?",
    "size-mismatch": "记录的文件大小: {saved}\n远端的文件大小: {new}\n大小不匹配, 是否继续?",
    "etag-mismatch": "记录的 ETag: {saved}\n远端的 ETag: {new}\nETag 不匹配, 无法保证文件完整性, 是否继续?",
    "weak-etag": "弱 ETag: {etag}, 无法保证文件完整性, 是否继续?",
    "no-etag": "服务端未提供 ETag, 无法保证文件完整性, 是否继续?",
    "lm-mismatch": "记录的最后修改时间: {saved}\n远端的最后修改时间: {new}\n最后修改时间不匹配, 是否继续?",
    "no-space": "剩余空间不足, 下载此文件还需要 {size}",
    "cancel": "下载取消",
    "fail": "下载失败: {url}",
    "reason": "原因: {err}",
    "keep": "未完成的文件已保留, 加 -c 可续传: {path}",
    "meta-fail": "获取元数据失败: {err}",
    "header-bad": "请求头格式错误: {raw}",
    "bad-out": "-o/--out 只能在单个 URL 时使用",
    "bigger": "本地文件比远端更大, 拒绝续传 (可用 -f 覆盖)",
    "bar-desc": "已用时间: {spent} | 速度: {speed}/s | 剩余时间: {left}",
    "noninteractive-no": "非交互环境, 已取消",
    "list-empty": "(没有未完成的下载)",
    "available-ips": "绑定的 IP 地址: {ips}",
    "throttled": "服务器限制并发: {n} 个连接被拒绝(403/限流)后退出, 实际并发约 {m}",
    "persist-denied": "持续被服务器拒绝 (HTTP {status})",
    "unknown-opt": "不支持的参数, 已忽略: {opt}",
}

EN = {
    "url-info": "File Name: {name}\nFile Size: {size} ({size_in_bytes} bytes)\nFile Path: {path}\nConcurrent: {concurrent}",
    "etag": "ETag: {etag}",
    "last-modified": "Last-Modified: {last_modified}",
    "resume": "Incomplete download. Resuming...",
    "progress-line": "Downloaded {completed} / {total} ({percentage}%)",
    "already": "Download already complete, skipping",
    "output": "Output path: {path}",
    "overwrite": "File already exists, overwrite?",
    "size-mismatch": "Original File Size: {saved}\nReceived File Size: {new}\nSize mismatch, continue?",
    "etag-mismatch": "Original ETag: {saved}\nReceived ETag: {new}\nETag mismatch, file integrity cannot be guaranteed. Continue?",
    "weak-etag": "Weak ETag: {etag}, file integrity cannot be guaranteed. Continue?",
    "no-etag": "Server doesn't provide an ETag, file integrity cannot be guaranteed. Continue?",
    "lm-mismatch": "Original Last-Modified: {saved}\nReceived Last-Modified: {new}\nLast-Modified mismatch, continue?",
    "no-space": "Not enough disk space, need another {size}",
    "cancel": "Cancelling...",
    "fail": "Download failed: {url}",
    "reason": "Reason: {err}",
    "keep": "Partial file kept. Resume with -c: {path}",
    "meta-fail": "Failed to fetch metadata: {err}",
    "header-bad": "Bad header: {raw}",
    "bad-out": "-o/--out requires exactly one URL",
    "bigger": "Local file is larger than the remote file (use -f to overwrite)",
    "bar-desc": "Time Elapsed: {spent} | Speed: {speed}/s | Time Left: {left}",
    "noninteractive-no": "Non-interactive, cancelled",
    "list-empty": "(no incomplete downloads)",
    "available-ips": "Bound IP addresses: {ips}",
    "throttled": "Server limits concurrency: {n} connection(s) were refused (403/throttle) and retired, effective concurrency ~{m}",
    "persist-denied": "Persistently refused by server (HTTP {status})",
    "unknown-opt": "Unsupported option, ignored: {opt}",
}


def use_zh() -> bool:
    forced = os.environ.get("FD_LANG", "").lower()
    if forced.startswith("zh"):
        return True
    if forced.startswith("en"):
        return False
    loc = (
        os.environ.get("LC_ALL")
        or os.environ.get("LC_MESSAGES")
        or os.environ.get("LANG")
        or ""
    ).lower()
    if loc.startswith("zh"):
        return True
    if loc.startswith("en"):
        return False
    return True


def t(key: str, **kwargs: object) -> str:
    table = ZH if use_zh() else EN
    return table[key].format(**kwargs)


def eprint(*parts: object) -> None:
    with IO_LOCK:
        print(*parts, file=sys.stderr, flush=True)


def format_size(size: float) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    unit = 0
    while size >= 1024.0 and unit < len(units) - 1:
        size /= 1024.0
        unit += 1
    return f"{size:.2f} {units[unit]}"


def format_speed_cell(speed: float | None) -> str:
    if speed is None:
        text = "n/a"
    else:
        units = ["B", "KiB", "MiB", "GiB", "TiB"]
        unit = 0
        value = float(speed)
        while value >= 1024.0 and unit < len(units) - 1:
            value /= 1024.0
            unit += 1
        number = f"{value:.0f}" if value >= 100 or unit == 0 else f"{value:.1f}"
        text = f"{number}{units[unit]}/s"
    return f"{text:>11}"


def format_time(seconds: float | None) -> str:
    if seconds is None or seconds < 0 or seconds == float("inf"):
        return "Unknown" if not use_zh() else "未知"
    sec = int(seconds)
    if sec < 86400:
        return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"
    days, rem = divmod(sec, 86400)
    return f"{days}d {rem // 3600:02d}:{(rem % 3600) // 60:02d}:{rem % 60:02d}"


def sanitize(filename: str) -> str:
    name = filename.replace("\\", "/").split("/")[-1]
    name = unquote(name)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    if name in ("", ".", ".."):
        name = "download"
    raw = name.encode("utf-8", "replace")
    if len(raw) <= 255:
        return name
    ext = ""
    if "." in name and len(name.rsplit(".", 1)[-1].encode()) <= 16:
        base, ext = name.rsplit(".", 1)
        ext = "." + ext
    else:
        base = name
    budget = 255 - len(ext.encode())
    encoded = base.encode()
    cut = encoded[: max(budget, 1)]
    while cut and (cut[-1] & 0xC0) == 0x80:
        cut = cut[:-1]
    return cut.decode(errors="ignore") + ext


def safe_filename(directory: str, filename: str) -> str:
    parts = []
    for part in filename.replace("\\", "/").split("/"):
        if part in ("", ".", ".."):
            continue
        parts.append(sanitize(part))
    if not parts:
        parts = ["download"]
    return os.path.join(directory, *parts)


def filename_from_cd(cd: str | None) -> str | None:
    if not cd:
        return None
    match = re.search(r"filename\*\s*=\s*([^']*)''([^;]+)", cd, re.I)
    if match:
        return sanitize(unquote(match.group(2).strip().strip('"')))
    match = re.search(r'filename\s*=\s*"([^"]+)"', cd, re.I)
    if match:
        return sanitize(match.group(1))
    match = re.search(r"filename\s*=\s*([^;]+)", cd, re.I)
    if match:
        return sanitize(match.group(1).strip().strip('"'))
    return None


def filename_from_url(url: str) -> str:
    path = unquote(urlsplit(url).path)
    base = os.path.basename(path.rstrip("/"))
    return sanitize(base) if base else "index.html"


def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    items = sorted((s, e) for s, e in ranges if e > s)
    if not items:
        return []
    out = [items[0]]
    for start, end in items[1:]:
        ps, pe = out[-1]
        if start <= pe:
            out[-1] = (ps, max(pe, end))
        else:
            out.append((start, end))
    return out


def add_range(ranges: list[tuple[int, int]], start: int, end: int) -> list[tuple[int, int]]:
    if end <= start:
        return ranges
    return merge_ranges([*ranges, (start, end)])


def covered(ranges: list[tuple[int, int]]) -> int:
    return sum(end - start for start, end in merge_ranges(ranges))


def missing_ranges(done: list[tuple[int, int]], total: int) -> list[tuple[int, int]]:
    cur = 0
    out: list[tuple[int, int]] = []
    for start, end in merge_ranges(done):
        if start > cur:
            out.append((cur, start))
        cur = max(cur, end)
    if cur < total:
        out.append((cur, total))
    return out


def split_ranges(
    ranges: list[tuple[int, int]],
    connections: int,
    min_chunk: int,
    max_chunk: int = 0,
) -> list[tuple[int, int]]:
    """把待下载区间切成分片。分片有上限, 方便空闲连接接手被退回的分片。"""
    total = sum(end - start for start, end in ranges)
    if total <= 0:
        return []
    connections = max(1, connections)
    if min_chunk > 0:
        connections = max(1, min(connections, max(1, total // min_chunk)))
    piece = max(1, (total + connections - 1) // connections)
    if max_chunk > 0:
        piece = min(piece, max(max_chunk, min_chunk, 1))
    out: list[tuple[int, int]] = []
    for start, end in ranges:
        cursor = start
        while cursor < end:
            take = min(piece, end - cursor)
            out.append((cursor, cursor + take))
            cursor += take
    return out


def confirm(yes: bool, message: str, default: bool = False) -> bool:
    if yes:
        return True
    if not sys.stdin.isatty():
        eprint(message)
        eprint(t("noninteractive-no") if not default else message)
        return default
    suffix = " [Y/n] " if default else " [y/N] "
    try:
        answer = input(message + suffix).strip().lower()
    except EOFError:
        return default
    if not answer:
        return default
    return answer in ("y", "yes", "是")


def registry_path() -> str:
    base = os.environ.get("FD_STATE_DIR")
    if not base:
        base = str(Path.home() / ".local" / "share" / "fast-down")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "downloads.json")


@contextlib.contextmanager
def registry_edit():
    path = registry_path()
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        try:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX)
        except Exception:
            pass
        raw = b""
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            raw += chunk
        try:
            data = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            data = {}
        data.setdefault("version", 1)
        data.setdefault("items", {})
        yield data
        text = json.dumps(data, ensure_ascii=False, indent=2).encode()
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, text)
    finally:
        try:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_UN)
        except Exception:
            pass
        os.close(fd)


def registry_upsert(record: dict) -> None:
    try:
        with registry_edit() as data:
            data["items"][record["path"]] = record
    except Exception as exc:
        eprint(exc)


def registry_remove(path: str) -> None:
    try:
        with registry_edit() as data:
            data["items"].pop(path, None)
    except Exception as exc:
        eprint(exc)


class HttpFailure(Exception):
    def __init__(self, status: int, reason: str, url: str):
        self.status = status
        self.reason = reason
        super().__init__(f"HTTP {status} {reason}".strip())
        self.url = url


class FatalError(Exception):
    pass


class PieceRetry(Exception):
    """某个分片这次没拿下来 (403/限流/网络错误), 需要放回队列让别的连接接手。"""

    def __init__(self, pos: int, status: int, msg: str):
        super().__init__(msg)
        self.pos = pos
        self.status = status


@dataclass
class Response:
    status: int
    reason: str
    headers: dict[str, str]
    header_list: list[tuple[str, str]]
    final_url: str
    _resp: object
    _conn: object

    def read(self, n: int) -> bytes:
        return self._resp.read(n)  # type: ignore[attr-defined]

    def close(self) -> None:
        try:
            self._resp.close()  # type: ignore[attr-defined]
        finally:
            try:
                self._conn.close()  # type: ignore[attr-defined]
            except Exception:
                pass

    def __enter__(self) -> Response:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def get(self, name: str, default: str | None = None) -> str | None:
        return self.headers.get(name.lower(), default)

    def get_all(self, name: str) -> list[str]:
        key = name.lower()
        return [v for k, v in self.header_list if k == key]


@dataclass
class Meta:
    url: str
    size: int | None
    etag: str | None
    last_modified: str | None
    filename: str | None
    accept_ranges: bool | None


def _header_map(msg: object) -> tuple[dict[str, str], list[tuple[str, str]]]:
    items: list[tuple[str, str]] = []
    folded: dict[str, str] = {}
    for key, value in msg.items():  # type: ignore[attr-defined]
        items.append((key.lower(), value))
        folded[key.lower()] = value
    return folded, items


def _read_status_line(sock: socket.socket) -> tuple[int, list[bytes]]:
    buff = b""
    while b"\r\n\r\n" not in buff and len(buff) < 65536:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buff += chunk
    head, _, rest = buff.partition(b"\r\n\r\n")
    lines = head.split(b"\r\n")
    if not lines or not lines[0].startswith(b"HTTP/"):
        raise HTTPException(f"bad proxy response: {lines[:1]!r}")
    parts = lines[0].split()
    code = int(parts[1]) if len(parts) > 1 else 0
    if rest:
        return code, [rest]
    return code, []


def _open_connection(
    url: str,
    timeout: float,
    ssl_ctx: ssl.SSLContext,
    proxy: str | None,
    source_ip: str | None,
) -> tuple[HTTPConnection, str, bool]:
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https"):
        raise FatalError(f"unsupported URL scheme: {parsed.scheme or url}")
    host = parsed.hostname
    if not host:
        raise FatalError(f"invalid URL: {url}")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    source = (source_ip, 0) if source_ip else None
    absolute = False
    if proxy:
        pu = urlsplit(proxy if "://" in proxy else "http://" + proxy)
        if pu.scheme in ("socks5", "socks5h", "socks4", "socks4a"):
            raise FatalError("SOCKS proxy needs PySocks; HTTP proxy is supported directly")
        ph, pp = pu.hostname, pu.port or 8080
        if not ph:
            raise FatalError(f"invalid proxy: {proxy}")
        if parsed.scheme == "https":
            sock = socket.create_connection((ph, pp), timeout=timeout, source_address=source)
            token = ""
            if pu.username:
                user = unquote(pu.username)
                password = unquote(pu.password or "")
                basic = base64.b64encode(f"{user}:{password}".encode()).decode()
                token = f"Proxy-Authorization: Basic {basic}\r\n"
            target = f"{host}:{port}"
            sock.sendall(
                f"CONNECT {target} HTTP/1.1\r\nHost: {target}\r\n{token}\r\n".encode()
            )
            code, leftover = _read_status_line(sock)
            if code != 200:
                sock.close()
                raise FatalError(f"proxy CONNECT failed: HTTP {code}")
            if leftover and leftover[0]:
                sock.close()
                raise FatalError("proxy CONNECT returned unexpected body")
            ssock = ssl_ctx.wrap_socket(sock, server_hostname=host)
            conn: HTTPConnection = HTTPSConnection(host, port, timeout=timeout, context=ssl_ctx)
            conn.sock = ssock
            return conn, url, False
        conn = HTTPConnection(ph, pp, timeout=timeout, source_address=source)
        conn.connect()
        absolute = True
        return conn, url, absolute
    if parsed.scheme == "https":
        conn = HTTPSConnection(
            host, port, timeout=timeout, context=ssl_ctx, source_address=source
        )
    else:
        conn = HTTPConnection(host, port, timeout=timeout, source_address=source)
    conn.connect()
    return conn, url, absolute


def resolve_proxy(explicit: str | None, scheme: str, host: str) -> str | None:
    no_proxy = os.environ.get("NO_PROXY") or os.environ.get("no_proxy") or ""
    if explicit == "":
        return None
    if explicit:
        return explicit
    names = [h.strip() for h in no_proxy.split(",") if h.strip()]
    if host in names or host in ("localhost", "127.0.0.1", "::1"):
        return None
    if scheme == "https":
        return (
            os.environ.get("https_proxy")
            or os.environ.get("HTTPS_PROXY")
            or os.environ.get("all_proxy")
            or os.environ.get("ALL_PROXY")
            or os.environ.get("http_proxy")
            or os.environ.get("HTTP_PROXY")
        )
    return (
        os.environ.get("http_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("all_proxy")
        or os.environ.get("ALL_PROXY")
    )


class CookieJar:
    def __init__(self) -> None:
        self._jars: dict[str, dict[str, str]] = {}
        self._lock = threading.Lock()

    def header_for(self, host: str) -> str | None:
        with self._lock:
            data = self._jars.get(host) or {}
            if not data:
                return None
            return "; ".join(f"{k}={v}" for k, v in data.items())

    def absorb(self, host: str, values: list[str]) -> None:
        if not values:
            return
        with self._lock:
            jar = self._jars.setdefault(host, {})
            for raw in values:
                pair = raw.split(";", 1)[0]
                if "=" not in pair:
                    continue
                name, value = pair.split("=", 1)
                name = name.strip()
                if name:
                    jar[name] = value.strip()


def http_request(
    method: str,
    url: str,
    headers: dict[str, str],
    timeout: float,
    ssl_ctx: ssl.SSLContext,
    proxy: str | None,
    source_ip: str | None,
    max_redirects: int,
    cookies: CookieJar | None,
) -> Response:
    current = url
    verb = method
    for _ in range(max_redirects + 1):
        parsed = urlsplit(current)
        host = parsed.hostname or ""
        send = dict(headers)
        if cookies is not None and "cookie" not in {k.lower() for k in send}:
            cookie = cookies.header_for(host)
            if cookie:
                send["Cookie"] = cookie
        conn, full, absolute = _open_connection(current, timeout, ssl_ctx, proxy, source_ip)
        path = full if absolute else (parsed.path or "/")
        if not absolute and parsed.query:
            path += "?" + parsed.query
        try:
            conn.request(verb, path, headers=send)
            resp = conn.getresponse()
        except Exception:
            conn.close()
            raise
        folded, items = _header_map(resp.headers)
        if cookies is not None:
            cookies.absorb(host, [v for k, v in items if k == "set-cookie"])
        if resp.status in (301, 302, 303, 307, 308):
            loc = folded.get("location")
            try:
                resp.read()
            except Exception:
                pass
            conn.close()
            if not loc:
                raise FatalError(f"redirect without Location from {current}")
            nxt = urljoin(current, loc)
            if resp.status == 303 and verb != "HEAD":
                verb = "GET"
            current = nxt
            continue
        return Response(resp.status, resp.reason, folded, items, current, resp, conn)
    raise FatalError(f"too many redirects: {url}")


def make_ssl(accept_certs: bool, accept_hosts: bool) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if accept_certs:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    elif accept_hosts:
        ctx.check_hostname = False
    return ctx


def parse_meta(resp: Response) -> Meta:
    size: int | None = None
    if resp.status == 206:
        cr = resp.get("content-range") or ""
        match = re.match(r"bytes (\d+)-(\d+)/(\d+|\*)", cr)
        if match and match.group(3) != "*":
            size = int(match.group(3))
    elif resp.get("content-length") and resp.get("content-length", "").isdigit():
        size = int(resp.get("content-length") or "0")
    ar = (resp.get("accept-ranges") or "").lower()
    if "none" in ar:
        ranges: bool | None = False
    elif "bytes" in ar:
        ranges = True
    else:
        ranges = None
    if resp.status == 206:
        ranges = True
    return Meta(
        url=resp.final_url,
        size=size,
        etag=resp.get("etag"),
        last_modified=resp.get("last-modified"),
        filename=filename_from_cd(resp.get("content-disposition")),
        accept_ranges=ranges,
    )


def fetch_meta(args: argparse.Namespace, url: str, headers: dict[str, str], ssl_ctx, cookies, source_ip) -> Meta:
    timeout = max(args.pull_timeout, 1) / 1000
    host = urlsplit(url).hostname or ""
    proxy = resolve_proxy(args.proxy, urlsplit(url).scheme, host)

    def attempt_head() -> Meta | None:
        for attempt in range(1, args.max_tries + 1):
            try:
                resp = http_request(
                    "HEAD",
                    url,
                    headers,
                    timeout,
                    ssl_ctx,
                    proxy,
                    source_ip,
                    args.max_redirects,
                    cookies,
                )
                with resp:
                    if args.verbose:
                        eprint(f"HEAD {resp.final_url} -> {resp.status}")
                    if resp.status in (401, 404, 410):
                        raise FatalError(str(HttpFailure(resp.status, resp.reason, resp.final_url)))
                    if resp.status >= 400:
                        return None
                    return parse_meta(resp)
            except FatalError:
                raise
            except Exception as exc:
                if attempt >= args.max_tries:
                    return None
                if args.verbose:
                    eprint(t("meta-fail", err=exc))
                time.sleep(args.retry_gap / 1000)
        return None

    meta = attempt_head()
    need_probe = meta is None or (
        meta.accept_ranges is None
        and meta.size is not None
        and args.connections > 1
        and (args.min_chunk_size <= 0 or meta.size >= args.min_chunk_size)
    ) or (meta is not None and meta.size is None)
    if meta is not None and not need_probe:
        return meta

    probe_headers = dict(headers)
    probe_headers["Range"] = "bytes=0-0"
    resp: Response | None = None
    last_err: Exception | None = None
    denied_status = 0
    for attempt in range(1, args.max_tries + 1):
        try:
            candidate = http_request(
                "GET",
                url,
                probe_headers,
                timeout,
                ssl_ctx,
                proxy,
                source_ip,
                args.max_redirects,
                cookies,
            )
        except FatalError:
            raise
        except Exception as exc:
            last_err = exc
            if attempt < args.max_tries:
                time.sleep(args.retry_gap / 1000 * attempt)
                continue
            break
        if args.verbose:
            eprint(f"GET {candidate.final_url} -> {candidate.status}")
        if candidate.status in (401, 404, 410):
            status, reason, furl = candidate.status, candidate.reason, candidate.final_url
            candidate.close()
            raise FatalError(str(HttpFailure(status, reason, furl)))
        if candidate.status in RETRY_STATUS:
            denied_status = candidate.status
            status, reason, furl = candidate.status, candidate.reason, candidate.final_url
            candidate.close()
            last_err = HttpFailure(status, reason, furl)
            if attempt < args.max_tries:
                time.sleep(args.retry_gap / 1000 * attempt)
                continue
            break
        if candidate.status >= 400 and candidate.status != 416:
            status, reason, furl = candidate.status, candidate.reason, candidate.final_url
            candidate.close()
            raise FatalError(str(HttpFailure(status, reason, furl)))
        resp = candidate
        break

    if resp is None:
        # 探测一直失败: 如果 HEAD 已经拿到了大小, 乐观地按支持 Range 继续, 由 worker 去重试
        if meta is not None:
            if meta.accept_ranges is None and meta.size is not None:
                meta.accept_ranges = True
            return meta
        raise FatalError(t("meta-fail", err=last_err or f"HTTP {denied_status}"))

    try:
        probed = parse_meta(resp)
        if resp.status in (200, 206):
            try:
                resp.read(1)
            except Exception:
                pass
        if probed.accept_ranges is None:
            probed.accept_ranges = True if resp.status == 206 else False
        if meta is not None:
            if probed.size is None:
                probed.size = meta.size
            probed.etag = probed.etag or meta.etag
            probed.last_modified = probed.last_modified or meta.last_modified
            probed.filename = probed.filename or meta.filename
            if probed.url == url:
                probed.url = meta.url
        return probed
    finally:
        resp.close()


@dataclass
class Result:
    gid: str
    kind: str  # OK, ERR, CNCL
    speed: float | None
    target: str
    error: str | None = None
    interrupted: bool = False


@dataclass
class Progress:
    ranges: list[tuple[int, int]] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def add(self, start: int, end: int) -> None:
        with self.lock:
            self.ranges = add_range(self.ranges, start, end)

    def snapshot(self) -> list[tuple[int, int]]:
        with self.lock:
            return list(merge_ranges(self.ranges))

    def total(self) -> int:
        with self.lock:
            return covered(self.ranges)


def load_control(path: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    prog = []
    for item in data.get("progress") or []:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            prog.append((int(item[0]), int(item[1])))
    data["progress"] = merge_ranges(prog)
    return data


def save_control(path: str, data: dict) -> None:
    tmp = path + ".tmp"
    payload = dict(data)
    payload["progress"] = [list(pair) for pair in payload.get("progress") or []]
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def build_headers(args: argparse.Namespace, url: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for raw in args.headers:
        if ":" not in raw:
            raise FatalError(t("header-bad", raw=raw))
        name, value = raw.split(":", 1)
        name, value = name.strip(), value.strip()
        if not name:
            raise FatalError(t("header-bad", raw=raw))
        headers[name] = value
    if args.browser:
        parsed = urlsplit(url)
        origin_host = parsed.hostname or ""
        default_port = 443 if parsed.scheme == "https" else 80
        if parsed.port and parsed.port != default_port:
            origin = f"{parsed.scheme}://{origin_host}:{parsed.port}"
        else:
            origin = f"{parsed.scheme}://{origin_host}"
        headers.setdefault("Origin", origin)
        headers.setdefault("Referer", url)
        headers.setdefault("User-Agent", BROWSER_UA)
    if args.user_agent:
        headers["User-Agent"] = args.user_agent
    if args.referer:
        headers["Referer"] = url if args.referer == "*" else args.referer
    return headers


def check_resume_identity(args: argparse.Namespace, saved: dict, meta: Meta) -> bool:
    if saved.get("file_size") not in (None, meta.size) and meta.size is not None:
        if not confirm(
            args.yes,
            t("size-mismatch", saved=saved.get("file_size"), new=meta.size),
            False,
        ):
            return False
    saved_etag = saved.get("etag")
    if saved_etag != meta.etag:
        if saved_etag is None and meta.etag is None:
            pass
        elif saved_etag is None:
            if not confirm(args.yes, t("no-etag"), False):
                return False
        elif not confirm(
            args.yes,
            t("etag-mismatch", saved=saved_etag, new=meta.etag),
            False,
        ):
            return False
    elif isinstance(saved_etag, str) and saved_etag.startswith("W/"):
        if not confirm(args.yes, t("weak-etag", etag=saved_etag), False):
            return False
    if saved.get("last_modified") != meta.last_modified and (
        saved.get("last_modified") or meta.last_modified
    ):
        if not confirm(
            args.yes,
            t(
                "lm-mismatch",
                saved=saved.get("last_modified"),
                new=meta.last_modified,
            ),
            False,
        ):
            return False
    return True


def draw_bar(
    ranges: list[tuple[int, int]],
    file_size: int,
    width: int,
    curr: int,
    start: float,
    avg_speed: float,
) -> tuple[str, str, float]:
    now = time.monotonic()
    elapsed = now - start
    if file_size <= 0:
        bar = BLOCK_CHARS[0] * width
        line1 = f"|{bar}| {0:6.2f}% ({format_size(curr):>8}/Unknown)"
        left = None
    else:
        percent = curr * 100 / file_size
        per = file_size / width
        chars = []
        merged = merge_ranges(ranges)
        index = 0
        for i in range(width):
            b0 = int(i * per)
            b1 = int((i + 1) * per)
            block = 0
            while index < len(merged) and merged[index][1] <= b0:
                index += 1
            j = index
            while j < len(merged) and merged[j][0] < b1:
                overlap = min(merged[j][1], b1) - max(merged[j][0], b0)
                if overlap > 0:
                    block += overlap
                j += 1
            level = int(round(block / per * (len(BLOCK_CHARS) - 1))) if per else 0
            level = max(0, min(len(BLOCK_CHARS) - 1, level))
            chars.append(BLOCK_CHARS[level])
        line1 = (
            f"|{''.join(chars)}| {percent:6.2f}% "
            f"({format_size(curr):>8}/{format_size(file_size)})"
        )
        left = (file_size - curr) / avg_speed if avg_speed > 1 else None
    line2 = t(
        "bar-desc",
        spent=format_time(elapsed),
        speed=f"{format_size(avg_speed):>8}",
        left=format_time(left) if file_size else ("Unknown" if not use_zh() else "未知"),
    )
    return line1, line2, elapsed


def print_summary(results: list[Result]) -> None:
    print("Download Results:")
    print("gid   |stat|avg speed  |path/URI")
    print("======+====+===========+=======================================================")
    for item in results:
        stat = {"OK": "OK  ", "ERR": "ERR ", "CNCL": "CNCL"}.get(item.kind, "ERR ")
        print(f"{item.gid}|{stat}|{format_speed_cell(item.speed)}|{item.target}")
    print()
    print("Status Legend:")
    kinds = {item.kind for item in results}
    if "OK" in kinds or not kinds:
        print("(OK):download completed.")
    if "ERR" in kinds:
        print("(ERR):error occurred.")
    if "CNCL" in kinds:
        print("(CNCL):download cancelled.")


def download_one(args: argparse.Namespace, url: str, source_cycle: list[str]) -> Result:
    gid = uuid.uuid4().hex[:6]
    try:
        return _download_one(args, url, gid, source_cycle)
    except KeyboardInterrupt:
        return Result(gid, "ERR", None, url, "interrupted", True)
    except FatalError as exc:
        eprint(t("fail", url=url))
        eprint(t("reason", err=exc))
        return Result(gid, "ERR", None, url, str(exc))
    except Exception as exc:
        eprint(t("fail", url=url))
        eprint(t("reason", err=exc))
        return Result(gid, "ERR", None, url, str(exc))


def _download_one(args: argparse.Namespace, url: str, gid: str, source_cycle: list[str]) -> Result:
    headers = build_headers(args, url)
    ssl_ctx = make_ssl(args.accept_invalid_certs, args.accept_invalid_hostnames)
    cookies = CookieJar() if args.cookie_store else None
    source_ip = source_cycle[0] if source_cycle else None
    meta = fetch_meta(args, url, headers, ssl_ctx, cookies, source_ip)
    final_url = meta.url or url
    directory = os.path.abspath(args.directory)
    os.makedirs(directory, exist_ok=True)
    if args.out:
        dest = safe_filename(directory, args.out)
        parent = os.path.dirname(dest)
        if parent:
            os.makedirs(parent, exist_ok=True)
    else:
        dest = os.path.join(directory, meta.filename or filename_from_url(final_url))
    ctrl = dest + CTRL_SUFFIX
    if meta.size and meta.accept_ranges is True:
        planned = split_ranges([(0, meta.size)], args.connections, args.min_chunk_size, args.max_chunk_size)
        threads = max(1, min(args.connections, len(planned)))
    else:
        threads = 1

    saved = load_control(ctrl)
    local_size = os.path.getsize(dest) if os.path.isfile(dest) else None
    complete = False
    if args.cont and not args.force and os.path.isfile(dest):
        if saved is None and meta.size is not None and local_size == meta.size:
            complete = True
        elif saved is not None and meta.size is not None and covered(saved["progress"]) >= meta.size:
            complete = True

    info = t(
        "url-info",
        name=os.path.basename(dest),
        size=format_size(meta.size or 0) if meta.size is not None else "Unknown",
        size_in_bytes=meta.size if meta.size is not None else "Unknown",
        path=dest,
        concurrent=threads,
    )
    eprint(info)
    if meta.etag:
        eprint(t("etag", etag=meta.etag))
    if meta.last_modified:
        eprint(t("last-modified", last_modified=meta.last_modified))

    if complete:
        if saved is not None and os.path.isfile(ctrl):
            os.remove(ctrl)
        registry_remove(dest)
        eprint(t("already"))
        eprint(t("output", path=dest))
        return Result(gid, "OK", None, dest)

    resume_from_ctrl = False
    initial: list[tuple[int, int]] = []
    elapsed_ms = 0
    if os.path.isfile(dest) and not args.force:
        if args.cont and saved is not None and meta.size is not None:
            if not check_resume_identity(args, saved, meta):
                eprint(t("cancel"))
                return Result(gid, "CNCL", None, dest)
            initial = list(saved["progress"])
            elapsed_ms = int(saved.get("elapsed_ms") or 0)
            resume_from_ctrl = True
            done = covered(initial)
            eprint(t("resume"))
            if meta.size:
                eprint(
                    t(
                        "progress-line",
                        completed=format_size(done),
                        total=format_size(meta.size),
                        percentage=done * 100 // meta.size,
                    )
                )
        elif args.cont and saved is None and meta.size is not None and local_size is not None:
            if local_size > meta.size:
                eprint(t("bigger"))
                return Result(gid, "ERR", None, dest, t("bigger"))
            if local_size > 0:
                initial = [(0, local_size)]
                resume_from_ctrl = True
                eprint(t("resume"))
                eprint(
                    t(
                        "progress-line",
                        completed=format_size(local_size),
                        total=format_size(meta.size),
                        percentage=local_size * 100 // meta.size,
                    )
                )
        elif not confirm(args.yes, t("overwrite"), False):
            eprint(t("cancel"))
            return Result(gid, "CNCL", None, dest)
        else:
            initial = []
            saved = None
    elif os.path.isfile(dest) and args.force:
        initial = []
        saved = None

    if meta.size == 0:
        open(dest, "wb").close()
        if os.path.isfile(ctrl):
            os.remove(ctrl)
        registry_remove(dest)
        eprint(t("output", path=dest))
        return Result(gid, "OK", None, dest)

    remaining = meta.size - covered(initial) if meta.size is not None else meta.size
    if remaining:
        free = shutil.disk_usage(directory).free
        if free < remaining:
            eprint(t("no-space", size=format_size(remaining - free)))
            eprint(t("cancel"))
            return Result(gid, "CNCL", None, dest)

    if source_cycle:
        eprint(t("available-ips", ips=", ".join(source_cycle)))

    fresh = not resume_from_ctrl
    fd = os.open(dest, os.O_RDWR | os.O_CREAT, 0o644)
    retired_cnt = [0]
    workers_n = 0
    try:
        if fresh:
            os.ftruncate(fd, 0)
            initial = []
        if meta.size is not None and os.fstat(fd).st_size < meta.size:
            os.ftruncate(fd, meta.size)
        progress = Progress(initial)
        stop = threading.Event()
        errors: list[BaseException] = []
        err_lock = threading.Lock()
        session_start = time.monotonic()
        display_start = session_start - elapsed_ms / 1000
        ctrl_data = {
            "url": final_url,
            "file_size": meta.size,
            "etag": meta.etag,
            "last_modified": meta.last_modified,
            "progress": progress.snapshot(),
            "elapsed_ms": elapsed_ms,
        }
        save_control(ctrl, ctrl_data)

        def persist() -> None:
            snap = progress.snapshot()
            ctrl_data["progress"] = snap
            ctrl_data["elapsed_ms"] = elapsed_ms + int((time.monotonic() - session_start) * 1000)
            save_control(ctrl, ctrl_data)
            registry_upsert(
                {
                    "path": dest,
                    "url": final_url,
                    "file_name": os.path.basename(dest),
                    "file_size": meta.size,
                    "etag": meta.etag,
                    "last_modified": meta.last_modified,
                    "progress": [list(p) for p in snap],
                    "elapsed_ms": ctrl_data["elapsed_ms"],
                }
            )

        use_multi = meta.size is not None and meta.accept_ranges is True
        if not use_multi:
            start_at = covered(initial) if resume_from_ctrl and initial else 0
            pieces = [(start_at, meta.size)]
            workers_n = 1
        else:
            holes = missing_ranges(progress.snapshot(), meta.size)
            pieces = split_ranges(holes, args.connections, args.min_chunk_size, args.max_chunk_size)
            workers_n = min(max(1, args.connections), len(pieces)) if pieces else 0

        work: queue.Queue[tuple[int, int | None]] = queue.Queue()
        for piece in pieces:
            work.put(piece)

        ip_lock = threading.Lock()
        ip_i = 0

        def next_ip() -> str | None:
            nonlocal ip_i
            if not source_cycle:
                return None
            with ip_lock:
                ip = source_cycle[ip_i % len(source_cycle)]
                ip_i += 1
                return ip

        active = set(range(1, workers_n + 1))
        active_lock = threading.Lock()
        last_limit = max(args.max_tries * 3, 10)
        retire_after = max(1, args.retire_after)

        def worker(wid: int) -> None:
            strikes = 0
            try:
                # 错开启动, 避免同一瞬间把服务端并发限制打满
                if stop.wait(0.05 * (wid - 1)):
                    return
                while not stop.is_set():
                    try:
                        start, end = work.get_nowait()
                    except queue.Empty:
                        return
                    try:
                        _fetch_piece(
                            args,
                            final_url,
                            headers,
                            ssl_ctx,
                            cookies,
                            next_ip(),
                            fd,
                            progress,
                            start,
                            end,
                            meta.size,
                            stop,
                            wid,
                        )
                        strikes = 0
                    except PieceRetry as exc:
                        # 把没下完的部分放回队列, 让别的连接接手
                        if end is None or exc.pos < end:
                            work.put((exc.pos, end))
                        strikes += 1
                        if args.verbose:
                            eprint(f"worker {wid} strike {strikes}: {exc}")
                        with active_lock:
                            alone = len(active) <= 1
                            if not alone and strikes >= retire_after:
                                active.discard(wid)
                                retired_cnt[0] += 1
                                return
                        if alone and strikes >= last_limit:
                            if exc.status:
                                raise FatalError(t("persist-denied", status=exc.status)) from exc
                            raise FatalError(str(exc)) from exc
                        wait = min(8.0, args.retry_gap / 1000 * (2 ** min(strikes, 4)))
                        if stop.wait(wait):
                            return
                    finally:
                        work.task_done()
            except BaseException as exc:  # noqa: BLE001
                with err_lock:
                    errors.append(exc)
                stop.set()
            finally:
                with active_lock:
                    active.discard(wid)

        threads_list = [
            threading.Thread(target=worker, args=(i + 1,), name=f"fd-{i+1}", daemon=True)
            for i in range(workers_n)
        ]
        for th in threads_list:
            th.start()

        tty = sys.stderr.isatty()
        shown = False
        prev = progress.total()
        avg = 0.0
        last_paint = time.monotonic()
        alpha = 0.9
        width = args.progress_width
        if width is None:
            cols = shutil.get_terminal_size(fallback=(80, 24)).columns
            width = max(10, min(80, cols - 36))
        painter_stop = threading.Event()

        def paint_once(final: bool = False) -> None:
            nonlocal shown, prev, avg, last_paint
            snap = progress.snapshot()
            curr = covered(snap)
            now = time.monotonic()
            dt = max(now - last_paint, 1e-6)
            inst = (curr - prev) / dt
            avg = avg * alpha + inst * (1 - alpha) if avg else inst
            prev = curr
            last_paint = now
            line1, line2, _ = draw_bar(snap, meta.size or 0, width, curr, display_start, avg)
            with IO_LOCK:
                if tty:
                    if shown:
                        sys.stderr.write("\x1b[2A\r")
                    sys.stderr.write(line1 + "\x1b[K\n" + line2 + "\x1b[K\n")
                    shown = True
                elif final:
                    sys.stderr.write("\n" + line1 + "  " + line2 + "\n")
                else:
                    sys.stderr.write("\r" + line1 + " " + line2 + "\x1b[K")
                sys.stderr.flush()

        if tty:
            with IO_LOCK:
                sys.stderr.write("\x1b[?25l")
                sys.stderr.flush()
        try:
            while any(th.is_alive() for th in threads_list):
                if painter_stop.is_set():
                    break
                try:
                    paint_once()
                    persist()
                except Exception:
                    pass
                if meta.size and progress.total() >= meta.size:
                    break
                time.sleep(args.repaint_gap / 1000)
            for th in threads_list:
                th.join()
        except KeyboardInterrupt:
            stop.set()
            for th in threads_list:
                th.join(timeout=2)
            persist()
            eprint(t("keep", path=dest))
            return Result(gid, "ERR", None, url, "interrupted", True)
        finally:
            painter_stop.set()
            try:
                paint_once(final=True)
            except Exception:
                pass
            if tty:
                with IO_LOCK:
                    sys.stderr.write("\x1b[?25h")
                    sys.stderr.flush()

        if retired_cnt[0]:
            eprint(t("throttled", n=retired_cnt[0], m=max(1, workers_n - retired_cnt[0])))

        if errors:
            persist()
            err = errors[0]
            eprint(t("fail", url=final_url))
            eprint(t("reason", err=err))
            eprint(t("keep", path=dest))
            return Result(gid, "ERR", None, url, str(err))

        if meta.size is not None and progress.total() < meta.size:
            persist()
            eprint(t("fail", url=final_url))
            eprint(t("reason", err="incomplete"))
            eprint(t("keep", path=dest))
            return Result(gid, "ERR", None, url, "incomplete")

        os.fsync(fd)
    finally:
        os.close(fd)

    if os.path.isfile(ctrl):
        os.remove(ctrl)
    registry_remove(dest)
    session = max(time.monotonic() - session_start, 1e-6)
    wrote = progress.total() - covered(initial)
    speed = wrote / session if wrote > 0 else 0.0
    eprint(t("output", path=dest))
    return Result(gid, "OK", speed, dest)


def _pwrite(fd: int, data: bytes, offset: int) -> None:
    view = memoryview(data)
    while view:
        if hasattr(os, "pwrite"):
            n = os.pwrite(fd, view, offset)
        else:
            with IO_LOCK:
                os.lseek(fd, offset, os.SEEK_SET)
                n = os.write(fd, view)
        if n <= 0:
            raise OSError("short write")
        offset += n
        view = view[n:]


def _fetch_piece(
    args: argparse.Namespace,
    url: str,
    headers: dict[str, str],
    ssl_ctx: ssl.SSLContext,
    cookies: CookieJar | None,
    source_ip: str | None,
    fd: int,
    progress: Progress,
    start: int,
    end: int | None,
    total: int | None,
    stop: threading.Event,
    wid: int,
) -> None:
    """下载 [start, end)。

    - 401/404/410: FatalError, 整个下载失败。
    - 403/429/5xx: 抛 PieceRetry, 由 worker 把剩余部分放回队列, 其他连接接手。
    - 网络错误: 本地重试 max_tries 次, 仍失败则抛 PieceRetry。
    """
    timeout = max(args.pull_timeout, 1) / 1000
    proxy = resolve_proxy(args.proxy, urlsplit(url).scheme, urlsplit(url).hostname or "")
    pos = start
    tries = 0
    while not stop.is_set():
        if end is not None and pos >= end:
            return
        hdrs = dict(headers)
        ranged = end is not None or pos > 0
        if ranged:
            hdrs["Range"] = f"bytes={pos}-" if end is None else f"bytes={pos}-{end - 1}"
        try:
            if args.verbose:
                eprint(f"worker {wid} GET {hdrs.get('Range', 'full')} {url}")
            resp = http_request(
                "GET",
                url,
                hdrs,
                timeout,
                ssl_ctx,
                proxy,
                source_ip,
                args.max_redirects,
                cookies,
            )
            with resp:
                if resp.status in (401, 404, 410):
                    raise FatalError(str(HttpFailure(resp.status, resp.reason, resp.final_url)))
                if resp.status in RETRY_STATUS:
                    raise PieceRetry(pos, resp.status, f"HTTP {resp.status} {resp.reason}".strip())
                if resp.status == 416:
                    if end is not None:
                        progress.add(pos, end)
                    return
                if resp.status >= 400:
                    raise HttpFailure(resp.status, resp.reason, resp.final_url)
                if ranged and resp.status not in (206, 200):
                    raise HttpFailure(resp.status, resp.reason, resp.final_url)
                if ranged and resp.status == 200 and pos != 0:
                    raise FatalError("server ignored Range; cannot resume this segment")
                while not stop.is_set():
                    if end is not None and pos >= end:
                        return
                    want = 256 * 1024
                    if end is not None:
                        want = min(want, end - pos)
                    buf = resp.read(want)
                    if not buf:
                        break
                    if end is not None and len(buf) > end - pos:
                        buf = buf[: end - pos]
                    _pwrite(fd, buf, pos)
                    progress.add(pos, pos + len(buf))
                    pos += len(buf)
                    tries = 0
                if stop.is_set():
                    return
                if end is None or pos >= end:
                    return
                raise HttpFailure(0, "short read", url)
        except (FatalError, PieceRetry):
            raise
        except Exception as exc:
            tries += 1
            if args.verbose:
                eprint(f"worker {wid} {exc}")
            if tries >= args.max_tries:
                raise PieceRetry(pos, 0, str(exc)) from exc
            if stop.wait(args.retry_gap / 1000):
                return


def cmd_list(details: bool) -> int:
    path = registry_path()
    if not os.path.isfile(path):
        print(t("list-empty"))
        return 0
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        print(t("list-empty"))
        return 0
    items = data.get("items") or {}
    if not items:
        print(t("list-empty"))
        return 0
    for rec in items.values():
        size = rec.get("file_size") or 0
        done = covered([(int(a), int(b)) for a, b in rec.get("progress") or []])
        print(f"{rec.get('file_name')}")
        print(f"  path: {rec.get('path')}")
        print(f"  size: {format_size(size)}  progress: {format_size(done)}")
        print(f"  url: {rec.get('url')}")
        if details:
            print(f"  etag: {rec.get('etag')}")
            print(f"  last-modified: {rec.get('last_modified')}")
            print(f"  elapsed_ms: {rec.get('elapsed_ms')}")
            ranges = rec.get("progress") or []
            preview = " ".join(f"({a},{int(b)-1})" for a, b in ranges[:12])
            print(f"  ranges: {preview}")
        print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fd",
        description="fast-down — 多线程下载器 (aria2c 风格参数)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  fd -x16 -d DIR --user-agent='Mozilla/5.0 ...' --referer='https://example.com/' URL\n"
            "  fd -c -x16 -d '专辑/VIDEO_TS' URL\n"
            "  fd -c URL1 URL2\n"
            "\n"
            "下载结束后会像 aria2c 一样打印 Download Results (OK / ERR)。\n"
            "已完成的文件再加 -c 会立刻结束, 不会重新下载。\n"
            "部分连接被 403/限流时, 只会放弃那几条连接, 其余连接继续下载。\n"
        ),
    )
    parser.add_argument("urls", nargs="+", metavar="URL", help="要下载的 URL, 可以多个")
    parser.add_argument(
        "-c",
        "--continue",
        dest="cont",
        action="store_true",
        help="断点续传。文件已下完时再次执行会立刻完成",
    )
    parser.add_argument("-f", "--force", action="store_true", help="强制覆盖已有文件, 重新下载")
    parser.add_argument("-d", "--dir", dest="directory", default=".", help="保存目录 (默认: .)")
    parser.add_argument(
        "-x",
        "--max-connection-per-server",
        dest="connections",
        type=int,
        default=32,
        help="每个服务器的最大连接数 (默认: 32), 例如 -x16",
    )
    parser.add_argument("-o", "--out", help="自定义文件名 (仅单个 URL)")
    parser.add_argument(
        "-p",
        "--proxy",
        "--all-proxy",
        dest="proxy",
        default=None,
        help='代理, 如 http://host:port 。-p "" 表示不使用代理',
    )
    parser.add_argument(
        "-H",
        "--header",
        dest="headers",
        action="append",
        default=[],
        metavar="Key: Value",
        help="自定义请求头, 可重复",
    )
    parser.add_argument("--user-agent", default=None, help="HTTP User-Agent, 与 aria2c 相同")
    parser.add_argument(
        "--referer",
        default=None,
        help="HTTP Referer。设为 * 时使用下载 URL 本身, 与 aria2c 相同",
    )
    parser.add_argument("--min-chunk-size", type=int, default=1024 * 1024, help="最小分片大小, 字节 (默认: 1048576)")
    parser.add_argument(
        "--max-chunk-size",
        type=int,
        default=64 * 1024 * 1024,
        help="最大分片大小, 字节 (默认: 67108864)。分片越小, 被拒绝的连接退出后越容易被其他连接接手; 0 表示不限制",
    )
    parser.add_argument(
        "--retire-after",
        type=int,
        default=3,
        help="单个连接连续失败(403/限流/网络错误)多少次后退出, 降低并发 (默认: 3)",
    )
    parser.add_argument("--retry-gap", type=int, default=500, help="重试间隔, 毫秒 (默认: 500)")
    parser.add_argument("--repaint-gap", type=int, default=200, help="进度条重绘间隔, 毫秒 (默认: 200)")
    parser.add_argument("--pull-timeout", type=int, default=5000, help="拉取超时, 毫秒 (默认: 5000)")
    parser.add_argument("-m", "--max-tries", type=int, default=5, help="每个分片最大尝试次数 (默认: 5)")
    parser.add_argument("--browser", action="store_true", help="补上浏览器常见的 Origin / Referer / User-Agent")
    parser.add_argument("-y", "--yes", action="store_true", help="全部确认")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--accept-invalid-certs", action="store_true", help="允许无效证书")
    parser.add_argument("--accept-invalid-hostnames", action="store_true", help="允许无效主机名")
    parser.add_argument("--max-redirects", type=int, default=20, help="最大重定向次数 (默认: 20)")
    parser.add_argument("--cookie-store", action="store_true", help="记住 Set-Cookie 并在后续请求带上")
    parser.add_argument("--progress-width", type=int, default=None, help="进度条宽度")
    parser.add_argument("--ip", dest="ips", action="append", default=[], help="绑定本地 IP, 可重复")
    return parser


def drop_unknown_options(parser: argparse.ArgumentParser, argv: list[str]) -> list[str]:
    """去掉不认识的参数 (连同它可能带的值), 打印提示后继续。"""
    known = parser._option_string_actions  # type: ignore[attr-defined]
    longs = [o for o in known if o.startswith("--")]
    url_re = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
    kept: list[str] = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--":
            kept.extend(argv[i:])
            break
        if len(tok) < 2 or not tok.startswith("-") or tok[1:].replace(".", "", 1).isdigit():
            kept.append(tok)
            i += 1
            continue
        if tok.startswith("--"):
            key = tok.split("=", 1)[0]
            matches = [o for o in longs if o.startswith(key)]
            real = key if key in known else (matches[0] if len(matches) == 1 else None)
        else:
            key = tok[:2]
            real = key if key in known else None
        if real is not None:
            kept.append(tok)
            action = known[real]
            exact = tok == key and tok == real or (tok.startswith("--") and "=" not in tok)
            if exact and action.nargs != 0 and i + 1 < len(argv):
                kept.append(argv[i + 1])
                i += 2
                continue
            i += 1
            continue
        # 不认识的参数
        shown = tok
        i += 1
        if "=" not in tok and i < len(argv):
            nxt = argv[i]
            if not nxt.startswith("-") and not url_re.match(nxt):
                shown = f"{tok} {nxt}"
                i += 1
        eprint(t("unknown-opt", opt=shown))
    return kept


def parse_args(argv: list[str]) -> argparse.Namespace:
    argv = list(argv)
    if argv and argv[0] == "list":
        parser = argparse.ArgumentParser(prog="fd list", description="显示未完成的下载")
        parser.add_argument("-d", "--details", action="store_true", help="显示详细信息")
        ns = parser.parse_args(argv[1:])
        ns.cmd = "list"
        return ns
    if argv and argv[0] == "download":
        argv = argv[1:]
    parser = build_parser()
    argv = drop_unknown_options(parser, argv)
    ns = parser.parse_intermixed_args(argv)
    ns.cmd = "download"
    if ns.connections < 1:
        parser.error("-x 必须 >= 1")
    if ns.max_tries < 1:
        parser.error("-m/--max-tries 必须 >= 1")
    if ns.min_chunk_size < 1:
        parser.error("--min-chunk-size 必须 >= 1")
    if ns.max_chunk_size < 0:
        parser.error("--max-chunk-size 必须 >= 0")
    if ns.retire_after < 1:
        parser.error("--retire-after 必须 >= 1")
    if ns.out and len(ns.urls) != 1:
        parser.error(t("bad-out"))
    return ns


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return int(code) if isinstance(code, int) else (0 if code is None else 2)
    if args.cmd == "list":
        return cmd_list(args.details)
    eprint(f"fast-down v{VERSION}")
    results: list[Result] = []
    cycle = list(args.ips)
    for url in args.urls:
        result = download_one(args, url, cycle)
        results.append(result)
        if result.interrupted:
            break
    print_summary(results)
    if any(item.kind == "ERR" for item in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
