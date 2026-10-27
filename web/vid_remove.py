#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
https://claude.ai/chat/887b9a93-30cf-4af2-ae7b-91cba00f337d
ts_sdt_clean.py

按 MPEG-TS 的 SDT 表结构精确定位，清除 service_provider_name / service_name，
并可把 service_type 置 0。只改 PID 0x0011 的 SDT section 里的对应字节，
视频/音频数据里碰巧出现的相同字节完全不会被碰。

处理流程：
  1. 探测包长 (188 / 192(M2TS) / 204) 和同步偏移。
  2. 用 numpy 向量化按 PID 筛出 SDT 包（PID 0x0011）。
  3. 重组跨包的 section，解析 table_id 0x42 / 0x46 里的 service_descriptor (tag 0x48)。
  4. provider / name 内容字节 -> 0x20（长度字节不变，文件大小不变）；
     service_type -> 0x00（可用 --keep-type 保留）。
  5. 重算该 section 的 CRC32 (MPEG-2) 并写回（可用 --no-crc 关闭）。

依赖:
    pip install numpy
    （--verify 需要系统有 mediainfo，可选）

用法:
    python3 ts_sdt_clean.py 文件.ts --dry-run
    python3 ts_sdt_clean.py 文件.ts
    python3 ts_sdt_clean.py 文件.ts --keep-type
    python3 ts_sdt_clean.py 文件.ts --match JX --match CCTV-4K
    python3 ts_sdt_clean.py 文件.ts --verify

建议先在文件副本上试。
"""

import os
import re
import sys
import json
import argparse
import subprocess

try:
    import numpy as np
except ImportError:
    print("错误：需要 numpy，请先安装: pip install numpy")
    sys.exit(1)

CHUNK_BYTES = 32 * 1024 * 1024
SDT_PID = 0x0011
NIT_PID = 0x0010
NIT_TABLES = (0x40, 0x41)       # 0x40 = NIT actual, 0x41 = NIT other
SERVICE_LIST_TAG = 0x41
SDT_TABLES = (0x42, 0x46)      # 0x42 = SDT actual, 0x46 = SDT other
SERVICE_DESCRIPTOR_TAG = 0x48
MULTILINGUAL_DESCRIPTOR_TAG = 0x5D   # multilingual_service_name_descriptor
TS_PACKET = 188

# 压缩包/镜像一律跳过
SKIP_EXTENSIONS = {
    ".zip", ".zipx", ".rar", ".7z",
    ".tar", ".gz", ".tgz", ".bz2", ".tbz", ".tbz2", ".xz", ".txz",
    ".zst", ".tzst", ".lz", ".lzma", ".lz4", ".z", ".lzo", ".br",
    ".cab", ".arj", ".lzh", ".lha", ".ace", ".cpio", ".sit", ".sitx",
    ".zoo", ".pak", ".alz", ".egg",
    ".jar", ".war", ".apk", ".ipa", ".xpi", ".rpm", ".deb",
    ".iso", ".img", ".dmg", ".wim", ".vhd", ".vhdx", ".vmdk", ".squashfs",
}
SKIP_SPLIT_REGEX = re.compile(r"\.(\d{3}|r\d{2}|z\d{2})$", re.IGNORECASE)


def should_skip(path):
    name = os.path.basename(path).lower()
    ext = os.path.splitext(name)[1]
    if ext in SKIP_EXTENSIONS:
        return ext
    m = SKIP_SPLIT_REGEX.search(name)
    return m.group(0) if m else None


# ---------------- CRC32 (MPEG-2: poly 0x04C11DB7, init 0xFFFFFFFF, 无反射, 无异或) ----------------
def _make_crc_table():
    table = []
    for i in range(256):
        c = i << 24
        for _ in range(8):
            c = ((c << 1) ^ 0x04C11DB7) if (c & 0x80000000) else (c << 1)
            c &= 0xFFFFFFFF
        table.append(c)
    return table


CRC_TABLE = _make_crc_table()


def crc32_mpeg(data):
    crc = 0xFFFFFFFF
    for b in data:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ CRC_TABLE[((crc >> 24) ^ b) & 0xFF]
    return crc


# ---------------- 包长 / 同步偏移探测 ----------------
def detect_layout(path):
    """返回 (stride, sync_offset)；探测不到返回 None。"""
    with open(path, "rb") as f:
        head = f.read(4 * 1024 * 1024)
    need = 20
    for stride in (188, 192, 204):
        if len(head) < stride * (need + 1):
            continue
        for s0 in range(stride):
            sl = head[s0::stride][:need]
            if len(sl) == need and sl.count(0x47) == need:
                return stride, s0
    return None


def printable(b):
    """把 DVB 文本字节粗略转成可读字符串，仅用于显示/匹配。"""
    s = b.decode("utf-8", errors="replace")
    return "".join(ch for ch in s if ch >= " " and ch != "\x7f").strip()


# ---------------- SDT 处理器 ----------------
class SdtProcessor:
    def __init__(self, f, dry_run, keep_type, no_crc, matches):
        self.f = f
        self.dry_run = dry_run
        self.keep_type = keep_type
        self.no_crc = no_crc
        self.matches = matches
        self.buf = bytearray()
        self.segs = []          # [(文件偏移, 长度)]，对应 buf 里每一段字节
        self.sections = 0
        self.modified_sections = 0
        self.modified_services = 0
        self.first_offset = None
        self.seen = {}          # (provider, name, type) -> 次数  (tag 0x48)
        self.seen5d = {}        # (lang, provider, name) -> 次数  (tag 0x5D)
        self.tags_seen = {}     # descriptor tag -> 次数
        self.unparsed = 0       # 没解析到任何 service 的 section 数
        self.unparsed_example = None

    def reset(self):
        self.buf = bytearray()
        self.segs = []

    def _total(self):
        if len(self.buf) < 3:
            return None
        return 3 + (((self.buf[1] & 0x0F) << 8) | self.buf[2])

    def push(self, data, off):
        i, n = 0, len(data)
        while i < n:
            if not self.buf and data[i] == 0xFF:   # 填充字节，本包后面没有新 section
                break
            total = self._total()
            take = (3 - len(self.buf)) if total is None else (total - len(self.buf))
            take = min(take, n - i)
            self.buf += data[i:i + take]
            self.segs.append((off + i, take))
            i += take
            total = self._total()
            if total is not None and len(self.buf) == total:
                self.finish()
                self.reset()

    def feed_packet(self, pkt, file_off):
        b1 = pkt[1]
        if b1 & 0x80:                 # transport_error_indicator
            return
        afc = (pkt[3] >> 4) & 3
        if not (afc & 1):             # 没有 payload
            return
        start = 4
        if afc & 2:
            start = 5 + pkt[4]
        if start >= TS_PACKET:
            return
        payload = pkt[start:TS_PACKET]
        poff = file_off + start
        if b1 & 0x40:                 # payload_unit_start_indicator
            ptr = payload[0]
            if self.buf:
                self.push(payload[1:1 + ptr], poff + 1)
                self.reset()          # 没补完的残缺 section 丢弃
            self.push(payload[1 + ptr:], poff + 1 + ptr)
        elif self.buf:
            self.push(payload, poff)

    @staticmethod
    def _parse_48(sec, a, b):
        """service_descriptor: 返回 (stype, ps, pe, ns, ne) 或 None"""
        if b - a < 3:
            return None
        plen = sec[a + 1]
        ps, pe = a + 2, a + 2 + plen
        if pe + 1 > b:
            return None
        nlen = sec[pe]
        ns, ne = pe + 1, pe + 1 + nlen
        if ne > b:
            return None
        return sec[a], ps, pe, ns, ne

    @staticmethod
    def _parse_5d(sec, a, b):
        """multilingual_service_name_descriptor: 返回 [(lang, ps, pe, ns, ne), ...]"""
        res = []
        p = a
        while p + 4 <= b:
            plen = sec[p + 3]
            ps, pe = p + 4, p + 4 + plen
            if pe + 1 > b:
                break
            nlen = sec[pe]
            ns, ne = pe + 1, pe + 1 + nlen
            if ne > b:
                break
            res.append((bytes(sec[p:p + 3]).decode("ascii", "replace"), ps, pe, ns, ne))
            p = ne
        return res

    @staticmethod
    def _blank(sec, s, e):
        if e > s and sec[s:e] != b" " * (e - s):
            sec[s:e] = b" " * (e - s)
            return True
        return False

    label = "SDT"

    def _commit(self, sec, changed):
        """有修改才重算 CRC 并写回。"""
        if not changed:
            return
        if not self.no_crc:
            sec[-4:] = crc32_mpeg(bytes(sec[:-4])).to_bytes(4, "big")
        self.modified_sections += 1
        if self.first_offset is None:
            self.first_offset = self.segs[0][0]
            print(f"[首次命中] {self.label} section 在文件偏移 {self.first_offset}")
        if not self.dry_run:
            p = 0
            for off, ln in self.segs:
                self.f.seek(off)
                self.f.write(bytes(sec[p:p + ln]))
                p += ln

    def finish(self):
        sec = bytearray(self.buf)
        if sec[0] not in SDT_TABLES or len(sec) < 15:
            return
        self.sections += 1
        end = len(sec) - 4            # 最后 4 字节是 CRC32
        pos = 11                      # 前 3 字节头 + 8 字节固定字段后开始是 service 循环
        changed = False
        parsed_any = False

        while pos + 5 <= end:
            desc_len = ((sec[pos + 3] & 0x0F) << 8) | sec[pos + 4]
            d = pos + 5
            dend = min(d + desc_len, end)
            p48, p5d = [], []
            while d + 2 <= dend:
                tag, ln = sec[d], sec[d + 1]
                body = d + 2
                if body + ln > dend:
                    break
                self.tags_seen[tag] = self.tags_seen.get(tag, 0) + 1
                if tag == SERVICE_DESCRIPTOR_TAG:
                    r = self._parse_48(sec, body, body + ln)
                    if r:
                        p48.append((body,) + r)
                elif tag == MULTILINGUAL_DESCRIPTOR_TAG:
                    p5d.extend(self._parse_5d(sec, body, body + ln))
                d = body + ln
            pos += 5 + desc_len

            if not p48 and not p5d:
                continue
            parsed_any = True

            texts = []
            for _, _, ps, pe, ns, ne in p48:
                texts += [printable(bytes(sec[ps:pe])), printable(bytes(sec[ns:ne]))]
            for _, ps, pe, ns, ne in p5d:
                texts += [printable(bytes(sec[ps:pe])), printable(bytes(sec[ns:ne]))]
            if self.matches and not any(m in t for m in self.matches for t in texts):
                continue

            svc_changed = False
            for abody, stype, ps, pe, ns, ne in p48:
                key = (printable(bytes(sec[ps:pe])), printable(bytes(sec[ns:ne])), stype)
                self.seen[key] = self.seen.get(key, 0) + 1
                svc_changed |= self._blank(sec, ps, pe)
                svc_changed |= self._blank(sec, ns, ne)
                if not self.keep_type and stype != 0:
                    sec[abody] = 0
                    svc_changed = True
            for lang, ps, pe, ns, ne in p5d:
                key = (lang, printable(bytes(sec[ps:pe])), printable(bytes(sec[ns:ne])))
                self.seen5d[key] = self.seen5d.get(key, 0) + 1
                svc_changed |= self._blank(sec, ps, pe)
                svc_changed |= self._blank(sec, ns, ne)
            if svc_changed:
                changed = True
                self.modified_services += 1

        if not parsed_any:
            self.unparsed += 1
            if self.unparsed_example is None:
                self.unparsed_example = (self.segs[0][0], bytes(sec[:96]).hex(" "))

        self._commit(sec, changed)


class NitProcessor(SdtProcessor):
    """NIT (PID 0x0010)：把 service_list_descriptor (tag 0x41) 里的 service_type 置 0。"""
    label = "NIT"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.seen_list = {}     # (service_id, service_type) -> 次数

    def _scan_desc(self, sec, a, b):
        changed = False
        d = a
        while d + 2 <= b:
            tag, ln = sec[d], sec[d + 1]
            body = d + 2
            if body + ln > b:
                break
            if tag == SERVICE_LIST_TAG:
                r = body
                while r + 3 <= body + ln:
                    sid = (sec[r] << 8) | sec[r + 1]
                    stype = sec[r + 2]
                    key = (sid, stype)
                    self.seen_list[key] = self.seen_list.get(key, 0) + 1
                    if stype != 0:
                        sec[r + 2] = 0
                        changed = True
                    r += 3
            d = body + ln
        return changed

    def finish(self):
        sec = bytearray(self.buf)
        if sec[0] not in NIT_TABLES or len(sec) < 16:
            return
        self.sections += 1
        end = len(sec) - 4
        pos = 8                                   # 3 字节头 + network_id(2) + 版本(1) + section 号(2)
        if pos + 2 > end:
            return
        nd_len = ((sec[pos] & 0x0F) << 8) | sec[pos + 1]
        changed = self._scan_desc(sec, pos + 2, min(pos + 2 + nd_len, end))
        pos += 2 + nd_len
        if pos + 2 > end:
            self._commit(sec, changed)
            return
        ts_len = ((sec[pos] & 0x0F) << 8) | sec[pos + 1]
        pos += 2
        tend = min(pos + ts_len, end)
        while pos + 6 <= tend:
            td_len = ((sec[pos + 4] & 0x0F) << 8) | sec[pos + 5]
            d = pos + 6
            if self._scan_desc(sec, d, min(d + td_len, tend)):
                changed = True
            pos = d + td_len
        if changed:
            self.modified_services += 1
        self._commit(sec, changed)


# ---------------- 主流程 ----------------
def scan_file(path, dry_run, keep_type, no_crc, matches):
    layout = detect_layout(path)
    if layout is None:
        print("跳过：没有探测到 TS 同步字节 0x47（不是 TS / M2TS 文件），不处理。")
        return None
    stride, s0 = layout
    kind = {188: "标准 TS", 192: "M2TS (192 字节)", 204: "TS + RS 校验 (204 字节)"}[stride]
    print(f"[布局] {kind}，包长 {stride}，同步偏移 {s0}")

    size = os.path.getsize(path)
    bad_sync = 0
    chunk_pkts = max(1, CHUNK_BYTES // stride)

    with open(path, "rb" if dry_run else "r+b") as f:
        proc = SdtProcessor(f, dry_run, keep_type, no_crc, matches)
        nit = NitProcessor(f, dry_run, keep_type, no_crc, matches)
        do_nit = not keep_type and not matches     # 用了 --match 时不动 NIT（里面没有名字可匹配）
        pos = s0
        while pos + stride <= size:
            f.seek(pos)
            data = f.read(chunk_pkts * stride)
            n = len(data) // stride
            if n == 0:
                break
            arr = np.frombuffer(data, dtype=np.uint8, count=n * stride).reshape(n, stride)
            ok = arr[:, 0] == 0x47
            bad_sync += int(n - ok.sum())
            pids = ((arr[:, 1].astype(np.uint16) & 0x1F) << 8) | arr[:, 2].astype(np.uint16)
            sel = ok & ((pids == SDT_PID) | ((pids == NIT_PID) if do_nit else False))
            idx = np.nonzero(sel)[0]
            for i in idx:
                target = nit if int(pids[i]) == NIT_PID else proc
                target.feed_packet(arr[i, :TS_PACKET].tobytes(), pos + int(i) * stride)
            pos += n * stride

    if bad_sync:
        print(f"[警告] 有 {bad_sync} 个包同步字节不是 0x47（已忽略），文件可能有损坏或丢同步。")
    proc.nit = nit
    proc.do_nit = do_nit
    return proc


def _norm(k):
    return k.replace(" ", "").replace("_", "").lower()


def _iter_items(d):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from _iter_items(v)
        else:
            yield k, v


SERVICE_KEYS = {"serviceprovider", "servicename", "servicetype", "servicetypestring"}


def _effectively_empty(v):
    """'en: - zh:' 这类只剩语言前缀和分隔符的值，视为空。"""
    t = re.sub(r"(?<![A-Za-z])[A-Za-z]{2,3}:", "", v).replace("-", "")
    return t.strip() == ""


def precheck_mediainfo(path):
    """
    用 mediainfo JSON 预检。返回 (有无Service字段, 字段列表)；
    mediainfo 不可用或失败时返回 (None, [])，表示无法判断。
    """
    try:
        out = subprocess.check_output(
            ["mediainfo", "--Output=JSON", "--Full", path], stderr=subprocess.DEVNULL)
        mi = json.loads(out.decode("utf-8", errors="replace"))
    except Exception:
        return None, []
    tracks = mi.get("media", {}).get("track", [])
    if isinstance(tracks, dict):
        tracks = [tracks]
    hits = []
    for t in tracks:
        for k, v in _iter_items(t):
            if _norm(k) in SERVICE_KEYS and isinstance(v, str) and not _effectively_empty(v):
                hits.append((k, v))
    return bool(hits), hits


DETAIL_FIELD_RE = re.compile(
    r"^\s*([0-9A-Fa-f]{6,})\s+(service_type|service_provider_name|service_name|provider_name):\s*(.*?)\s*$")
DETAIL_TABLE_RE = re.compile(r"table_id:\s*\d+\s*\(0x([0-9A-Fa-f]+)\)(.*)")


def diagnose_residual(path, limit=5):
    """
    用 mediainfo --Details=1 流式读取，找出仍然有值的 service_type / provider / name 字段，
    打印所在偏移和所属的表，找到 limit 处就停止（不读完整个输出）。
    """
    try:
        proc = subprocess.Popen(["mediainfo", "--Details=1", path],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except Exception:
        print("[定位] 无法运行 mediainfo --Details=1。")
        return
    print(f"[定位] 用 mediainfo --Details=1 查找残留位置（最多 {limit} 处，可能要一点时间）...")
    last_table = "未知表"
    found = 0
    try:
        for raw in proc.stdout:
            line = raw.decode("utf-8", errors="replace").rstrip()
            m = DETAIL_TABLE_RE.search(line)
            if m:
                last_table = f"table_id 0x{m.group(1).upper()}{m.group(2)}"
                continue
            m = DETAIL_FIELD_RE.match(line)
            if not m:
                continue
            off, key, val = m.groups()
            if key == "service_type":
                if val == "0" or val.startswith("0 "):
                    continue
            elif not val.strip():
                continue
            found += 1
            print(f"  - 文件偏移 {int(off, 16)} (0x{off.lstrip('0').upper() or '0'}) "
                  f"{key} = {val}   [{last_table}]")
            if found >= limit:
                break
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    if found == 0:
        print("  （没有找到明确的残留字段，可能是 mediainfo 其他位置的值，请贴相关输出给我）")


def final_check(path):
    """
    收尾检查：
      1) mediainfo JSON 检查 Service 字段；没有残留 -> 结束。
      2) 有残留 -> 自动运行 mediainfo --Details=1 定位残留（最多 5 处）。
      3) 定位完毕后，再用 mediainfo JSON 检查一遍。
      4) 此时仍有残留才询问 y / n：回车或 y（默认）= 忽略，n = 不忽略（退出码 1）。
    """
    print("\n[收尾检查] 重新用 mediainfo 检查 Service 字段...")
    has, hits = precheck_mediainfo(path)
    if has is None:
        print("[收尾检查] mediainfo 不可用或执行失败，无法检查。")
        return True
    if not has:
        print("[收尾检查] 已清理干净，mediainfo 里没有 Service 字段了。")
        return True

    print("[收尾检查] 没有去除干净，mediainfo 仍然读到：")
    for k, v in hits:
        print(f"  - {k} = \"{v}\"")

    diagnose_residual(path)

    print("\n[收尾检查] 定位完毕，再用 mediainfo JSON 检查一遍...")
    has, hits = precheck_mediainfo(path)
    if has is None:
        print("[收尾检查] mediainfo 不可用或执行失败，无法再次检查。")
        return True
    if not has:
        print("[收尾检查] 已清理干净，mediainfo 里没有 Service 字段了。")
        return True
    print("[收尾检查] 仍有残留：")
    for k, v in hits:
        print(f"  - {k} = \"{v}\"")

    try:
        ans = input("是否忽略？[Y/n]（默认 y）: ").strip().lower()
    except EOFError:      # 非交互环境（管道/计划任务）按默认处理
        ans = ""
    if ans in ("", "y", "yes"):
        print("已忽略。")
        return True
    print("未忽略：该文件仍有残留，请检查。")
    return False


def verify_with_mediainfo(path):
    try:
        out = subprocess.check_output(["mediainfo", path], stderr=subprocess.STDOUT)
    except Exception:
        print("（未能运行 mediainfo，跳过校验）")
        return
    print("\n[校验] mediainfo 里 Service 相关字段：")
    found = False
    for line in out.decode("utf-8", errors="replace").splitlines():
        if line.strip().lower().startswith("service"):
            print("  " + line.strip())
            found = True
    if not found:
        print("  （没有 Service 相关字段）")


def main():
    ap = argparse.ArgumentParser(description="按 SDT 结构精确清除 TS 里的 Service provider/name/type")
    ap.add_argument("file", help="TS / M2TS 文件路径")
    ap.add_argument("--dry-run", action="store_true", help="只解析并打印，不写入")
    ap.add_argument("--keep-type", action="store_true", help="不修改 service_type")
    ap.add_argument("--no-crc", action="store_true", help="修改后不重算 CRC32")
    ap.add_argument("--match", action="append", default=[],
                    help="只处理 provider 或 name 包含该文字的 service，可重复；不传则处理全部")
    ap.add_argument("--no-precheck", action="store_true",
                    help="不做 mediainfo 预检，直接扫描 SDT")
    ap.add_argument("--no-final-check", action="store_true",
                    help="处理后不做 mediainfo 收尾检查")
    ap.add_argument("--diagnose", action="store_true",
                    help="只做诊断：用 mediainfo --Details=1 找出仍有值的 service 字段位置，不修改文件")
    ap.add_argument("--verify", action="store_true", help="处理后用 mediainfo 再看一遍 Service 字段")
    args = ap.parse_args()

    skipped = should_skip(args.file)
    if skipped:
        print(f"跳过：{skipped} 属于压缩包/镜像格式，不处理（{args.file}）")
        return
    if not os.path.isfile(args.file):
        print(f"错误：找不到文件 {args.file}")
        sys.exit(1)

    if args.diagnose:
        diagnose_residual(args.file)
        return

    if not args.no_precheck:
        print(f"正在用 mediainfo 预检: {args.file}")
        has, hits = precheck_mediainfo(args.file)
        if has is None:
            print("[预检] mediainfo 不可用或执行失败，无法预检，继续直接扫描。")
        elif not has:
            print("跳过：mediainfo 里没有 Service provider / name / type 字段，不需要处理。")
            return
        else:
            for k, v in hits:
                print(f"[预检] {k} = \"{v}\"")

    proc = scan_file(args.file, args.dry_run, args.keep_type, args.no_crc, args.match)
    if proc is None:
        return

    print()
    print(f"解析到 SDT section：{proc.sections} 个")
    print(f"需要修改的 section：{proc.modified_sections} 个，service 描述符：{proc.modified_services} 处"
          f"{'（dry-run，未实际写入）' if args.dry_run else ''}")
    if proc.seen:
        print("\n出现过的 service（provider / name / service_type -> 次数）：")
        for (p, n, t), c in sorted(proc.seen.items(), key=lambda x: -x[1]):
            print(f"  - \"{p}\" / \"{n}\" / 0x{t:02X} -> {c} 次")
    if proc.seen5d:
        print("\n多语言名称 (tag 0x5D)（语言 / provider / name -> 次数）：")
        for (l, p, n), c in sorted(proc.seen5d.items(), key=lambda x: -x[1]):
            print(f"  - {l} / \"{p}\" / \"{n}\" -> {c} 次")
    if proc.tags_seen:
        tags = ", ".join(f"0x{t:02X}x{c}" for t, c in sorted(proc.tags_seen.items()))
        print(f"\nSDT 里出现的描述符 tag：{tags}")
    if proc.unparsed:
        print(f"\n[注意] 有 {proc.unparsed} 个 SDT section 没解析到任何 service 描述符，"
              f"示例（文件偏移 {proc.unparsed_example[0]}，前 96 字节）：")
        print("  " + proc.unparsed_example[1])
    if proc.sections == 0:
        print("\n没有找到任何 SDT 表（PID 0x0011, table_id 0x42/0x46）。")

    nit = proc.nit
    if not proc.do_nit:
        why = "用了 --keep-type" if args.keep_type else "用了 --match"
        print(f"\n[NIT] 未处理（{why}）。")
    else:
        print(f"\n[NIT] 解析到 {nit.sections} 个 section，需要修改 {nit.modified_sections} 个"
              f"{'（dry-run，未实际写入）' if args.dry_run else ''}")
        if nit.seen_list:
            print("  service_list_descriptor (tag 0x41)（service_id / service_type -> 次数）：")
            for (sid, t), c in sorted(nit.seen_list.items(), key=lambda x: -x[1]):
                print(f"    - {sid} / 0x{t:02X} -> {c} 次")

    if args.verify and not args.dry_run:
        verify_with_mediainfo(args.file)

    if not args.dry_run and not args.no_final_check:
        if not final_check(args.file):
            sys.exit(1)


if __name__ == "__main__":
    main()
