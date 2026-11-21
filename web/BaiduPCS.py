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
# 分片: <8GB 用 4MB，>=8GB 用 16MB，>=32GB 用 64MB; 单文件最多 1000 片, 超过就自动加大分片。
#
# 线路阶梯 (c10 -> c9 -> c8 ... -> c1, 到底再回 c10):
#   1) 普通接口 (列目录/precreate/create/locateupload 等): 同一条线路连续 2 次连不上 (超时/握手失败/连接重置/DNS 失败),
#      就换到 c10.pcs.baidu.com, 再连续 2 次连不上换 c9, 然后 c8 ... 倒序往下。
#      注意: xpan 接口官方只在 pan.baidu.com, 备用线路返回的不是 JSON 接口数据时一律当作失败继续换, 不会把乱码当成功。
#   2) 分片上传: 同一个分片连续 2 次连不上 (还没发出数据就失败), 或者连续 10 次太慢 (发了数据但超过 -timeout 时限没传完),
#      就换到下一条阶梯线路 c10 -> c9 -> c8 ...; 接口报错 (errno) 说明线路是通的, 不计入这两个连续计数。
#   -switch-conn / -switch-slow / -line-top 可以改这三个数字; -apifallback=false 可关闭普通接口的阶梯切换。
#   开了 -rotatehost 时分片仍保持原来的逐次轮换。
#
# 线路冷却 (所有模式都生效, 含智能择优 / -rotatehost / -nosmart / -host 指定线路):
#   同一条 pcs 线路 (所有分片、所有请求合计) 连续 3 次 "完全连不上" (-cool-fails), 就冷却 300 秒 (-cooldown, 0 关闭):
#   冷却期间换线会跳过它; 正在用它的分片下一次重试直接换线, 不再等连续 2 次; 只要有一次上传成功就清零计数。
#   只有 "完全连不上" 才计入冷却:
#     - 连接/握手阶段失败或超时、DNS 失败、连接被拒、分片一个字节都没发出去
#     - 分片发送中连续 -nodata-timeout 秒 (默认 6) 没有任何新数据
#   下面这些都不算, 不会冷却, 还会把这条线路的连续计数清零 (说明线路是通的), 只按原来的逻辑处理 (连续太慢 -switch-slow 次才换线):
#     - 速度低: 有速度但超过 -timeout 时限没传完
#     - 传到一半被重置/断开、响应不是 JSON、接口返回 errno
#     - 本地文件读取错误
#   智能择优自己的线路冷却 (LineSelector) 也是同样的标准: 只有 "完全连不上" 连续 -cool-fails 次才冷却, 速度低只影响测速排名, 不冷却。
#
# 零速度快速判定 (-nodata-timeout, 默认 6 秒):
#   分片还没发完时, 连续 6 秒没有任何新数据 (包括连接/握手阶段一个字节都没发出去) 就立刻中断本次尝试, 不再等 -timeout 的整体时限。
#   这种情况按 '连不上' 算, 连续 2 次就换线 (c10 -> c9 -> ...), 同时计入线路冷却。-timeout 仍然是单次尝试的总时限 (慢但有速度的分片用它, 不冷却)。
#
# 网络容错: 普通接口遇到网络错误会自动重试 NET_RETRY 次 (同线路间隔 3/6/9... 秒, 最长 30 秒, 换线路时等 1 秒)。
#   分片上传自己有 SLICE_RETRY 次重试 (间隔 2/4/6... 秒, 最长 10 秒)。
#
# -v 详细模式会额外打印:
#   - 每个分片的开始/完成 (大小、用时、速度、线路), 失败原因与重试 (第几次、连不上/太慢的连续次数、换到哪条线路、等待多久)
#   - 每 3 秒列出所有正在上传的分片: 实时速度、重试次数、本次用时 (等待重试的分片也会列出)
#   - 每 20 秒一行文件总进度: 百分比、实时速度、平均速度、活跃分片数、已完成分片数、重试数、总用时、ETA
#   - 文件大小/分片数、存在性检查、precreate、create、校验等各步骤信息
#   - 被排除的文件及原因 / 被包含的文件

import argparse
import collections
import glob
import hashlib
import http.client
import json
import os
import posixpath
import re
import socket
import ssl
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
SLICE_RETRY = 30  # 单个分片最多尝试次数 (要够走完 "连续 10 次太慢" 再换线路的阶梯)
NET_RETRY = 12  # 普通接口 (非分片) 遇到网络错误时的最大尝试次数 (每条线路 2 次, 够走 6 条线路)
CONN_SWITCH = 2  # 连续这么多次连不上就换线路
SLOW_SWITCH = 10  # 分片连续这么多次太慢就换线路
LADDER_TOP = 10  # 阶梯起点: c10 -> c9 -> ... -> c1
COOL_FAILS = 3  # 同一条线路 (所有分片合计) 连续这么多次完全连不上, 就进入冷却 (冷却时长 HOST_COOLDOWN)
NODATA_TIMEOUT = 6  # 分片发送中连续这么多秒没有任何新数据 (含一个字节都没发出去) 就立刻中断, 不等整体时限
MAX_SLICES = 1000  # 单个文件最多切成多少个分片
DEFAULT_PREFER = "c2,c5,d"  # 智能择优: 优先测试的线路
PREFER_STRIKES = 3  # 优先线路连续这么多轮不如主线路, 就不再优先
SWITCH_MARGIN = 1.15  # 测速线路要比主线路快 15% 以上才切换
MIN_MAIN_SAMPLES = 3  # 主线路至少有这么多个分片样本才做比较
MIN_PROBE_SAMPLES = 2  # 测速线路至少有这么多个样本才有资格当主线路
MAX_CANDIDATES = 8
HOST_COOLDOWN = 300  # 线路连续完全连不上后冷却秒数
SPEED_WINDOW = 4.0  # 实时速度的滑动窗口秒数
QUIET = False  # 多文件并发时关闭每个文件各自的 \r 进度行
VERBOSE = False  # -v: 详细输出
PRINT_LOCK = threading.Lock()


EXPIRED_CODES = (-6, 110, 111, 20016)  # token 无效/过期 (20016: nas access token expired)


class TokenExpired(RuntimeError):
    pass


class LocalFileError(Exception):
    """本地文件打不开/读不全。跟线路无关: 不计入换线计数, 也不计入线路冷却。"""


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


def ladder_pick(k, top, avoid=()):
    """倒序阶梯: k=0 -> c<top>, k=1 -> c<top-1> ... 到 c1 后回到 c<top>。
    跳过 avoid 里的线路。返回 (线路, 新的 k)。"""
    top = max(1, int(top))
    for j in range(top):
        h = "https://c%d.pcs.baidu.com" % (top - (k + j) % top)
        if h not in avoid:
            return h, k + j + 1
    return "https://c%d.pcs.baidu.com" % (top - k % top), k + 1  # 全被 avoid 了: 硬着头皮按顺序来


def looks_like_api(body):
    """备用线路返回的内容必须是 JSON 对象, 否则当作这条线路不可用。"""
    try:
        return isinstance(json.loads(body), dict)
    except Exception:
        return False


class HostHealth:
    """全局线路冷却, 所有分片/所有请求共用, 与是否开智能择优无关。
    只统计 "完全连不上" (连接/握手失败、一个字节都没发出去、-nodata-timeout 秒无任何新数据):
    同一条 pcs 线路连续 fails 次 -> 冷却 cooldown 秒 (cooldown<=0 关闭)。
    速度慢、传到一半断开、接口报错等失败不调用 fail(), 只调用 ok(host, False) 清零连续计数, 不会冷却。
    冷却中的线路: 阶梯/轮换换线时被跳过, 正在使用它的分片下一次重试直接换走。"""

    def __init__(self, cooldown=HOST_COOLDOWN, fails=COOL_FAILS):
        self.lock = threading.Lock()
        self.cooldown = float(cooldown or 0)
        self.fails = max(1, int(fails))
        self.st = {}
        self.on_cool = None  # 进入冷却时回调 (通知智能择优换主线路)

    @staticmethod
    def _key(host):
        h = norm_host(host)
        return h if h.endswith(".pcs.baidu.com") else ""  # 只管上传线路, 不管 pan.baidu.com / openapi

    def fail(self, host):
        """记一次 '完全连不上'。返回 True 表示这一次让线路刚好进入冷却。"""
        k = self._key(host)
        if not k or self.cooldown <= 0:
            return False
        now = time.time()
        with self.lock:
            e = self.st.setdefault(k, {"cons": 0, "dead": 0.0})
            if e["dead"] > now:
                return False  # 已经在冷却, 别的分片的在途失败不重复触发
            e["cons"] += 1
            if e["cons"] < self.fails:
                return False
            e["cons"] = 0
            e["dead"] = now + self.cooldown
        log("cool", "线路 %s 连续 %d 次完全连不上, 冷却 %d 秒 (期间不再使用)" % (short_host(k), self.fails, int(self.cooldown)))
        cb = self.on_cool
        if cb:
            try:
                cb(k)
            except Exception:
                pass
        return True

    def ok(self, host, clear=True):
        """线路是通的。clear=True (真正上传成功) 连冷却一起清掉; False (连上了但慢/断开/接口报错) 只清连续计数。"""
        k = self._key(host)
        if not k:
            return
        with self.lock:
            e = self.st.get(k)
            if e:
                e["cons"] = 0
                if clear:
                    e["dead"] = 0.0

    def is_dead(self, host):
        k = self._key(host)
        if not k:
            return False
        with self.lock:
            e = self.st.get(k)
            return bool(e and e["dead"] > time.time())

    def dead_set(self):
        now = time.time()
        with self.lock:
            return {h for h, e in self.st.items() if e["dead"] > now}


class LineSelector:
    """智能择优线路: 始终有 slots 个分片在轮流测速, 其余分片走主线路; 测速最快且明显超过主线路就切换。"""

    def __init__(self, main, prefer, slots, cooldown=HOST_COOLDOWN, cool_fails=COOL_FAILS):
        self.lock = threading.Lock()
        self.cooldown = cooldown if cooldown and cooldown > 0 else HOST_COOLDOWN
        self.cool_fails = max(1, int(cool_fails))
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

    def fallback_from(self, host, secs=None):
        with self.lock:
            host = norm_host(host)
            if host in self.stats:
                self.stats[host]["dead_until"] = time.time() + (secs or self.cooldown)
                self.stats[host]["cons_fail"] = self.cool_fails
            if self.main == host:
                self._replace_main()

    def record(self, host, nbytes, elapsed, ok, role, down=True):
        """down=True: 这次失败是 "完全连不上" (一个字节没发出去 / 无数据), 才计入冷却的连续失败。
        down=False: 失败但线路是通的 (速度低/传到一半断开), 只记失败次数, 并清零连续计数, 不冷却。"""
        with self.lock:
            st = self.stats.get(host)
            if st is None:
                return
            if not ok:
                st["fails"] += 1
                if down:
                    st["cons_fail"] += 1
                    if st["cons_fail"] >= self.cool_fails:
                        st["dead_until"] = time.time() + self.cooldown
                        if VERBOSE:
                            print("%s [smart] 线路 %s 连续 %d 次完全连不上, 冷却 %d 秒" % (
                                time.strftime("%H:%M:%S"), short_host(host), st["cons_fail"], self.cooldown))
                        if host == self.main:
                            self._replace_main()
                else:
                    st["cons_fail"] = 0
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
            try:
                chunk = self.f.read(min(size, self.left))
            except OSError as e:
                raise LocalFileError("读取本地文件失败: %s" % e)
            if not chunk:
                raise LocalFileError("读取本地文件失败 (文件被截断?)")
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
    """一次分片尝试的取消开关。set() 除了打标记, 还会直接关掉正在使用的 socket,
    这样卡在 send/recv 里的线程也能立刻被打断 (而不是等到 socket 超时)。"""

    def __init__(self):
        self._ev = threading.Event()
        self.reason = ""
        self.kind = ""  # "nodata": 一直没有数据 (按完全连不上算); "deadline": 超过整体时限 (按太慢算)
        self._conn = None
        self._lock = threading.Lock()

    def attach(self, conn):
        with self._lock:
            self._conn = conn
        if self._ev.is_set():
            self._kill()

    def _kill(self):
        with self._lock:
            c = self._conn
        if c is None:
            return
        try:
            if c.sock is not None:
                c.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            c.close()
        except Exception:
            pass

    def set(self, reason, kind=""):
        if not self.reason:
            self.reason = reason
            self.kind = kind
        self._ev.set()
        self._kill()

    def is_set(self):
        return self._ev.is_set()


class Inflight:
    """正在发送的分片。单次时限一到就中断本次尝试 (是否换线由 upload_slice 按连续次数决定)。"""

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

    def poll(self, timeout, nodata, sel, log_fn=None, total=0):
        """每秒由 guard 线程调用一次。
        - nodata (默认 6 秒): 数据还没发完时, 连续这么久没有任何新字节 (含一个字节都没发出去) -> 立刻中断
        - timeout (-timeout): 单次尝试总时限, 到点不管快慢都中断 (数据发完后等服务器响应也受它限制)"""
        if not (timeout and timeout > 0) and not (nodata and nodata > 0):
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
                fully_sent = st["size"] > 0 and st["sent"] >= st["size"]
                if budget and el >= budget:
                    st["cancel"].set("超过时限 %ds" % int(budget), "deadline")
                    notes.append((seq, "deadline", st["host"], spd, el, budget, st["sent"]))
                elif nodata and nodata > 0 and not fully_sent and idle >= nodata:
                    st["cancel"].set("超过 %d 秒没有任何新数据" % int(nodata), "nodata")
                    notes.append((seq, "nodata", st["host"], spd, el, nodata, st["sent"]))
        if sel and self.tick % 5 == 0:
            for h, spds in by_host.items():
                sel.note_live(h, mean(spds))
        if not log_fn:
            return
        for seq, kind, host, spd, el, limit, sent in notes:
            if kind == "nodata":
                log_fn("分片 %d/%d 超过 %ds 没有任何新数据 (已发 %s, 线路 %s, 用时 %s), 中断本次尝试" % (
                    seq + 1, total or (seq + 1), int(limit), convert_size(sent, 2), short_host(host), fmt_elapsed(el)))
            else:
                log_fn("分片 %d/%d 超过时限 %ds 仍未完成 (速度 %s/s, 线路 %s, 用时 %s), 中断本次尝试" % (
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
                 line_host=None, smart=True, prefer=DEFAULT_PREFER, probes=0,
                 conn_switch=CONN_SWITCH, slow_switch=SLOW_SWITCH, ladder_top=LADDER_TOP, api_fallback=True,
                 nodata_timeout=NODATA_TIMEOUT, cooldown=HOST_COOLDOWN, cool_fails=COOL_FAILS):
        self.cfg_path = cfg_path
        self.parallel = parallel if parallel > 0 else 20
        self.rotate_host = rotate_host
        self.norefresh = norefresh
        self.slice_timeout = slice_timeout if slice_timeout and slice_timeout > 0 else None
        self.conn_switch = max(1, int(conn_switch))  # 连续几次连不上就换线路
        self.slow_switch = max(1, int(slow_switch))  # 分片连续几次太慢就换线路
        self.ladder_top = max(1, int(ladder_top))  # 阶梯起点 c<ladder_top>
        self.api_fallback = bool(api_fallback)  # 普通接口是否启用阶梯切换
        self.nodata_timeout = float(nodata_timeout) if nodata_timeout and nodata_timeout > 0 else None  # 零速度快速超时
        self.health = HostHealth(cooldown, cool_fails)  # 全局线路冷却 (任何模式都生效, 只统计完全连不上)
        self.lock = threading.Lock()
        self.refreshed_at = 0.0
        self.user_line = bool(norm_host(line_host)) and not rotate_host  # 用户指定了线路
        self.line_host = norm_host(line_host) if self.user_line else FIXED_HOST
        self.smart = bool(smart) and not rotate_host and self.parallel >= 2
        self.selector = None
        if self.smart:
            slots = probes if probes and probes > 0 else max(1, min(5, self.parallel // 4))
            slots = min(slots, max(1, self.parallel - 1))
            self.selector = LineSelector(self.line_host, [x for x in str(prefer or "").split(",") if x.strip()], slots,
                                         cooldown, cool_fails)
        if self.selector is not None:
            self.health.on_cool = lambda h: self.selector.fallback_from(h, self.health.cooldown)
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

    def _request(self, method, url, data=None, headers=None, timeout=30, retries=NET_RETRY, rotate=None):
        """发一次 HTTP 请求。网络层错误 (SSL 握手超时/连接重置/DNS 失败/超时等) 自动重试 retries 次。
        同一条线路连续 conn_switch (默认 2) 次连不上, 就按 c10 -> c9 -> c8 ... 倒序换线路 (只替换域名, 路径不变)。
        备用线路返回的不是 JSON 接口数据时当作失败, 继续换下一条。
        HTTP 错误码 (4xx/5xx) 在原线路上不重试, 原样返回交给上层解析。
        线路冷却只统计 "完全连不上" (urllib 在建立连接/握手/发送请求阶段抛出的 URLError);
        连上之后等响应超时、读响应中途断开等不算冷却。
        data 是一次性流 (分片上传) 时必须传 retries=1, 由 upload_slice 自己重试。"""
        retries = max(1, retries)
        if rotate is None:
            rotate = self.api_fallback
        u = urllib.parse.urlparse(url)
        base = "%s://%s" % (u.scheme, u.netloc)
        tail = url[len(base):]
        cur, fails, k, last = base, 0, 0, None
        for i in range(retries):
            req = urllib.request.Request(cur + tail, data=data, headers=headers or {}, method=method)
            req.add_header("User-Agent", UA)
            err = None
            down = False  # 是否 "完全连不上" (连接/握手阶段就失败)
            status, body = 0, b""
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status, body = resp.status, resp.read()
            except urllib.error.HTTPError as e:
                status, body = e.code, e.read()
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError,
                    ssl.SSLError, http.client.HTTPException, OSError) as e:
                err = e
                down = isinstance(e, urllib.error.URLError)  # urllib 只把连接/握手/发送阶段的错误包成 URLError
            net_err = err is not None
            if err is None:
                if cur == base or looks_like_api(body):
                    self.health.ok(cur)
                    if cur != base:
                        log("net", "备用线路 %s 响应正常" % short_host(cur))
                    return status, body
                err = RuntimeError("备用线路 %s 返回的不是接口数据 (HTTP %d)" % (short_host(cur), status))
            last = err
            fails += 1
            if net_err:
                if down:
                    self.health.fail(cur)  # 完全连不上才算线路冷却; 备用线路返回非 JSON 只说明它不服务这个接口
                else:
                    self.health.ok(cur, False)  # 连上了, 只是响应慢/中途断开: 不冷却, 清零连续计数
            if i == retries - 1:
                break
            if rotate and fails >= self.conn_switch:
                nxt, k = ladder_pick(k, self.ladder_top, {cur, base} | self.health.dead_set())
                log("net", "请求失败 (%s: %s), 连续 %d 次连不上, 换线路 %s -> %s, 重试 %d/%d" % (
                    type(err).__name__, truncate(str(err), 80), fails, short_host(cur), short_host(nxt), i + 2, retries))
                cur, fails = nxt, 0
                time.sleep(1)
            else:
                wait = min(30, fails * 3)
                log("net", "请求失败 (%s: %s), 线路 %s, %d 秒后重试 %d/%d" % (
                    type(err).__name__, truncate(str(err), 80), short_host(cur), wait, i + 2, retries))
                time.sleep(wait)
        raise last

    def refresh(self):
        q = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": self.cfg["refresh_token"],
            "client_id": self.cfg["client_id"],
            "client_secret": self.cfg["client_secret"],
        })
        _, body = self._request("GET", "https://openapi.baidu.com/oauth/2.0/token?" + q, rotate=False)
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

    def post_slice(self, host, remote, upload_id, seq, src, progress, cancel=None, deadline=None, stat=None):
        local, offset, n = src
        q = urllib.parse.urlencode({
            "method": "upload", "access_token": self.cfg["access_token"],
            "type": "tmpfile", "path": remote, "uploadid": upload_id, "partseq": str(seq),
        })
        boundary = "----baidu%s" % hashlib.md5(os.urandom(8)).hexdigest()
        head = ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"file\"\r\n"
                "Content-Type: application/octet-stream\r\n\r\n" % boundary).encode()
        tail = ("\r\n--%s--\r\n" % boundary).encode()
        path = "/rest/2.0/pcs/superfile2?" + q
        u = urllib.parse.urlparse(host)
        try:
            body = SliceBody(local, offset, n, head, tail, progress, cancel, deadline)
        except OSError as e:
            raise LocalFileError("打开本地文件失败: %s" % e)  # 本地问题, 与线路无关
        conn = None
        ok = False
        try:
            # 直接用 http.client: 这样 guard 线程能在 cancel 时关掉 socket, 卡住的 connect 之后的 send/recv 会立刻断开。
            # 连接/握手阶段的超时用 nodata_timeout (默认 6 秒), 连上之后 socket 超时改回 -timeout。
            connect_to = self.nodata_timeout or self.slice_timeout
            conn = http.client.HTTPSConnection(u.hostname, u.port or 443, timeout=connect_to,
                                               context=ssl.create_default_context())
            if cancel is not None:
                cancel.attach(conn)
            conn.connect()
            if conn.sock is not None:
                conn.sock.settimeout(self.slice_timeout)
            conn.request("POST", path, body=body, headers={
                "User-Agent": UA,
                "Content-Type": "multipart/form-data; boundary=%s" % boundary,
                "Content-Length": str(body.length),
            })
            r = conn.getresponse()
            status, resp = r.status, r.read()
            if status >= 400 and not resp:
                raise RuntimeError("HTTP %d 空响应" % status)
            code, parsed = parse_api_code(resp)
            if not parsed:
                raise RuntimeError("百度接口返回无法解析: HTTP %d %s" % (status, truncate(resp)))
            if code != 0:
                raise ApiError(code, resp.decode("utf-8", "replace"))
            ok = True
            return resp
        except Exception as e:
            # socket 被 cancel 强行关掉时会冒出各种奇怪的异常, 统一还原成 "被中断" 的超时
            if cancel is not None and cancel.is_set() and not isinstance(e, (TimeoutError, ApiError)):
                raise TimeoutError(cancel.reason or "分片尝试被中断")
            raise
        finally:
            body.close()
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
            if stat is not None:
                stat["sent"] = body.sent  # 本次尝试已发出的字节数: 0 说明根本没连上, >0 说明连上了但没传完
            if not ok and body.sent and progress:
                progress(-body.sent)  # 失败: 回滚这次尝试已计入的字节, 重试时不会重复统计

    def upload_slice(self, remote, upload_id, seq, src, progress, hosts, hosts_cb=None, report=None, rotate=False,
                     lg=None, on_retry=None, total=0, tag="", on_attempt=None, on_wait=None):
        """上传一个分片。
        线路切换规则 (未开 -rotatehost 时):
          - 连续 conn_switch 次连不上 (一个字节都没发出去就失败, 或连续 nodata 秒没有新数据) -> 换线路
          - 连续 slow_switch 次太慢 (发出了数据但超过时限没传完) -> 换线路
          换线顺序: c10 -> c9 -> c8 ... -> c1 -> c10 ...
          接口返回 errno 说明线路是通的, 不计入这两个连续计数。
        线路冷却 (所有模式都生效):
          只有 "完全连不上" (一个字节都没发出去 / nodata 秒无任何新数据) 才计入冷却;
          速度低 (有速度但超时限)、传到一半断开、接口报错、本地文件错误都不冷却。"""
        hosts = hosts or [self.line_host]
        idx = 0  # 仅 -rotatehost 模式使用
        host = hosts[0]
        last = None
        conn_fail = slow_fail = ladder_k = 0
        n = src[2]
        label = "分片 %d/%d" % (seq + 1, total) if total else "分片 %d" % (seq + 1)
        for i in range(SLICE_RETRY):
            if i > 0 and isinstance(last, ApiError) and last.code in EXPIRED_CODES:
                self.ensure_token(True)
            else:
                self.ensure_token(False)
            if self.rotate_host:
                # 轮换模式: 跳过冷却中的线路 (全都在冷却就硬着头皮用当前这条)
                for _ in range(len(hosts)):
                    host = hosts[idx % len(hosts)]
                    if not self.health.is_dead(host):
                        break
                    idx += 1
                else:
                    host = hosts[idx % len(hosts)]
            elif self.health.is_dead(host):
                # 这条线路已经被别的分片判定冷却了, 不再等自己连续失败, 直接换
                old = host
                host, ladder_k = ladder_pick(ladder_k, self.ladder_top, {old} | self.health.dead_set())
                conn_fail = slow_fail = 0
                if lg:
                    lg("%s 线路 %s 冷却中, 直接换到 %s" % (label, short_host(old), short_host(host)))
            t0 = time.time()
            # 每一次尝试都是同一个时限, 不随重试次数放宽
            limit = self.slice_timeout if self.slice_timeout else None
            deadline = (t0 + limit) if limit else None
            cancel = Cancel()
            stat = {"sent": 0}
            if on_attempt:
                on_attempt(host, i, cancel, limit)
            if lg:
                lg("%s 开始 %s 线路 %s%s 第 %d/%d 次%s" % (
                    label, convert_size(n, 2), short_host(host), (" (%s)" % tag) if tag and i == 0 else "",
                    i + 1, SLICE_RETRY, (" 时限 %ds" % int(limit)) if limit else ""))
            try:
                body = self.post_slice(host, remote, upload_id, seq, src, progress, cancel, deadline, stat)
                el = time.time() - t0
                if report:
                    report(host, n, el, True, i)
                self.health.ok(host)
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
                sent = stat.get("sent", 0)
                local_err = isinstance(e, LocalFileError)
                if isinstance(e, ApiError) and (e.code in (400, 413, 31024, 31364) or (self.norefresh and e.code in EXPIRED_CODES)):
                    if lg:
                        lg("%s 失败 (不可重试): %s" % (label, err_text(e)))
                    raise
                timed_out = is_timeout(e) or cancel.is_set()

                # 判定这次失败的类型, 更新连续计数
                # is_conn: 算 "连不上", 用于连续 conn_switch 次换线
                # is_down: 完全连不上 (一个字节没发出去 / nodata 无新数据), 才计入线路冷却
                is_conn = False
                is_down = False
                if isinstance(e, ApiError):
                    kind = "接口报错"
                    conn_fail = slow_fail = 0
                elif local_err:
                    kind = "本地文件错误"  # 不动任何连续计数
                elif timed_out and sent > 0 and cancel.kind != "nodata":
                    kind = "太慢 %d/%d" % (slow_fail + 1, self.slow_switch)
                    slow_fail += 1
                    conn_fail = 0
                else:
                    conn_fail += 1
                    slow_fail = 0
                    is_conn = True
                    if cancel.kind == "nodata":
                        is_down = True
                        kind = "无数据 %d/%d" % (conn_fail, self.conn_switch)
                    elif sent == 0:
                        is_down = True
                        kind = "连不上 %d/%d" % (conn_fail, self.conn_switch)
                    else:
                        kind = "传输中断 %d/%d" % (conn_fail, self.conn_switch)

                # 全局冷却: 只有 "完全连不上" 才算一次失败, 所有分片合计连续 cool_fails 次 -> 冷却 (任何模式都生效)
                # 速度慢/传到一半断开/接口报错: 线路是通的, 只清零连续计数, 不冷却
                cooled = False
                if is_down:
                    cooled = self.health.fail(host)
                    kind += " 计入冷却"
                elif not local_err:
                    self.health.ok(host, False)

                # 智能择优也一样: 接口报错/本地错误与线路无关不上报; 其余失败上报, 但只有 "完全连不上" 才计入它的冷却
                if report and not isinstance(e, ApiError) and not local_err:
                    report(host, 0, el, False, i, is_down)

                nxt = host
                why = ""
                if self.rotate_host:
                    # -rotatehost: 保持原来的逐次轮换
                    if timed_out and hosts_cb:
                        hosts = hosts_cb() or hosts
                        idx = (hosts.index(host) + 1) % len(hosts) if host in hosts else 0
                    else:
                        idx += 1
                    for _ in range(len(hosts)):  # 跳过冷却中的线路
                        if not self.health.is_dead(hosts[idx % len(hosts)]):
                            break
                        idx += 1
                    nxt = hosts[idx % len(hosts)]
                else:
                    if cooled:
                        why = "线路进入冷却"
                    elif conn_fail >= self.conn_switch:
                        why = "连续 %d 次连不上" % conn_fail
                    elif slow_fail >= self.slow_switch:
                        why = "连续 %d 次上传太慢" % slow_fail
                    if why:
                        nxt, ladder_k = ladder_pick(ladder_k, self.ladder_top, {host} | self.health.dead_set())
                        conn_fail = slow_fail = 0

                last_try = (i == SLICE_RETRY - 1)
                if on_retry and not last_try:
                    on_retry()
                wait = min(10, (i + 1) * 2)
                if lg:
                    if last_try:
                        lg("%s 第 %d/%d 次失败 [用时 %.1fs, 已发 %s] (%s): %s | 已用完重试次数, 放弃" % (
                            label, i + 1, SLICE_RETRY, el, convert_size(sent, 2), kind, err_text(e)))
                    else:
                        lg("%s 第 %d/%d 次失败 [用时 %.1fs, 已发 %s] (%s): %s | 线路 %s%s | %d 秒后重试" % (
                            label, i + 1, SLICE_RETRY, el, convert_size(sent, 2), kind, err_text(e), short_host(host),
                            (" -> %s 换到 %s" % (why, short_host(nxt))) if nxt != host else "", wait))
                elif nxt != host:
                    print("分片 %d %s, 第 %d/%d 次, 换线路 %s -> %s" % (
                        seq, why or ("%s" % kind), i + 1, SLICE_RETRY, short_host(host), short_host(nxt)))
                host = nxt
                if not last_try:
                    if on_wait:
                        on_wait(el)
                    time.sleep(wait)
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
                            def report(h, nbytes, elapsed, ok, attempt, down=True, role=role):
                                sel.record(h, nbytes, elapsed, ok, role if attempt == 0 else "retry", down)
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
                inflight.poll(self.slice_timeout, self.nodata_timeout, sel, lambda m: log(fid, m), total_slices)

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
        sums["content"] = sums["md5"] = content.hexdigest()
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
    p.add_argument("-prefer", "--prefer", default=DEFAULT_PREFER, help="智能择优时优先测试的线路, 逗号分隔, 默认 c2,c5,d; 留空则不优先")
    p.add_argument("-probes", "--probes", type=int, default=0, help="同时测速的分片数, 默认自动 (按 -parallel/4, 限制 1~5)")
    p.add_argument("-timeout", "--timeout", type=float, default=60.0, help="每次分片尝试的时限, 默认 60 秒。到点无论快慢都中断本次尝试 (算一次 '太慢', 不冷却线路)。0 表示关闭")
    p.add_argument("-norefresh", "--norefresh", action="store_true", help="只用 config 里的 access_token, 绝不刷新 (过期直接报错); 此时不要求 client_id/secret/refresh_token")
    p.add_argument("-switch-conn", "--switch-conn", dest="switch_conn", type=int, default=CONN_SWITCH,
                   help="连续这么多次连不上就换线路 (c10 -> c9 -> c8 ...), 默认 %d; 对普通接口和分片都生效" % CONN_SWITCH)
    p.add_argument("-switch-slow", "--switch-slow", dest="switch_slow", type=int, default=SLOW_SWITCH,
                   help="分片连续这么多次上传太慢 (超时限没传完) 就换线路, 默认 %d" % SLOW_SWITCH)
    p.add_argument("-line-top", "--line-top", dest="line_top", type=int, default=LADDER_TOP,
                   help="换线路阶梯的起点, 默认 %d, 即 c%d -> c%d -> ... -> c1" % (LADDER_TOP, LADDER_TOP, LADDER_TOP - 1))
    p.add_argument("-nodata-timeout", "--nodata-timeout", dest="nodata_timeout", type=float, default=NODATA_TIMEOUT,
                   help="分片发送中连续这么多秒没有任何新数据 (含连接/握手阶段) 就立刻中断本次尝试并按 '完全连不上' 计数 (计入换线和线路冷却), 默认 %d 秒, 0 关闭" % NODATA_TIMEOUT)
    p.add_argument("-cooldown", "--cooldown", type=float, default=HOST_COOLDOWN,
                   help="线路冷却秒数: 同一条线路连续 -cool-fails 次 '完全连不上' (连接/握手失败、一个字节都没发出去、-nodata-timeout 秒无新数据) 就冷却这么久, 期间不再使用 (所有模式生效, 含智能择优/-rotatehost/-nosmart/-host)。速度低/传到一半断开/接口报错不冷却。默认 %d, 0 关闭" % HOST_COOLDOWN)
    p.add_argument("-cool-fails", "--cool-fails", dest="cool_fails", type=int, default=COOL_FAILS,
                   help="同一条线路 (所有分片合计) 连续这么多次完全连不上就进入冷却, 默认 %d" % COOL_FAILS)
    p.add_argument("-apifallback", "--apifallback", type=bool_arg, default=True,
                   help="普通接口 (列目录/precreate/create 等) 连不上时是否按 c10 -> c9 ... 换线路, 默认开启, -apifallback=false 关闭")

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
    if args.cool_fails < 1:
        print("-cool-fails 必须 >= 1", file=sys.stderr)
        return 2
    if args.switch_conn < 1 or args.switch_slow < 1 or args.line_top < 1:
        print("-switch-conn / -switch-slow / -line-top 必须 >= 1", file=sys.stderr)
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
              "smart=%s prefer=%s probes=%d norefresh=%s switch-conn=%d switch-slow=%d line-top=%d apifallback=%s nodata-timeout=%s" % (
                  args.parallel, args.transfers, args.policy, args.timeout, args.norapid, args.md5, args.rotatehost,
                  args.host or "-", args.smart and not args.nosmart, args.prefer or "-", args.probes, args.norefresh,
                  args.switch_conn, args.switch_slow, args.line_top, args.apifallback, args.nodata_timeout))
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
                    args.host, args.smart and not args.nosmart, args.prefer, args.probes,
                    args.switch_conn, args.switch_slow, args.line_top, args.apifallback, args.nodata_timeout,
                    args.cooldown, args.cool_fails)
    print("[0] 线路冷却: %s" % (
        "同一条线路连续 %d 次完全连不上 (无数据/握手失败) 冷却 %d 秒 (所有模式生效; 速度低造成的失败不冷却)" % (
            client.health.fails, int(client.health.cooldown))
        if client.health.cooldown > 0 else "关闭"))
    print("[0] 线路阶梯: 连续 %d 次连不上%s就换 c%d -> c%d -> ... -> c1%s; 普通接口阶梯切换: %s" % (
        client.conn_switch,
        "或分片连续 %d 次太慢" % client.slow_switch if not client.rotate_host else "",
        client.ladder_top, max(1, client.ladder_top - 1),
        " (-rotatehost 时分片保持逐次轮换)" if client.rotate_host else "",
        "开启" if client.api_fallback else "关闭"))
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
