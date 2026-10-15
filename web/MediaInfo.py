#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MediaInfo.py —— 用 ffprobe 生成媒体信息 txt（需要先安装 ffmpeg）

用法:
    python MediaInfo.py 视频.mkv                  # BDInfo 风格 -> media_视频.txt
    python MediaInfo.py 视频.mkv --full           # 完整 MediaInfo 风格 -> media_视频_full.txt
    python MediaInfo.py /path                     # 文件夹（默认不递归，只处理该目录下的媒体文件）
    python MediaInfo.py /path/*                   # 与上一条等价（shell 展开后的文件会被一起处理）
    python MediaInfo.py /path -r                  # 递归子文件夹
    python MediaInfo.py /path -n 3                # 只取前 3 个文件（生成 3 个 txt）
    python MediaInfo.py /path -d /out             # 指定 txt 输出目录（默认是本脚本所在目录）

说明:
  * 输出文件名: media_文件名.txt；--full 时为 media_文件名_full.txt。
    文件名过长会自动截断；同名文件会在结尾加 (1)、(2) ...
  * 识别不到视频或音频信息的文件不会生成 txt，只打印错误。
  * 给了多个路径（例如 /path/* 被 shell 展开）时，其中的子文件夹默认被忽略，加 -r 才会递归进去；
    只给一个文件夹时，处理该文件夹下的文件。
  * 也可以当模块导入: get_media_info(path) -> (简洁文本, 完整文本)
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

BITMAP_SUB_CODECS = {"hdmv_pgs_subtitle", "dvd_subtitle", "xsub"}

MEDIA_EXTS = {
    # 视频
    ".mkv", ".mp4", ".m4v", ".mov", ".avi", ".wmv", ".flv", ".f4v", ".ts", ".m2ts", ".mts", ".mpg", ".mpeg",
    ".vob", ".webm", ".ogv", ".3gp", ".3g2", ".rm", ".rmvb", ".asf", ".divx", ".mxf", ".m2v", ".h264", ".264",
    ".h265", ".265", ".hevc", ".ivf", ".evo", ".mpv", ".y4m",
    # 音频
    ".mka", ".mp3", ".flac", ".wav", ".aac", ".m4a", ".ogg", ".oga", ".opus", ".wma", ".ape", ".ac3", ".eac3",
    ".ec3", ".dts", ".dtshd", ".thd", ".truehd", ".aiff", ".aif", ".alac", ".wv", ".tta", ".mp2", ".mpa", ".amr",
    ".mlp", ".dsf", ".dff", ".caf", ".au",
}


class MediaInfoError(Exception):
    """识别不到视频/音频信息，或文件无法读取"""


# ===================== 媒体信息解析（ffprobe） =====================
_MI_LANG_NAMES = {
    "ja": "Japanese", "jpn": "Japanese", "jp": "Japanese",
    "en": "English", "eng": "English",
    "ko": "Korean", "kor": "Korean",
    "fr": "French", "fre": "French", "fra": "French",
    "de": "German", "ger": "German", "deu": "German",
    "es": "Spanish", "spa": "Spanish",
    "it": "Italian", "ita": "Italian",
    "ru": "Russian", "rus": "Russian",
    "pt": "Portuguese", "por": "Portuguese",
    "th": "Thai", "tha": "Thai",
    "vi": "Vietnamese", "vie": "Vietnamese",
    "id": "Indonesian", "ind": "Indonesian",
    "ms": "Malay", "may": "Malay", "msa": "Malay",
    "ar": "Arabic", "ara": "Arabic",
    "hi": "Hindi", "hin": "Hindi",
    "nl": "Dutch", "dut": "Dutch", "nld": "Dutch",
    "pl": "Polish", "pol": "Polish",
    "tr": "Turkish", "tur": "Turkish",
    "sv": "Swedish", "swe": "Swedish",
    "da": "Danish", "dan": "Danish",
    "no": "Norwegian", "nor": "Norwegian",
    "fi": "Finnish", "fin": "Finnish",
    "he": "Hebrew", "heb": "Hebrew",
    "el": "Greek", "ell": "Greek", "gre": "Greek",
    "cs": "Czech", "cze": "Czech", "ces": "Czech",
    "hu": "Hungarian", "hun": "Hungarian",
    "ro": "Romanian", "rum": "Romanian", "ron": "Romanian",
    "uk": "Ukrainian", "ukr": "Ukrainian",
}
_MI_ZH_CODES = {"zh", "chi", "zho", "chs", "cht", "cmn", "yue",
                "zh-cn", "zh-tw", "zh-hk", "zh-sg", "zh-hans", "zh-hant"}

_MI_VIDEO_CODECS = {
    # 主流
    "h264": "MPEG-4 AVC Video", "hevc": "HEVC Video", "vvc": "VVC (H.266) Video",
    "av1": "AV1 Video", "vp9": "VP9 Video", "vp8": "VP8 Video", "vp7": "VP7 Video",
    "vp6": "VP6 Video", "vp6f": "VP6 Video", "vp6a": "VP6 Video", "vp5": "VP5 Video",
    "avs3": "AVS3 Video", "avs2": "AVS2 Video", "cavs": "AVS Video",
    # MPEG 系
    "mpeg1video": "MPEG-1 Video", "mpeg2video": "MPEG-2 Video", "mpeg4": "MPEG-4 Visual Video",
    "h261": "H.261 Video", "h263": "H.263 Video", "h263p": "H.263+ Video", "h263i": "H.263 Video",
    # Microsoft / DivX 老格式
    "vc1": "VC-1 Video", "vc1image": "VC-1 Video",
    "wmv1": "WMV7 Video", "wmv2": "WMV8 Video", "wmv3": "WMV9 Video", "wmv3image": "WMV9 Video",
    "msmpeg4v1": "MS MPEG-4 v1 Video", "msmpeg4v2": "MS MPEG-4 v2 Video", "msmpeg4v3": "MS MPEG-4 v3 (DivX 3) Video",
    "msmpeg4": "MS MPEG-4 Video", "msvideo1": "MS Video 1", "cinepak": "Cinepak Video",
    # 其它常见
    "theora": "Theora Video", "flv1": "Sorenson Spark (FLV) Video", "svq1": "Sorenson Video 1",
    "svq3": "Sorenson Video 3", "rv10": "RealVideo 1", "rv20": "RealVideo 2", "rv30": "RealVideo 3",
    "rv40": "RealVideo 4", "indeo3": "Indeo 3 Video", "indeo4": "Indeo 4 Video", "indeo5": "Indeo 5 Video",
    "mjpeg": "Motion JPEG Video", "mjpegb": "Motion JPEG-B Video", "jpeg2000": "JPEG 2000 Video",
    "prores": "Apple ProRes Video", "dnxhd": "DNxHD/DNxHR Video", "dvvideo": "DV Video",
    "cfhd": "CineForm Video", "ffv1": "FFV1 Video", "huffyuv": "HuffYUV Video", "ffvhuff": "FFVHuff Video",
    "utvideo": "Ut Video", "magicyuv": "MagicYUV Video", "hap": "HAP Video", "apv": "APV Video",
    "rawvideo": "Raw Video", "v210": "Uncompressed 10-bit 4:2:2 Video", "gif": "GIF Animation",
    "png": "PNG Image", "bmp": "BMP Image", "tiff": "TIFF Image", "webp": "WebP Image",
    "smc": "Apple Graphics Video", "rpza": "Apple Video", "qtrle": "QuickTime Animation Video",
}


def _mi_video_codec(s):
    """视频编码显示名：mpeg4 会按 codec_tag 区分 Xvid / DivX / 通用 MPEG-4 Visual"""
    c = (s.get("codec_name") or "").lower()
    tag = (s.get("codec_tag_string") or "").strip().lower()
    if c == "mpeg4":
        if tag.startswith("xvid"):
            return "Xvid Video"
        if tag in ("divx", "dx50", "div5", "div4", "div6", "dvx1", "dvx2", "dvx3"):
            return "DivX Video"
        return "MPEG-4 Visual Video"
    if c in _MI_VIDEO_CODECS:
        return _MI_VIDEO_CODECS[c]
    if c:
        return c.upper() + " Video"
    return "Unknown Video"


def _mi_lang(lang, title=""):
    """语言代码 -> 显示名。zh/zh-tw 等 -> 中文，ja/jp -> Japanese，其他 -> 英文全名"""
    code = (lang or "und").lower().strip()
    t = (title or "").lower()
    is_zh = code in _MI_ZH_CODES or (code in ("und", "") and re.search(r"中文|国语|國語|chinese|mandarin|cantonese", t))
    if is_zh:
        if code in ("zh-tw", "cht", "zh-hant") or re.search(r"繁|台|taiwan|traditional|\bcht\b", t):
            return "中文-台湾"
        if code in ("zh-hk", "yue") or re.search(r"港|hong ?kong|\bhk\b|粤|粵|cantonese", t):
            return "中文-香港"
        return "中文"
    if code in ("und", "mis", "zxx", ""):
        return ""  # 未标注语言：音频行直接省略这一项
    return _MI_LANG_NAMES.get(code, code.upper())


def _mi_bps(stream):
    """取码率 (bps 整数)，没有 bit_rate 时回退到 mkv 的 BPS 标签；都没有返回 0"""
    candidates = [stream.get("bit_rate")]
    tags = stream.get("tags") or {}
    for k, v in tags.items():
        if k.upper().startswith("BPS"):
            candidates.append(v)
    for br in candidates:
        try:
            n = int(float(br))
            if n > 0:
                return n
        except Exception:
            continue
    return 0


def _mi_kbps(stream, fallback_bps=0, approx=False):
    n = _mi_bps(stream)
    est = False
    if n <= 0 and fallback_bps > 0:
        n, est = int(fallback_bps), approx
    if n <= 0:
        return ""
    return f"{'~' if est else ''}{round(n / 1000)} kbps"


def _mi_fps(s):
    for key in ("r_frame_rate", "avg_frame_rate"):
        v = s.get(key) or ""
        try:
            a, b = v.split("/")
            a, b = float(a), float(b)
            if a > 0 and b > 0:
                return f"{a / b:.3f}".rstrip("0").rstrip(".") + " fps"
        except Exception:
            continue
    return ""


def _mi_resolution(s, interlaced=None):
    w = int(s.get("width") or 0)
    h = int(s.get("height") or 0)
    if w >= 7600 or h >= 4000:
        base = 4320
    elif w >= 3800 or h >= 2000:
        base = 2160
    elif w >= 2500 or h >= 1300:
        base = 1440
    elif w >= 1900 or h >= 1000:
        base = 1080
    elif w >= 1260 or h >= 700:
        base = 720
    elif h >= 560:
        base = 576
    elif h >= 520:
        base = 540
    elif h >= 460:
        base = 480
    else:
        base = h
    if not base:
        return ""
    if interlaced is None:
        interlaced = (s.get("field_order") or "progressive") not in ("progressive", "unknown", "")
    return f"{base}{'i' if interlaced else 'p'}"


def _mi_aspect(s):
    dar = s.get("display_aspect_ratio")
    if dar and dar not in ("0:1", "N/A"):
        return dar
    w = int(s.get("width") or 0)
    h = int(s.get("height") or 0)
    if w and h:
        from math import gcd
        g = gcd(w, h)
        return f"{w // g}:{h // g}"
    return ""


def _mi_profile(s):
    prof = (s.get("profile") or "").strip()
    codec = (s.get("codec_name") or "").lower()
    try:
        lv = int(s.get("level") or 0)
    except Exception:
        lv = 0
    if lv in (-99, -1):
        lv = 0

    # VP9 自带 "Profile 0" 之类，不再追加 Profile；没有 profile 的编码返回空
    if not prof or prof.lower() == "unknown":
        return ""
    pl_ = prof.lower()
    out = prof if (pl_.startswith("profile") or pl_.endswith("profile")) else f"{prof} Profile"

    if lv > 0:
        if codec == "h264":
            out += f" {lv / 10:.1f}"
        elif codec == "hevc":
            out += f" {lv / 30:.1f}"
        elif codec == "vvc":
            out += f" {lv // 16}.{(lv % 16) // 3}"
        elif codec == "av1":
            out += f" {2 + (lv >> 2)}.{lv & 3}"          # seq_level_idx -> 如 8 -> 4.0, 13 -> 5.1
        elif codec == "mpeg2video":
            lvname = {10: "Low", 8: "Main", 6: "High-1440", 4: "High"}.get(lv)
            if lvname:
                out += f" @ {lvname} Level"
        elif codec == "mpeg4":
            out += f" @ L{lv}"
    return out


def _mi_audio_codec(s):
    c = (s.get("codec_name") or "").lower()
    prof = (s.get("profile") or "")
    pl = prof.lower()
    if c in ("pcm_bluray", "pcm_dvd"):
        return "LPCM Audio"
    if c.startswith("pcm"):
        return "PCM Audio"
    if c.startswith("adpcm"):
        return "ADPCM Audio"
    if c.startswith("dsd"):
        return "DSD Audio"
    if c == "ac3":
        return "Dolby Digital Audio"
    if c == "eac3":
        return "Dolby Digital Plus + Atmos Audio" if "atmos" in pl else "Dolby Digital Plus Audio"
    if c == "truehd":
        return "Dolby TrueHD + Atmos Audio" if "atmos" in pl else "Dolby TrueHD Audio"
    if c == "dts":
        if "dts:x" in pl:
            return "DTS:X Master Audio"
        if re.search(r"\bma\b", pl):
            return "DTS-HD Master Audio"
        if "hra" in pl or "high res" in pl:
            return "DTS-HD High-Res Audio"
        if "express" in pl:
            return "DTS Express Audio"
        if re.search(r"\bes\b", pl):
            return "DTS-ES Audio"
        if "96/24" in pl:
            return "DTS 96/24 Audio"
        return "DTS Audio"
    if c in ("aac", "aac_latm"):
        return "HE-AAC Audio" if "he-aac" in pl else "AAC Audio"
    names = {
        "flac": "FLAC Audio", "mp3": "MP3 Audio", "mp3float": "MP3 Audio", "mp2": "MP2 Audio", "mp1": "MP1 Audio",
        "opus": "Opus Audio", "vorbis": "Vorbis Audio", "alac": "ALAC Audio", "ac4": "Dolby AC-4 Audio",
        "mlp": "MLP Audio", "ape": "Monkey's Audio", "wavpack": "WavPack Audio", "tta": "TTA Audio",
        "wmav1": "WMA Audio", "wmav2": "WMA Audio", "wmapro": "WMA Pro Audio", "wmalossless": "WMA Lossless Audio",
        "wmavoice": "WMA Voice Audio", "amr_nb": "AMR-NB Audio", "amr_wb": "AMR-WB Audio",
        "speex": "Speex Audio", "cook": "RealAudio Cook", "ra_144": "RealAudio 1.0", "ra_288": "RealAudio 2.0",
        "sipr": "RealAudio SIPR", "atrac3": "ATRAC3 Audio", "atrac3p": "ATRAC3+ Audio", "atrac9": "ATRAC9 Audio",
        "atrac1": "ATRAC1 Audio", "g723_1": "G.723.1 Audio", "g729": "G.729 Audio", "gsm": "GSM Audio",
        "qcelp": "QCELP Audio", "evrc": "EVRC Audio", "iamf": "IAMF Audio", "mpegh_3d_audio": "MPEG-H 3D Audio",
        "usac": "xHE-AAC (USAC) Audio", "nellymoser": "Nellymoser Audio", "dvaudio": "DV Audio",
        "binkaudio_rdft": "Bink Audio", "binkaudio_dct": "Bink Audio", "smackaudio": "Smacker Audio",
    }
    if c in names:
        return names[c]
    return (c.upper() + " Audio") if c else "Audio"


def _mi_channels(s):
    layout = s.get("channel_layout") or ""
    m = re.match(r"^(\d+)\.(\d+)", layout)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    if layout == "mono":
        return "1.0"
    if layout == "stereo":
        return "2.0"
    ch = int(s.get("channels") or 0)
    return {1: "1.0", 2: "2.0", 3: "2.1", 4: "4.0", 6: "5.1", 7: "6.1", 8: "7.1"}.get(ch, f"{ch}.0" if ch else "")


def _mi_samplerate(s):
    try:
        sr = int(s.get("sample_rate") or 0)
        if sr <= 0:
            return ""
        return f"{sr / 1000:.1f}".rstrip("0").rstrip(".") + " kHz"
    except Exception:
        return ""


def _mi_bitdepth(s):
    for key in ("bits_per_raw_sample", "bits_per_sample"):
        try:
            v = int(s.get(key) or 0)
            if v > 0:
                return f"{v}-bit"
        except Exception:
            continue
    return ""


def _mi_video_bitdepth(s):
    """视频位深：优先 bits_per_raw_sample，没有则从 pix_fmt 推断 (yuv420p -> 8-bit, yuv420p10le -> 10-bit)"""
    try:
        v = int(s.get("bits_per_raw_sample") or 0)
        if v > 0:
            return f"{v}-bit"
    except Exception:
        pass
    pf = (s.get("pix_fmt") or "").lower()
    if not pf:
        return ""
    m = re.search(r"(\d{2})(?:le|be)?$", pf)          # yuv420p10le / gbrp12be
    if m and int(m.group(1)) in (9, 10, 12, 14, 16):
        return f"{int(m.group(1))}-bit"
    m = re.match(r"^p(\d{3})", pf)                      # p010le / p016le
    if m:
        return f"{int(m.group(1))}-bit"
    return "8-bit"


def _mi_join(parts):
    return " / ".join(p for p in parts if p)


_MI_COLOR_PRIMARIES = {
    "bt709": "BT.709", "bt470m": "BT.470 System M", "bt470bg": "BT.601 PAL", "smpte170m": "BT.601 NTSC",
    "smpte240m": "SMPTE 240M", "film": "Generic film", "bt2020": "BT.2020",
    "smpte428": "XYZ (SMPTE ST 428-1)", "smpte431": "DCI P3", "smpte432": "Display P3", "ebu3213": "EBU Tech 3213",
}
_MI_TRANSFER = {
    "bt709": "BT.709", "smpte170m": "BT.601", "bt470m": "BT.470 System M", "bt470bg": "BT.470 System B/G",
    "smpte240m": "SMPTE 240M", "linear": "Linear", "log100": "Logarithmic (100:1)",
    "log316": "Logarithmic (316.22777:1)", "iec61966-2-4": "xvYCC", "bt1361e": "BT.1361",
    "iec61966-2-1": "sRGB/sYCC", "bt2020-10": "BT.2020 (10-bit)", "bt2020-12": "BT.2020 (12-bit)",
    "smpte2084": "PQ (SMPTE ST 2084)", "smpte428": "SMPTE ST 428-1", "arib-std-b67": "HLG (ARIB STD-B67)",
}
_MI_MATRIX = {
    "gbr": "RGB", "bt709": "BT.709", "fcc": "FCC", "bt470bg": "BT.601", "smpte170m": "BT.601",
    "smpte240m": "SMPTE 240M", "ycgco": "YCgCo", "bt2020nc": "BT.2020 non-constant",
    "bt2020c": "BT.2020 constant", "smpte2085": "SMPTE ST 2085", "ictcp": "ICtCp",
    "chroma-derived-nc": "Chromaticity-derived non-constant", "chroma-derived-c": "Chromaticity-derived constant",
}
_MI_SUB_TYPES = {
    "hdmv_pgs_subtitle": "PGS (sup)", "dvd_subtitle": "VobSub (sub/idx)", "dvb_subtitle": "DVB Subtitle",
    "xsub": "XSUB", "subrip": "SRT", "srt": "SRT", "ass": "ASS", "ssa": "SSA", "webvtt": "WebVTT (vtt)",
    "mov_text": "Timed Text (MP4 tx3g)", "text": "Plain Text", "microdvd": "MicroDVD", "sami": "SAMI",
    "realtext": "RealText", "jacosub": "JACOsub", "subviewer": "SubViewer", "subviewer1": "SubViewer 1",
    "mpl2": "MPL2", "pjs": "PJS", "stl": "Spruce STL", "vplayer": "VPlayer", "eia_608": "CEA-608",
    "arib_caption": "ARIB Caption", "dvb_teletext": "DVB Teletext", "ttml": "TTML", "lrc": "LRC",
}


def _mi_f(x):
    """'30000/1001' / '12.5' / 'N/A' -> float 或 None"""
    try:
        if isinstance(x, str) and "/" in x:
            a, b = x.split("/")
            b = float(b)
            return float(a) / b if b else None
        return float(x)
    except Exception:
        return None


def _mi_parse_hms(v):
    try:
        h, m, sec = str(v).split(":")
        return int(h) * 3600 + int(m) * 60 + float(sec)
    except Exception:
        return None


def _mi_stream_duration(s, fallback=None):
    d = _mi_f(s.get("duration"))
    if not d:
        for k, v in (s.get("tags") or {}).items():
            if k.upper().startswith("DURATION"):
                d = _mi_parse_hms(v)
                if d:
                    break
    return d or fallback


def _mi_dur_h(sec):
    if not sec or sec <= 0:
        return ""
    total_ms = int(round(sec * 1000))
    h, rem = divmod(total_ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    parts = []
    if h:
        parts.append(f"{h} h")
    if m:
        parts.append(f"{m} min")
    if s:
        parts.append(f"{s} s")
    if ms and not h:
        parts.append(f"{ms} ms")
    return " ".join(parts) or "0 s"


def _mi_ts(sec):
    total_ms = int(round((sec or 0) * 1000))
    h, rem = divmod(total_ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def _mi_size(n):
    try:
        n = float(n)
    except Exception:
        return ""
    for unit in ("Bytes", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return f"{int(n)} Bytes" if unit == "Bytes" else f"{n:.2f} {unit}"
        n /= 1024.0


def _mi_rate(bps):
    if not bps or bps <= 0:
        return ""
    if bps >= 1_000_000:
        return f"{bps / 1_000_000:.2f} Mb/s"
    return f"{round(bps / 1000)} kb/s"


def _mi_kv(k, v):
    return f"{k:<41}: {v}"


def _mi_yesno(v):
    return "Yes" if v else "No"


# ---------- 额外探测：隔行 / HDR10+ / 首个视频包位置 ----------
def _mi_probe_video_extra(full_path):
    """解码前几帧：读取 interlaced_frame（MBAFF/PAFF 也会被标为隔行）、HDR10+ 动态元数据、首包文件偏移"""
    info = {"interlaced": None, "pos": None, "hdr10plus": False, "side": []}
    try:
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-read_intervals", "%+#8",
               "-show_entries", "packet=pos:frame=interlaced_frame,top_field_first:frame_side_data_list",
               "-print_format", "json", full_path]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=40)
        d = json.loads(proc.stdout or "{}")
    except Exception:
        return info
    # 同时请求 packet 和 frame 时，ffprobe 会合并输出到 packets_and_frames 并用 type 区分
    mixed = d.get("packets_and_frames") or []
    packets = d.get("packets") or [x for x in mixed if x.get("type") == "packet"]
    frames = d.get("frames") or [x for x in mixed if x.get("type") == "frame"]
    for p in packets:
        try:
            info["pos"] = int(p.get("pos"))
            break
        except Exception:
            continue
    flags = [f.get("interlaced_frame") for f in frames if "interlaced_frame" in f]
    if flags:
        try:
            info["interlaced"] = any(int(x or 0) == 1 for x in flags)
        except Exception:
            pass
    for f in frames:
        for sd in f.get("side_data_list") or []:
            t = sd.get("side_data_type") or ""
            if "2094-40" in t or "HDR10+" in t:
                info["hdr10plus"] = True
            if ("Mastering display" in t or "Content light level" in t) and \
                    all((x.get("side_data_type") or "") != t for x in info["side"]):
                info["side"].append(sd)   # x265 等把 HDR 静态元数据写在 SEI 里，流级别读不到，从帧里补
    return info


def _mi_scan_encoder(full_path, pos=None):
    """在首个视频帧附近的字节里找 x264 / x265 写入的编码参数字符串"""
    pats = [("x264", re.compile(rb"x264 - core[ -~]*")),
            ("x265", re.compile(rb"x265 \(build[ -~]*"))]
    try:
        with open(full_path, "rb") as f:
            chunks = []
            if pos is not None and pos >= 0:
                f.seek(pos)
                chunks.append(f.read(1024 * 1024))
            f.seek(0)
            chunks.append(f.read(8 * 1024 * 1024))
    except Exception:
        return {}
    for data in chunks:
        for lib, rx in pats:
            m = rx.search(data)
            if m:
                return {"lib": lib, "text": m.group(0).decode("ascii", "replace").strip()}
    return {}


def _mi_enc_tag(s, enc):
    lib = enc.get("lib")
    codec = (s.get("codec_name") or "").lower()
    if lib == "x264" and codec == "h264":
        return "x264"
    if lib == "x265" and codec == "hevc":
        return "x265"
    return ""


def _mi_is_interlaced(s, extra, enc):
    """隔行判断：field_order 为 tt/bb/tb/bt；或解码帧带 interlaced 标记（MBAFF 也算）；或 x264 参数 interlaced=1"""
    fo = (s.get("field_order") or "").lower()
    if fo in ("tt", "bb", "tb", "bt"):
        return True
    if extra.get("interlaced") is True:
        return True
    if re.search(r"(?<!fake-)interlaced=1", enc.get("text", "")):
        return True
    return False


# ---------- HDR ----------
def _mi_find_dovi(s):
    for d in s.get("side_data_list") or []:
        t = d.get("side_data_type") or ""
        if "DOVI" in t or "Dolby Vision" in t:
            return d
    return None


def _mi_hdr_list(s, extra):
    out = []
    trc = (s.get("color_transfer") or "").lower()
    if trc == "smpte2084":
        out.append("HDR10+" if extra.get("hdr10plus") else "HDR10")
    elif trc == "arib-std-b67":
        out.append("HLG")
    dovi = _mi_find_dovi(s)
    if dovi:
        p = dovi.get("dv_profile")
        c = dovi.get("dv_bl_signal_compatibility_id")
        txt = f"Dolby Vision Profile {p}"
        if p in (7, 8, 9, 10) and c is not None:
            txt += f".{c}"
        if dovi.get("el_present_flag"):
            txt += " (with EL)"
        if c == 0:  # 无 HDR10/SDR/HLG 兼容层（如 Profile 5），不再标 HDR10
            out = [x for x in out if not x.startswith("HDR10")]
        out.append(txt)
    return out


def _mi_hdr_detail_lines(s, extra):
    L = []
    side = list(s.get("side_data_list") or [])
    have = {(x.get("side_data_type") or "") for x in side}
    side += [x for x in (extra.get("side") or []) if (x.get("side_data_type") or "") not in have]
    for d in side:
        t = d.get("side_data_type") or ""
        if "Mastering display" in t:
            def g(k):
                v = _mi_f(d.get(k))
                return v
            try:
                L.append(_mi_kv("Mastering display color primaries",
                                f"R: x={g('red_x'):.4f} y={g('red_y'):.4f}, G: x={g('green_x'):.4f} y={g('green_y'):.4f}, "
                                f"B: x={g('blue_x'):.4f} y={g('blue_y'):.4f}, "
                                f"White point: x={g('white_point_x'):.4f} y={g('white_point_y'):.4f}"))
                mn, mx = g("min_luminance"), g("max_luminance")
                L.append(_mi_kv("Mastering display luminance", f"min: {mn:.4f} cd/m2, max: {mx:.0f} cd/m2"))
            except Exception:
                pass
        elif "Content light level" in t:
            L.append(_mi_kv("Maximum Content Light Level", f"{d.get('max_content')} cd/m2"))
            L.append(_mi_kv("Maximum Frame-Average Light Level", f"{d.get('max_average')} cd/m2"))
    hdr = _mi_hdr_list(s, extra)
    dovi = _mi_find_dovi(s)
    fmt_parts = []
    if "HDR10+" in hdr:
        fmt_parts.append("HDR10+ (SMPTE ST 2094-40)")
    elif "HDR10" in hdr:
        fmt_parts.append("HDR10 (SMPTE ST 2086)")
    if "HLG" in hdr:
        fmt_parts.append("HLG")
    if dovi:
        fmt_parts.append(
            f"Dolby Vision, Version {dovi.get('dv_version_major', '?')}.{dovi.get('dv_version_minor', '?')}, "
            f"Profile {dovi.get('dv_profile')}, Level {dovi.get('dv_level')}, "
            f"compatibility id {dovi.get('dv_bl_signal_compatibility_id')}, "
            f"BL {_mi_yesno(dovi.get('bl_present_flag'))} / EL {_mi_yesno(dovi.get('el_present_flag'))} / "
            f"RPU {_mi_yesno(dovi.get('rpu_present_flag'))}")
    if fmt_parts:
        L.insert(0, _mi_kv("HDR format", " / ".join(fmt_parts)))
    return L


# ---------- 像素格式 ----------
def _mi_space_chroma(pf):
    pf = (pf or "").lower()
    if not pf:
        return "", ""
    if pf.startswith(("gbr", "rgb", "bgr", "argb", "rgba", "bgra", "abgr", "pal8")):
        return "RGB", "4:4:4"
    if pf.startswith(("gray", "ya8", "ya16")):
        return "Y", ""
    m = re.search(r"yuva?j?(\d)(\d)(\d)", pf)
    if m:
        return "YUV", f"{m.group(1)}:{m.group(2)}:{m.group(3)}"
    if pf in ("nv12", "nv21") or pf.startswith("p01") or pf.startswith("p21"):
        return "YUV", "4:2:0"
    if pf in ("yuyv422", "uyvy422", "yvyu422", "nv16", "nv20le", "nv20be", "p210le", "p216le"):
        return "YUV", "4:2:2"
    if pf in ("nv24", "nv42", "p410le", "p416le"):
        return "YUV", "4:4:4"
    return "YUV", ""


# ---------- 完整信息（MediaInfo 风格） ----------
def _mi_tag_lines(tags, skip=()):
    out = []
    for k, v in (tags or {}).items():
        if k.lower() in skip:
            continue
        v = str(v)
        if len(v) > 600:
            v = v[:600] + " ..."
        out.append(_mi_kv(k, v))
    return out


def _mi_common_stream_lines(s, container_dur):
    L = []
    sid = s.get("id")
    L.append(_mi_kv("ID", f"{s.get('index', 0) + 1}" + (f" ({sid})" if sid else "")))
    return L


def _mi_lang_full(lang, title=""):
    name = _mi_lang(lang, title)
    code = (lang or "").strip()
    if name and code and code.lower() not in ("und",):
        return f"{name} ({code})"
    return name or ""


def _mi_disp_lines(s):
    disp = s.get("disposition") or {}
    L = [_mi_kv("Default", _mi_yesno(disp.get("default"))), _mi_kv("Forced", _mi_yesno(disp.get("forced")))]
    if disp.get("hearing_impaired"):
        L.append(_mi_kv("Hearing impaired", "Yes"))
    if disp.get("visual_impaired"):
        L.append(_mi_kv("Visual impaired", "Yes"))
    if disp.get("original"):
        L.append(_mi_kv("Original", "Yes"))
    if disp.get("comment"):
        L.append(_mi_kv("Commentary", "Yes"))
    return L


def _mi_full_video(s, head, container_dur, extra, enc, interlaced, video_fallback):
    L = [head]
    tags = s.get("tags") or {}
    L += _mi_common_stream_lines(s, container_dur)
    name = _mi_video_codec(s)
    etag = _mi_enc_tag(s, enc)
    L.append(_mi_kv("Format", name[:-6] if name.endswith(" Video") else name))
    if s.get("codec_long_name"):
        L.append(_mi_kv("Format/Info", s["codec_long_name"]))
    prof = _mi_profile(s)
    if prof:
        L.append(_mi_kv("Format profile", prof))
    tag = s.get("codec_tag_string") or ""
    if tag and not tag.startswith("[0]"):
        L.append(_mi_kv("Codec ID", tag))
    dur = _mi_stream_duration(s, container_dur)
    if dur:
        L.append(_mi_kv("Duration", _mi_dur_h(dur)))
    kb = _mi_kbps(s, video_fallback, approx=True)
    if kb:
        bps_txt = kb.replace(" kbps", "")
        try:
            L.append(_mi_kv("Bit rate", _mi_rate(int(bps_txt.lstrip("~")) * 1000) + (" (estimated)" if kb.startswith("~") else "")))
        except Exception:
            L.append(_mi_kv("Bit rate", kb))
    w, h = s.get("width"), s.get("height")
    if w and h:
        L.append(_mi_kv("Width", f"{w} pixels"))
        L.append(_mi_kv("Height", f"{h} pixels"))
    dar = _mi_aspect(s)
    if dar:
        L.append(_mi_kv("Display aspect ratio", dar))
    sar = s.get("sample_aspect_ratio")
    if sar and sar not in ("0:1", "N/A", "1:1"):
        L.append(_mi_kv("Pixel aspect ratio", sar))
    fps = _mi_fps(s)
    if fps:
        r, a = _mi_f(s.get("r_frame_rate")), _mi_f(s.get("avg_frame_rate"))
        mode = "Constant" if (r and a and abs(r - a) < 0.01) else "Variable"
        L.append(_mi_kv("Frame rate mode", mode))
        L.append(_mi_kv("Frame rate", fps.replace(" fps", " FPS")))
    space, chroma = _mi_space_chroma(s.get("pix_fmt"))
    if space:
        L.append(_mi_kv("Color space", space))
    if chroma:
        L.append(_mi_kv("Chroma subsampling", chroma))
    bd = _mi_video_bitdepth(s)
    if bd:
        L.append(_mi_kv("Bit depth", bd.replace("-bit", " bits")))
    scan = "Interlaced" if interlaced else "Progressive"
    if interlaced and re.search(r"(?<!fake-)interlaced=1", enc.get("text", "")):
        scan = "Interlaced (MBAFF)"
    L.append(_mi_kv("Scan type", scan))
    nb = tags.get("NUMBER_OF_FRAMES") or s.get("nb_frames")
    if nb and str(nb) != "N/A":
        L.append(_mi_kv("Frame count", nb))
    nbytes = tags.get("NUMBER_OF_BYTES")
    if nbytes:
        L.append(_mi_kv("Stream size", _mi_size(nbytes)))
    if s.get("color_range") and s.get("color_range") != "unknown":
        L.append(_mi_kv("Color range", {"tv": "Limited", "pc": "Full"}.get(s["color_range"], s["color_range"])))
    for key, label, table in (("color_primaries", "Color primaries", _MI_COLOR_PRIMARIES),
                              ("color_transfer", "Transfer characteristics", _MI_TRANSFER),
                              ("color_space", "Matrix coefficients", _MI_MATRIX)):
        v = s.get(key)
        if v and v != "unknown":
            L.append(_mi_kv(label, table.get(v.lower(), v)))
    L += _mi_hdr_detail_lines(s, extra)
    if etag:
        m = re.match(r"x26[45] (?:- core |\(build )(\d+)", enc.get("text", ""))
        L.append(_mi_kv("Writing library", enc["text"].split(" - options:")[0].split(" - H.26")[0]))
        if " options: " in enc.get("text", ""):
            L.append(_mi_kv("Encoding settings", enc["text"].split(" options: ", 1)[1]))
    lang = _mi_lang_full(tags.get("language"), tags.get("title", ""))
    if tags.get("title"):
        L.append(_mi_kv("Title", tags["title"]))
    if lang:
        L.append(_mi_kv("Language", lang))
    L += _mi_disp_lines(s)
    L += _mi_tag_lines(tags, skip=("language", "title"))
    return L


def _mi_full_audio(s, head, container_dur):
    L = [head]
    tags = s.get("tags") or {}
    L += _mi_common_stream_lines(s, container_dur)
    name = _mi_audio_codec(s)
    L.append(_mi_kv("Format", name[:-6] if name.endswith(" Audio") else name))
    if s.get("codec_long_name"):
        L.append(_mi_kv("Format/Info", s["codec_long_name"]))
    if s.get("profile") and s["profile"] != "unknown":
        L.append(_mi_kv("Format profile", s["profile"]))
    tag = s.get("codec_tag_string") or ""
    if tag and not tag.startswith("[0]"):
        L.append(_mi_kv("Codec ID", tag))
    dur = _mi_stream_duration(s, container_dur)
    if dur:
        L.append(_mi_kv("Duration", _mi_dur_h(dur)))
    bps = _mi_bps(s)
    if bps:
        L.append(_mi_kv("Bit rate", _mi_rate(bps)))
    ch = int(s.get("channels") or 0)
    if ch:
        L.append(_mi_kv("Channel(s)", f"{ch} channel{'s' if ch > 1 else ''}"))
    if s.get("channel_layout"):
        L.append(_mi_kv("Channel layout", s["channel_layout"]))
    sr = _mi_samplerate(s)
    if sr:
        L.append(_mi_kv("Sampling rate", sr))
    bd = _mi_bitdepth(s)
    if bd:
        L.append(_mi_kv("Bit depth", bd.replace("-bit", " bits")))
    nbytes = tags.get("NUMBER_OF_BYTES")
    if nbytes:
        L.append(_mi_kv("Stream size", _mi_size(nbytes)))
    if tags.get("title"):
        L.append(_mi_kv("Title", tags["title"]))
    lang = _mi_lang_full(tags.get("language"), tags.get("title", ""))
    if lang:
        L.append(_mi_kv("Language", lang))
    L += _mi_disp_lines(s)
    L += _mi_tag_lines(tags, skip=("language", "title"))
    return L


def _mi_full_sub(s, head, container_dur):
    L = [head]
    tags = s.get("tags") or {}
    L += _mi_common_stream_lines(s, container_dur)
    c = (s.get("codec_name") or "").lower()
    L.append(_mi_kv("Format", _MI_SUB_TYPES.get(c, c.upper() or "Unknown")))
    if s.get("codec_long_name"):
        L.append(_mi_kv("Format/Info", s["codec_long_name"]))
    L.append(_mi_kv("Type", "Graphic (bitmap)" if c in BITMAP_SUB_CODECS else "Text"))
    tag = s.get("codec_tag_string") or ""
    if tag and not tag.startswith("[0]"):
        L.append(_mi_kv("Codec ID", tag))
    dur = _mi_stream_duration(s, container_dur)
    if dur:
        L.append(_mi_kv("Duration", _mi_dur_h(dur)))
    bps = _mi_bps(s)
    if bps:
        L.append(_mi_kv("Bit rate", _mi_rate(bps)))
    nb = tags.get("NUMBER_OF_FRAMES")
    if nb:
        L.append(_mi_kv("Count of elements", nb))
    nbytes = tags.get("NUMBER_OF_BYTES")
    if nbytes:
        L.append(_mi_kv("Stream size", _mi_size(nbytes)))
    if tags.get("title"):
        L.append(_mi_kv("Title", tags["title"]))
    lang = _mi_lang_full(tags.get("language"), tags.get("title", ""))
    if lang:
        L.append(_mi_kv("Language", lang))
    L += _mi_disp_lines(s)
    L += _mi_tag_lines(tags, skip=("language", "title"))
    return L


def _mi_build_full(full_path, data, streams, extra, enc, first_video, video_fallback):
    fmt = data.get("format") or {}
    container_dur = _mi_f(fmt.get("duration"))
    sections = []

    g = ["General"]
    g.append(_mi_kv("Complete name", full_path))
    g.append(_mi_kv("Format", fmt.get("format_long_name") or fmt.get("format_name") or ""))
    try:
        size = fmt.get("size") or os.path.getsize(full_path)
        g.append(_mi_kv("File size", _mi_size(size)))
    except Exception:
        pass
    if container_dur:
        g.append(_mi_kv("Duration", _mi_dur_h(container_dur)))
    try:
        g.append(_mi_kv("Overall bit rate", _mi_rate(int(float(fmt.get("bit_rate"))))))
    except Exception:
        pass
    g.append(_mi_kv("Streams / Chapters", f"{len(streams)} / {len(data.get('chapters') or [])}"))
    g += _mi_tag_lines(fmt.get("tags"))
    sections.append(g)

    vids = [s for s in streams if s.get("codec_type") == "video" and not (s.get("disposition") or {}).get("attached_pic")]
    auds = [s for s in streams if s.get("codec_type") == "audio"]
    subs = [s for s in streams if s.get("codec_type") == "subtitle"]
    covers = [s for s in streams if s.get("codec_type") == "video" and (s.get("disposition") or {}).get("attached_pic")]

    for i, s in enumerate(vids, 1):
        head = "Video" if len(vids) == 1 else f"Video #{i}"
        if s is first_video:
            inter = _mi_is_interlaced(s, extra, enc)
            sections.append(_mi_full_video(s, head, container_dur, extra, enc, inter, video_fallback))
        else:
            inter = _mi_is_interlaced(s, {}, {})
            sections.append(_mi_full_video(s, head, container_dur, {}, {}, inter, 0))
    for i, s in enumerate(auds, 1):
        sections.append(_mi_full_audio(s, "Audio" if len(auds) == 1 else f"Audio #{i}", container_dur))
    for i, s in enumerate(subs, 1):
        sections.append(_mi_full_sub(s, "Text" if len(subs) == 1 else f"Text #{i}", container_dur))

    chapters = data.get("chapters") or []
    if chapters:
        m = ["Menu", _mi_kv("Chapters", len(chapters))]
        for i, c in enumerate(chapters, 1):
            st = _mi_f(c.get("start_time")) or 0.0
            title = (c.get("tags") or {}).get("title") or f"Chapter {i}"
            m.append(_mi_kv(_mi_ts(st), title))
        sections.append(m)

    others = [s for s in streams if s.get("codec_type") in ("attachment", "data")] + covers
    if others:
        o = ["Other"]
        for s in others[:60]:
            t = s.get("tags") or {}
            kind = "Cover" if s in covers else (s.get("codec_type") or "").capitalize()
            label = t.get("filename") or s.get("codec_name") or ""
            mime = t.get("mimetype")
            o.append(_mi_kv(kind, f"{label}" + (f" ({mime})" if mime else "")))
        if len(others) > 60:
            o.append(_mi_kv("...", f"另有 {len(others) - 60} 项未显示"))
        sections.append(o)

    return "\n\n".join("\n".join(sec) for sec in sections)




# ===================== 对外接口 =====================
def get_media_info(path):
    """返回 (简洁文本, 完整文本)。识别不到视频或音频信息时抛出 MediaInfoError。"""
    full_path = os.path.abspath(path)
    if not os.path.exists(full_path):
        raise MediaInfoError("文件不存在")
    if os.path.isdir(full_path):
        raise MediaInfoError("这是文件夹，不是文件")
    if not shutil.which("ffprobe"):
        raise MediaInfoError("未找到 ffprobe 命令，请先安装 ffmpeg")

    cmd = ["ffprobe", "-v", "error", "-print_format", "json",
           "-show_streams", "-show_chapters", "-show_format", full_path]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60)
    except subprocess.TimeoutExpired:
        raise MediaInfoError("ffprobe 读取超时（文件过大或路径异常）")
    try:
        data = json.loads(proc.stdout or "{}")
    except Exception:
        data = {}
    streams = data.get("streams") or []

    real_videos = [s for s in streams if s.get("codec_type") == "video"
                   and not (s.get("disposition") or {}).get("attached_pic")]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    if not real_videos and not audios:
        reason = ((proc.stderr or "").strip().splitlines() or [""])[-1]
        raise MediaInfoError("未识别到视频或音频信息" + (f"（{reason}）" if reason else ""))

    # 流本身没有码率时（常见于 mp4/ts），用「整体码率 - 音频码率」估算视频码率，前面加 ~ 表示估算值
    try:
        fmt_bps = int(float((data.get("format") or {}).get("bit_rate") or 0))
    except Exception:
        fmt_bps = 0
    audio_bps_sum = sum(_mi_bps(s) for s in audios)
    video_fallback = 0
    if len(real_videos) == 1 and fmt_bps > audio_bps_sum:
        video_fallback = fmt_bps - audio_bps_sum

    # 第一个视频流：解码前几帧判断隔行/HDR10+，并在首帧附近查找 x264/x265 编码参数
    first_video = real_videos[0] if real_videos else None
    extra, enc = {}, {}
    if first_video is not None:
        extra = _mi_probe_video_extra(full_path)
        enc = _mi_scan_encoder(full_path, extra.get("pos"))

    lines = []
    subs = []
    for s in streams:
        ctype = s.get("codec_type")
        tags = s.get("tags") or {}
        lang = tags.get("language", "und")
        title = tags.get("title", "") or ""

        if ctype == "video":
            if (s.get("disposition") or {}).get("attached_pic"):
                continue  # 跳过封面图
            is_first = s is first_video
            inter = _mi_is_interlaced(s, extra if is_first else {}, enc if is_first else {})
            codec = _mi_video_codec(s)
            etag = _mi_enc_tag(s, enc) if is_first else ""
            if etag:
                codec += f" ({etag})"
            lines.append("VIDEO: " + _mi_join([
                codec, _mi_resolution(s, inter), _mi_fps(s), _mi_aspect(s),
                _mi_kbps(s, video_fallback, approx=True), _mi_profile(s), _mi_video_bitdepth(s)
            ] + _mi_hdr_list(s, extra if is_first else {})))
        elif ctype == "audio":
            kbps = _mi_kbps(s)
            lines.append("AUDIO: " + _mi_join([
                _mi_audio_codec(s), _mi_lang(lang, title), kbps,
                _mi_channels(s), _mi_samplerate(s), kbps, _mi_bitdepth(s)
            ]))
        elif ctype == "subtitle":
            subs.append(_mi_lang(lang, title) or "Unknown")

    if subs:
        lines.append("Subtitle: " + " / ".join(subs))
    lines.append(f"章节： {len(data.get('chapters') or [])}")

    try:
        full_text = _mi_build_full(full_path, data, streams, extra, enc, first_video, video_fallback)
    except Exception as e:
        full_text = "完整信息生成失败: " + str(e)
    return "\n".join(lines), full_text


# ===================== 命令行部分 =====================
def _natural_key(p):
    return [int(t) if t.isdigit() else t.casefold() for t in re.split(r"(\d+)", p)]


def _is_media_name(name):
    return os.path.splitext(name)[1].lower() in MEDIA_EXTS


def _list_dir(folder, recursive):
    out = []
    if recursive:
        for root, _dirs, files in os.walk(folder):
            for f in files:
                if _is_media_name(f):
                    out.append(os.path.join(root, f))
    else:
        try:
            for f in os.listdir(folder):
                fp = os.path.join(folder, f)
                if os.path.isfile(fp) and _is_media_name(f):
                    out.append(fp)
        except OSError as e:
            print(f"[错误] 无法读取文件夹 {folder}: {e}", file=sys.stderr)
    return out


def collect_files(paths, recursive):
    """把命令行路径整理成文件列表（去重 + 自然排序）。返回 (files, error_count)"""
    expanded, errors = [], 0
    for p in paths:
        # 带通配符且本身不存在：shell 没展开（引号 / Windows），这里自己展开
        if any(c in p for c in "*?[") and not os.path.exists(p):
            matches = glob.glob(p)
            if not matches:
                print(f"[错误] 没有匹配到任何文件: {p}", file=sys.stderr)
                errors += 1
            expanded += matches
        else:
            expanded.append(p)

    single = len(expanded) == 1
    files = []
    for p in expanded:
        if os.path.isdir(p):
            # 只给了一个文件夹 -> 处理其中的文件；多个路径里的文件夹只有 -r 时才进入
            if single or recursive:
                files += _list_dir(p, recursive)
        elif os.path.isfile(p):
            # 单个文件：不看扩展名；多个路径（如 /path/*）：只保留媒体扩展名，和给文件夹时一致
            if single or _is_media_name(p):
                files.append(p)
        else:
            print(f"[错误] 路径不存在: {p}", file=sys.stderr)
            errors += 1

    seen, uniq = set(), []
    for f in files:
        key = os.path.abspath(f)
        if key not in seen:
            seen.add(key)
            uniq.append(key)
    uniq.sort(key=_natural_key)
    return uniq, errors


def _truncate_bytes(text, max_bytes):
    raw = text.encode("utf-8")
    if len(raw) <= max_bytes:
        return text
    return raw[:max_bytes].decode("utf-8", "ignore")


def make_out_path(out_dir, src_path, full):
    """media_文件名.txt / media_文件名_full.txt；名字过长截断；重名加 (1)(2)"""
    stem = os.path.splitext(os.path.basename(src_path))[0]
    prefix = "media_"
    suffix = "_full" if full else ""
    reserve = len((prefix + suffix + "(9999).txt").encode("utf-8"))
    stem = _truncate_bytes(stem, 255 - reserve).rstrip(" .") or "unnamed"
    base = f"{prefix}{stem}{suffix}"
    cand = os.path.join(out_dir, base + ".txt")
    i = 1
    while os.path.exists(cand):
        cand = os.path.join(out_dir, f"{base}({i}).txt")
        i += 1
    return cand


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser(
        prog="MediaInfo.py",
        description="用 ffprobe 生成媒体信息 txt：默认 BDInfo 风格，--full 为完整 MediaInfo 风格。")
    ap.add_argument("paths", nargs="+", help="文件或文件夹（/path 与 /path/* 等价）")
    ap.add_argument("--full", action="store_true", help="输出完整 MediaInfo 信息（文件名 media_xxx_full.txt）")
    ap.add_argument("-r", "--recursive", action="store_true", help="递归子文件夹（默认不递归）")
    ap.add_argument("-n", "--num", type=int, default=None, metavar="N", help="只取前 N 个文件（生成 N 个 txt）")
    ap.add_argument("-d", "--dir", default=None, metavar="DIR", help="txt 输出文件夹（默认是 MediaInfo.py 所在文件夹）")
    args = ap.parse_args(argv)

    if args.num is not None and args.num < 1:
        ap.error("-n 必须是大于 0 的整数")

    out_dir = os.path.abspath(args.dir) if args.dir else os.path.dirname(os.path.abspath(__file__))
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as e:
        print(f"[错误] 无法创建输出文件夹 {out_dir}: {e}", file=sys.stderr)
        return 1

    files, errors = collect_files(args.paths, args.recursive)
    if args.num is not None:
        files = files[:args.num]
    if not files:
        print("[错误] 没有找到可处理的媒体文件", file=sys.stderr)
        return 1

    ok = 0
    for f in files:
        try:
            brief, full = get_media_info(f)
        except MediaInfoError as e:
            print(f"[错误] {f}: {e}", file=sys.stderr)
            errors += 1
            continue
        except Exception as e:
            print(f"[错误] {f}: 执行异常 {e}", file=sys.stderr)
            errors += 1
            continue
        out_path = make_out_path(out_dir, f, args.full)
        try:
            with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write((full if args.full else brief).rstrip("\n") + "\n")
        except OSError as e:
            print(f"[错误] 写入失败 {out_path}: {e}", file=sys.stderr)
            errors += 1
            continue
        ok += 1
        print(f"[OK] {f}\n     -> {out_path}")

    print(f"完成：成功 {ok} 个，失败 {errors} 个。")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
