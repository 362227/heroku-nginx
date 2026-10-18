#!/usr/bin/env python3
"""gigafile.py — gigafile.nu 上传 / 下载 (纯标准库, 无需 pip 安装任何东西)

  python gigafile.py upload FILE [FILE ...]        上传 (多线程分块, 单行进度条)
  python gigafile.py dl -x16 -d DIR URL [URL ...]  下载 (多连接 Range, 可断点续传)

下载参数贴近 aria2c / fd;  upload 可用 -n 调线程数, -s 调分块大小。
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import queue
import re
import shutil
import socket
import ssl
import sys
import threading
import time
import unicodedata
import urllib.request
import uuid
from collections import deque
from dataclasses import dataclass, field
from html.parser import HTMLParser
from http.client import HTTPConnection, HTTPException, HTTPSConnection
from http.cookiejar import CookieJar
from urllib.parse import quote, unquote, urljoin, urlsplit

VERSION = "4.0"
HOME = os.environ.get("GIGAFILE_HOME", "https://gigafile.nu/")
CTRL_SUFFIX = ".fdctrl"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0"
)
RETRY_STATUS = (403, 429, 500, 502, 503, 504)
BLOCKS = " ▏▎▍▌▋▊▉█"
ASCII_BLOCKS = " .:-=+*#@"


# ───────────────────────────── 基础工具 ─────────────────────────────


class FatalError(Exception):
    pass


class Aborted(Exception):
    pass


class PieceRetry(Exception):
    """下载分片这次没拿下来, 放回队列让别的连接接手。"""

    def __init__(self, pos: int, status: int, msg: str):
        super().__init__(msg)
        self.pos = pos
        self.status = status


def enable_vt() -> bool:
    if os.name != "nt":
        return True
    try:
        import ctypes

        k32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        h = k32.GetStdHandle(-12)
        mode = ctypes.c_ulong()
        if not k32.GetConsoleMode(h, ctypes.byref(mode)):
            return False
        return bool(k32.SetConsoleMode(h, mode.value | 0x0004))
    except Exception:
        return False


def dwidth(s: str) -> int:
    """终端显示宽度 (中日韩全角字符占 2 列)。"""
    w = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


def clip(s: str, width: int) -> str:
    if dwidth(s) <= width:
        return s
    out, w = [], 0
    for ch in s:
        cw = dwidth(ch)
        if w + cw > width:
            break
        out.append(ch)
        w += cw
    return "".join(out)


def middle_clip(s: str, width: int) -> str:
    if dwidth(s) <= width:
        return s
    keep = max(width - 1, 2)
    head = clip(s, keep // 2 + keep % 2)
    tail = ""
    for ch in reversed(s):
        if dwidth(tail) + dwidth(ch) > keep // 2:
            break
        tail = ch + tail
    return head + "…" + tail


def format_size(size: float) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    i = 0
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.2f} {units[i]}" if i else f"{int(size)} B"


def format_speed(speed: float | None) -> str:
    if speed is None:
        return "n/a"
    return format_size(speed) + "/s"


def format_time(sec: float | None) -> str:
    if sec is None or sec < 0 or sec == float("inf") or sec > 86400 * 99:
        return "--:--:--"
    s = int(sec)
    if s < 86400:
        return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
    d, r = divmod(s, 86400)
    return f"{d}d {r // 3600:02d}:{(r % 3600) // 60:02d}:{r % 60:02d}"


def parse_size(text: str | int) -> int:
    """'100MB' / '50M' / '1048576' -> 字节数"""
    if isinstance(text, int):
        return text
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*([KMGT]?)(?:i?B)?\s*$", str(text), re.I)
    if not m:
        raise argparse.ArgumentTypeError(f"无法识别的大小: {text}")
    mult = {"": 1, "K": 1 << 10, "M": 1 << 20, "G": 1 << 30, "T": 1 << 40}[m.group(2).upper()]
    return int(float(m.group(1)) * mult)


def sanitize(name: str) -> str:
    name = name.replace("\\", "/").split("/")[-1]
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    if name in ("", ".", ".."):
        name = "download"
    raw = name.encode("utf-8", "replace")
    if len(raw) <= 255:
        return name
    base, ext = name, ""
    if "." in name and len(name.rsplit(".", 1)[-1].encode()) <= 16:
        base, e = name.rsplit(".", 1)
        ext = "." + e
    cut = base.encode()[: max(255 - len(ext.encode()), 1)]
    while cut and (cut[-1] & 0xC0) == 0x80:
        cut = cut[:-1]
    return cut.decode(errors="ignore") + ext


# ───────────────────────────── 单行进度条 ─────────────────────────────


class Console:
    """所有终端输出都经过这里: 进度条永远只占一行, 日志会先擦掉进度条再输出。"""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.tty = sys.stderr.isatty()
        self.vt = self.tty and enable_vt()
        self.last_w = 0
        self.drawn = False
        self.ascii = False
        self._last_plain = 0.0

    def cols(self) -> int:
        try:
            return os.get_terminal_size(sys.stderr.fileno()).columns
        except (OSError, ValueError):
            return shutil.get_terminal_size(fallback=(80, 24)).columns

    def _erase(self) -> None:
        if self.drawn and self.tty:
            sys.stderr.write("\r" + " " * self.last_w + "\r")
        self.drawn = False
        self.last_w = 0

    def log(self, msg: str) -> None:
        with self.lock:
            self._erase()
            sys.stderr.write(msg + "\n")
            sys.stderr.flush()

    def status(self, text: str, force: bool = False) -> None:
        with self.lock:
            if self.tty:
                text = clip(text, self.cols() - 1)
                w = dwidth(text)
                pad = " " * max(0, self.last_w - w)
                sys.stderr.write("\r" + text + pad)
                sys.stderr.flush()
                self.last_w = w
                self.drawn = True
            else:  # 重定向到文件时: 每 10 秒一行, 不刷屏
                now = time.monotonic()
                if force or now - self._last_plain >= 10:
                    self._last_plain = now
                    sys.stderr.write(text + "\n")
                    sys.stderr.flush()

    def end_line(self) -> None:
        with self.lock:
            if self.drawn and self.tty:
                sys.stderr.write("\n")
                sys.stderr.flush()
            self.drawn = False
            self.last_w = 0

    def cursor(self, show: bool) -> None:
        if self.vt:
            with self.lock:
                sys.stderr.write("\x1b[?25h" if show else "\x1b[?25l")
                sys.stderr.flush()


CON = Console()


def make_bar(ranges: list[tuple[int, int]], total: int, width: int) -> str:
    chars = ASCII_BLOCKS if CON.ascii else BLOCKS
    if total <= 0 or width <= 0:
        return " " * max(width, 0)
    per = total / width
    out: list[str] = []
    idx = 0
    n = len(chars) - 1
    for i in range(width):
        b0, b1 = int(i * per), int((i + 1) * per)
        got = 0
        while idx < len(ranges) and ranges[idx][1] <= b0:
            idx += 1
        j = idx
        while j < len(ranges) and ranges[j][0] < b1:
            ov = min(ranges[j][1], b1) - max(ranges[j][0], b0)
            if ov > 0:
                got += ov
            j += 1
        level = int(round(got / per * n)) if per else 0
        out.append(chars[max(0, min(n, level))])
    return "".join(out)


def merge_ranges(ranges) -> list[tuple[int, int]]:
    items = sorted((s, e) for s, e in ranges if e > s)
    if not items:
        return []
    out = [items[0]]
    for s, e in items[1:]:
        ps, pe = out[-1]
        if s <= pe:
            out[-1] = (ps, max(pe, e))
        else:
            out.append((s, e))
    return out


def covered(ranges) -> int:
    return sum(e - s for s, e in merge_ranges(ranges))


def missing_ranges(done, total: int) -> list[tuple[int, int]]:
    cur, out = 0, []
    for s, e in merge_ranges(done):
        if s > cur:
            out.append((cur, s))
        cur = max(cur, e)
    if cur < total:
        out.append((cur, total))
    return out


class Painter(threading.Thread):
    """后台线程, 定时把进度画成一行。snapshot() 返回 (已完成区间, 已完成字节)。"""

    def __init__(self, label: str, total: int, snapshot, extra=lambda: "", interval: float = 0.2):
        super().__init__(daemon=True)
        self.label, self.total, self.snapshot, self.extra = label, total, snapshot, extra
        self.interval = interval
        self.halt = threading.Event()
        self.samples: deque[tuple[float, int]] = deque()
        self.started = time.monotonic()
        self.speed = 0.0

    def run(self) -> None:
        CON.cursor(False)
        while not self.halt.wait(self.interval):
            try:
                self.paint()
            except Exception:
                pass

    def paint(self, final: bool = False) -> None:
        ranges, cur = self.snapshot()
        now = time.monotonic()
        self.samples.append((now, cur))
        while len(self.samples) > 2 and now - self.samples[0][0] > 4.0:
            self.samples.popleft()
        t0, c0 = self.samples[0]
        if now - t0 > 0.3:
            self.speed = max(0.0, (cur - c0) / (now - t0))
        left = (self.total - cur) / self.speed if self.speed > 1 and self.total else None
        pct = cur * 100 / self.total if self.total else 0.0
        avail = CON.cols() - 1
        size_txt = f"{format_size(cur)}/{format_size(self.total)}" if self.total else format_size(cur)
        extra = self.extra()
        label = middle_clip(self.label, 20)
        label = label + " " * (min(20, dwidth(self.label)) - dwidth(label))
        bw = 0
        head = tail = ""
        for show_label, show_extra, show_size in ((1, 1, 1), (0, 1, 1), (0, 0, 1), (0, 0, 0)):
            head = (label + " ") if show_label else ""
            tail = (
                f" {pct:5.1f}%"
                + (f" {size_txt}" if show_size else "")
                + f" {format_speed(self.speed):>11} ETA {format_time(left)}"
                + (f" {extra}" if show_extra and extra else "")
            )
            bw = avail - dwidth(head) - dwidth(tail) - 2
            if bw >= 10:
                break
        bw = max(bw, 4)
        lb, rb = ("[", "]") if CON.ascii else ("|", "|")
        CON.status(head + lb + make_bar(ranges, self.total, bw) + rb + tail, force=final)

    def finish(self) -> None:
        self.halt.set()
        if self.is_alive():
            self.join(timeout=1)
        try:
            self.paint(final=True)
        except Exception:
            pass
        CON.end_line()
        CON.cursor(True)


# ───────────────────────────── HTTP 层 ─────────────────────────────


@dataclass
class Response:
    status: int
    reason: str
    headers: dict
    final_url: str
    _resp: object
    _conn: object

    def read(self, n: int = -1) -> bytes:
        return self._resp.read(n)  # type: ignore[attr-defined]

    def close(self) -> None:
        try:
            self._resp.close()  # type: ignore[attr-defined]
        finally:
            try:
                self._conn.close()  # type: ignore[attr-defined]
            except Exception:
                pass

    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def get(self, name: str, default: str | None = None) -> str | None:
        return self.headers.get(name.lower(), default)


def resolve_proxy(explicit: str | None, scheme: str, host: str) -> str | None:
    if explicit == "":
        return None
    if explicit:
        return explicit
    try:
        if urllib.request.proxy_bypass(host):  # type: ignore[attr-defined]
            return None
        p = urllib.request.getproxies()
    except Exception:
        return None
    return p.get(scheme) or p.get("all") or p.get("https") or p.get("http")


def _read_connect_reply(sock: socket.socket) -> int:
    buff = b""
    while b"\r\n\r\n" not in buff and len(buff) < 65536:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buff += chunk
    line = buff.split(b"\r\n", 1)[0]
    if not line.startswith(b"HTTP/"):
        raise HTTPException(f"bad proxy response: {line!r}")
    parts = line.split()
    return int(parts[1]) if len(parts) > 1 else 0


def open_conn(url: str, timeout: float, ctx: ssl.SSLContext, proxy: str | None):
    """返回 (连接, 是否需要绝对路径请求行)。支持 HTTP 代理 / HTTPS CONNECT。"""
    p = urlsplit(url)
    if p.scheme not in ("http", "https"):
        raise FatalError(f"不支持的 URL: {url}")
    host = p.hostname
    if not host:
        raise FatalError(f"无效的 URL: {url}")
    port = p.port or (443 if p.scheme == "https" else 80)
    if not proxy:
        if p.scheme == "https":
            conn = HTTPSConnection(host, port, timeout=timeout, context=ctx)
        else:
            conn = HTTPConnection(host, port, timeout=timeout)
        conn.connect()
        return conn, False
    pu = urlsplit(proxy if "://" in proxy else "http://" + proxy)
    if pu.scheme.startswith("socks"):
        raise FatalError("暂不支持 SOCKS 代理, 请使用 HTTP 代理")
    ph, pp = pu.hostname, pu.port or 8080
    if not ph:
        raise FatalError(f"无效的代理: {proxy}")
    if p.scheme != "https":
        conn = HTTPConnection(ph, pp, timeout=timeout)
        conn.connect()
        return conn, True
    sock = socket.create_connection((ph, pp), timeout=timeout)
    auth = ""
    if pu.username:
        cred = f"{unquote(pu.username)}:{unquote(pu.password or '')}"
        auth = "Proxy-Authorization: Basic " + base64.b64encode(cred.encode()).decode() + "\r\n"
    target = f"{host}:{port}"
    sock.sendall(f"CONNECT {target} HTTP/1.1\r\nHost: {target}\r\n{auth}\r\n".encode())
    code = _read_connect_reply(sock)
    if code != 200:
        sock.close()
        raise FatalError(f"代理 CONNECT 失败: HTTP {code}")
    ssock = ctx.wrap_socket(sock, server_hostname=host)
    conn = HTTPSConnection(host, port, timeout=timeout, context=ctx)
    conn.sock = ssock
    return conn, False


class Net:
    def __init__(self, args: argparse.Namespace) -> None:
        self.timeout = float(args.timeout)
        self.proxy = args.proxy
        self.verbose = args.verbose
        self.ctx = ssl.create_default_context()
        if args.insecure:
            self.ctx.check_hostname = False
            self.ctx.verify_mode = ssl.CERT_NONE
        self.jar = CookieJar()
        self.max_redirects = 10
        self.extra: dict[str, str] = {}
        for raw in getattr(args, "headers", []) or []:
            if ":" not in raw:
                raise FatalError(f"请求头格式错误: {raw}")
            k, v = raw.split(":", 1)
            self.extra[k.strip()] = v.strip()
        self.ua = getattr(args, "user_agent", None) or UA
        self.referer = getattr(args, "referer", None)

    def base_headers(self) -> dict[str, str]:
        h = {"User-Agent": self.ua, "Accept": "*/*"}
        if self.referer:
            h["Referer"] = self.referer
        h.update(self.extra)
        return h

    def cookie_for(self, url: str) -> str | None:
        req = urllib.request.Request(url)
        self.jar.add_cookie_header(req)
        return req.get_header("Cookie")

    def store_cookies(self, url: str, resp) -> None:
        try:
            self.jar.extract_cookies(resp, urllib.request.Request(url))
        except Exception:
            pass

    def connect(self, url: str, timeout: float | None = None):
        p = urlsplit(url)
        proxy = resolve_proxy(self.proxy, p.scheme, p.hostname or "")
        return open_conn(url, timeout or self.timeout, self.ctx, proxy)

    @staticmethod
    def path_of(url: str) -> str:
        p = urlsplit(url)
        path = quote(p.path or "/", safe="/%:@!$&'()*+,;=-._~")
        return path + ("?" + p.query if p.query else "")

    def request(self, method: str, url: str, headers: dict | None = None, timeout: float | None = None) -> Response:
        cur = url
        for _ in range(self.max_redirects + 1):
            send = self.base_headers()
            send.update(headers or {})
            ck = self.cookie_for(cur)
            if ck and not any(k.lower() == "cookie" for k in send):
                send["Cookie"] = ck
            conn, absolute = self.connect(cur, timeout)
            try:
                conn.request(method, cur if absolute else self.path_of(cur), headers=send)
                resp = conn.getresponse()
            except Exception:
                conn.close()
                raise
            self.store_cookies(cur, resp)
            if resp.status in (301, 302, 303, 307, 308):
                loc = resp.getheader("Location")
                try:
                    resp.read()
                except Exception:
                    pass
                conn.close()
                if not loc:
                    raise FatalError(f"重定向缺少 Location: {cur}")
                cur = urljoin(cur, loc)
                if resp.status == 303:
                    method = "GET"
                continue
            folded = {k.lower(): v for k, v in resp.getheaders()}
            return Response(resp.status, resp.reason, folded, cur, resp, conn)
        raise FatalError(f"重定向次数过多: {url}")


# ───────────────────────────── 结果 / 汇总 ─────────────────────────────


@dataclass
class Result:
    kind: str  # OK / ERR / CNCL
    target: str
    speed: float | None = None
    size: int = 0
    url: str | None = None
    error: str | None = None
    interrupted: bool = False


def confirm(yes: bool, message: str) -> bool:
    if yes:
        return True
    if not sys.stdin.isatty():
        CON.log(message + "  (非交互环境, 已取消)")
        return False
    try:
        return input(message + " [y/N] ").strip().lower() in ("y", "yes", "是")
    except EOFError:
        return False


def print_summary(title: str, results: list[Result], with_url: bool) -> None:
    print()
    print(title)
    print("stat|avg speed  |size       |path/URI")
    print("====+===========+===========+" + "=" * 45)
    for r in results:
        stat = {"OK": "OK  ", "ERR": "ERR ", "CNCL": "CNCL"}.get(r.kind, "ERR ")
        spd = format_speed(r.speed) if r.speed is not None else "n/a"
        print(f"{stat}|{spd:>11}|{format_size(r.size):>11}|{r.target}")
        if with_url and r.url:
            print(f"    -> {r.url}")
        if r.error and r.kind != "OK":
            print(f"    !! {r.error}")


# ═════════════════════════════ 上传 ═════════════════════════════

SEND_BUF = 512 * 1024


class Gate:
    """保证各分块按顺序"收尾": 第 n 块要等前 n 块全部完成才发出最后几个字节。
    服务器是按到达顺序拼接分块的, 所以最后几个字节被扣住, 它就没法提前处理这一块。"""

    def __init__(self) -> None:
        self.cv = threading.Condition()
        self.done = 0

    def wait_turn(self, n: int, abort: threading.Event) -> None:
        with self.cv:
            while self.done < n:
                if abort.is_set():
                    raise Aborted()
                self.cv.wait(0.3)

    def finish(self, n: int) -> None:
        with self.cv:
            self.done = max(self.done, n + 1)
            self.cv.notify_all()


@dataclass
class UpJob:
    path: str
    name: str
    size: int
    chunk: int
    nchunks: int
    token: str
    upload_url: str
    lifetime: int
    sent: list = field(default_factory=list)
    gate: Gate = field(default_factory=Gate)
    abort: threading.Event = field(default_factory=threading.Event)
    result_data: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)


def _field(boundary: str, name: str, value: str) -> bytes:
    return (
        f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'
    ).encode("utf-8")


def send_chunk(net: Net, args: argparse.Namespace, job: UpJob, n: int) -> dict:
    start = n * job.chunk
    length = min(job.chunk, job.size - start)
    boundary = "----gfpy" + uuid.uuid4().hex
    head = b"".join(
        [
            _field(boundary, "id", job.token),
            _field(boundary, "name", job.name),
            _field(boundary, "chunk", str(n)),
            _field(boundary, "chunks", str(job.nchunks)),
            _field(boundary, "lifetime", str(job.lifetime)),
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="blob"\r\n'
                "Content-Type: application/octet-stream\r\n\r\n"
            ).encode(),
        ]
    )
    tail = f"\r\n--{boundary}--\r\n".encode()
    total_len = len(head) + length + len(tail)
    buf = bytearray(SEND_BUF)
    mv = memoryview(buf)
    tries = 0
    while True:
        if job.abort.is_set():
            raise Aborted()
        job.sent[n] = 0
        conn = None
        try:
            conn, absolute = net.connect(job.upload_url, timeout=net.timeout)
            conn.putrequest("POST", job.upload_url if absolute else net.path_of(job.upload_url), skip_accept_encoding=True)
            conn.putheader("User-Agent", net.ua)
            conn.putheader("Accept", "*/*")
            conn.putheader("Content-Type", f"multipart/form-data; boundary={boundary}")
            conn.putheader("Content-Length", str(total_len))
            ck = net.cookie_for(job.upload_url)
            if ck:
                conn.putheader("Cookie", ck)
            conn.endheaders()
            sock = conn.sock
            sock.sendall(head)
            with open(job.path, "rb") as fh:
                fh.seek(start)
                remain = length
                while remain:
                    if job.abort.is_set():
                        raise Aborted()
                    k = fh.readinto(mv[: min(SEND_BUF, remain)])
                    if not k:
                        raise OSError("读取文件失败 (文件在上传过程中被修改?)")
                    sock.sendall(mv[:k])
                    job.sent[n] += k
                    remain -= k
            job.gate.wait_turn(n, job.abort)  # 按顺序放出最后几个字节
            sock.sendall(tail)
            sock.settimeout(max(net.timeout * 6, 120))
            resp = conn.getresponse()
            raw = resp.read()
            net.store_cookies(job.upload_url, resp)
            if resp.status >= 400:
                raise OSError(f"HTTP {resp.status} {resp.reason}")
            try:
                data = json.loads(raw.decode("utf-8", "replace"))
            except ValueError:
                raise OSError(f"服务器返回了无法解析的内容: {raw[:120]!r}")
            if "status" not in data or data["status"]:
                raise FatalError(f"服务器拒绝了第 {n + 1} 块: {data}")
            job.gate.finish(n)
            return data
        except (Aborted, FatalError):
            raise
        except Exception as exc:
            tries += 1
            job.sent[n] = 0
            if tries >= args.max_tries:
                raise FatalError(f"第 {n + 1} 块多次失败: {exc}") from exc
            CON.log(f"第 {n + 1}/{job.nchunks} 块出错 ({exc}), 第 {tries} 次重试…")
            if job.abort.wait(min(10.0, 0.5 * 2 ** tries)):
                raise Aborted()
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass


def pick_chunk_size(args: argparse.Namespace, size: int) -> int:
    if args.chunk_size and args.chunk_size != "auto":
        return max(parse_size(args.chunk_size), 1 << 20)
    # 自动: 让线程都有活干, 但单块不超过 100MB、不小于 16MB
    guess = math.ceil(size / (args.threads * 2))
    return int(min(100 << 20, max(16 << 20, guess)))


def upload_file(args: argparse.Namespace, net: Net, path: str) -> Result:
    name = os.path.basename(path)
    size = os.path.getsize(path)
    if size == 0:
        return Result("ERR", path, error="空文件无法上传")
    chunk = pick_chunk_size(args, size)
    nchunks = math.ceil(size / chunk)
    threads = max(1, min(args.threads, nchunks))
    CON.log(f"文件: {name}  大小: {format_size(size)}  分块: {nchunks} x {format_size(chunk)}  线程: {threads}")

    try:
        with net.request("GET", HOME) as r:
            page = r.read(2_000_000).decode("utf-8", "replace")
    except FatalError:
        raise
    except Exception as exc:
        return Result("ERR", path, size=size, error=f"无法连接 gigafile.nu: {exc}")
    m = re.search(r'var\s+server\s*=\s*"(.+?)"', page)
    if not m:
        return Result("ERR", path, size=size, error="找不到上传服务器地址 (网站可能改版了)")
    scheme = urlsplit(HOME).scheme
    job = UpJob(
        path=path,
        name=name,
        size=size,
        chunk=chunk,
        nchunks=nchunks,
        token=uuid.uuid1().hex,
        upload_url=f"{scheme}://{m.group(1)}/upload_chunk.php",
        lifetime=args.lifetime,
    )
    job.sent = [0] * nchunks

    def snapshot():
        sent = list(job.sent)
        return [(i * chunk, i * chunk + s) for i, s in enumerate(sent) if s > 0], sum(sent)

    painter = Painter(name, size, snapshot, extra=lambda: f"块 {job.gate.done}/{nchunks}")
    painter.start()
    started = time.monotonic()
    pending: queue.Queue[int] = queue.Queue()
    for i in range(1, nchunks):
        pending.put(i)
    lock = threading.Lock()

    def remember(data: dict) -> None:
        if "url" in data:
            with lock:
                job.result_data = data

    def worker() -> None:
        try:
            while not job.abort.is_set():
                try:
                    n = pending.get_nowait()
                except queue.Empty:
                    return
                remember(send_chunk(net, args, job, n))
        except Aborted:
            pass
        except BaseException as exc:  # noqa: BLE001
            with lock:
                job.errors.append(exc)
            job.abort.set()

    try:
        # 第 0 块单独先传, 让服务器先下发会话 cookie
        remember(send_chunk(net, args, job, 0))
        ths = [threading.Thread(target=worker, daemon=True) for _ in range(threads)] if nchunks > 1 else []
        for th in ths:
            th.start()
        while any(th.is_alive() for th in ths):
            time.sleep(0.2)
    except KeyboardInterrupt:
        job.abort.set()
        painter.finish()
        CON.log("已取消上传")
        return Result("ERR", path, size=size, error="interrupted", interrupted=True)
    except Aborted:
        pass
    except BaseException as exc:  # noqa: BLE001
        job.abort.set()
        job.errors.append(exc)
    painter.finish()

    elapsed = max(time.monotonic() - started, 1e-6)
    if job.errors:
        return Result("ERR", path, size=size, error=str(job.errors[0]))
    url = job.result_data.get("url")
    if not url:
        return Result("ERR", path, size=size, error=f"服务器没有返回下载链接: {job.result_data}")
    return Result("OK", path, speed=size / elapsed, size=size, url=url)


def collect_files(paths: list[str], yes: bool) -> list[str]:
    files: list[str] = []
    for p in paths:
        if os.path.isdir(p):
            found: list[str] = []
            for root, dirs, names in os.walk(p):
                dirs.sort()
                for n in sorted(names):
                    found.append(os.path.join(root, n))
                if len(found) > 200:
                    raise FatalError(f"目录文件过多 (>200): {p}, 请指定具体文件")
            files.extend(found)
        elif os.path.isfile(p):
            files.append(p)
        else:
            raise FatalError(f"路径不存在: {p}")
    if not files:
        raise FatalError("没有可上传的文件")
    if len(files) > 1 or any(os.path.isdir(p) for p in paths):
        total = sum(os.path.getsize(f) for f in files)
        if not confirm(yes, f"将逐个上传 {len(files)} 个文件, 共 {format_size(total)}, 继续?"):
            raise FatalError("已取消")
    return files


def cmd_upload(args: argparse.Namespace) -> int:
    net = Net(args)
    files = collect_files(args.files, args.yes)
    results: list[Result] = []
    for f in files:
        try:
            res = upload_file(args, net, f)
        except FatalError as exc:
            res = Result("ERR", f, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            res = Result("ERR", f, error=str(exc))
        results.append(res)
        if res.kind == "OK":
            CON.log(f"完成: {res.url}")
        else:
            CON.log(f"失败: {f}  ({res.error})")
        if res.interrupted:
            break
    print_summary("Upload Results:", results, with_url=True)
    return 0 if all(r.kind == "OK" for r in results) else 1


# ═════════════════════════════ 下载 ═════════════════════════════


class _Node:
    __slots__ = ("tag", "attrs", "kids", "parent")

    def __init__(self, tag: str, attrs: dict, parent: "_Node | None") -> None:
        self.tag, self.attrs, self.parent = tag, attrs, parent
        self.kids: list = []

    def elements(self) -> list["_Node"]:
        return [k for k in self.kids if isinstance(k, _Node)]

    def text(self) -> str:
        return "".join(k if isinstance(k, str) else k.text() for k in self.kids)

    def has_class(self, c: str) -> bool:
        return c in (self.attrs.get("class") or "").split()

    def walk(self):
        for k in self.kids:
            if isinstance(k, _Node):
                yield k
                yield from k.walk()


class _Dom(HTMLParser):
    VOID = {"br", "img", "input", "meta", "link", "hr", "area", "base", "col", "embed", "source", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = _Node(tag, {k: (v or "") for k, v in attrs}, self.cur)
        self.cur.kids.append(n)
        if tag not in self.VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(_Node(tag, {k: (v or "") for k, v in attrs}, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.kids.append(data)


@dataclass
class Item:
    name: str
    size_hint: str
    url: str


def parse_page(html: str, page_url: str) -> list[Item]:
    dom = _Dom()
    dom.feed(html)
    dom.close()
    root = dom.root
    p = urlsplit(page_url)
    base = f"{p.scheme}://{p.netloc}"
    m = re.match(r"^/([A-Za-z0-9_-]+)/?$", p.path)
    if not m:
        raise FatalError(f"不是有效的 gigafile 链接: {page_url}")
    page_id = m.group(1)
    items: list[Item] = []
    if any(n.attrs.get("id") == "contents_matomete" for n in root.walk()):
        for el in (n for n in root.walk() if n.has_class("matomete_file")):
            info = next((n for n in el.walk() if n.has_class("matomete_file_info")), None)
            btn = next((n for n in el.walk() if n.has_class("download_panel_btn_dl")), None)
            if info is None or btn is None:
                continue
            kids = info.elements()
            fid = re.search(r"download\(\d+, *'(.+?)'", btn.attrs.get("onclick", ""))
            if len(kids) < 3 or not fid:
                continue
            sm = re.search(r"（(.+?)）", kids[2].text().strip())
            items.append(
                Item(sanitize(kids[1].text().strip()), sm.group(1) if sm else "", f"{base}/download.php?file={fid.group(1)}")
            )
    else:
        dl = next((n for n in root.walk() if n.attrs.get("id") == "dl"), None)
        sz = next((n for n in root.walk() if n.has_class("dl_size")), None)
        if dl is not None and dl.text().strip():
            items.append(
                Item(sanitize(dl.text().strip()), sz.text().strip() if sz is not None else "", f"{base}/download.php?file={page_id}")
            )
    return items


@dataclass
class Meta:
    size: int | None
    ranges: bool
    etag: str | None
    cd_name: str | None = None
    cd_raw: str | None = None


def _fix_mojibake(text: str) -> str:
    """http.client 按 latin-1 解码响应头; 原始字节若其实是 UTF-8 / Shift-JIS / GBK 就还原。"""
    if all(ord(c) < 128 for c in text):
        return text
    try:
        raw = text.encode("latin-1")
    except UnicodeEncodeError:
        return text
    for enc in ("utf-8", "cp932", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return text


def filename_from_cd(cd: str | None) -> str | None:
    if not cd:
        return None
    m = re.search(r"filename\*\s*=\s*([^']*)'[^']*'([^;]+)", cd, re.I)
    if m:
        try:
            return sanitize(unquote(m.group(2).strip().strip('"'), encoding=(m.group(1) or "utf-8").strip() or "utf-8", errors="replace"))
        except LookupError:
            return sanitize(unquote(m.group(2).strip().strip('"'), errors="replace"))
    cd = _fix_mojibake(cd)
    m = re.search(r'filename\s*=\s*"([^"]+)"', cd, re.I) or re.search(r"filename\s*=\s*([^;]+)", cd, re.I)
    if m:
        val = m.group(1).strip().strip('"')
        return sanitize(unquote(val) if "%" in val else val)
    return None


def name_is_degraded(name: str) -> bool:
    """文件名主体里一个像样的字符都没有 (全是下划线/符号/替换字符)。"""
    stem = name.rsplit(".", 1)[0] if "." in name else name
    return not re.search(r"[^\W_]", stem)


def probe(net: Net, url: str, args: argparse.Namespace) -> Meta:
    last: object = None
    for attempt in range(1, args.max_tries + 1):
        try:
            resp = net.request("GET", url, {"Range": "bytes=0-0"})
        except FatalError:
            raise
        except Exception as exc:
            last = exc
            time.sleep(args.retry_gap / 1000 * attempt)
            continue
        with resp:
            if resp.status in (401, 404, 410):
                raise FatalError(f"HTTP {resp.status} (文件不存在、已过期或需要密码)")
            if resp.status in RETRY_STATUS:
                last = f"HTTP {resp.status}"
                time.sleep(args.retry_gap / 1000 * attempt)
                continue
            if resp.status >= 400 and resp.status != 416:
                raise FatalError(f"HTTP {resp.status} {resp.reason}")
            size: int | None = None
            ranges = False
            if resp.status == 206:
                mm = re.match(r"bytes (\d+)-(\d+)/(\d+|\*)", resp.get("content-range") or "")
                if mm and mm.group(3) != "*":
                    size = int(mm.group(3))
                ranges = True
            else:
                cl = resp.get("content-length") or ""
                if cl.isdigit():
                    size = int(cl)
            cd = resp.get("content-disposition")
            return Meta(size, ranges and size is not None, resp.get("etag"), filename_from_cd(cd), cd)
    raise FatalError(f"获取文件信息失败: {last}")


class Progress:
    def __init__(self, initial=()) -> None:
        self.ranges = merge_ranges(initial)
        self.lock = threading.Lock()

    def add(self, start: int, end: int) -> None:
        if end <= start:
            return
        with self.lock:
            r = self.ranges
            # 常见情况: 在已有区间末尾追加, 免去整体重排
            for i, (s, e) in enumerate(r):
                if s <= start <= e:
                    if end > e:
                        r[i] = (s, end)
                        if i + 1 < len(r) and r[i + 1][0] <= end:
                            self.ranges = merge_ranges(r)
                    return
            self.ranges = merge_ranges([*r, (start, end)])

    def snapshot(self) -> list[tuple[int, int]]:
        with self.lock:
            return list(self.ranges)


def split_ranges(ranges, connections: int, min_chunk: int, max_chunk: int) -> list[tuple[int, int]]:
    total = sum(e - s for s, e in ranges)
    if total <= 0:
        return []
    connections = max(1, connections)
    if min_chunk > 0:
        connections = max(1, min(connections, max(1, total // min_chunk)))
    piece = max(1, (total + connections - 1) // connections)
    if max_chunk > 0:
        piece = min(piece, max(max_chunk, min_chunk, 1))
    out = []
    for s, e in ranges:
        cur = s
        while cur < e:
            take = min(piece, e - cur)
            out.append((cur, cur + take))
            cur += take
    return out


def load_control(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    data["progress"] = merge_ranges([(int(a), int(b)) for a, b in data.get("progress") or []])
    return data


def save_control(path: str, data: dict) -> None:
    tmp = path + ".tmp"
    payload = dict(data)
    payload["progress"] = [list(p) for p in payload.get("progress") or []]
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError:
        pass


def fetch_piece(net, args, url, fh, progress, start, end, stop, use_range, wid) -> None:
    """下载 [start, end)。401/404/410 致命; 403/429/5xx/网络错误抛 PieceRetry。"""
    pos = start
    tries = 0
    while not stop.is_set():
        if pos >= end:
            return
        hdrs = {"Range": f"bytes={pos}-{end - 1}"} if use_range else {}
        try:
            if args.verbose:
                CON.log(f"[{wid}] GET {hdrs.get('Range', 'full')}")
            resp = net.request("GET", url, hdrs)
            with resp:
                if resp.status in (401, 404, 410):
                    raise FatalError(f"HTTP {resp.status} (文件不存在或已过期)")
                if resp.status in RETRY_STATUS or resp.status == 416:
                    raise PieceRetry(pos, resp.status, f"HTTP {resp.status} {resp.reason}".strip())
                if resp.status >= 400:
                    raise OSError(f"HTTP {resp.status} {resp.reason}")
                if use_range and resp.status == 200 and pos != 0:
                    raise FatalError("服务器忽略了 Range, 无法分段下载")
                while not stop.is_set():
                    if pos >= end:
                        return
                    buf = resp.read(min(256 * 1024, end - pos))
                    if not buf:
                        break
                    fh.seek(pos)
                    fh.write(buf)
                    progress.add(pos, pos + len(buf))
                    pos += len(buf)
                    tries = 0
                if stop.is_set() or pos >= end:
                    return
                raise OSError("连接被提前关闭")
        except (FatalError, PieceRetry):
            raise
        except Exception as exc:
            tries += 1
            if args.verbose:
                CON.log(f"[{wid}] {exc}")
            if tries >= args.max_tries:
                raise PieceRetry(pos, 0, str(exc)) from exc
            if stop.wait(args.retry_gap / 1000):
                return


def download_item(args, net: Net, item: Item, outname: str | None) -> Result:
    directory = os.path.abspath(args.directory)
    os.makedirs(directory, exist_ok=True)
    meta = probe(net, item.url, args)
    if args.verbose:
        CON.log(f"页面文件名: {item.name!r}\nContent-Disposition: {meta.cd_raw!r}")
    if outname:
        name = sanitize(outname)
    elif name_is_degraded(item.name) and meta.cd_name and not name_is_degraded(meta.cd_name):
        name = meta.cd_name
        CON.log(f"页面文件名无法识别 ({item.name}), 改用服务器返回的文件名")
    else:
        name = item.name
    dest = os.path.join(directory, name)
    ctrl = dest + CTRL_SUFFIX
    size = meta.size
    if size is None:
        raise FatalError("服务器没有返回文件大小")
    use_range = meta.ranges
    conns = max(1, min(args.connections, len(split_ranges([(0, size)], args.connections, args.min_chunk_size, args.max_chunk_size)))) if use_range else 1
    CON.log(f"文件名称: {name}\n文件大小: {format_size(size)} ({size} 字节)\n文件路径: {dest}\n并行数量: {conns}" + ("" if use_range else "  (服务器不支持 Range, 单连接)"))

    saved = load_control(ctrl)
    local = os.path.getsize(dest) if os.path.isfile(dest) else None
    initial: list[tuple[int, int]] = []
    if os.path.isfile(dest) and not args.force:
        if args.cont:
            if saved is None and local == size:
                CON.log("文件已下载完成, 跳过")
                return Result("OK", dest, size=size)
            if saved is not None:
                if covered(saved["progress"]) >= size and local == size:
                    os.remove(ctrl)
                    CON.log("文件已下载完成, 跳过")
                    return Result("OK", dest, size=size)
                if saved.get("file_size") not in (None, size):
                    if not confirm(args.yes, f"记录的文件大小 {saved.get('file_size')} 与远端 {size} 不一致, 是否继续?"):
                        return Result("CNCL", dest, size=size)
                elif saved.get("etag") and meta.etag and saved["etag"] != meta.etag:
                    if not confirm(args.yes, "ETag 与上次不一致, 无法保证文件完整, 是否继续?"):
                        return Result("CNCL", dest, size=size)
                if use_range:
                    initial = list(saved["progress"])
            elif local is not None and 0 < local < size and use_range:
                initial = [(0, local)]
            elif local is not None and local > size:
                return Result("ERR", dest, size=size, error="本地文件比远端更大, 拒绝续传 (可用 -f 覆盖)")
            if initial:
                CON.log(f"未完成的下载, 继续下载... 已有 {format_size(covered(initial))}")
        elif not confirm(args.yes, f"文件已经存在: {name}, 是否覆盖?"):
            CON.log("下载取消")
            return Result("CNCL", dest, size=size)

    remaining = size - covered(initial)
    free = shutil.disk_usage(directory).free
    if free < remaining:
        CON.log(f"剩余空间不足, 还需要 {format_size(remaining - free)}")
        return Result("CNCL", dest, size=size, error="磁盘空间不足")

    if size == 0:
        open(dest, "wb").close()
        return Result("OK", dest, size=0)

    with open(dest, "r+b" if os.path.exists(dest) and initial else "wb") as fh:
        fh.truncate(size)

    progress = Progress(initial)
    stop = threading.Event()
    errors: list[BaseException] = []
    err_lock = threading.Lock()
    retired = [0]
    ctrl_data = {"url": item.url, "file_size": size, "etag": meta.etag, "progress": [], "elapsed_ms": 0}

    def persist() -> None:
        ctrl_data["progress"] = progress.snapshot()
        save_control(ctrl, ctrl_data)

    persist()
    painter = Painter(name, size, lambda: (lambda s: (s, covered(s)))(progress.snapshot()), extra=lambda: f"x{conns - retired[0]}")
    painter.start()
    started = time.monotonic()
    retire_after = max(1, args.retire_after)
    last_limit = max(args.max_tries * 3, 10)

    def run_round(pieces: list[tuple[int, int]], nworkers: int) -> None:
        work: queue.Queue[tuple[int, int]] = queue.Queue()
        for pc in pieces:
            work.put(pc)
        active = set(range(1, nworkers + 1))
        alock = threading.Lock()

        def worker(wid: int) -> None:
            strikes = 0
            fh = None
            try:
                if stop.wait(0.05 * (wid - 1)):
                    return
                fh = open(dest, "r+b", buffering=0)
                while not stop.is_set():
                    try:
                        start, end = work.get_nowait()
                    except queue.Empty:
                        return
                    try:
                        fetch_piece(net, args, item.url, fh, progress, start, end, stop, use_range, wid)
                        strikes = 0
                    except PieceRetry as exc:
                        if exc.pos < end:
                            work.put((exc.pos, end))
                        strikes += 1
                        if args.verbose:
                            CON.log(f"[{wid}] strike {strikes}: {exc}")
                        with alock:
                            alone = len(active) <= 1
                            if not alone and strikes >= retire_after:
                                active.discard(wid)
                                retired[0] += 1
                                return
                        if alone and strikes >= last_limit:
                            if exc.status:
                                raise FatalError(f"持续被服务器拒绝 (HTTP {exc.status})") from exc
                            raise FatalError(str(exc)) from exc
                        if stop.wait(min(8.0, args.retry_gap / 1000 * (2 ** min(strikes, 4)))):
                            return
            except BaseException as exc:  # noqa: BLE001
                with err_lock:
                    errors.append(exc)
                stop.set()
            finally:
                with alock:
                    active.discard(wid)
                if fh:
                    fh.close()

        ths = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(1, nworkers + 1)]
        for th in ths:
            th.start()
        last_save = time.monotonic()
        while any(th.is_alive() for th in ths):
            time.sleep(0.2)
            if time.monotonic() - last_save > 2:
                persist()
                last_save = time.monotonic()

    try:
        nworkers = conns
        for _round in range(6):
            holes = missing_ranges(progress.snapshot(), size)
            if not holes or stop.is_set():
                break
            before = covered(progress.snapshot())
            pieces = split_ranges(holes, args.connections, args.min_chunk_size, args.max_chunk_size) if use_range else holes[:1]
            run_round(pieces, max(1, min(nworkers - retired[0], len(pieces))) if use_range else 1)
            if errors:
                break
            if covered(progress.snapshot()) <= before and _round >= 2:
                break
    except KeyboardInterrupt:
        stop.set()
        persist()
        painter.finish()
        CON.log(f"已中断, 未完成的文件已保留, 加 -c 可续传: {dest}")
        return Result("ERR", dest, size=size, error="interrupted", interrupted=True)

    painter.finish()
    persist()
    if retired[0]:
        CON.log(f"服务器限制并发: {retired[0]} 个连接被拒绝后退出, 实际并发约 {max(1, conns - retired[0])}")
    done = covered(progress.snapshot())
    if errors or done < size:
        err = str(errors[0]) if errors else "incomplete"
        left = size - done
        CON.log(f"下载失败: {item.url}\n原因: {err}")
        if left > 0:
            CON.log(f"还有 {format_size(left)} 未下载 ({done * 100 / size:.1f}% 已完成); 加 -c 续传, 若持续被拒绝请降低 -x")
        return Result("ERR", dest, size=size, error=err)
    if os.path.getsize(dest) != size:
        return Result("ERR", dest, size=size, error="文件大小校验失败")
    if os.path.isfile(ctrl):
        os.remove(ctrl)
    elapsed = max(time.monotonic() - started, 1e-6)
    wrote = size - covered(initial)
    return Result("OK", dest, speed=wrote / elapsed, size=size)


def cmd_dl(args: argparse.Namespace) -> int:
    net = Net(args)
    CON.log(f"gigafile.py v{VERSION}")
    results: list[Result] = []
    multi_url = len(args.urls) > 1
    if args.out and multi_url:
        CON.log("-o/--out 只能在单个 URL 时使用")
        return 2
    for url in args.urls:
        try:
            with net.request("GET", url) as r:
                if r.status == 404:
                    raise FatalError("页面不存在 (链接错误或已过期)")
                if r.status >= 400:
                    raise FatalError(f"页面返回 HTTP {r.status}")
                html = r.read(5_000_000).decode("utf-8", "replace")
            items = parse_page(html, url)
            if not items:
                raise FatalError("解析下载页失败 (文件可能已过期/被删除, 或网站改版)")
        except FatalError as exc:
            CON.log(f"下载失败: {url}\n原因: {exc}")
            results.append(Result("ERR", url, error=str(exc)))
            continue
        except Exception as exc:  # noqa: BLE001
            CON.log(f"下载失败: {url}\n原因: {exc}")
            results.append(Result("ERR", url, error=str(exc)))
            continue
        if len(items) > 1:
            CON.log(f"打包链接, 共 {len(items)} 个文件")
        for it in items:
            try:
                res = download_item(args, net, it, args.out if len(items) == 1 else None)
            except (FatalError, Exception) as exc:  # noqa: BLE001
                CON.log(f"下载失败: {it.name}\n原因: {exc}")
                res = Result("ERR", it.name, error=str(exc))
            results.append(res)
            if res.interrupted:
                break
        if results and results[-1].interrupted:
            break
    print_summary("Download Results:", results, with_url=False)
    return 0 if all(r.kind == "OK" for r in results) else 1


# ═════════════════════════════ CLI ═════════════════════════════


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-p", "--proxy", default=None, help='HTTP 代理, 如 http://127.0.0.1:7890; -p "" 表示不用代理 (默认读取系统/环境变量)')
    common.add_argument("-t", "--timeout", type=float, default=15, help="网络超时, 秒 (默认 15)")
    common.add_argument("-m", "--max-tries", type=int, default=8, help="单个分块/分片最大尝试次数 (默认 8)")
    common.add_argument("-y", "--yes", action="store_true", help="所有确认都选是")
    common.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    common.add_argument("--ascii", action="store_true", help="进度条只用 ASCII 字符 (中文 Windows 控制台进度条错位时使用)")
    common.add_argument("--insecure", action="store_true", help="不校验 HTTPS 证书")

    parser = argparse.ArgumentParser(
        prog="gigafile.py",
        description="gigafile.nu 上传 / 下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n  python gigafile.py upload movie.mkv\n  python gigafile.py upload movie.mkv -n 12\n  python gigafile.py dl -x16 -d D:\\down https://66.gigafile.nu/xxxx\n  python gigafile.py dl -c -x16 URL    (断点续传)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="{upload,dl}")

    up = sub.add_parser("upload", aliases=["up", "u"], parents=[common], help="上传文件")
    up.add_argument("files", nargs="+", metavar="FILE", help="要上传的文件 (也可以是目录, 会逐个上传其中的文件)")
    up.add_argument("-n", "--threads", "--thread-num", dest="threads", type=int, default=16, help="并发上传线程数 (默认 16)")
    up.add_argument("-s", "--chunk-size", default="30MB", help="分块大小, 如 50MB (默认 30MB; auto 表示按文件大小自动选 16~100MB)")
    up.add_argument("-l", "--lifetime", type=int, default=100, help="保存天数 (默认 100)")

    dl = sub.add_parser("dl", aliases=["download", "d", "get"], parents=[common], help="下载文件")
    dl.add_argument("urls", nargs="+", metavar="URL", help="gigafile 下载链接, 可以多个")
    dl.add_argument("-x", "--max-connection-per-server", "--connections", dest="connections", type=int, default=16, help="并发连接数 (默认 16), 例如 -x16")
    dl.add_argument("-d", "--dir", dest="directory", default=".", help="保存目录 (默认 当前目录)")
    dl.add_argument("-o", "--out", default=None, help="自定义文件名 (仅单个文件)")
    dl.add_argument("-c", "--continue", dest="cont", action="store_true", default=True, help="断点续传 (默认已开启); 已下完的文件会直接跳过")
    dl.add_argument("--no-continue", dest="cont", action="store_false", help="关闭断点续传: 文件已存在时询问是否覆盖")
    dl.add_argument("-f", "--force", action="store_true", help="强制覆盖已有文件")
    dl.add_argument("-H", "--header", dest="headers", action="append", default=[], metavar="Key: Value", help="自定义请求头, 可重复")
    dl.add_argument("--user-agent", default=None, help="自定义 User-Agent")
    dl.add_argument("--referer", default=None, help="自定义 Referer")
    dl.add_argument("--min-chunk-size", type=parse_size, default=1 << 20, help="最小分片 (默认 1MB)")
    dl.add_argument("--max-chunk-size", type=parse_size, default=64 << 20, help="最大分片 (默认 64MB), 0 不限")
    dl.add_argument("--retire-after", type=int, default=3, help="单连接连续失败几次后退出以降低并发 (默认 3)")
    dl.add_argument("--retry-gap", type=int, default=500, help="重试间隔, 毫秒 (默认 500)")
    return parser


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    CON.ascii = bool(args.ascii or os.environ.get("FD_ASCII"))
    args.cmd = {"up": "upload", "u": "upload", "download": "dl", "d": "dl", "get": "dl"}.get(args.cmd, args.cmd)
    if args.max_tries < 1:
        print("-m 必须 >= 1", file=sys.stderr)
        return 2
    try:
        if args.cmd == "upload":
            if args.threads < 1:
                print("-n 必须 >= 1", file=sys.stderr)
                return 2
            return cmd_upload(args)
        if args.connections < 1:
            print("-x 必须 >= 1", file=sys.stderr)
            return 2
        return cmd_dl(args)
    except FatalError as exc:
        CON.log(f"错误: {exc}")
        return 1
    except KeyboardInterrupt:
        CON.end_line()
        return 130


if __name__ == "__main__":
    sys.exit(main())
