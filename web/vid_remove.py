#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
https://claude.ai/chat/106d1dc4-e1de-4172-9c8b-cfed1eed640e
vid_remove.py

用 mediainfo 找出文件里含指定关键字的字段值，然后在文件里把它们原地清成等长空格，
不改变文件大小。

关键字（DEFAULT_KEYWORDS，不区分大小写）会匹配 mediainfo JSON 里所有字段的值
（含嵌套的 "extra"，如 videoai / Title 等）。命中后分两路处理：

  A. 命中的字段是 Service provider / Service name / Service type（SDT_FIELD_PREFIXES）
     → 按 MPEG-TS 的 SDT 表结构处理：
       解析 PID 0x11 上的 SDT 段（table_id 0x42/0x46，支持跨 TS 包拼段），
       在 service_descriptor(0x48) 里的 provider_name / service_name 中，
       含关键字（不区分大小写）的整段清成空格（保留编码前缀字节），
       然后重算该段的 CRC32，保证流仍然合法。
       service_type 只是 1 字节编码，不是文字，不会被改。
       如果文件不是 MPEG-TS（找不到 TS 同步结构），自动退回到 B 的做法。

  B. 命中的字段不是 Service 字段
     → 沿用以前的逻辑：把字段值（以及值里实际匹配到的关键字原文）
       当作文字，在整个文件里按字节搜索，替换成等长空格。

  两类都有命中就两类都做。A 先于 B 执行（这样 B 不会在 CRC 重算前破坏 SDT）。

普通字段（DEFAULT_FIELDS / --field / --only-field）只保留"清除值"逻辑：
字段有值就把该值清空。伪字段 "*UTC" 仍然可用（检查 mediainfo 里有没有
"YYYY-MM-DD HH:MM:SS UTC" 格式的值，有才全文件正则扫描清空）。

处理优先级（从高到低）：
1. 扩展名在 SKIP_EXTENSIONS 里（压缩包/镜像，含分卷）→ 一律跳过。
2. Service provider / name / type 里命中关键字 → 一定处理（不检查轨道）。
3. 否则：没有视频轨道也没有音频轨道 → 跳过；有 → 继续。

依赖:
    系统装有 mediainfo 命令行工具（例如: sudo apt install mediainfo）

用法:
    python3 vid_remove.py 文件.ts
    python3 vid_remove.py 文件.ts --dry-run
    python3 vid_remove.py 文件.ts --keyword "SomeTag"        # 在默认关键字基础上追加
    python3 vid_remove.py 文件.ts --only-keyword "HHWEB"     # 只用这些关键字
    python3 vid_remove.py 文件.ts --no-keywords              # 不启用关键字规则
    python3 vid_remove.py 文件.ts --field "Title"            # 额外的普通字段：有值就清空
    python3 vid_remove.py 文件.ts --only-field "*UTC"        # 只用这些普通字段
    python3 vid_remove.py 文件.ts --text "手动指定的额外文字"
"""

import os
import re
import sys
import json
import struct
import argparse
import subprocess

CHUNK_SIZE = 32 * 1024 * 1024  # 32MB 一块，顺序读取

# 这些扩展名的文件一律跳过（不区分大小写）
SKIP_EXTENSIONS = {
    ".zip", ".zipx", ".rar", ".7z",
    ".tar", ".gz", ".tgz", ".bz2", ".tbz", ".tbz2", ".xz", ".txz",
    ".zst", ".tzst", ".lz", ".lzma", ".lz4", ".z", ".lzo", ".br",
    ".cab", ".arj", ".lzh", ".lha", ".ace", ".cpio", ".sit", ".sitx",
    ".zoo", ".pak", ".alz", ".egg",
    ".jar", ".war", ".apk", ".ipa", ".xpi", ".rpm", ".deb",
    ".iso", ".img", ".dmg", ".wim", ".vhd", ".vhdx", ".vmdk", ".squashfs",
}

# 分卷压缩包：.001 .002 / .r00 .r01 / .z01 .z02 等
SKIP_SPLIT_REGEX = re.compile(r"\.(\d{3}|r\d{2}|z\d{2})$", re.IGNORECASE)


def should_skip(path: str):
    """是压缩包/镜像（含分卷）就返回命中的后缀，否则返回 None。"""
    name = os.path.basename(path).lower()
    ext = os.path.splitext(name)[1]
    if ext in SKIP_EXTENSIONS:
        return ext
    m = SKIP_SPLIT_REGEX.search(name)
    if m:
        return m.group(0)
    return None


# ==== 默认关键字（不区分大小写，值里"包含"即命中，命中后清空整个字段值）====
DEFAULT_KEYWORDS = [
    "Enhanced using",
    "HHWEB",
    "KPOPLIVE",
    "kpoplive.top",
    "QHstudIo",
]

# ==== 属于 Service 的字段（归一化后按"前缀"匹配，兼容 _String 之类的变体）====
# 关键字命中这些字段 → 走 MPEG-TS SDT 表结构处理。
# 如果你的 mediainfo 把 Title 之类也放在 Service 下面，想让它走 SDT，往这里加。
SDT_FIELD_PREFIXES = ("serviceprovider", "servicename", "servicetype")

# ==== 扫描关键字时忽略的字段（文件名/路径本身不在文件内容里）====
KEYWORD_IGNORE_PREFIXES = ("completename", "foldername", "filename", "fileextension")

# ==== 普通字段（只有"清除值"逻辑）====
# 大小写、空格、下划线都不敏感。"*UTC" 是伪字段。
DEFAULT_FIELDS = [
    "*000000000000000UTC",
]

# 字段名里只要有这些词（按下划线拆词、小写），就不拿来判断是否启用 *UTC 扫描
UTC_IGNORE_TOKENS = {"date", "dates", "duration"}


def is_date_key(key: str) -> bool:
    """xxx_Date / Duration_Start 这类字段不是文本，不用来判断是否启用 *UTC 扫描。"""
    tokens = set(key.replace(" ", "_").lower().split("_"))
    return bool(tokens & UTC_IGNORE_TOKENS)


# 匹配形如 "2026-09-27 15:00:00 UTC" 的时间戳，长度固定（23字节）
UTC_TIME_REGEX = re.compile(rb"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC")
UTC_TIME_REGEX_STR = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC")
UTC_MAX_LEN = 23
UTC_LABEL = "*UTC (正则时间戳)"
UTC_MARKER = "*utc"


def normalize_key(k: str) -> str:
    """字段名统一成不含空格/下划线的小写形式，方便比较。"""
    return k.replace(" ", "").replace("_", "").lower()


def is_utc_marker(field: str) -> bool:
    return field.strip().lower() == UTC_MARKER


def is_sdt_key(k: str) -> bool:
    return normalize_key(k).startswith(SDT_FIELD_PREFIXES)


def is_ignored_key(k: str) -> bool:
    return normalize_key(k).startswith(KEYWORD_IGNORE_PREFIXES)


# ----------------------------------------------------------------------
# mediainfo
# ----------------------------------------------------------------------
def run_mediainfo(path: str) -> dict:
    try:
        out = subprocess.check_output(
            ["mediainfo", "--Output=JSON", "--Full", path],
            stderr=subprocess.STDOUT,
        )
    except FileNotFoundError:
        print("错误：没有找到 mediainfo 命令，请先安装，例如: sudo apt install mediainfo")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print("mediainfo 执行失败：")
        print(e.output.decode(errors="replace"))
        sys.exit(1)
    return json.loads(out.decode("utf-8", errors="replace"))


def get_tracks(mi_json: dict):
    tracks = mi_json.get("media", {}).get("track", [])
    if isinstance(tracks, dict):
        tracks = [tracks]
    return tracks


def iter_track_items(track: dict):
    """遍历 track 里的所有键值对，递归展开嵌套字典（如 "extra"）。"""
    for k, v in track.items():
        if isinstance(v, dict):
            yield from iter_track_items(v)
        else:
            yield k, v


def extract_fields(mi_json: dict, wanted_fields):
    """普通字段：字段名匹配且有值，就收集该值（只有清除值逻辑）。"""
    wanted_norm = {normalize_key(f): f for f in wanted_fields}
    found = {}
    for track in get_tracks(mi_json):
        for k, v in iter_track_items(track):
            nk = normalize_key(k)
            if nk in wanted_norm and isinstance(v, str) and v.strip() != "":
                found[nk] = v
                print(f"[普通字段] {wanted_norm[nk]} (mediainfo字段: {k}) = \"{v}\"")
    return found


def extract_keyword_hits(mi_json: dict, keywords):
    """
    在所有字段的值里查找关键字（不区分大小写，包含即命中）。
    返回 [(字段名, 完整值, 命中的关键字, 值里匹配到的原文), ...]
    """
    hits = []
    for track in get_tracks(mi_json):
        for k, v in iter_track_items(track):
            if not isinstance(v, str) or v.strip() == "" or is_ignored_key(k):
                continue
            v_lower = v.lower()
            for kw in keywords:
                pos = v_lower.find(kw.lower())
                if pos == -1:
                    continue
                matched = v[pos:pos + len(kw)]
                route = "SDT" if is_sdt_key(k) else "全文件字节搜索"
                print(f"[关键字命中] {k} = \"{v}\"，含 \"{kw}\" → {route}")
                hits.append((k, v, kw, matched))
    return hits


def find_av_tracks(mi_json: dict):
    video = audio = 0
    for track in get_tracks(mi_json):
        t = str(track.get("@type", "")).lower()
        if t == "video":
            video += 1
        elif t == "audio":
            audio += 1
    return video, audio


def mediainfo_has_utc_timestamp(mi_json: dict):
    for track in get_tracks(mi_json):
        for k, v in iter_track_items(track):
            if is_date_key(k):
                continue
            if isinstance(v, str) and UTC_TIME_REGEX_STR.search(v):
                return (k, v)
    return None


# ----------------------------------------------------------------------
# MPEG-TS / SDT
# ----------------------------------------------------------------------
TS_PACKET_SIZES = (188, 192, 204)  # 188 标准 / 192 M2TS(4字节时间戳) / 204 带 RS
SDT_PID = 0x11
SDT_TABLE_IDS = (0x42, 0x46)  # actual / other TS


def _make_crc_table():
    table = []
    for i in range(256):
        c = i << 24
        for _ in range(8):
            c = ((c << 1) ^ 0x04C11DB7) if (c & 0x80000000) else (c << 1)
            c &= 0xFFFFFFFF
        table.append(c)
    return table


_CRC_TABLE = _make_crc_table()


def mpeg_crc32(data: bytes) -> int:
    """MPEG-2 CRC32（poly 0x04C11DB7，init 0xFFFFFFFF，不反转，不异或）。"""
    crc = 0xFFFFFFFF
    for b in data:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ _CRC_TABLE[((crc >> 24) ^ b) & 0xFF]
    return crc


def detect_ts_layout(f, file_size):
    """返回 (第一个同步字节偏移, 包间距)；不是 TS 返回 None。"""
    f.seek(0)
    head = f.read(204 * 12)
    for pkt in TS_PACKET_SIZES:
        for s in range(pkt):
            n = (len(head) - s) // pkt
            if n < 5:
                break
            if all(head[s + i * pkt] == 0x47 for i in range(min(n, 10))):
                return s, pkt
    return None


class Section:
    """跨 TS 包拼装一个 PSI 段，同时记录每一段对应的文件偏移，方便写回。"""

    def __init__(self):
        self.segs = []          # [(文件偏移, 长度)]，按段内顺序
        self.buf = bytearray()
        self.total = None

    @property
    def complete(self):
        return self.total is not None and len(self.buf) >= self.total

    def feed(self, abs_off: int, data: bytes) -> int:
        """喂数据，返回消耗的字节数（不会超过本段长度）。"""
        used = 0
        if self.total is None:
            k = min(3 - len(self.buf), len(data))
            if k > 0:
                self.segs.append((abs_off, k))
                self.buf += data[:k]
                used = k
            if len(self.buf) < 3:
                return used
            self.total = 3 + (((self.buf[1] & 0x0F) << 8) | self.buf[2])
        k = min(self.total - len(self.buf), len(data) - used)
        if k > 0:
            self.segs.append((abs_off + used, k))
            self.buf += data[used:used + k]
            used += k
        return used


def _text_matches(raw: bytes, kws_lower):
    low = raw.lower()
    for k in kws_lower:
        if k.encode("utf-8") in low:
            return True
    if raw[:1] == b"\x11":  # UCS-2 BE
        try:
            dec = raw[1:].decode("utf-16-be", errors="ignore").lower()
            return any(k in dec for k in kws_lower)
        except Exception:
            pass
    return False


def _blank_field(new: bytearray, start: int, length: int):
    """把 DVB 文本字段清成空格，保留开头的编码前缀字节。"""
    first = new[start]
    if first == 0x10:
        pre = 3
    elif first < 0x20:
        pre = 1
    else:
        pre = 0
    body = length - pre
    if body <= 0:
        return
    if first == 0x11:
        fill = (b"\x00\x20" * (body // 2 + 1))[:body]
    else:
        fill = b"\x20" * body
    new[start + pre:start + length] = fill


def patch_sdt(buf: bytes, kws_lower):
    """
    按 SDT 结构解析一个完整段：
      11 字节头 → 循环(service_id 2B, EIT 标志 1B, running/free_CA/desc_loop_len 2B, 描述符…) → CRC32
    在 service_descriptor(0x48) 里检查 provider_name / service_name。
    返回 (新段内容(CRC 尚未重算), [(标签, 原文本), ...])
    """
    new = bytearray(buf)
    hits = []
    end = len(buf) - 4
    pos = 11
    while pos + 5 <= end:
        dll = ((buf[pos + 3] & 0x0F) << 8) | buf[pos + 4]
        dpos = pos + 5
        dend = min(dpos + dll, end)
        while dpos + 2 <= dend:
            tag, dlen = buf[dpos], buf[dpos + 1]
            body = dpos + 2
            if body + dlen > dend:
                break
            if tag == 0x48 and dlen >= 3:
                # service_type(1) provider_len(1) provider service_len(1) service
                p_len = buf[body + 1]
                p_start = body + 2
                n_len_pos = p_start + p_len
                if n_len_pos < body + dlen:
                    n_len = buf[n_len_pos]
                    n_start = n_len_pos + 1
                    fields = [("Service provider", p_start, p_len)]
                    if n_start + n_len <= body + dlen:
                        fields.append(("Service name", n_start, n_len))
                    for label, s, l in fields:
                        if l <= 0:
                            continue
                        raw = bytes(buf[s:s + l])
                        if _text_matches(raw, kws_lower):
                            hits.append((label, raw.decode("utf-8", errors="replace")))
                            _blank_field(new, s, l)
            dpos = body + dlen
        pos += 5 + dll
    return new, hits


def process_sdt(path: str, keywords, dry_run: bool):
    """
    扫描整个文件里所有 PID 0x11 的 SDT 段并清除含关键字的 provider/service name，重算 CRC。
    不是 MPEG-TS 返回 None，否则返回统计 dict。
    """
    kws_lower = [k.lower() for k in keywords]
    file_size = os.path.getsize(path)
    stats = {"sdt_sections": 0, "modified": 0, "fields": 0}
    first_print = [True]

    with open(path, "rb" if dry_run else "r+b") as f:
        layout = detect_ts_layout(f, file_size)
        if layout is None:
            return None
        sync, pkt = layout
        print(f"[SDT] 识别为 MPEG-TS：包长 {pkt}，首个同步字节偏移 {sync}")

        def handle(sec: Section):
            buf = bytes(sec.buf[:sec.total])
            if len(buf) < 15 or buf[0] not in SDT_TABLE_IDS:
                return
            stats["sdt_sections"] += 1
            new, hits = patch_sdt(buf, kws_lower)
            if not hits:
                return
            new[-4:] = struct.pack(">I", mpeg_crc32(bytes(new[:-4])))
            stats["modified"] += 1
            stats["fields"] += len(hits)
            if first_print[0]:
                first_print[0] = False
                for label, text in hits:
                    print(f"[SDT 首次命中] {label} = \"{text}\"，文件偏移 {sec.segs[0][0]}")
            if dry_run:
                return
            bo = 0
            for off, ln in sec.segs:
                if new[bo:bo + ln] != buf[bo:bo + ln]:
                    f.seek(off)
                    f.write(bytes(new[bo:bo + ln]))
                bo += ln

        chunk_bytes = max(1, CHUNK_SIZE // pkt) * pkt
        pos = sync
        cur = None
        while pos < file_size:
            f.seek(pos)
            data = f.read(chunk_bytes)
            n = len(data) // pkt
            if n == 0:
                break
            for i in range(n):
                base = i * pkt
                p = data[base:base + 188]
                if p[0] != 0x47:
                    cur = None
                    continue
                pid = ((p[1] & 0x1F) << 8) | p[2]
                if pid != SDT_PID:
                    continue
                afc = (p[3] >> 4) & 3
                if not afc & 1:
                    continue
                ps = 4
                if afc & 2:
                    ps += 1 + p[4]
                if ps >= 188:
                    continue
                payload = p[ps:188]
                abs0 = pos + base + ps

                if p[1] & 0x40:  # payload_unit_start
                    ptr = payload[0]
                    tail = payload[1:1 + ptr]
                    if cur is not None and not cur.complete and tail:
                        cur.feed(abs0 + 1, tail)
                        if cur.complete:
                            handle(cur)
                    cur = None
                    idx = 1 + ptr
                    while idx < len(payload) and payload[idx] != 0xFF:
                        sec = Section()
                        used = sec.feed(abs0 + idx, payload[idx:])
                        if sec.complete:
                            handle(sec)
                            idx += used
                        else:
                            cur = sec
                            break
                elif cur is not None:
                    cur.feed(abs0, payload)
                    if cur.complete:
                        handle(cur)
                        cur = None
            pos += n * pkt
    return stats


# ----------------------------------------------------------------------
# 全文件字节搜索（旧逻辑）
# ----------------------------------------------------------------------
def blank_occurrences(path: str, texts, dry_run: bool, use_utc_regex: bool = False):
    if not texts and not use_utc_regex:
        print("没有要处理的文字，跳过全文件搜索。")
        return

    patterns = []
    for t in texts:
        b = t.encode("utf-8")
        if len(b) == 0:
            continue
        patterns.append((t, b, bytes([0x20]) * len(b)))

    patterns.sort(key=lambda p: len(p[1]), reverse=True)

    if not patterns and not use_utc_regex:
        print("没有有效的搜索文字，跳过全文件搜索。")
        return

    max_pat_len = max((len(p[1]) for p in patterns), default=0)
    if use_utc_regex:
        max_pat_len = max(max_pat_len, UTC_MAX_LEN)
    overlap = max_pat_len - 1 if max_pat_len > 0 else 0

    file_size = os.path.getsize(path)
    total_hits = {t: 0 for t, _, _ in patterns}
    if use_utc_regex:
        total_hits[UTC_LABEL] = 0

    mode = "rb" if dry_run else "r+b"
    with open(path, mode) as f:
        offset = 0
        carry = b""
        while offset < file_size:
            f.seek(offset)
            data = f.read(CHUNK_SIZE)
            if not data:
                break

            buf = carry + data
            buf_base_offset = offset - len(carry)

            for text, pat, replacement in patterns:
                search_from = 0
                while True:
                    idx = buf.find(pat, search_from)
                    if idx == -1:
                        break
                    abs_offset = buf_base_offset + idx
                    total_hits[text] += 1
                    if total_hits[text] == 1:
                        print(f"[首次命中] \"{text}\" 在文件偏移 {abs_offset}")
                    if not dry_run:
                        f.seek(abs_offset)
                        f.write(replacement)
                    search_from = idx + len(pat)

            if use_utc_regex:
                for m in UTC_TIME_REGEX.finditer(buf):
                    idx, end = m.start(), m.end()
                    abs_offset = buf_base_offset + idx
                    total_hits[UTC_LABEL] += 1
                    if total_hits[UTC_LABEL] == 1:
                        matched_text = buf[idx:end].decode("ascii", errors="replace")
                        print(f"[首次命中] UTC时间戳 \"{matched_text}\" 在文件偏移 {abs_offset}")
                    if not dry_run:
                        f.seek(abs_offset)
                        f.write(bytes([0x20]) * (end - idx))

            offset += len(data)
            carry = buf[-overlap:] if overlap > 0 else b""

    print()
    tag = "（dry-run，未实际写入）" if dry_run else ""
    for t, _, _ in patterns:
        print(f"\"{t}\": 共命中 {total_hits[t]} 次{tag}")
    if use_utc_regex:
        print(f"{UTC_LABEL}: 共命中 {total_hits[UTC_LABEL]} 次{tag}")


def dedupe(items):
    seen, out = set(), []
    for t in items:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def main():
    parser = argparse.ArgumentParser(
        description="用 mediainfo 找出含关键字的字段值并原地清成等长空格。"
                    "Service 字段按 MPEG-TS SDT 结构处理（并重算 CRC），其余字段全文件字节搜索。")
    parser.add_argument("file", help="要处理的文件路径")
    parser.add_argument("--keyword", action="append", default=[],
                        help="额外关键字（不区分大小写），追加到默认关键字，可重复。")
    parser.add_argument("--only-keyword", action="append", default=None,
                        help="只用这些关键字（忽略默认关键字），可重复。")
    parser.add_argument("--no-keywords", action="store_true",
                        help="不启用关键字规则")
    parser.add_argument("--field", action="append", default=[],
                        help="额外的普通字段名：有值就清空该值，可重复。"
                             "传 \"*UTC\" 可开启 UTC 时间戳检查/清空。")
    parser.add_argument("--only-field", action="append", default=None,
                        help="只用这些普通字段（忽略默认字段列表），可重复。")
    parser.add_argument("--text", action="append", default=[],
                        help="手动额外指定的文字，不依赖 mediainfo，可重复。")
    parser.add_argument("--dry-run", action="store_true",
                        help="只查找并打印命中次数，不实际写入")
    args = parser.parse_args()

    skipped_ext = should_skip(args.file)
    if skipped_ext:
        print(f"跳过：{skipped_ext} 属于压缩包/镜像格式，不处理（{args.file}）")
        return

    if args.no_keywords:
        keywords = []
    elif args.only_keyword is not None:
        keywords = args.only_keyword
    else:
        keywords = DEFAULT_KEYWORDS + args.keyword

    fields_raw = args.only_field if args.only_field is not None else DEFAULT_FIELDS + args.field
    use_utc_requested = any(is_utc_marker(f) for f in fields_raw)
    plain_fields = [f for f in fields_raw if not is_utc_marker(f)]

    print(f"正在用 mediainfo 分析文件: {args.file}")
    mi_json = run_mediainfo(args.file)

    kw_hits = extract_keyword_hits(mi_json, keywords) if keywords else []
    sdt_hits = [h for h in kw_hits if is_sdt_key(h[0])]
    plain_hits = [h for h in kw_hits if not is_sdt_key(h[0])]

    video_count, audio_count = find_av_tracks(mi_json)
    if sdt_hits:
        print("[优先] Service 字段命中关键字，一定处理，不检查轨道。")
        print(f"[轨道] 视频轨道 {video_count} 条，音频轨道 {audio_count} 条（仅供参考）")
    else:
        if video_count == 0 and audio_count == 0:
            print("跳过：mediainfo 没有识别到任何视频轨道或音频轨道，不是媒体文件，不处理。")
            return
        print(f"[轨道] 视频轨道 {video_count} 条，音频轨道 {audio_count} 条")

    # 普通字段（只清除值）
    found = extract_fields(mi_json, plain_fields) if plain_fields else {}

    # *UTC
    use_utc_regex = False
    if use_utc_requested:
        hit = mediainfo_has_utc_timestamp(mi_json)
        if hit:
            use_utc_regex = True
            print(f"[*UTC] 在 mediainfo 字段 \"{hit[0]}\" 中发现时间戳: \"{hit[1]}\"，将启用全文件扫描清空。")
        else:
            print("[*UTC] mediainfo 中未发现该格式的时间戳，跳过全文件扫描。")

    # ---- A. SDT ----
    plain_texts = list(found.values()) + args.text
    for _, v, _, matched in plain_hits:
        plain_texts.append(v)
        if matched != v:
            plain_texts.append(matched)

    if sdt_hits:
        sdt_kws = dedupe([h[2] for h in sdt_hits])
        print()
        print(f"[SDT] 按 MPEG-TS SDT 结构查询，关键字: {sdt_kws}")
        stats = process_sdt(args.file, sdt_kws, args.dry_run)
        if stats is None:
            print("[SDT] 文件不是 MPEG-TS，退回全文件字节搜索。")
            for _, v, _, matched in sdt_hits:
                plain_texts.append(v)
                if matched != v:
                    plain_texts.append(matched)
        else:
            tag = "（dry-run，未实际写入）" if args.dry_run else ""
            print(f"[SDT] 扫描 SDT 段 {stats['sdt_sections']} 个，"
                  f"修改 {stats['modified']} 个段，清空字段 {stats['fields']} 处，"
                  f"CRC 已重算{tag}")
            if any(normalize_key(h[0]).startswith("servicetype") for h in sdt_hits):
                print("[SDT] 提示：Service type 是 1 字节类型码，不是文字，不会被改。")

    # ---- B. 全文件字节搜索 ----
    uniq_texts = dedupe(plain_texts)
    if not uniq_texts and not use_utc_regex:
        if not sdt_hits:
            print("没有抓到任何目标值，也没有手动指定 --text，*UTC 也未命中，无事可做。")
        return

    if uniq_texts:
        print()
        print("全文件字节搜索将要清空的文字列表：")
        for t in uniq_texts:
            print(f"  - \"{t}\"")
        print()

    blank_occurrences(args.file, uniq_texts, args.dry_run, use_utc_regex=use_utc_regex)


if __name__ == "__main__":
    main()
