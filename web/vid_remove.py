#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vid_remove.py

自动用 mediainfo 提取文件里的指定字段（比如 Service provider / Service name /
Service type / videoai），把这些字段的值当作"要清空的文字"，在文件里按原始字节搜索
所有出现位置，原地替换成等长空格，不改变文件大小、不解析容器结构本身。

三类规则：
1. 普通字段（DEFAULT_FIELDS）：只要 mediainfo 里这个字段有值，就清空该值。
2. 条件规则（CONDITIONAL_RULES）：只有字段的值包含指定关键字时才清空。
   例如 Writing application / Writing library 只有值里含 "ShanaEncoder" 才清，
   值是别的（如 Lavf61.3.103）则完全不动。
3. 伪字段 "*UTC"：先检查 mediainfo JSON 里是否有字段的值符合
   "YYYY-MM-DD HH:MM:SS UTC" 格式，有才对整个文件做正则全文扫描并清空；
   没有就跳过全文件正则扫描。

mediainfo JSON 会把非标准标签（如 videoai）放进嵌套的 "extra" 字典里，
所以这里用 iter_track_items 递归展开所有嵌套字典。

依赖:
    需要系统装有 mediainfo 命令行工具（例如: sudo apt install mediainfo）

用法:
    python3 vid_remove.py 文件.mp4
    python3 vid_remove.py 文件.mp4 --dry-run
    python3 vid_remove.py 文件.mp4 --field "Title"         # 在默认字段基础上追加
    python3 vid_remove.py 文件.mp4 --only-field "Title"    # 只用这一个字段，不用默认的
    python3 vid_remove.py 文件.mp4 --only-field "*UTC"     # 只检查/清空 UTC 时间戳
    python3 vid_remove.py 文件.mp4 --no-rules              # 不启用条件规则
    python3 vid_remove.py 文件.mp4 --text "手动指定的额外文字"
"""

import os
import re
import sys
import json
import argparse
import subprocess

CHUNK_SIZE = 32 * 1024 * 1024  # 32MB 一块，顺序读取

# ==== 在这里自定义要自动抓取的 mediainfo 字段名 ====
# 大小写、空格、下划线都不敏感（内部会归一化比较）
DEFAULT_FIELDS = [
    "Service provider",
    "Service name",
    "Service type",
    "videoai",
    "*UTC",
]

# ==== 条件规则：(字段名列表, 关键字列表) ====
# 只有当这些字段中某个字段的值"包含"关键字（不区分大小写）时，才清空。
# 值不含关键字时，该字段原样保留。
# 注意：mediainfo 界面里显示的 "Writing application" / "Writing library"，
# 在 JSON(--Full) 里的键名其实是 Encoded_Application / Encoded_Library，
# 所以两种叫法都列出来，保证都能匹配上。
CONDITIONAL_RULES = [
    (
        [
            "Writing application",
            "Writing library",
            "Encoded_Application",
            "Encoded_Application_String",
            "Encoded_Library",
            "Encoded_Library_String",
            "Encoded_Library_Name",
        ],
        ["ShanaEncoder"],
    ),
]

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
    if isinstance(tracks, dict):  # 只有一个 track 时可能不是列表
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
    """普通字段：只要字段名匹配且有值，就收集该值。"""
    wanted_norm = {normalize_key(f): f for f in wanted_fields}
    found = {}  # 归一化字段名 -> 值

    for track in get_tracks(mi_json):
        for k, v in iter_track_items(track):
            nk = normalize_key(k)
            if nk in wanted_norm and isinstance(v, str) and v.strip() != "":
                found[nk] = v
                print(f"[提取到] {wanted_norm[nk]} (mediainfo字段: {k}) = \"{v}\"")

    return found


def extract_conditional(mi_json: dict, rules):
    """
    条件规则：字段名匹配，并且值里包含关键字时，才收集。
    收集内容：字段的完整值 + 值里实际匹配到的关键字原文（保持文件里的大小写）。
    返回文字列表（可能重复，后面统一去重）。
    """
    results = []
    rule_list = [
        ({normalize_key(f) for f in fields}, keywords)
        for fields, keywords in rules
    ]

    for track in get_tracks(mi_json):
        for k, v in iter_track_items(track):
            if not isinstance(v, str) or v.strip() == "":
                continue
            nk = normalize_key(k)
            for field_set, keywords in rule_list:
                if nk not in field_set:
                    continue
                v_lower = v.lower()
                for kw in keywords:
                    pos = v_lower.find(kw.lower())
                    if pos == -1:
                        continue
                    matched = v[pos:pos + len(kw)]
                    print(f"[条件命中] mediainfo字段 {k} = \"{v}\"，含关键字 \"{kw}\"")
                    results.append(v)
                    if matched != v:
                        results.append(matched)
    return results


def mediainfo_has_utc_timestamp(mi_json: dict):
    """mediainfo 里是否有字段的值符合 UTC 时间戳格式。命中返回 (字段名, 值)。"""
    for track in get_tracks(mi_json):
        for k, v in iter_track_items(track):
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

    # 长的先处理，避免短的先把长的破坏掉
    patterns.sort(key=lambda p: len(p[1]), reverse=True)

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
        description="自动用 mediainfo 提取指定字段，在文件里原地替换为等长空格"
                    "（不改变文件大小）。支持条件规则（值含指定关键字才清）和 *UTC 伪字段。")
    parser.add_argument("file", help="要处理的文件路径")
    parser.add_argument("--field", action="append", default=[],
                        help="额外要抓取的字段名，追加到默认字段列表，可重复传多次。"
                             "也可以传 \"*UTC\" 来额外开启 UTC 时间戳检查/清空。")
    parser.add_argument("--only-field", action="append", default=None,
                        help="只用这些字段（忽略默认字段列表），可重复传多次。")
    parser.add_argument("--text", action="append", default=[],
                        help="手动额外指定的文字，不依赖mediainfo，可重复传多次")
    parser.add_argument("--no-rules", action="store_true",
                        help="不启用 CONDITIONAL_RULES 条件规则（如 ShanaEncoder）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只查找并打印命中次数，不实际写入")
    args = parser.parse_args()

    wanted_fields_raw = args.only_field if args.only_field is not None else DEFAULT_FIELDS + args.field

    use_utc_regex_requested = any(is_utc_marker(f) for f in wanted_fields_raw)
    wanted_fields = [f for f in wanted_fields_raw if not is_utc_marker(f)]
    rules = [] if args.no_rules else CONDITIONAL_RULES

    mi_json = None
    found = {}
    conditional_texts = []

    if wanted_fields or use_utc_regex_requested or rules:
        print(f"正在用 mediainfo 分析文件: {args.file}")
        mi_json = run_mediainfo(args.file)
        if wanted_fields:
            found = extract_fields(mi_json, wanted_fields)
        if rules:
            conditional_texts = extract_conditional(mi_json, rules)
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

    texts = list(found.values()) + conditional_texts + args.text
    seen = set()
    uniq_texts = []
    for t in texts:
        if t not in seen:
            seen.add(t)
            uniq_texts.append(t)

    if not uniq_texts and not use_utc_regex:
        print("没有从 mediainfo 抓到任何目标值，也没有手动指定 --text，"
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
