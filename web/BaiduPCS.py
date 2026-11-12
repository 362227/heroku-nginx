#!/usr/bin/env python3
# baidu-upload.py: 百度网盘开放平台 (xpan + access_token) 上传。
# 分片、并发、重名策略、速度显示与之前的 Go 版一致；不用 BDUSS。
#
# 基本用法:
#   python3 baidu-upload.py -file ./a.zip -dest /备份/ -parallel 40 -norapid
#   python3 baidu-upload.py -file '/content/gofile-dl/bd/*.*' -dest /备份/
#   python3 baidu-upload.py -file ./a.zip -dest /备份/ -v        # 详细模式: 每个分片进度/实时速度/重试情况
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
# 分片: <8GB 用 4MB，>=8GB 用 16MB，>=32GB 用 64MB; 单文件最多 100 片, 超过就自动加大分片。
#
# -v 详细模式会额外打印:
#   - 每个分片的开始/完成 (大小、用时、速度、线路), 失败原因与重试 (第几次、换到哪条线路、等待多久)
#   - 每 3 秒列出所有正在上传的分片: 实时速度、重试次数、本次用时 (等待重试的分片也会列出)
#   - 每 20 秒一行文件总进度: 百分比、实时速度、平均速度、活跃分片数、已完成分片数、重试数、总用时、ETA
#   - 文件大小/分片数、存在性检查、precreate、create、校验等各步骤信息
#   - 被排除的文件及原因 / 被包含的文件

import argparse
import collections
import glob
import hashlib
import json
import os
import posixpath
import re
import socket
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
FIXED_HOST = "https://c2.pcs.baidu.com"
SLICE_RETRY = 8
MAX_SLICES = 1000  # 单个文件最多切成多少个分片
DEFAULT_PREFER = "c2,c5,d"  # 智能择优: 优先测试的线路
PREFER_STRIKES = 3  # 优先线路连续这么多轮不如主线路, 就不再优先
SWITCH_MARGIN = 1.15  # 测速线路要比主线路快 15% 以上才切换
MIN_MAIN_SAMPLES = 3  # 主线路至少有这么多个分片样本才做比较
MIN_PROBE_SAMPLES = 2  # 测速线路至少有这么多个样本才有资格当主线路
MAX_CANDIDATES = 8
HOST_COOLDOWN = 300  # 线路连续失败后冷却秒数
SPEED_WINDOW = 4.0  # 实时速度的滑动窗口秒数
QUIET = False  # 多文件并发时关闭每个文件各自的 \r 进度行
VERBOSE = False  # -v: 详细输出
PRINT_LOCK = threading.Lock()


EXPIRED_CODES = (-6, 110, 111, 20016)  # token 无效/过期 (20016: nas access token expired)


class TokenExpired(RuntimeError):
    pass


def log(fid, msg):
    """带时间戳的整行日志, 多线程下不会串行。"""
    ts = time.strftime("%H:%M:%S")
    with PRINT_LOCK:
        print("%s [%s] %s" % (ts, fid, msg))
        sys.stdout.flush()


def log_lines(fid, msgs):
    """一次锁住多行, 避免同一文件的分片进度被别的线程插开。"""
    if not msgs:
        return
    ts = time.strftime("%H:%M:%S")
    with PRINT_LOCK:
        for msg in msgs:
            print("%s [%s] %s" % (ts, fid, msg))
        sys.stdout.flush()


def vlog(fid, msg):
    if VERBOSE:
        log(fid, msg)


class Meter:
    """字节计数 + 滑动窗口实时速度。add() 可传负数 (分片失败时回滚已计字节)。"""

    def __init__(self, window=SPEED_WINDOW):
        self.lock = threading.Lock()
        self.total = 0
        self.window = window
        self.samples = collections.deque([(time.time(), 0)])

    def add(self, n):
        with self.lock:
            self.total += n

    def rate(self):
        """采样一次并返回窗口内平均速度 (B/s); 建议每秒调用一次。"""
        now = time.time()
        with self.lock:
            self.samples.append((now, self.total))
            while len(self.samples) > 2 and self.samples[1][0] <= now - self.window:
                self.samples.popleft()
            t0, b0 = self.samples[0]
            dt = now - t0
            if dt < 0.3:
                return 0.0
            return max(0.0, (self.total - b0) / dt)


G_METER = Meter()  # 所有文件的全局已发送字节


def norm_host(h):
    h = (h or "").strip()
    if not h:
        return ""
    if "://" not in h:
        if "." not in h:
            h = "%s.pcs.baidu.com" % h  # c2 -> c2.pcs.baidu.com
        h = "https://" + h
    u = urllib.parse.urlparse(h)
    if not u.hostname:
        return ""
    return "%s://%s" % ("https" if u.scheme == "http" else (u.scheme or "https"), u.hostname)


def short_host(h):
    n = urllib.parse.urlparse(h).hostname or h
    return n[:-len(".pcs.baidu.com")] if n.endswith(".pcs.baidu.com") else n


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


class LineSelector:
    """智能择优线路: 始终有 slots 个分片在轮流测速, 其余分片走主线路; 测速最快且明显超过主线路就切换。"""

    def __init__(self, main, prefer, slots):
        self.lock = threading.Lock()
        self.main = main
        self.slots = slots
        self.probing = 0
        self.main_win = collections.deque(maxlen=15)
        self.stats = {}
        self.hints = []
        prefer = [norm_host(x) for x in prefer if norm_host(x)]
        for h in prefer:
            self.add(h, True)
        self.add(main)
        self.add(FIXED_HOST)

    def add(self, h, prefer=False):
        h = norm_host(h)
        if not h or h in self.stats or len(self.stats) >= MAX_CANDIDATES:
            return
        self.stats[h] = {"probe": collections.deque(maxlen=3), "n": 0, "slow": 0, "cons_fail": 0, "fails": 0,
                         "dead_until": 0.0, "prefer": prefer, "bytes": 0, "time": 0.0, "ok": 0}
        self.hints.append(h)

    def add_hosts(self, hosts):
        with self.lock:
            for h in hosts or []:
                self.add(h)

    def _speed(self, h):
        return mean(self.stats[h]["probe"])

    def _pick_probe(self):
        now = time.time()
        cands = [h for h in self.hints if h != self.main and self.stats[h]["dead_until"] <= now]
        if not cands:
            return None

        def key(h):
            st = self.stats[h]
            return (st["n"] / (2.0 if st["prefer"] else 1.0), self.hints.index(h))  # 优先线路测得更勤
        h = min(cands, key=key)
        self.stats[h]["n"] += 1
        return h

    def assign(self):
        with self.lock:
            if self.probing < self.slots:
                h = self._pick_probe()
                if h:
                    self.probing += 1
                    return h, "probe"
            return self.main, "main"

    def release(self, role):
        if role == "probe":
            with self.lock:
                self.probing -= 1

    def order(self, first=None):
        with self.lock:
            now = time.time()
            rest = sorted([h for h in self.hints if h != self.main and self.stats[h]["dead_until"] <= now],
                          key=lambda h: -self._speed(h))
            out = []
            for h in [first, self.main] + rest:
                if h and h not in out:
                    out.append(h)
            return out or [self.main]

    def _switch(self, new, why):
        old = self.main
        if self.main_win:
            m = mean(self.main_win)
            self.stats[old]["probe"].extend([m, m])  # 让旧主线路以后还能被比较
        self.main = new
        self.main_win.clear()
        with PRINT_LOCK:
            print("%s [smart] 主线路切换: %s -> %s (%s)" % (time.strftime("%H:%M:%S"), short_host(old), short_host(new), why))

    def _replace_main(self):
        now = time.time()
        cands = [h for h in self.hints if h != self.main and self.stats[h]["dead_until"] <= now]
        if cands:
            cands.sort(key=lambda h: (-self._speed(h), self.hints.index(h)))
            self._switch(cands[0], "原主线路不可用")

    def fallback_from(self, host):
        with self.lock:
            host = norm_host(host)
            if host in self.stats:
                self.stats[host]["dead_until"] = time.time() + HOST_COOLDOWN
                self.stats[host]["cons_fail"] = 3
            if self.main == host:
                self._replace_main()

    def record(self, host, nbytes, elapsed, ok, role):
        with self.lock:
            st = self.stats.get(host)
            if st is None:
                return
            if not ok:
                st["fails"] += 1
                st["cons_fail"] += 1
                if st["cons_fail"] >= 3:
                    st["dead_until"] = time.time() + HOST_COOLDOWN
                    if VERBOSE:
                        print("%s [smart] 线路 %s 连续失败 %d 次, 冷却 %d 秒" % (
                            time.strftime("%H:%M:%S"), short_host(host), st["cons_fail"], HOST_COOLDOWN))
                    if host == self.main:
                        self._replace_main()
                if role == "probe" and st["prefer"]:
                    st["slow"] += 1
                    if st["slow"] >= PREFER_STRIKES:
                        st["prefer"] = False
                        print("[smart] %s 连续 %d 轮测速失败/偏慢, 不再优先测试" % (short_host(host), PREFER_STRIKES))
                return
            st["cons_fail"] = 0
            speed = nbytes / max(elapsed, 1e-3)
            st["ok"] += 1
            st["bytes"] += nbytes
            st["time"] += elapsed
            if role == "main":
                if host == self.main:
                    self.main_win.append(speed)
                return
            if role != "probe":
                return
            st["probe"].append(speed)
            if VERBOSE:
                print("%s [smart] 测速 %s: %s/s (主线路 %s: %s/s)" % (
                    time.strftime("%H:%M:%S"), short_host(host), convert_size(speed, 1), short_host(self.main),
                    convert_size(mean(self.main_win), 1) if self.main_win else "?"))
            if len(self.main_win) < MIN_MAIN_SAMPLES:
                return
            main_mean = mean(self.main_win)
            if st["prefer"]:
                st["slow"] = st["slow"] + 1 if speed < main_mean else 0
                if st["slow"] >= PREFER_STRIKES:
                    st["prefer"] = False
                    print("[smart] %s 连续 %d 轮不如主线路, 不再优先测试" % (short_host(host), PREFER_STRIKES))
            now = time.time()
            best, best_speed = None, 0.0
            for h, s in self.stats.items():
                if h == self.main or s["dead_until"] > now or len(s["probe"]) < MIN_PROBE_SAMPLES:
                    continue
                sp = mean(s["probe"])
                if sp > best_speed:
                    best, best_speed = h, sp
            if best and best_speed > main_mean * SWITCH_MARGIN:
                self._switch(best, "测速 %s/s > 主线路 %s/s" % (convert_size(best_speed, 1), convert_size(main_mean, 1)))

    def note_live(self, host, speed):
        """用进行中的分片速度更新择优, 不必等一整片传完。"""
        if speed <= 0:
            return
        with self.lock:
            host = norm_host(host)
            st = self.stats.get(host)
            if st is None:
                return
            if host == self.main:
                self.main_win.append(speed)
            else:
                st["probe"].append(speed)
            if len(self.main_win) < MIN_MAIN_SAMPLES:
                return
            main_mean = mean(self.main_win)
            if main_mean <= 0:
                return
            now = time.time()
            best, best_speed = None, 0.0
            for h, s in self.stats.items():
                if h == self.main or s["dead_until"] > now or len(s["probe"]) < MIN_PROBE_SAMPLES:
                    continue
                sp = mean(s["probe"])
                if sp > best_speed:
                    best, best_speed = h, sp
            if best and best_speed > main_mean * SWITCH_MARGIN:
                self._switch(best, "实时 %s/s > 主线路 %s/s" % (convert_size(best_speed, 1), convert_size(main_mean, 1)))

    def summary(self):
        with self.lock:
            lines = []
            for h in self.hints:
                st = self.stats[h]
                if st["ok"] or st["fails"]:
                    avg = st["bytes"] / st["time"] if st["time"] else 0
                    lines.append("%s%s: 平均 %s/s, 成功 %d 片, 失败 %d 次" % (
                        short_host(h), "(主)" if h == self.main else "", convert_size(avg, 1), st["ok"], st["fails"]))
            return lines


class SliceBody:
    """分片请求体: 边读文件边发送, 不把整片装进内存 (multipart 头 + 文件片段 + 尾)。
    每读出一块文件数据就回调 progress(n), 用来得到真实的实时上传字节数。"""

    def __init__(self, path, offset, n, head, tail, progress=None, cancel=None, deadline=None):
        self.f = open(path, "rb")
        self.f.seek(offset)
        self.left = n
        self.head, self.tail = head, tail
        self.length = len(head) + n + len(tail)
        self.progress = progress
        self.cancel = cancel
        self.deadline = deadline
        self.sent = 0  # 本次尝试已发出的文件字节数

    def _check_cancel(self):
        if self.deadline and time.time() >= self.deadline:
            raise TimeoutError("超过分片时限")
        if self.cancel is not None and self.cancel.is_set():
            raise TimeoutError(self.cancel.reason or "分片尝试被中断")

    def read(self, size=-1):
        self._check_cancel()
        if size is None or size < 0:
            size = self.length
        out = b""
        if self.head:
            out, self.head = self.head[:size], self.head[size:]
            size -= len(out)
        if size > 0 and self.left > 0:
            chunk = self.f.read(min(size, self.left))
            if not chunk:
                raise IOError("读取本地文件失败 (文件被截断?)")
            self.left -= len(chunk)
            self.sent += len(chunk)
            if self.progress:
                self.progress(len(chunk))
            out += chunk
            size -= len(chunk)
        if size > 0 and self.left == 0 and self.tail:
            t, self.tail = self.tail[:size], self.tail[size:]
            out += t
        return out

    def close(self):
        self.f.close()


def slice_md5(path, offset, n):
    h = hashlib.md5()
    with open(path, "rb") as f:
        f.seek(offset)
        left = n
        while left > 0:
            chunk = f.read(min(MB, left))
            if not chunk:
                break
            h.update(chunk)
            left -= len(chunk)
    return h.hexdigest()


class Cancel:
    def __init__(self):
        self._ev = threading.Event()
        self.reason = ""

    def set(self, reason):
        if not self.reason:
            self.reason = reason
        self._ev.set()

    def is_set(self):
        return self._ev.is_set()


class Inflight:
    """正在发送的分片。单次时限一到就中断换线, 不管还在不在出数据。"""

    def __init__(self):
        self.lock = threading.Lock()
        self.items = {}
        self.tick = 0
        self.explained = False

    def begin(self, seq, host, cancel, size, budget=None):
        now = time.time()
        with self.lock:
            self.items[seq] = {
                "host": norm_host(host) or host,
                "cancel": cancel,
                "t0": now,
                "last": now,
                "sent": 0,
                "size": size,
                "budget": budget,
            }

    def add(self, seq, n):
        if n <= 0:
            return
        with self.lock:
            st = self.items.get(seq)
            if not st or st["cancel"].is_set():
                return
            st["sent"] += n
            st["last"] = time.time()

    def end(self, seq):
        with self.lock:
            self.items.pop(seq, None)

    def poll(self, timeout, sel, log_fn=None, total=0):
        if not timeout or timeout <= 0:
            return
        now = time.time()
        self.tick += 1
        with self.lock:
            notes, by_host = [], {}
            for seq, st in self.items.items():
                if st["cancel"] is None or st["cancel"].is_set():
                    continue
                el = now - st["t0"]
                idle = now - st["last"]
                spd = st["sent"] / el if el >= 0.3 else 0.0
                if el >= 5 and spd > 0:
                    by_host.setdefault(st["host"], []).append(spd)
                budget = st.get("budget") or timeout
                if budget and el >= budget:
                    # 到了本次时限就换线, 不管还在不在出数据
                    st["cancel"].set("超过时限 %ds" % int(budget))
                    notes.append((seq, "deadline", st["host"], spd, el, budget))
                elif idle >= timeout:
                    st["cancel"].set("超过 %d 秒没有新数据" % int(timeout))
                    notes.append((seq, "stall", st["host"], spd, el, timeout))
        if sel and self.tick % 5 == 0:
            for h, spds in by_host.items():
                sel.note_live(h, mean(spds))
        if not log_fn:
            return
        for note in notes:
            seq, kind, host, spd, el, limit = note
            if kind == "stall":
                log_fn("分片 %d/%d 超过 %ds 没有新数据 (速度 %s/s, 线路 %s), 换线重试" % (
                    seq + 1, total or (seq + 1), int(limit), convert_size(spd, 1), short_host(host)))
            else:
                log_fn("分片 %d/%d 超过时限 %ds 仍未完成 (速度 %s/s, 线路 %s, 用时 %s), 换线重试" % (
                    seq + 1, total or (seq + 1), int(limit), convert_size(spd, 1), short_host(host), fmt_elapsed(el)))


def is_timeout(e):
    if isinstance(e, (socket.timeout, TimeoutError)):
        return True
    if isinstance(e, urllib.error.URLError) and isinstance(getattr(e, "reason", None), (socket.timeout, TimeoutError)):
        return True
    return "timed out" in str(e).lower()


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
        base = MAX_BLOCK
    elif size >= MID_THRESHOLD:
        base = MID_BLOCK
    else:
        base = MIN_BLOCK
    if block_count(size, base) > MAX_SLICES:  # 分片数最多 MAX_SLICES, 超过就加大分片, 按 MB 向上取整
        need = -(-size // MAX_SLICES)
        base = -(-need // MB) * MB
    return base


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


def fmt_elapsed(sec):
    sec = max(0, sec)
    if sec >= 3600:
        s = int(sec)
        return "%dh%dm%ds" % (s // 3600, (s % 3600) // 60, s % 60)
    if sec >= 60:
        s = int(sec)
        return "%dm%ds" % (s // 60, s % 60)
    return "%.1fs" % sec


def err_text(e, n=160):
    if isinstance(e, ApiError):
        return "errno=%s %s" % (e.code, truncate(e.body, n))
    return "%s: %s" % (type(e).__name__, truncate(str(e), n))


class Client:
    def __init__(self, cfg_path, parallel=4, rotate_host=False, norefresh=False, slice_timeout=60.0,
                 line_host=None, smart=True, prefer=DEFAULT_PREFER, probes=0):
        self.cfg_path = cfg_path
        self.parallel = parallel if parallel > 0 else 20
        self.rotate_host = rotate_host
        self.norefresh = norefresh
        self.slice_timeout = slice_timeout if slice_timeout and slice_timeout > 0 else None
        self.lock = threading.Lock()
        self.refreshed_at = 0.0
        self.user_line = bool(norm_host(line_host)) and not rotate_host  # 用户指定了线路
        self.line_host = norm_host(line_host) if self.user_line else FIXED_HOST
        self.smart = bool(smart) and not rotate_host and self.parallel >= 2
        self.selector = None
        if self.smart:
            slots = probes if probes and probes > 0 else max(1, min(5, self.parallel // 4))
            slots = min(slots, max(1, self.parallel - 1))
            self.selector = LineSelector(self.line_host, [x for x in str(prefer or "").split(",") if x.strip()], slots)
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
                if VERBOSE:
                    print("%s [token] 需要刷新 access_token (force=%s)" % (time.strftime("%H:%M:%S"), force),
                          file=sys.stderr)
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
                if VERBOSE:
                    print("%s [token] 接口返回 token 过期 (errno=%s), 重新获取后重试" % (time.strftime("%H:%M:%S"), code),
                          file=sys.stderr)
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

    def post_slice(self, host, remote, upload_id, seq, src, progress, cancel=None, deadline=None):
        local, offset, n = src
        q = urllib.parse.urlencode({
            "method": "upload", "access_token": self.cfg["access_token"],
            "type": "tmpfile", "path": remote, "uploadid": upload_id, "partseq": str(seq),
        })
        boundary = "----baidu%s" % hashlib.md5(os.urandom(8)).hexdigest()
        head = ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"file\"\r\n"
                "Content-Type: application/octet-stream\r\n\r\n" % boundary).encode()
        tail = ("\r\n--%s--\r\n" % boundary).encode()
        url = host.rstrip("/") + "/rest/2.0/pcs/superfile2?" + q
        body = SliceBody(local, offset, n, head, tail, progress, cancel, deadline)
        ok = False
        try:
            status, resp = self._request("POST", url, body, {
                "Content-Type": "multipart/form-data; boundary=%s" % boundary,
                "Content-Length": str(body.length),
            }, timeout=self.slice_timeout)
            if status >= 400 and not resp:
                raise RuntimeError("HTTP %d 空响应" % status)
            code, parsed = parse_api_code(resp)
            if not parsed:
                raise RuntimeError("百度接口返回无法解析: HTTP %d %s" % (status, truncate(resp)))
            if code != 0:
                raise ApiError(code, resp.decode("utf-8", "replace"))
            ok = True
            return resp
        finally:
            body.close()
            if not ok and body.sent and progress:
                progress(-body.sent)  # 失败: 回滚这次尝试已计入的字节, 重试时不会重复统计

    def upload_slice(self, remote, upload_id, seq, src, progress, hosts, hosts_cb=None, report=None, rotate=False,
                     lg=None, on_retry=None, total=0, tag="", on_attempt=None, on_wait=None):
        hosts = hosts or [self.line_host]
        idx = 0
        last = None
        n = src[2]
        label = "分片 %d/%d" % (seq + 1, total) if total else "分片 %d" % (seq + 1)
        for i in range(SLICE_RETRY):
            if i > 0 and isinstance(last, ApiError) and last.code in EXPIRED_CODES:
                self.ensure_token(True)
            else:
                self.ensure_token(False)
            host = hosts[idx % len(hosts)]
            t0 = time.time()
            # 每一次尝试都是同一个时限, 到点就换线, 不随重试次数放宽
            limit = self.slice_timeout if self.slice_timeout else None
            deadline = (t0 + limit) if limit else None
            cancel = Cancel()
            if on_attempt:
                on_attempt(host, i, cancel, limit)
            if lg:
                lg("%s 开始 %s 线路 %s%s 第 %d/%d 次%s" % (
                    label, convert_size(n, 2), short_host(host), (" (%s)" % tag) if tag and i == 0 else "",
                    i + 1, SLICE_RETRY, (" 时限 %ds" % int(limit)) if limit else ""))
            try:
                body = self.post_slice(host, remote, upload_id, seq, src, progress, cancel, deadline)
                el = time.time() - t0
                if report:
                    report(host, n, el, True, i)
                md5 = ""
                try:
                    md5 = json.loads(body).get("md5") or ""
                except Exception:
                    pass
                if lg:
                    lg("%s 完成 %s 用时 %.1fs 速度 %s/s 线路 %s%s" % (
                        label, convert_size(n, 2), el, convert_size(n / max(el, 1e-3), 2), short_host(host),
                        " (重试 %d 次后成功)" % i if i else ""))
                return md5 or slice_md5(*src)
            except Exception as e:
                last = e
                el = time.time() - t0
                if report and not isinstance(e, ApiError):  # 接口有响应说明线路通, 不算线路问题
                    report(host, 0, el, False, i)
                if isinstance(e, ApiError) and (e.code in (400, 413, 31024, 31364) or (self.norefresh and e.code in EXPIRED_CODES)):
                    if lg:
                        lg("%s 失败 (不可重试): %s" % (label, err_text(e)))
                    raise
                timed_out = is_timeout(e)
                if timed_out:
                    # 超时一定换服务器: 先拿最新列表, 再切到当前之后的下一个
                    if hosts_cb:
                        hosts = hosts_cb() or hosts
                    idx = (hosts.index(host) + 1) % len(hosts) if host in hosts else 0
                elif self.rotate_host or rotate:
                    idx += 1
                nxt = hosts[idx % len(hosts)]
                last_try = (i == SLICE_RETRY - 1)
                if on_retry and not last_try:
                    on_retry()
                if lg:
                    if last_try:
                        lg("%s 第 %d/%d 次失败 [用时 %.1fs]: %s | 已用完重试次数, 放弃" % (
                            label, i + 1, SLICE_RETRY, el, err_text(e)))
                    else:
                        lg("%s 第 %d/%d 次失败 [用时 %.1fs]: %s | 线路 %s%s | %d 秒后重试" % (
                            label, i + 1, SLICE_RETRY, el, err_text(e), short_host(host),
                            (" -> 切换 %s" % short_host(nxt)) if nxt != host else "", (i + 1) * 2))
                elif timed_out:
                    print("分片 %d 超时 (%s 秒), 第 %d/%d 次, 切换服务器 %s -> %s" % (
                        seq, self.slice_timeout, i + 1, SLICE_RETRY, short_host(host), short_host(nxt)))
                if not last_try:
                    if on_wait:
                        on_wait(el)
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
                vlog(fid, "校验重试 %d/5 ..." % (i + 1))
            try:
                listing = self.list_dir(directory)
            except Exception as e:
                last = e
                vlog(fid, "读取目录失败: %s" % err_text(e))
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
        total_slices = len(blocks)
        if not need:
            need = list(range(len(blocks)))
        need = [x for x in need if 0 <= x < len(blocks)]
        size = sums["size"]
        block = sums["block"]
        host_lock = threading.Lock()
        host_list = [self.line_host]
        host_at = 0.0
        done_seqs = set()
        st_lock = threading.Lock()
        state = {"active": 0, "done": 0, "retries": 0}
        meter = Meter()
        todo_bytes = sum(min(block, max(0, size - s * block)) for s in need)
        pre_done = size - todo_bytes  # 秒传/断点续传时已经在网盘上的字节
        start = time.time()
        sel = self.selector
        lg = (lambda m: log(fid, m)) if VERBOSE else None

        if VERBOSE:
            log(fid, "开始分片上传: 共 %d 片, 需上传 %d 片 (%s), 并发 %d, 分片大小 %s, uploadid=%s" % (
                total_slices, len(need), convert_size(todo_bytes, 2), self.parallel, convert_size(block, 2), upload_id))

        def progress(n):
            meter.add(n)
            G_METER.add(n)

        def on_retry():
            with st_lock:
                state["retries"] += 1

        # -v: 每个正在上传的分片单独计时/计字节, 供每 3 秒打印实时速度
        live_lock = threading.Lock()
        live = {}
        inflight = Inflight()

        def slice_add(seq, n):
            meter.add(n)
            G_METER.add(n)
            with live_lock:
                st = live.get(seq)
                if st is None or st["waiting"]:
                    return
                if n < 0:
                    st["sent"] = max(0, st["sent"] + n)
                    st["samples"].clear()
                    st["samples"].append((time.time(), st["sent"]))
                else:
                    st["sent"] += n

        def slice_begin(seq, host, attempt, nbytes):
            now = time.time()
            with live_lock:
                live[seq] = {
                    "host": short_host(host),
                    "attempt": attempt,
                    "size": nbytes,
                    "sent": 0,
                    "t0": now,
                    "last_el": 0.0,
                    "samples": collections.deque([(now, 0)]),
                    "waiting": False,
                }

        def slice_wait(seq, elapsed):
            with live_lock:
                st = live.get(seq)
                if st and not st["waiting"]:
                    st["waiting"] = True
                    st["last_el"] = elapsed
                    st["attempt"] += 1

        def slice_end(seq):
            with live_lock:
                live.pop(seq, None)

        def sample_live(now):
            rows = []
            with live_lock:
                for seq, st in live.items():
                    spd_s = 0.0
                    if not st["waiting"]:
                        st["samples"].append((now, st["sent"]))
                        while len(st["samples"]) > 2 and st["samples"][1][0] <= now - SPEED_WINDOW:
                            st["samples"].popleft()
                        t0s, b0 = st["samples"][0]
                        dt = now - t0s
                        if dt >= 0.3:
                            spd_s = max(0.0, (st["sent"] - b0) / dt)
                    rows.append((seq, st["host"], st["attempt"], st["sent"], st["size"],
                                 spd_s, now - st["t0"], st["last_el"], st["waiting"]))
            rows.sort(key=lambda r: r[0])
            return rows

        def pick_host(seq, force=False):
            nonlocal host_list, host_at
            if not self.rotate_host and not force:
                return [self.line_host]
            with host_lock:
                if time.time() - host_at > 30 or not host_list or host_at == 0:
                    try:
                        fresh = self.locate_upload(remote, upload_id)
                        if fresh:
                            host_list = fresh
                            host_at = time.time()
                            print("[%s] 上传服务器列表: %s" % (fid, ", ".join(fresh)))
                    except Exception:
                        pass
                n = len(host_list)
                return [host_list[(seq + i) % n] for i in range(n)] or [self.line_host]

        def run_phase(seqs, smart_mode):
            stop = threading.Event()
            err = [None]

            def worker(seq):
                if stop.is_set():
                    return
                off = seq * block
                n = min(block, max(0, size - off))
                src = (local, off, n)
                with st_lock:
                    state["active"] += 1

                def progress_one(nbytes, seq=seq):
                    if VERBOSE:
                        slice_add(seq, nbytes)
                    else:
                        progress(nbytes)
                    if nbytes > 0:
                        inflight.add(seq, nbytes)

                def began(host, attempt, cancel=None, limit=None, seq=seq, nbytes=n):
                    if cancel is not None:
                        inflight.begin(seq, host, cancel, nbytes, limit)
                    if VERBOSE:
                        slice_begin(seq, host, attempt, nbytes)

                def waited(elapsed, seq=seq):
                    if VERBOSE:
                        slice_wait(seq, elapsed)

                hooks = {"on_attempt": began, "on_wait": waited}
                try:
                    if smart_mode:
                        host, role = sel.assign()
                        try:
                            def report(h, nbytes, elapsed, ok, attempt, role=role):
                                sel.record(h, nbytes, elapsed, ok, role if attempt == 0 else "retry")
                            md5 = self.upload_slice(remote, upload_id, seq, src, progress_one, sel.order(host),
                                                    lambda: sel.order(None), report, True,
                                                    lg=lg, on_retry=on_retry, total=total_slices,
                                                    tag="测速" if role == "probe" else "主线路", **hooks)
                        finally:
                            sel.release(role)
                    else:
                        md5 = self.upload_slice(remote, upload_id, seq, src, progress_one, pick_host(seq),
                                                lambda: pick_host(seq, True),
                                                lg=lg, on_retry=on_retry, total=total_slices, **hooks)
                except Exception as e:
                    if err[0] is None:
                        err[0] = RuntimeError("分片 %d 上传失败: %s" % (seq, e))
                        stop.set()
                    return
                finally:
                    inflight.end(seq)
                    if VERBOSE:
                        slice_end(seq)
                    with st_lock:
                        state["active"] -= 1
                blocks[seq] = md5
                with st_lock:
                    done_seqs.add(seq)
                    state["done"] += 1

            with ThreadPoolExecutor(max_workers=self.parallel) as pool:
                futs = [pool.submit(worker, x) for x in seqs]
                for fut in as_completed(futs):
                    fut.result()
            return err[0]

        pstop = threading.Event()

        def printer():
            # 每秒采样一次算实时速度.
            # -v: 每 3 秒打印所有正在上传的分片, 每 20 秒打印一行文件总进度.
            # 普通模式每秒刷新 \r 行.
            tick = 0
            while not pstop.wait(1):
                spd = meter.rate()
                tick += 1
                now = time.time()
                if VERBOSE:
                    rows = sample_live(now)
                    if tick % 3 == 0:
                        lines = []
                        for seq, host, attempt, sent_b, sl_size, sspd, el, last_el, waiting in rows:
                            label = "分片 %d/%d" % (seq + 1, total_slices)
                            if waiting:
                                lines.append("%s 等待重试 重试 %d 次 上次用时 %s 线路 %s" % (
                                    label, attempt, fmt_elapsed(last_el), host))
                            else:
                                lines.append("%s 实时 %s/s 重试 %d 次 本次用时 %s 线路 %s 已传 %s/%s" % (
                                    label, convert_size(sspd, 2), attempt, fmt_elapsed(el), host,
                                    convert_size(max(sent_b, 0), 2), convert_size(sl_size, 2)))
                        log_lines(fid, lines)
                    if tick % 20 == 0:
                        sent = min(size, pre_done + max(meter.total, 0))
                        with st_lock:
                            act, dn, rt = state["active"], state["done"], state["retries"]
                        avg = meter.total / max(now - start, 1e-3)
                        remain = size - sent
                        eta = fmt_elapsed(remain / spd) if spd > 1024 else "--"
                        log(fid, "↑ %s/%s (%.1f%%) 实时 %s/s 平均 %s/s 活跃 %d 片 完成 %d/%d 重试 %d 次 用时 %s ETA %s" % (
                            convert_size(sent, 2), convert_size(size, 2), sent * 100.0 / size if size else 100.0,
                            convert_size(spd, 2), convert_size(avg, 2), act, dn, len(need), rt,
                            fmt_elapsed(now - start), eta))
                else:
                    sent = min(size, pre_done + max(meter.total, 0))
                    sys.stdout.write("\r[%s] ↑ %s/%s %s/s in %s ............" % (
                        fid, convert_size(sent, 2), convert_size(size, 2),
                        convert_size(spd, 2), fmt_elapsed(now - start)))
                    sys.stdout.flush()

        def guard():
            while not pstop.wait(1):
                inflight.poll(self.slice_timeout, sel, lambda m: log(fid, m), total_slices)

        t = threading.Thread(target=printer, daemon=True)
        g = threading.Thread(target=guard, daemon=True)
        g.start()
        if VERBOSE or not QUIET:
            t.start()

        def learn_hosts():
            if sel:
                try:
                    hs = self.locate_upload(remote, upload_id)
                    sel.add_hosts(hs)
                    vlog(fid, "locateupload 返回线路: %s" % ", ".join(short_host(h) for h in hs))
                except Exception as e:
                    vlog(fid, "locateupload 失败: %s" % err_text(e))

        # 没指定线路: 一开始就智能择优; 指定了线路: 先走指定线路, 整体失败才启用智能择优
        smart_first = sel is not None and not self.user_line
        if smart_first:
            learn_hosts()
        err = run_phase(need, smart_first)
        if err and sel is not None and self.user_line:
            left = [x for x in need if x not in done_seqs]
            print("\n[%s] 指定线路 %s 整体上传失败 (%s), 不判失败, 启用智能择优线路继续上传剩余 %d 个分片" % (
                fid, short_host(self.line_host), err, len(left)))
            sel.fallback_from(self.line_host)
            learn_hosts()
            err = run_phase(left, True)

        pstop.set()
        elapsed = time.time() - start
        avg = max(meter.total, 0) / max(elapsed, 1e-3)
        g.join(timeout=1.5)
        if t.ident is not None:
            t.join(timeout=1.5)
        if VERBOSE:
            with st_lock:
                dn, rt = state["done"], state["retries"]
            log(fid, "分片阶段%s: 完成 %d/%d 片, 重试 %d 次, 用时 %s, 平均 %s/s" % (
                "失败" if err else "结束", dn, len(need), rt, fmt_elapsed(elapsed), convert_size(avg, 2)))
        elif not QUIET:
            uploaded = size if err is None else min(size, pre_done + max(meter.total, 0))
            sys.stdout.write("\r[%s] ↑ %s/%s 平均 %s/s in %s ............\n" % (
                fid, convert_size(uploaded, 2), convert_size(size, 2),
                convert_size(avg, 2), fmt_elapsed(elapsed)))
        if err:
            raise err
        vlog(fid, "调用 create 合并分片 ...")
        self.create(remote, upload_id, sums, policy, blocks)
        vlog(fid, "create 完成")

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
        if block > MIN_BLOCK and block_count(size, block) <= MAX_SLICES and block not in (MID_BLOCK, MAX_BLOCK):
            print("[%s] 单文件最多 %d 个分片, 分片大小调整为 %s (共 %d 片)" % (
                fid, MAX_SLICES, convert_size(block, 2), block_count(size, block)))
        vlog(fid, "本地文件 %s, 大小 %s, mtime %s, 分片大小 %s, 共 %d 片, 目标 %s, 策略 %s, 秒传 %s" % (
            local, convert_size(size, 2), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
            convert_size(block, 2), block_count(size, block), remote, policy, "是" if rapid else "否"))
        try:
            state, remote_size = self.check_exist(remote)
        except ApiError as e:
            vlog(fid, "检查目标是否存在失败 (按不存在处理): %s" % err_text(e))
            state, remote_size = "none", 0
        vlog(fid, "目标检查结果: %s%s" % (state, (", 网盘大小 %s" % convert_size(remote_size, 2)) if state == "file" else ""))
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
            t_scan = time.time()
            sums = sum_file(local, block, True, fid)
            vlog(fid, "MD5 扫描完成, 用时 %s, content-md5=%s, 分块数 %d" % (
                fmt_elapsed(time.time() - t_scan), sums["content"], len(sums["blocks"])))
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
        vlog(fid, "目录已就绪, 调用 precreate ...")
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
        vlog(fid, "precreate 返回: uploadid=%s, return_type=%s, 需要上传的分片: %s" % (
            pre.get("uploadid"), pre.get("return_type"),
            pre.get("block_list") if pre.get("block_list") is not None else "全部"))

        print("[%s] 开始上传文件...\n" % fid)
        need = pre.get("block_list") or []
        if not scan_md5:
            need = []
        self.upload_blocks(fid, local, remote, pre["uploadid"], sums, need, policy)
        self.verify_remote(fid, remote, sums["size"])
        print("[%s] 上传文件成功, 保存到网盘路径: %s" % (fid, remote))
        return sums["size"], False


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
    last_read = 0
    show = bool(fid) and (VERBOSE or not QUIET)
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
            now = time.time()
            if show and now - last >= 3:
                speed = int((read - last_read) / max(now - last, 0.001))  # 区间速度, 而不是从头平均
                if VERBOSE:
                    log(fid, "扫描 MD5 %s/%s (%.1f%%) 实时 %s/s" % (
                        convert_size(read, 2), convert_size(st.st_size, 2), read * 100.0 / st.st_size,
                        convert_size(speed, 2)))
                else:
                    sys.stdout.write("\r[%s] 扫描 MD5 %s/%s %s/s" % (
                        fid, convert_size(read, 2), convert_size(st.st_size, 2), convert_size(speed, 2)))
                    sys.stdout.flush()
                last, last_read = now, read
    if in_block:
        sums["blocks"].append(block_hash.hexdigest())
    if with_content:
        sums["content"] = sums["md5"] = content.hexdigest() if False else content.hexdigest()
        sums["slice"] = sums["content"] if st.st_size <= SLICE_MD5 else slice_hash.hexdigest()
    if show and not VERBOSE:
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
    p.add_argument("-host", "--host", default="", help="指定上传线路, 如 c2 / c4 / d 或完整域名; 指定后整体上传失败才启用智能择优")
    p.add_argument("-smart", "--smart", type=bool_arg, default=True, help="智能择优线路 (默认开启, -smart=false 关闭; 开了 -rotatehost 时不生效)")
    p.add_argument("-nosmart", "--nosmart", action="store_true", help="同 -smart=false")
    p.add_argument("-prefer", "--prefer", default=DEFAULT_PREFER, help="智能择优时优先测试的线路, 逗号分隔, 默认 c2,c4; 留空则不优先")
    p.add_argument("-probes", "--probes", type=int, default=0, help="同时测速的分片数, 默认自动 (按 -parallel/4, 限制 1~5)")
    p.add_argument("-timeout", "--timeout", type=float, default=60.0, help="每次分片尝试的时限, 默认 60 秒。到点无论快慢、第几次重试, 都中断并换线。0 表示关闭")
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
    g.add_argument("-v", "--verbose", action="store_true",
                   help="详细模式: 每 3 秒列出所有正在上传的分片(实时速度/重试次数/本次用时), 每 20 秒一行文件总进度, 以及各步骤详细信息")
    args = p.parse_args()

    global QUIET, VERBOSE
    VERBOSE = bool(args.verbose)

    if args.policy not in (SIZE, SKIP, OVERWRITE, RSYNC):
        print("未知重名策略 %r，可选 size | skip | overwrite | rsync" % args.policy, file=sys.stderr)
        return 2
    if (not args.file and not args.files_from) or not args.dest.startswith("/"):
        print("用法: python3 baidu-upload.py -file 本地文件或通配符 [-dest /网盘目录/] [-exclude PAT] [-include PAT] "
              "[-min-size 1M] [-R] [-n] [-v] ...  (-h 查看全部)", file=sys.stderr)
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

    if VERBOSE:
        print("[v] 详细模式已开启; 参数: parallel=%d transfers=%d policy=%s timeout=%s norapid=%s md5=%s rotatehost=%s host=%s "
              "smart=%s prefer=%s probes=%d norefresh=%s" % (
                  args.parallel, args.transfers, args.policy, args.timeout, args.norapid, args.md5, args.rotatehost,
                  args.host or "-", args.smart and not args.nosmart, args.prefer or "-", args.probes, args.norefresh))
        if filt.rules:
            print("[v] 过滤规则 (按顺序): %s" % " | ".join(r.text() for r in filt.rules))

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
            if VERBOSE:
                print("[包含] %s%s" % (rel, "  (来自 files-from, 绕过名字规则)" if bypass else (("  (" + why + ")") if why else "")))
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

    if args.host and args.rotatehost:
        print("-host 与 -rotatehost 同时指定, 忽略 -host")
    client = Client(args.config, args.parallel, args.rotatehost, args.norefresh, args.timeout,
                    args.host, args.smart and not args.nosmart, args.prefer, args.probes)
    if client.selector:
        print("[0] 智能择优线路: 开启, 同时测速 %d 个分片, 优先测试 %s, 候选 %s%s" % (
            client.selector.slots, args.prefer or "无",
            ", ".join(short_host(h) for h in client.selector.hints),
            ", 指定线路 %s 整体失败才启用" % short_host(client.line_host) if client.user_line else ""))
    elif args.rotatehost:
        print("[0] 智能择优线路: 关闭 (已启用 -rotatehost)")
    else:
        print("[0] 智能择优线路: 关闭%s" % (", 指定线路 %s" % short_host(client.line_host) if client.user_line else ""))
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
    plan_bytes = 0
    for path, _rel in picked:
        try:
            plan_bytes += os.path.getsize(path)
        except OSError:
            pass

    def global_progress():
        # 每秒采样算实时速度; 不开 -v 时每 2 秒打印一行总进度
        tick = 0
        while not stop_progress.wait(1):
            spd = G_METER.rate()
            tick += 1
            if tick % 2:
                continue
            now = time.time()
            avg = max(G_METER.total, 0) / max(now - started, 1e-3)
            print("[进度] 已完成 %d/%d 个文件, 已上传 %s / %s, 实时 %s/s, 平均 %s/s, 用时 %s" % (
                finished[0], len(picked), convert_size(max(G_METER.total, 0), 2), convert_size(plan_bytes, 2),
                convert_size(spd, 2), convert_size(avg, 2), fmt_elapsed(now - started)))

    if QUIET and not VERBOSE:
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

    if client.selector:
        for line in client.selector.summary():
            print("[smart] " + line)
    elapsed = time.time() - started
    print("\n上传结束, 时间: %s, 总大小: %s, 平均速度: %s/s" % (
        fmt_elapsed(elapsed), convert_size(total), convert_size(total / max(elapsed, 1e-3), 2)))
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
