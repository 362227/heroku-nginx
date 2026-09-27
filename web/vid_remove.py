#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vid_remove.py

自动用 mediainfo 提取文件里的指定字段（比如 Service provider / Service name /
Service type），把这些字段的值当作"要清空的文字"，在文件里按原始字节搜索
所有出现位置，原地替换成等长空格，不改变文件大小、不解析容器结构本身。

另外支持一个特殊伪字段 "*UTC"：不经过普通字段匹配，而是先检查 mediainfo
JSON 里是否有任何字段的值本身就符合 "YYYY-MM-DD HH:MM:SS UTC" 格式
（比如 "2026-09-26 13:55:54 UTC"）——如果有，才会对整个文件做正则全文扫描
并把匹配到的文字原地替换成等长空格；如果 mediainfo 里根本没有这种格式的
值，就直接跳过全文件扫描，不浪费时间。
这个开关的用法和普通字段完全一样——把 "*UTC" 放进 DEFAULT_FIELDS /
--field / --only-field 里即可，不需要额外的参数。

依赖:
    需要系统装有 mediainfo 命令行工具（例如: sudo apt install mediainfo）
    （如果既没有普通字段也没有 *UTC，会完全跳过 mediainfo 调用）

用法:
    python3 vid_remove.py 文件.mkv
    python3 vid_remove.py 文件.mkv --dry-run
    python3 vid_remove.py 文件.mkv --field "Title"        # 在默认字段基础上追加
    python3 vid_remove.py 文件.mkv --only-field "Title"   # 只用这一个字段，不用默认的
    python3 vid_remove.py 文件.mkv --only-field "*UTC"    # 只检查/清空 UTC 时间戳
    python3 vid_remove.py 文件.mkv --text "手动指定的额外文字"  # 完全不依赖mediainfo也能加

默认抓取字段在下面 DEFAULT_FIELDS 里，直接改这个列表就能自定义。
"""

import os
import re
import sys
import json
import argparse
import subprocess

CHUNK_SIZE = 32 * 1024 * 1024  # 32MB 一块，顺序读取

# ==== 在这里自定义要自动抓取的 mediainfo 字段名 ====
# 大小写、空格、下划线都不敏感（内部会归一化比较），随便写成 mediainfo 显示的样子即可
# 特殊伪字段 "*UTC"：先检查 mediainfo 里是否存在该格式的时间戳，存在才用正则在
# 整个文件里查找并清空。
DEFAULT_FIELDS = [
    "Service provider",
    "Service name",
    "Service type",
    "00000000000000000000000000000000UTC",
]

# 匹配形如 "2026-09-27 15:00:00 UTC" 的时间戳，长度固定（23字节），
# 方便和普通字段一样按等长空格原地替换。
UTC_TIME_REGEX = re.compile(rb"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC")
# 字符串版本，用来检查 mediainfo JSON 里的字段值是否含有该格式（存在性检查用）
UTC_TIME_REGEX_STR = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC")
UTC_MAX_LEN = 23  # "YYYY-MM-DD HH:MM:SS UTC" 的字节长度
UTC_LABEL = "*UTC (正则时间戳)"
UTC_MARKER = "*utc"  # 归一化后用于识别伪字段的标记


def normalize_key(k: str) -> str:
    """把字段名统一成不含空格/下划线的小写形式，方便比较。
    "Service_Provider" / "Service provider" / "ServiceProvider" 都会变成 "serviceprovider"
    """
    return k.replace(" ", "").replace("_", "").lower()


def is_utc_marker(field: str) -> bool:
    """判断某个字段名是否是特殊的 "*UTC" 伪字段标记（大小写不敏感）。"""
    return field.strip().lower() == UTC_MARKER


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


def extract_fields(mi_json: dict, wanted_fields):
    """
    遍历 mediainfo JSON 里的所有 track（General/Video/Audio/Menu...），
    把每个字段名归一化后跟 wanted_fields 比对，命中的值收集起来（去重打印）。
    """
    wanted_norm = {normalize_key(f): f for f in wanted_fields}
    found = {}  # 归一化字段名 -> 值

    media = mi_json.get("media", {})
    tracks = media.get("track", [])
    if isinstance(tracks, dict):  # 只有一个track时可能不是列表
        tracks = [tracks]

    for track in tracks:
        for k, v in track.items():
            nk = normalize_key(k)
            if nk in wanted_norm and isinstance(v, str) and v.strip() != "":
                found[nk] = v
                print(f"[提取到] {wanted_norm[nk]} (mediainfo字段: {k}) = \"{v}\"")

    return found


def mediainfo_has_utc_timestamp(mi_json: dict):
    """
    检查 mediainfo JSON 里是否有任何字段的值本身符合 UTC 时间戳格式
    （"YYYY-MM-DD HH:MM:SS UTC"），比如 "Encoded date" / "Tagged date" 等字段
    的值。命中返回 (字段名, 值)，没有命中返回 None。
    """
    media = mi_json.get("media", {})
    tracks = media.get("track", [])
    if isinstance(tracks, dict):
        tracks = [tracks]

    for track in tracks:
        for k, v in track.items():
            if isinstance(v, str) and UTC_TIME_REGEX_STR.search(v):
                return (k, v)
    return None


def blank_occurrences(path: str, texts, dry_run: bool, use_utc_regex: bool = False):
    if not texts and not use_utc_regex:
        print("没有要处理的文字，退出。")
        return

    patterns = []
    for t in texts:
        b = t.encode("utf-8")
        if len(b) == 0:
            continue
        patterns.append((t, b, bytes([0x20]) * len(b)))

    if not patterns and not use_utc_regex:
        print("没有有效的搜索文字，退出。")
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
                    idx = m.start()
                    end = m.end()
                    length = end - idx
                    abs_offset = buf_base_offset + idx
                    total_hits[UTC_LABEL] += 1
                    if total_hits[UTC_LABEL] == 1:
                        matched_text = buf[idx:end].decode("ascii", errors="replace")
                        print(f"[首次命中] UTC时间戳 \"{matched_text}\" 在文件偏移 {abs_offset}")
                    if not dry_run:
                        f.seek(abs_offset)
                        f.write(bytes([0x20]) * length)

            offset += len(data)
            carry = buf[-overlap:] if overlap > 0 else b""

    print()
    for t, _, _ in patterns:
        print(f"\"{t}\": 共命中 {total_hits[t]} 次"
              f"{'（dry-run，未实际写入）' if dry_run else ''}")
    if use_utc_regex:
        print(f"{UTC_LABEL}: 共命中 {total_hits[UTC_LABEL]} 次"
              f"{'（dry-run，未实际写入）' if dry_run else ''}")


def main():
    parser = argparse.ArgumentParser(
        description="自动用 mediainfo 提取指定字段（如 Service provider/name/type），"
                    "在文件里原地替换为等长空格（不改变文件大小）。"
                    "特殊伪字段 *UTC 会先检查 mediainfo 中是否存在 "
                    "\"YYYY-MM-DD HH:MM:SS UTC\" 格式的值，存在才对全文件做正则清空。")
    parser.add_argument("file", help="要处理的文件路径")
    parser.add_argument("--field", action="append", default=[],
                         help="额外要抓取的字段名，追加到默认字段列表，可重复传多次。"
                              "也可以传 \"*UTC\" 来额外开启 UTC 时间戳检查/清空。")
    parser.add_argument("--only-field", action="append", default=None,
                         help="只用这些字段（忽略默认字段列表），可重复传多次。"
                              "也可以只传 \"*UTC\"。")
    parser.add_argument("--text", action="append", default=[],
                         help="手动额外指定的文字，不依赖mediainfo，可重复传多次")
    parser.add_argument("--dry-run", action="store_true",
                         help="只查找并打印命中次数，不实际写入")
    args = parser.parse_args()

    wanted_fields_raw = args.only_field if args.only_field is not None else DEFAULT_FIELDS + args.field

    # 把 "*UTC" 这个伪字段单独摘出来，不参与普通 mediainfo 字段匹配
    use_utc_regex_requested = any(is_utc_marker(f) for f in wanted_fields_raw)
    wanted_fields = [f for f in wanted_fields_raw if not is_utc_marker(f)]

    mi_json = None
    found = {}

    if wanted_fields or use_utc_regex_requested:
        print(f"正在用 mediainfo 分析文件: {args.file}")
        mi_json = run_mediainfo(args.file)
        if wanted_fields:
            found = extract_fields(mi_json, wanted_fields)
    else:
        print("未指定任何 mediainfo 字段，跳过 mediainfo 分析。")

    # *UTC：先检查 mediainfo 里是否真的存在该格式的时间戳，没有就不扫文件
    use_utc_regex = False
    if use_utc_regex_requested:
        hit = mediainfo_has_utc_timestamp(mi_json) if mi_json is not None else None
        if hit:
            field_name, field_value = hit
            use_utc_regex = True
            print(f"[*UTC] 在 mediainfo 字段 \"{field_name}\" 中发现时间戳: "
                  f"\"{field_value}\"，将启用全文件扫描清空。")
        else:
            print("[*UTC] mediainfo 中未发现该格式的时间戳，跳过全文件扫描。")

    texts = list(found.values()) + args.text
    seen = set()
    uniq_texts = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            uniq_texts.append(t)

    if not uniq_texts and not use_utc_regex:
        print("没有从 mediainfo 抓到任何目标字段的值，也没有手动指定 --text，"
              "*UTC 也未命中，无事可做。")
        return

    if uniq_texts:
        print()
        print("将要清空的文字列表：")
        for t in uniq_texts:
            print(f"  - \"{t}\"")
        print()

    blank_occurrences(args.file, uniq_texts, args.dry_run, use_utc_regex=use_utc_regex)


if __name__ == "__main__":
    main()
