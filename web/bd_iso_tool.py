#!/usr/bin/env python3
"""
DVD / 蓝光 ISO / 普通视频文件 -> 缩略图联系表 + MediaInfo  (ISO 不挂载)   GUI + 命令行

  python bd_iso_tool.py                      打开 GUI (可把 ISO 拖进去, 批量)
  python bd_iso_tool.py a.iso b.mkv 目录 ... 命令行批量处理 (目录加 -r 递归; --ext .xxx 追加扩展名)
  python bd_iso_tool.py --gui a.iso          打开 GUI 并预先加入文件

GUI 的设置自动保存在脚本旁边的  "DVD蓝光iso截图.json"  里, 下次打开自动恢复.
命令行默认用内置默认值; 加 --use-config 则以 GUI 保存的设置为基础.

原理:
  * 蓝光: ffmpeg/ffprobe 的 bluray: 协议 (libbluray 直接读 ISO). MediaInfo 精简/完整 = 移植自 MediaInfo.py (ffprobe);
          仅 "MediaInfo 原生" 模式才用 7-Zip 流式读出主 m2ts 开头一段给 mediainfo 命令行
  * DVD : 自己解析 ISO9660, 找到最大标题集的 VOB 在 ISO 内的偏移, 用 ffmpeg 的 subfile 协议直接读;
          MediaInfo 读 VTS_xx_0.IFO
依赖: ffmpeg/ffprobe (蓝光需带 libbluray, gyan.dev full 构建), MediaInfo CLI, pip install pillow
      蓝光另需 7-Zip;  GUI 拖拽需 pip install tkinterdnd2 (没装也能用按钮添加)
"""
import argparse
import contextlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import traceback
from pathlib import Path

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
SEC = 2048
CONFIG_NAME = "DVD蓝光iso截图.json"

# ============================================================ 设置
DEFAULTS = {
    # 截图
    "grid_cols": 2, "grid_rows": 3, "thumb_width": 640,
    "seek_mode": "auto",          # auto: DVD 先按字节再按时间 / bytes / time   (蓝光始终按时间)
    "tonemap": False, "keep_thumbs": False,
    "sheet_fmt": "jpg", "jpeg_quality": 92, "make_sheet": True,
    # 联系表内容
    "show_filename": True, "show_fileinfo": True, "show_video": True,
    "show_audio": True, "show_subs": True, "show_timestamp": True, "font_scale": 1.0,
    # MediaInfo
    # simple 精简(BDInfo风格) / full 完整 / all 完整(spoiler折叠)+精简 / mi_normal,mi_full MediaInfo命令行原生
    "do_mediainfo": True, "mediainfo_mode": "simple",
    "save_mediainfo": True, "head_mb": 128,
    # 输出
    "out_mode": "iso_dir", "out_dir": "", "tmp_dir": "",
    "exist_mode": "overwrite",      # 同名输出已存在时: overwrite 覆盖 / skip 跳过 / rename 自动改名 (1)
    "comment": "", "comment_color": "#8CC8FF",   # 联系表信息区最后一行的注释 (可写广告/备注)
    # 高级
    "recursive": False, "extra_exts": "", "preroll": 10,
    "playlist": "", "duration": "", "debug": False,
    "ffmpeg": "", "ffprobe": "", "sevenz": "", "mediainfo": "",
    # 界面记忆
    "geometry": "", "last_dir": "",
}


def config_path():
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    return base / CONFIG_NAME


def load_config():
    cfg = dict(DEFAULTS)
    try:
        data = json.loads(config_path().read_text(encoding="utf-8"))
        for k, v in data.items():
            if k in DEFAULTS and isinstance(v, type(DEFAULTS[k])) or (k in DEFAULTS and isinstance(DEFAULTS[k], float) and isinstance(v, int)):
                cfg[k] = v
        if data.get("skip_existing") is True and "exist_mode" not in data:  # 兼容旧设置
            cfg["exist_mode"] = "skip"
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        data = {k: cfg.get(k, v) for k, v in DEFAULTS.items()}
        config_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print("保存设置失败:", e)


# ============================================================ 通用
class Cancelled(Exception):
    pass


CANCEL = threading.Event()


def check_cancel():
    if CANCEL.is_set():
        raise Cancelled()


DEFAULT_VIDEO_EXTS = {'.3g2', '.3gp', '.asf', '.avi', '.divx', '.dv', '.f4v', '.flv', '.m2t', '.m2ts',
                      '.m2v', '.m2p', '.m4v', '.mkv', '.mod', '.mov', '.mp4', '.mpe', '.mpeg', '.mpg',
                      '.mts', '.mxf', '.ogm', '.ogv', '.qt', '.rm', '.rmvb', '.ts', '.tp', '.trp',
                      '.vob', '.webm', '.wmv', '.wtv', '.xvid'}


def media_exts(extra=""):
    """默认视频扩展名 + 用户追加的 + .iso"""
    exts = set(DEFAULT_VIDEO_EXTS)
    for e in re.split(r"[,\s;]+", str(extra or "")):
        e = e.strip().lower()
        if e:
            exts.add(e if e.startswith(".") else "." + e)
    exts.add(".iso")
    return exts


def _natural(p):
    return [int(t) if t.isdigit() else t.casefold() for t in re.split(r"(\d+)", str(p))]


def collect_inputs(paths, recursive, exts, strict=True):
    """文件/目录 -> 文件列表 (去重, 自然排序). strict: 单独给的文件也必须是已知扩展名"""
    out, seen = [], set()
    for p in paths:
        p = Path(str(p).strip("{}"))
        if p.is_dir():
            it = p.rglob("*") if recursive else p.iterdir()
            found = sorted((x for x in it if x.is_file() and x.suffix.lower() in exts), key=_natural)
        elif p.is_file() and (not strict or p.suffix.lower() in exts):
            found = [p]
        else:
            found = []
        for f in found:
            k = str(f.resolve())
            if k not in seen:
                seen.add(k)
                out.append(f)
    return out


def find_tool(name, given=None, extra=()):
    if given:
        return given
    p = shutil.which(name)
    if p:
        return p
    for e in extra:
        if os.path.isfile(e):
            return e
    return None


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", creationflags=CREATE_NO_WINDOW, **kw)


def fmt_t(sec):
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


# ============================================================ ffmpeg
def check_bluray_protocol(ffmpeg):
    r = run([ffmpeg, "-hide_banner", "-protocols"])
    return re.search(r"^\s*bluray\s*$", (r.stdout or "") + (r.stderr or ""), re.M) is not None


def bd_src(iso: Path):
    return "bluray:" + iso.resolve().as_posix()


def get_probe(ffprobe, pre, url):
    cmd = [ffprobe, "-v", "error"] + pre + ["-show_format", "-show_streams", "-of", "json", url]
    r = run(cmd)
    try:
        return json.loads(r.stdout)
    except Exception:
        sys.stderr.write((r.stderr or "")[-800:] + "\n")
        return None


def is_black(path):
    try:
        from PIL import Image, ImageStat
        im = Image.open(path).convert("L")
        return ImageStat.Stat(im).mean[0] < 6 and im.getextrema()[1] < 40
    except Exception:
        return False


def clean_err(err):
    keep = [l for l in (err or "").splitlines()
            if "deprecated pixel format" not in l and "showinfo" not in l and l.strip()]
    return "\n".join(keep)


def make_thumbs(ffmpeg, pre, url, duration, n, width, outdir, tonemap, dvd=False,
                dvd_range=None, seek_mode="auto", debug=False, preroll=10):
    """dvd_range = (ISO路径, 标题集起始字节, 结束字节), 用于不依赖时间戳的"按字节偏移"取帧"""
    outdir.mkdir(parents=True, exist_ok=True)
    vf = ["yadif=deint=interlaced",                    # 只处理被标记为隔行的帧 (HDTV 1080i / DVD)
          "scale='trunc(iw*sar/2)*2':ih", "setsar=1"]  # 按 SAR 还原画面比例 (DVD / 1440x1080 等非方形像素)
    if tonemap:
        vf.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
                  "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    vf.append(f"scale={width}:-2")
    vf = ",".join(vf)

    def grab(t, out):
        # 防白色马赛克: 先 seek 到目标前 preroll 秒(落在关键帧), 再从那里一路解码到目标时间,
        # 这样目标帧一定是从完整的参考帧链解出来的, 而不是从非关键帧起解码 (TS/HDTV 常见)
        roll = min(float(preroll), t)
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "warning"] + pre
        cmd += ["-probesize", "100M", "-analyzeduration", "100M",
                "-ss", f"{t - roll:.3f}", "-i", url, "-ss", f"{roll:.3f}",
                "-map", "0:v:0", "-frames:v", "1", "-vf", vf, "-q:v", "2", "-update", "1", str(out)]
        r = run(cmd)
        if debug:
            print("   $ " + " ".join(cmd))
            print("   " + clean_err(r.stderr).replace("\n", "\n   "))
        return (out.exists() and out.stat().st_size > 0), clean_err(r.stderr)

    def grab_bytes(frac, out):
        """从 ISO 内标题集的 frac 位置(按字节)开始读, 跳过开头 10 帧(此处可能缺参考帧)后取一帧;
        返回 (ok, err, 帧的原始 PTS 秒)"""
        path, s0, e0 = dvd_range
        st = s0 + int((e0 - s0) * frac)
        st -= st % SEC
        u = f"subfile,,start,{st},end,{e0},,:{path}"
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "info", "-copyts", "-probesize", "50M",
               "-i", u, "-map", "0:v:0", "-frames:v", "1",
               "-vf", "select=gte(n\\,10),showinfo," + vf, "-q:v", "2", "-update", "1", str(out)]
        r = run(cmd)
        m = re.findall(r"pts_time:\s*(-?[\d.]+)", r.stderr or "")
        if debug:
            print("   $ " + " ".join(cmd))
            print("   " + clean_err(r.stderr)[-600:].replace("\n", "\n   "))
        return ((out.exists() and out.stat().st_size > 0), clean_err(r.stderr),
                float(m[0]) if m else None)

    pts0 = [None]

    def byte_time(frac, pts):
        if pts0[0] is None:
            tmp = outdir / "_pts0.jpg"
            _, _, p0 = grab_bytes(0.0, tmp)
            pts0[0] = p0 if p0 is not None else 0.0
            try:
                tmp.unlink()
            except OSError:
                pass
        if pts is not None and 0 <= pts - pts0[0] <= duration + 10:
            return pts - pts0[0]
        return duration * frac  # PTS 不可信时按字节比例估算

    order = []
    if dvd_range and seek_mode in ("auto", "bytes"):
        order.append("bytes")
    if seek_mode in ("auto", "time") or not dvd_range:
        order.append("time")

    files, black_cnt, shown = [], 0, False
    for i in range(n):
        check_cancel()
        frac0 = (i + 1) / (n + 1)
        t0 = duration * frac0
        out = outdir / f"thumb_{i + 1:02d}.jpg"
        got = got_black = False
        t_used, last_err = t0, ""
        for method in order:
            if method == "bytes":
                for df in (0.0, 0.012, -0.012, 0.03, -0.03):
                    check_cancel()
                    f = min(max(frac0 + df, 0.0), 0.995)
                    ok2, err2, pts = grab_bytes(f, out)
                    last_err = err2 or last_err
                    if ok2:
                        if not is_black(out):
                            got, t_used = True, byte_time(f, pts)
                            break
                        got_black = True
            else:
                for off in (0, 3, 8, -4, 15, 30):
                    check_cancel()
                    t2 = min(max(t0 + off, 0), max(duration - 1, 0))
                    ok2, err2 = grab(t2, out)
                    last_err = err2 or last_err
                    if ok2:
                        if not is_black(out):
                            got, t_used = True, t2
                            break
                        got_black = True
            if got:
                break
        if got:
            print(f"  [{i + 1}/{n}] {fmt_t(t_used)} ok")
            files.append((t_used, out))
        elif got_black and out.exists():
            black_cnt += 1
            print(f"  [{i + 1}/{n}] {fmt_t(t0)} (仍是黑屏)")
            files.append((t0, out))
            if not shown and last_err:
                print("  ffmpeg 提示:", last_err[-400:])
                shown = True
        else:
            print(f"  [{i + 1}/{n}] {fmt_t(t0)} 失败: {last_err[-200:]}")
    if black_cnt:
        print(f"!! 有 {black_cnt}/{n} 张截图重试后仍是黑屏")
    return files


# ============================================================ 蓝光: 7z + mediainfo
def list_m2ts(sevenz, iso):
    r = run([sevenz, "l", "-slt", str(iso)])
    items, cur = [], {}
    for line in (r.stdout or "").splitlines() + [""]:
        if not line.strip():
            if "Path" in cur:
                items.append(cur)
            cur = {}
        elif " = " in line:
            k, v = line.split(" = ", 1)
            cur[k.strip()] = v.strip()
    res = []
    for it in items:
        p = it.get("Path", "")
        if re.search(r"BDMV[\\/]STREAM[\\/][^\\/]+\.m2ts$", p, re.I) and it.get("Size", "").isdigit():
            res.append((p, int(it["Size"])))
    return res


def read_head(sevenz, iso, inner, head_mb, dest):
    want = head_mb * 1024 * 1024
    got = 0
    p = subprocess.Popen([sevenz, "e", "-so", str(iso), inner],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         creationflags=CREATE_NO_WINDOW)
    try:
        with open(dest, "wb") as f:
            while got < want:
                chunk = p.stdout.read(min(4 * 1024 * 1024, want - got))
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
    finally:
        p.kill()
        p.wait()
    return got


def do_mediainfo_bd(sevenz, mediainfo, iso, head_mb, raw_mode, tmpdir):
    """返回 (原始文本或None, JSON或None, m2ts名, 大小). raw_mode: simple 不跑文本 / normal / full"""
    streams = list_m2ts(sevenz, iso)
    if not streams:
        return "未在 ISO 中找到 BDMV/STREAM/*.m2ts", None, None, 0
    inner, size = max(streams, key=lambda x: x[1])
    print(f"主视频流: {inner}  ({size / 1024 ** 3:.2f} GB), 读取前 {head_mb} MB 给 MediaInfo ...")
    mj, txt = None, None
    with tempfile.TemporaryDirectory(dir=tmpdir) as td:
        tmp = Path(td) / Path(inner.replace("\\", "/")).name
        read_head(sevenz, iso, inner, head_mb, tmp)
        check_cancel()
        if raw_mode in ("normal", "full"):
            txt = run([mediainfo] + (["--Full"] if raw_mode == "full" else []) + [str(tmp)]).stdout
        try:
            mj = json.loads(run([mediainfo, "--Output=JSON", str(tmp)]).stdout)
        except Exception:
            mj = None
    return txt, mj, inner, size


# ============================================================ DVD (ISO9660 直读)
def _iso_dir(f, lba, size):
    f.seek(lba * SEC)
    data = f.read(size)
    pos, res = 0, []
    while pos < len(data):
        ln = data[pos]
        if ln == 0:
            pos = (pos // SEC + 1) * SEC
            continue
        rec = data[pos:pos + ln]
        pos += ln
        ext = int.from_bytes(rec[2:6], "little")
        sz = int.from_bytes(rec[10:14], "little")
        flags, nl = rec[25], rec[32]
        name = rec[33:33 + nl]
        if name in (b"\x00", b"\x01"):
            continue
        res.append((name.decode("latin-1").split(";")[0], ext, sz, bool(flags & 2)))
    return res


def scan_dvd(iso):
    """返回 {vts号: {'ifo': (lba,size)|None, 'vobs': [(part,lba,size,name)...]}}; 不是 DVD 返回 None"""
    try:
        with open(iso, "rb") as f:
            root = None
            for sec in range(16, 32):
                f.seek(sec * SEC)
                d = f.read(SEC)
                if len(d) < SEC or d[1:6] != b"CD001":
                    return None
                if d[0] == 1:
                    root = (int.from_bytes(d[158:162], "little"), int.from_bytes(d[166:170], "little"))
                    break
                if d[0] == 255:
                    return None
            if not root:
                return None
            vt = [e for e in _iso_dir(f, *root) if e[3] and e[0].upper() == "VIDEO_TS"]
            if not vt:
                return None
            files = _iso_dir(f, vt[0][1], vt[0][2])
    except OSError:
        return None
    vts = {}
    for name, lba, size, isdir in files:
        m = re.match(r"^VTS_(\d\d)_(\d)\.(VOB|IFO|BUP)$", name, re.I)
        if not m or isdir:
            continue
        n, part, ext = int(m.group(1)), int(m.group(2)), m.group(3).upper()
        e = vts.setdefault(n, {"ifo": None, "vobs": []})
        if ext == "IFO" and part == 0:
            e["ifo"] = (lba, size)
        elif ext == "VOB" and part >= 1:
            e["vobs"].append((part, lba, size, name))
    for e in vts.values():
        e["vobs"].sort()
    return {k: v for k, v in vts.items() if v["vobs"]}


def read_range(iso, lba, size):
    with open(iso, "rb") as f:
        f.seek(lba * SEC)
        return f.read(size)


def dvd_pick_main(vts):
    n = max(vts, key=lambda k: sum(v[2] for v in vts[k]["vobs"]))
    return n, vts[n]


def dvd_source(iso, vobs, tmpdir):
    """返回 (ffmpeg前置参数, url, 需清理的目录, (路径,起,止)|None)"""
    path = iso.resolve().as_posix()
    contiguous = all(vobs[i + 1][1] == vobs[i][1] + (vobs[i][2] + SEC - 1) // SEC
                     for i in range(len(vobs) - 1))
    if contiguous:
        start = vobs[0][1] * SEC
        end = vobs[-1][1] * SEC + vobs[-1][2]
        return [], f"subfile,,start,{start},end,{end},,:{path}", None, (path, start, end)
    lines = ["ffconcat version 1.0"]
    for _, lba, size, _n in vobs:
        u = f"subfile,,start,{lba * SEC},end,{lba * SEC + size},,:{path}".replace("'", "'\\''")
        lines.append(f"file '{u}'")
    lst = Path(tempfile.mkdtemp(dir=tmpdir)) / "vobs.ffconcat"
    lst.write_text("\n".join(lines), encoding="utf-8")
    return (["-f", "concat", "-safe", "0", "-protocol_whitelist", "file,subfile,concat"],
            str(lst), lst.parent, None)


def dvd_css_scan(iso, vobs):
    """抽样检查第一个 VOB 里视频 PES 包的加扰标志位. 返回 (被加扰包数, 视频包总数)"""
    lba, size = vobs[0][1], vobs[0][2]
    nsec = size // SEC
    scr = tot = 0
    with open(iso, "rb") as f:
        for i in range(2000):
            f.seek((lba + i * nsec // 2000) * SEC)
            d = f.read(SEC)
            if len(d) < SEC or d[:4] != b"\x00\x00\x01\xba":
                continue
            off = 14 + (d[13] & 7)
            if d[off:off + 3] == b"\x00\x00\x01" and (d[off + 3] & 0xF0) == 0xE0:
                flags = d[off + 6]
                if (flags & 0xC0) == 0x80:
                    tot += 1
                    if flags & 0x30:
                        scr += 1
    return scr, tot


def do_mediainfo_dvd(mediainfo, iso, n, vt, raw_mode, tmpdir):
    """对 VTS_xx_0.IFO 跑 MediaInfo. 返回 (原始文本或None, JSON, 时长秒)"""
    if not vt["ifo"]:
        return None, None, None
    data = read_range(iso, *vt["ifo"])
    txt = None
    with tempfile.TemporaryDirectory(dir=tmpdir) as td:
        tmp = Path(td) / f"VTS_{n:02d}_0.IFO"
        tmp.write_bytes(data)
        if raw_mode in ("normal", "full"):
            txt = run([mediainfo] + (["--Full"] if raw_mode == "full" else []) + [str(tmp)]).stdout
        try:
            mj = json.loads(run([mediainfo, "--Output=JSON", str(tmp)]).stdout)
        except Exception:
            mj = None
    dur = None
    try:
        dur = float(mj["media"]["track"][0]["Duration"])
        if dur > 100000:
            dur /= 1000.0
    except Exception:
        pass
    return txt, mj, dur


# ============================================================ 信息摘要
CH = {1: "1.0", 2: "2.0", 3: "2.1", 4: "4.0", 5: "5.0", 6: "5.1", 7: "6.1", 8: "7.1"}


def to_f(v):
    try:
        return float(str(v).split("/")[0].strip())
    except Exception:
        return None


def f_br(bps):
    if not bps:
        return None
    return f"{bps / 1e6:.1f} Mb/s" if bps >= 1e6 else f"{bps / 1e3:.0f} kb/s"


def ch_str(v):
    m = re.search(r"\d+", str(v or ""))
    if not m:
        return None
    n = int(m.group())
    return CH.get(n, f"{n}ch")


def info_from_mediainfo(mj):
    tracks = mj.get("media", {}).get("track", [])
    v_lines, a_lines, s_items = [], [], []
    for t in tracks:
        ty = t.get("@type")
        if ty == "Video":
            p = [f"{t.get('Format', '?')} {t.get('Format_Profile', '')}".strip()]
            if t.get("Width") and t.get("Height"):
                p.append(f"{t['Width']}x{t['Height']}" + ("i" if t.get("ScanType") == "Interlaced" else ""))
            fr = to_f(t.get("FrameRate"))
            if fr:
                p.append(f"{fr:.3f} fps")
            for key, suf in (("BitRate", ""), ("BitRate_Nominal", ""), ("BitRate_Maximum", " (max)")):
                b = f_br(to_f(t.get(key)))
                if b:
                    p.append(b + suf)
                    break
            if t.get("DisplayAspectRatio_String"):
                p.append("DAR " + t["DisplayAspectRatio_String"])
            if t.get("BitDepth"):
                p.append(f"{t['BitDepth']}bit")
            if t.get("HDR_Format"):
                p.append(t["HDR_Format"])
            v_lines.append(" | ".join(p))
        elif ty == "Audio":
            name = t.get("Format_Commercial_IfAny") or (
                t.get("Format", "?") + (" " + t["Format_AdditionalFeatures"] if t.get("Format_AdditionalFeatures") else ""))
            p = [name]
            c = ch_str(t.get("Channels"))
            if c:
                p.append(c)
            sr = to_f(t.get("SamplingRate"))
            if sr:
                p.append(f"{sr / 1000:g} kHz")
            if t.get("BitDepth"):
                p.append(f"{t['BitDepth']}bit")
            b = f_br(to_f(t.get("BitRate")) or to_f(t.get("BitRate_Maximum")))
            if b:
                p.append(b)
            lang = t.get("Language")
            a_lines.append(" ".join(p) + (f" [{lang}]" if lang else ""))
        elif ty == "Text":
            lang = t.get("Language")
            s_items.append(f"{t.get('Format', 'Sub')}" + (f"[{lang}]" if lang else ""))
    return v_lines, a_lines, s_items


def info_from_probe(pr):
    v_lines, a_lines, s_items = [], [], []
    for s in pr.get("streams", []):
        ct = s.get("codec_type")
        lang = (s.get("tags") or {}).get("language")
        if ct == "video" and s.get("disposition", {}).get("attached_pic", 0) == 0:
            p = [f"{s.get('codec_name', '?').upper()} {s.get('profile', '')}".strip(),
                 f"{s.get('width')}x{s.get('height')}"]
            fr = None
            try:
                a, b = str(s.get("avg_frame_rate", "")).split("/")
                fr = float(a) / float(b)
            except Exception:
                pass
            if fr:
                p.append(f"{fr:.3f} fps")
            b = f_br(to_f(s.get("bit_rate")))
            if b:
                p.append(b)
            v_lines.append(" | ".join(p))
        elif ct == "audio":
            p = [f"{s.get('codec_name', '?').upper()} {s.get('profile', '')}".strip()]
            if s.get("channels"):
                p.append(CH.get(int(s["channels"]), f"{s['channels']}ch"))
            if s.get("sample_rate"):
                p.append(f"{int(s['sample_rate']) / 1000:g} kHz")
            b = f_br(to_f(s.get("bit_rate")))
            if b:
                p.append(b)
            a_lines.append(" ".join(p) + (f" [{lang}]" if lang else ""))
        elif ct == "subtitle":
            s_items.append(s.get("codec_name", "sub").upper() + (f"[{lang}]" if lang else ""))
    return v_lines, a_lines, s_items


def collect_info(iso, kind, duration, inner, mj, probe, extra, css_enc, brief=None, size_label="ISO 大小"):
    parts = [kind, f"{size_label} {iso.stat().st_size / 1024 ** 3:.2f} GB"]
    if duration:
        parts.append("时长 " + fmt_t(duration))
    if inner:
        parts.append("主流 " + Path(inner.replace("\\", "/")).name)
    if extra:
        parts.append(extra)
    if css_enc:
        parts.append("[!] VOB 被 CSS 加密, 无法截图")
    info = {"name": iso.name, "fileinfo": "  |  ".join(parts), "video": [], "audio": [], "subs": None}
    if brief:  # 联系表里的视频/音频/字幕行直接用 BDInfo 风格的精简文本
        ls = brief.splitlines()
        info["video"] = [l for l in ls if l.startswith("VIDEO:")][:2]
        info["audio"] = [l for l in ls if l.startswith("AUDIO:")][:8]
        sub = [l for l in ls if l.startswith("Subtitle:")]
        info["subs"] = sub[0] if sub else None
        return info
    v, a, s = ([], [], [])
    if mj:
        v, a, s = info_from_mediainfo(mj)
    elif probe:
        v, a, s = info_from_probe(probe)
    info["audio"] = [f"音频{i}: " + x for i, x in enumerate(a[:8], 1)]
    if len(a) > 8:
        info["audio"].append(f"... 另有 {len(a) - 8} 条音轨")
    info["video"] = ["视频: " + x for x in v[:2]]
    info["subs"] = (f"字幕({len(s)}): " + ", ".join(s)) if s else None
    return info


def sheet_lines(info, c):
    lines = []
    if c["show_filename"]:
        lines.append(info["name"])
    if c["show_fileinfo"]:
        lines.append(info["fileinfo"])
    if c["show_video"]:
        lines += info["video"]
    if c["show_audio"]:
        lines += info["audio"]
    if c["show_subs"] and info["subs"]:
        lines.append(info["subs"])
    return lines


def simple_report(info):
    return "\n".join([info["name"], info["fileinfo"]] + info["video"] + info["audio"]
                     + ([info["subs"]] if info["subs"] else []))


# ============================================================ BDInfo 风格 / 完整 MediaInfo 风格
# 移植自用户的 MediaInfo.py (基于 ffprobe), 改为直接读 bluray: / subfile 源, 不要求是真实文件
BITMAP_SUB_CODECS = {"hdmv_pgs_subtitle", "dvd_subtitle", "xsub"}


class MediaInfoError(Exception):
    """识别不到视频/音频信息，或文件无法读取"""


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
    "h264": "MPEG-4 AVC Video", "hevc": "HEVC Video", "vvc": "VVC (H.266) Video",
    "av1": "AV1 Video", "vp9": "VP9 Video", "vp8": "VP8 Video", "vp7": "VP7 Video",
    "vp6": "VP6 Video", "vp6f": "VP6 Video", "vp6a": "VP6 Video", "vp5": "VP5 Video",
    "avs3": "AVS3 Video", "avs2": "AVS2 Video", "cavs": "AVS Video",
    "mpeg1video": "MPEG-1 Video", "mpeg2video": "MPEG-2 Video", "mpeg4": "MPEG-4 Visual Video",
    "h261": "H.261 Video", "h263": "H.263 Video", "h263p": "H.263+ Video", "h263i": "H.263 Video",
    "vc1": "VC-1 Video", "vc1image": "VC-1 Video",
    "wmv1": "WMV7 Video", "wmv2": "WMV8 Video", "wmv3": "WMV9 Video", "wmv3image": "WMV9 Video",
    "msmpeg4v1": "MS MPEG-4 v1 Video", "msmpeg4v2": "MS MPEG-4 v2 Video", "msmpeg4v3": "MS MPEG-4 v3 (DivX 3) Video",
    "msmpeg4": "MS MPEG-4 Video", "msvideo1": "MS Video 1", "cinepak": "Cinepak Video",
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
        return ""
    return _MI_LANG_NAMES.get(code, code.upper())


def _mi_bps(stream):
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


_MI_STD_HEIGHTS = (4320, 2160, 1440, 1080, 720, 576, 540, 480, 360, 240)
_MI_STD_WIDTHS = ((7680, 4320), (4096, 2160), (3840, 2160), (2560, 1440), (1920, 1080), (1280, 720))


def _mi_resolution(s, interlaced=None):
    w = int(s.get("width") or 0)
    h = int(s.get("height") or 0)
    base = 0
    heights = _MI_STD_HEIGHTS if w < 1260 else [x for x in _MI_STD_HEIGHTS if x >= 720]
    for sh in heights:
        if abs(h - sh) <= sh * 0.03:
            base = sh
            break
    if not base:
        for sw, sh in _MI_STD_WIDTHS:
            if sw * 0.95 <= w <= sw * 1.01:
                base = sh
                break
    if not base:
        base = h
    if not base:
        return ""
    if interlaced is None:
        interlaced = (s.get("field_order") or "progressive") not in ("progressive", "unknown", "")
    return f"{base}{'i' if interlaced else 'p'}"


_MI_COMMON_AR = (
    ("1:1", 1.0), ("5:4", 1.25), ("4:3", 4 / 3), ("1.37:1", 1.37), ("3:2", 1.5), ("16:10", 1.6),
    ("5:3", 5 / 3), ("16:9", 16 / 9), ("1.85:1", 1.85), ("2:1", 2.0), ("2.20:1", 2.2),
    ("2.35:1", 2.35), ("21:9", 64 / 27), ("2.39:1", 2.39), ("2.40:1", 2.40),
)


def _mi_aspect(s):
    r = None
    dar = s.get("display_aspect_ratio")
    if dar and dar not in ("0:1", "N/A"):
        try:
            a, b = dar.split(":")
            if float(b) > 0 and float(a) > 0:
                r = float(a) / float(b)
        except Exception:
            r = None
    if r is None:
        w = int(s.get("width") or 0)
        h = int(s.get("height") or 0)
        if w and h:
            r = w / h
    if not r:
        return ""
    name, val = min(_MI_COMMON_AR, key=lambda x: abs(r - x[1]) / x[1])
    if abs(r - val) / val <= 0.005:
        return name
    return f"{r:.2f}:1"


def _mi_profile(s):
    prof = (s.get("profile") or "").strip()
    codec = (s.get("codec_name") or "").lower()
    try:
        lv = int(s.get("level") or 0)
    except Exception:
        lv = 0
    if lv in (-99, -1):
        lv = 0
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
            out += f" {2 + (lv >> 2)}.{lv & 3}"
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
    try:
        v = int(s.get("bits_per_raw_sample") or 0)
        if v > 0:
            return f"{v}-bit"
    except Exception:
        pass
    pf = (s.get("pix_fmt") or "").lower()
    if not pf:
        return ""
    m = re.search(r"(\d{2})(?:le|be)?$", pf)
    if m and int(m.group(1)) in (9, 10, 12, 14, 16):
        return f"{int(m.group(1))}-bit"
    m = re.match(r"^p(\d{3})", pf)
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


def _mi_probe_video_extra(ffprobe, pre, url):
    """解码前几帧: 读取 interlaced_frame、HDR10+ 动态元数据、静态 HDR 元数据"""
    info = {"interlaced": None, "pos": None, "hdr10plus": False, "side": []}
    try:
        cmd = [ffprobe, "-v", "error"] + pre + ["-select_streams", "v:0", "-read_intervals", "%+#8",
               "-show_entries", "packet=pos:frame=interlaced_frame,top_field_first:frame_side_data_list",
               "-print_format", "json", url]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60, creationflags=CREATE_NO_WINDOW)
        d = json.loads(proc.stdout or "{}")
    except Exception:
        return info
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
                info["side"].append(sd)
    return info


def _mi_scan_encoder(full_path, pos=None):
    """在首个视频帧附近的字节里找 x264 / x265 写入的编码参数字符串 (仅普通视频文件)"""
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
    fo = (s.get("field_order") or "").lower()
    if fo in ("tt", "bb", "tb", "bt"):
        return True
    if extra.get("interlaced") is True:
        return True
    if re.search(r"(?<!fake-)interlaced=1", enc.get("text", "")):
        return True
    return False


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
        if c == 0:
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
                return _mi_f(d.get(k))
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


def _mi_build_full(label, data, streams, extra, enc, first_video, video_fallback):
    fmt = data.get("format") or {}
    container_dur = _mi_f(fmt.get("duration"))
    sections = []

    g = ["General"]
    g.append(_mi_kv("Complete name", label))
    g.append(_mi_kv("Format", fmt.get("format_long_name") or fmt.get("format_name") or ""))
    if fmt.get("size"):
        g.append(_mi_kv("File size", _mi_size(fmt.get("size"))))
    if container_dur:
        g.append(_mi_kv("Duration", _mi_dur_h(container_dur)))
    try:
        g.append(_mi_kv("Overall bit rate", _mi_rate(int(float(fmt.get("bit_rate"))))))
    except Exception:
        pass
    n_ch = len(data.get("chapters") or [])
    if n_ch:
        g.append(_mi_kv("Streams / Chapters", f"{len(streams)} / {n_ch}"))
    else:
        g.append(_mi_kv("Streams", len(streams)))
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
            lab = t.get("filename") or s.get("codec_name") or ""
            mime = t.get("mimetype")
            o.append(_mi_kv(kind, f"{lab}" + (f" ({mime})" if mime else "")))
        if len(others) > 60:
            o.append(_mi_kv("...", f"另有 {len(others) - 60} 项未显示"))
        sections.append(o)

    return "\n\n".join("\n".join(sec) for sec in sections)


def _mi_apply_langs(streams, mj):
    """DVD: ffprobe 读 VOB 拿不到音轨/字幕语言, 用 IFO 的 MediaInfo 结果按顺序补上 (数量一致时才补)"""
    tracks = (mj or {}).get("media", {}).get("track", [])
    for ctype, mtype in (("audio", "Audio"), ("subtitle", "Text")):
        ss = [s for s in streams if s.get("codec_type") == ctype]
        ts = [t for t in tracks if t.get("@type") == mtype]
        if ss and len(ss) == len(ts):
            for s, t in zip(ss, ts):
                lang = t.get("Language")
                if lang and not (s.get("tags") or {}).get("language"):
                    s.setdefault("tags", {})["language"] = lang


def get_media_info_src(label, ffprobe, pre, url, lang_mj=None, duration_override=None, file_path=None):
    """对 bluray:/subfile 源生成 (精简文本, 完整文本, ffprobe JSON). 识别不到视频/音频时抛 MediaInfoError"""
    cmd = [ffprobe, "-v", "error", "-probesize", "50M", "-analyzeduration", "50M"] + pre + \
          ["-print_format", "json", "-show_streams", "-show_chapters", "-show_format", url]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=300, creationflags=CREATE_NO_WINDOW)
    except subprocess.TimeoutExpired:
        raise MediaInfoError("ffprobe 读取超时")
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

    if lang_mj:
        _mi_apply_langs(streams, lang_mj)
    fmt = data.setdefault("format", {})
    if duration_override:  # DVD: 用 IFO 里的精确时长, 码率按它重算
        fmt["duration"] = f"{duration_override:.6f}"
        try:
            size = int(fmt.get("size") or 0)
            if size:
                fmt["bit_rate"] = str(int(size * 8 / duration_override))
        except Exception:
            pass

    try:
        fmt_bps = int(float(fmt.get("bit_rate") or 0))
    except Exception:
        fmt_bps = 0
    audio_bps_sum = sum(_mi_bps(s) for s in audios)
    video_fallback = 0
    if len(real_videos) == 1 and fmt_bps > audio_bps_sum:
        video_fallback = fmt_bps - audio_bps_sum

    first_video = real_videos[0] if real_videos else None
    extra, enc = {}, {}
    if first_video is not None:
        extra = _mi_probe_video_extra(ffprobe, pre, url)
        if file_path:  # 普通视频文件: 读文件字节找 x264/x265 编码参数 (ISO 里没法按文件读, 不做)
            enc = _mi_scan_encoder(file_path, extra.get("pos"))

    lines, subs = [], []
    for s in streams:
        ctype = s.get("codec_type")
        tags = s.get("tags") or {}
        lang = tags.get("language", "und")
        title = tags.get("title", "") or ""
        if ctype == "video":
            if (s.get("disposition") or {}).get("attached_pic"):
                continue
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
    n_chapters = len(data.get("chapters") or [])
    if n_chapters > 0:
        lines.append(f"章节： {n_chapters}")

    try:
        full_text = _mi_build_full(label, data, streams, extra, enc, first_video, video_fallback)
    except Exception as e:
        full_text = "完整信息生成失败: " + str(e)
    return "\n".join(lines), full_text, data


SPOILER_OPEN = '[spoiler title="Mediainfo" open="no" style="default" icon="plus" anchor_in_url="no"]'
SPOILER_CLOSE = "[/spoiler]"


def format_all(brief, full):
    """完整版放进 spoiler 折叠块, 后面空一行再接简洁版"""
    return f"{SPOILER_OPEN}\n{full.rstrip()}\n{SPOILER_CLOSE}\n\n{brief.rstrip()}"


# ============================================================ 联系表
def load_font(size):
    from PIL import ImageFont
    for f in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\meiryo.ttc",
              r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            continue
    return ImageFont.load_default()


def wrap(draw, text, font, maxw):
    out, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) > maxw and cur:
            out.append(cur)
            cur = ch
        else:
            cur += ch
    out.append(cur)
    return out


def make_sheet(files, outpath, cols, rows, lines, show_ts=True, quality=92, font_scale=1.0,
               comment="", comment_color="#8CC8FF"):
    from PIL import Image, ImageDraw
    if not files:
        print("没有成功的截图, 无法生成联系表")
        return False
    imgs = {i: (t, Image.open(p)) for i, (t, p) in enumerate(files)}
    w, h = imgs[0][1].size
    gap, margin = 6, 14
    fs = max(12, int(max(15, w // 34) * font_scale))
    font = load_font(fs)
    tfont = load_font(max(12, int(max(14, w // 30) * font_scale)))
    line_h = int(fs * 1.45)

    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    sheet_w = margin * 2 + cols * w + (cols - 1) * gap
    wrapped = []
    for ln in lines:
        wrapped += wrap(d0, ln, font, sheet_w - margin * 2)
    cwrapped = []  # 注释: 最后一行(可多行, 字面写 \n 也换行), 用单独颜色
    for ln in str(comment or "").replace("\\n", "\n").splitlines():
        if ln.strip():
            cwrapped += wrap(d0, ln, font, sheet_w - margin * 2)
    try:
        from PIL import ImageColor
        ccolor = ImageColor.getrgb(comment_color or "#8CC8FF")
    except Exception:
        ccolor = (140, 200, 255)
    nlines = len(wrapped) + len(cwrapped)
    head_h = (margin * 2 + line_h * nlines) if nlines else margin
    sheet_h = head_h + rows * h + (rows - 1) * gap + margin

    sheet = Image.new("RGB", (sheet_w, sheet_h), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    y = margin
    for i, ln in enumerate(wrapped):
        d.text((margin, y), ln, font=font, fill=(255, 220, 120) if i == 0 else (235, 235, 235))
        y += line_h
    for ln in cwrapped:
        d.text((margin, y), ln, font=font, fill=ccolor)
        y += line_h
    for idx in range(cols * rows):
        if idx not in imgs:
            continue
        t, im = imgs[idx]
        x = margin + (idx % cols) * (w + gap)
        yy = head_h + (idx // cols) * (h + gap)
        sheet.paste(im.resize((w, h)), (x, yy))
        if show_ts:
            d.text((x + 8, yy + h - int(fs * 1.9)), fmt_t(t), font=tfont, fill=(255, 255, 255),
                   stroke_width=2, stroke_fill=(0, 0, 0))
    if str(outpath).lower().endswith(".png"):
        sheet.save(outpath)
    else:
        sheet.save(outpath, quality=int(quality))
    print(f"联系表: {outpath}")
    return True


# ============================================================ 核心处理
def unique_path(p):
    """已存在则在扩展名前加 (1)(2)... 直到不重名"""
    p = Path(p)
    if not p.exists():
        return p
    for i in range(1, 10000):
        q = p.with_name(f"{p.stem} ({i}){p.suffix}")
        if not q.exists():
            return q
    return p


def out_dirs(iso, c):
    isodir = iso.resolve().parent
    outdir = Path(c["out_dir"]) if (c["out_mode"] == "dir" and c["out_dir"]) else isodir
    return outdir, (Path(c["tmp_dir"]) if c["tmp_dir"] else isodir)


MI_MODES = ("simple", "full", "all", "mi_normal", "mi_full")


def process_iso(iso, cfg):
    """处理单个 ISO. 返回 dict(report, sheet, report_path, skipped). 失败抛 RuntimeError"""
    c = {**DEFAULTS, **cfg}
    iso = Path(iso)
    if not iso.is_file():
        raise RuntimeError(f"找不到文件: {iso}")
    outdir, tmpdir = out_dirs(iso, c)
    outdir.mkdir(parents=True, exist_ok=True)
    tmpdir.mkdir(parents=True, exist_ok=True)
    is_iso = iso.suffix.lower() == ".iso"
    base = iso.stem if is_iso else iso.name   # 非 ISO 保留扩展名, 避免 a.mkv / a.mp4 重名覆盖
    sheet_path = outdir / f"{base}_sheet.{'png' if c['sheet_fmt'] == 'png' else 'jpg'}"
    mi_path = outdir / f"{base}.mediainfo.txt"
    res = {"report": None, "sheet": None, "report_path": None, "skipped": False}

    exist = c["exist_mode"] if c["exist_mode"] in ("overwrite", "skip", "rename") else "overwrite"
    sheet_skip = mi_skip = False
    if exist == "rename":
        sheet_path, mi_path = unique_path(sheet_path), unique_path(mi_path)
    elif exist == "skip":
        sheet_skip = c["make_sheet"] and sheet_path.exists()
        mi_skip = c["do_mediainfo"] and c["save_mediainfo"] and mi_path.exists()
        if sheet_skip:
            print(f"联系表已存在, 跳过: {sheet_path.name}")
        if mi_skip:
            print(f"MediaInfo 文件已存在, 跳过: {mi_path.name}")
    need_sheet = c["make_sheet"] and not sheet_skip
    do_mi = c["do_mediainfo"] and not mi_skip
    need_save = do_mi and c["save_mediainfo"]
    if (sheet_skip or mi_skip) and not need_sheet and not do_mi:
        res["skipped"] = True
        return res

    ffmpeg = find_tool("ffmpeg", c["ffmpeg"] or None)
    ffprobe = find_tool("ffprobe", c["ffprobe"] or None)
    sevenz = find_tool("7z", c["sevenz"] or None, [r"C:\Program Files\7-Zip\7z.exe",
                                                    r"C:\Program Files (x86)\7-Zip\7z.exe"])
    mediainfo = find_tool("mediainfo", c["mediainfo"] or None, [r"C:\Program Files\MediaInfo\MediaInfo.exe"])
    playlist = int(c["playlist"]) if str(c["playlist"]).strip() else None
    duration = float(c["duration"]) if str(c["duration"]).strip() else None

    mode = {"normal": "mi_normal"}.get(c["mediainfo_mode"], c["mediainfo_mode"])  # 兼容旧设置
    if mode not in MI_MODES:
        mode = "simple"
    need_info = need_sheet and (c["show_video"] or c["show_audio"] or c["show_subs"])
    want_brief = do_mi or need_info           # 需要 ffprobe 流信息(精简/完整/联系表信息行)
    want_raw = do_mi and mode.startswith("mi_")  # 需要 MediaInfo 命令行的原始输出
    raw_mode = {"mi_normal": "normal", "mi_full": "full"}.get(mode, "simple") if want_raw else "simple"
    if want_raw and not mediainfo:
        print("未找到 mediainfo, MediaInfo 原生模式不可用, 将改用精简文本")

    dvd = scan_dvd(iso) if is_iso else None
    kind = "DVD-Video" if dvd else ("Blu-ray" if is_iso else iso.suffix[1:].upper() + " 视频文件")
    label = iso.name if is_iso else str(iso.resolve())
    probe, mj, raw, inner, extra = None, None, None, None, None
    brief = full = None
    pre, url, cleanup, rng, css_enc = [], None, None, None, False
    header = ""

    def run_brief(lang_mj=None, dur=None):
        nonlocal brief, full, probe
        try:
            brief, full, probe = get_media_info_src(label, ffprobe, pre, url, lang_mj, dur,
                                                    None if is_iso else url)
        except MediaInfoError as e:
            print("ffprobe 读取流信息失败:", e)

    try:
        if dvd:
            n, vt = dvd_pick_main(dvd)
            total = sum(v[2] for v in vt["vobs"])
            inner = f"VTS_{n:02d} ({len(vt['vobs'])} VOB)"
            print(f"DVD-Video: 主标题集 VTS_{n:02d}, {len(vt['vobs'])} 个 VOB, {total / 1024 ** 3:.2f} GB")
            if not ffmpeg:
                raise RuntimeError("找不到 ffmpeg")
            pre, url, cleanup, rng = dvd_source(iso, vt["vobs"], tmpdir)
            scr, tot = dvd_css_scan(iso, vt["vobs"])
            css_enc = tot > 0 and scr > tot // 2
            if css_enc:
                print(f"!! 检测到 VOB 被 CSS 加密 ({scr}/{tot}): ffmpeg 无法解码, 截图会是黑屏/花屏, "
                      "需先解密 (MakeMKV/DVDFab/DVD Decrypter)")
            else:
                print(f"CSS 加密检测: 无 ({scr}/{tot})")
            dur = None
            if mediainfo and (want_raw or want_brief):  # IFO: 精确时长 + 音轨/字幕语言 + 原始文本
                raw, mj, dur = do_mediainfo_dvd(mediainfo, iso, n, vt, raw_mode, tmpdir)
            duration = duration or dur
            if ffprobe and want_brief:
                run_brief(mj, duration)
            elif ffprobe and duration is None:
                probe = get_probe(ffprobe, pre, url)
            if duration is None and probe:
                try:
                    duration = float(probe["format"]["duration"])
                except Exception:
                    pass
            print(f"时长: {fmt_t(duration)}" if duration else "取不到时长, 可在 设置-高级 里手动指定")
            if duration:
                extra = f"平均码率 {total * 8 / duration / 1e6:.1f} Mb/s"
            header = (f"ISO            : {iso.name}\n类型           : DVD-Video\n"
                      f"主标题集       : VTS_{n:02d} ({len(vt['vobs'])} 个 VOB, {total / 1024 ** 3:.2f} GiB)\n"
                      + (f"时长           : {fmt_t(duration)}\n" if duration else "") + "\n")
        elif not is_iso:
            # ---- 普通视频文件: 直接用文件路径
            if not ffmpeg:
                raise RuntimeError("找不到 ffmpeg")
            url = str(iso.resolve())
            if ffprobe and want_brief:
                run_brief()
            elif ffprobe:
                probe = get_probe(ffprobe, pre, url)
            if duration is None and probe:
                try:
                    duration = float(probe["format"]["duration"])
                except Exception:
                    pass
            print(f"时长: {fmt_t(duration)}" if duration else "ffprobe 读取时长失败")
            if want_raw and mediainfo:
                raw = run([mediainfo] + (["--Full"] if raw_mode == "full" else []) + [url]).stdout
        else:
            if ffmpeg and ffprobe:
                if not check_bluray_protocol(ffmpeg):
                    print("!! 当前 ffmpeg 不支持 bluray: 协议, 请换 gyan.dev 的 full 构建")
                else:
                    pre = ["-playlist", str(playlist)] if playlist is not None else []
                    url = bd_src(iso)
                    if want_brief:
                        run_brief()
                    else:
                        probe = get_probe(ffprobe, pre, url)
                    if duration is None and probe:
                        try:
                            duration = float(probe["format"]["duration"])
                        except Exception:
                            pass
                    print(f"时长: {fmt_t(duration)}" if duration else "ffprobe 读取时长失败")
            # 只有 MediaInfo 原生模式, 或 ffprobe 读不了时, 才走 7z + mediainfo (读主 m2ts 开头一段)
            need_old = want_raw or (brief is None and want_brief)
            if need_old and sevenz and mediainfo:
                raw, mj, inner, msize = do_mediainfo_bd(sevenz, mediainfo, iso, int(c["head_mb"]),
                                                        raw_mode, tmpdir)
                header = (f"ISO            : {iso.name}\n类型           : Blu-ray\n"
                          f"主视频流       : {inner}\n"
                          f"该文件实际大小 : {msize} bytes ({msize / 1024 ** 3:.2f} GiB)\n"
                          + (f"播放列表时长   : {fmt_t(duration)} (ffprobe/libbluray)\n" if duration else "")
                          + "注意: 下面的 MediaInfo 只分析了文件开头一段, 其中的 Duration / Overall bitrate "
                            "/ File size 不代表整盘, 以上方信息为准。\n\n")
            elif need_old:
                print("缺少 7z 或 mediainfo, 蓝光的 MediaInfo 原生读取已跳过")
        check_cancel()

        info = collect_info(iso, kind, duration, inner, mj, probe, extra, css_enc, brief,
                            "ISO 大小" if is_iso else "文件大小")

        # ---- MediaInfo 报告
        if do_mi:
            if mode == "simple" and brief:
                report = brief
            elif mode == "full" and full:
                report = full
            elif mode == "all" and brief and full:
                report = format_all(brief, full)
            elif mode.startswith("mi_") and raw:
                report = header + raw
            else:
                report = simple_report(info)
            res["report"] = report
            if c["save_mediainfo"]:
                mi_path.write_text(report.rstrip("\n") + "\n", encoding="utf-8")
                res["report_path"] = str(mi_path)
                print(f"MediaInfo: {mi_path}")

        # ---- 联系表
        if need_sheet:
            if not (ffmpeg and duration and url):
                raise RuntimeError("缺少 ffmpeg / 时长 / 可读取的视频源, 无法截图 (可在 设置-高级 里手动指定时长)")
            try:
                import PIL  # noqa
            except ImportError:
                raise RuntimeError("需要 pillow: pip install pillow")
            cols, rows = int(c["grid_cols"]), int(c["grid_rows"])
            cnt = cols * rows
            lines = sheet_lines(info, c)
            args = (ffmpeg, pre, url, duration, cnt, int(c["thumb_width"]))
            kw = dict(tonemap=c["tonemap"], dvd=bool(dvd), dvd_range=rng,
                      seek_mode=c["seek_mode"], debug=c["debug"],
                      preroll=float(c["preroll"]))
            if c["keep_thumbs"]:
                files = make_thumbs(*args, outdir=outdir / f"{base}_thumbs", **kw)
                ok = make_sheet(files, sheet_path, cols, rows, lines, c["show_timestamp"],
                                c["jpeg_quality"], c["font_scale"], c["comment"], c["comment_color"])
            else:
                with tempfile.TemporaryDirectory(dir=tmpdir) as td:
                    files = make_thumbs(*args, outdir=Path(td), **kw)
                    ok = make_sheet(files, sheet_path, cols, rows, lines, c["show_timestamp"],
                                    c["jpeg_quality"], c["font_scale"], c["comment"], c["comment_color"])
            if ok:
                res["sheet"] = str(sheet_path)
        return res
    finally:
        if cleanup:
            shutil.rmtree(cleanup, ignore_errors=True)


# ============================================================ 命令行
def cli(argv):
    ap = argparse.ArgumentParser(description="DVD/蓝光 ISO: 联系表 + MediaInfo (不挂载). 不带参数则打开 GUI")
    ap.add_argument("iso", nargs="*", help="ISO / 视频文件 / 目录, 可多个")
    ap.add_argument("-r", "--recursive", action="store_true", help="目录递归子文件夹")
    ap.add_argument("--ext", help="追加要识别的视频扩展名, 如 .mkv,.rmvb")
    ap.add_argument("--preroll", type=float, help="预解码秒数 (默认 10, 防 HDTV 白色马赛克; 关键帧间隔很长时加大)")
    ap.add_argument("--gui", action="store_true", help="打开 GUI (可同时带 ISO 预加入列表)")
    ap.add_argument("--use-config", action="store_true", help=f"以 GUI 保存的设置 ({CONFIG_NAME}) 为基础")
    ap.add_argument("-o", "--outdir", help="输出目录, 默认 ISO 所在目录")
    ap.add_argument("--grid", help="联系表 列x行, 默认 2x3")
    ap.add_argument("-w", "--width", type=int, help="单格截图宽度")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--seek-time", action="store_true", help="DVD: 只按时间 seek 取帧")
    g.add_argument("--seek-bytes", action="store_true", help="DVD: 只按字节位置取帧")
    ap.add_argument("--mi-mode", choices=list(MI_MODES),
                    help="simple=精简(BDInfo风格) full=完整 all=完整(spoiler折叠)+精简 mi_normal/mi_full=MediaInfo命令行原生输出")
    ap.add_argument("--full", action="store_true", help="等同 --mi-mode full")
    ap.add_argument("--all", action="store_true", help="等同 --mi-mode all")
    ap.add_argument("--print-mediainfo", action="store_true", help="在终端打印 MediaInfo")
    ap.add_argument("--no-mediainfo", action="store_true", help="不读取 MediaInfo")
    ap.add_argument("--no-save-mediainfo", action="store_true", help="MediaInfo 只显示不存 txt")
    ap.add_argument("--no-thumbs", action="store_true", help="不生成联系表")
    ap.add_argument("--hide", default="", help="联系表隐藏项, 逗号分隔: filename,fileinfo,video,audio,subs,timestamp")
    ap.add_argument("--fmt", choices=["jpg", "png"])
    ap.add_argument("--quality", type=int)
    ap.add_argument("--font-scale", type=float)
    ap.add_argument("--tonemap", action="store_true", help="HDR 转 SDR 再截图")
    ap.add_argument("--keep-thumbs", action="store_true", help="保留单张截图")
    ap.add_argument("--skip-existing", action="store_true", help="同名输出已存在则跳过 (= --exists skip)")
    ap.add_argument("--exists", choices=["overwrite", "skip", "rename"],
                    help="同名输出已存在时: overwrite 覆盖(默认) / skip 跳过 / rename 自动改名加 (1)")
    ap.add_argument("--comment", help="联系表信息区最后一行的注释 (可写广告/备注, \\n 换行)")
    ap.add_argument("--comment-color", help="注释颜色, 如 red / #FF8800")
    ap.add_argument("--playlist", type=int, help="蓝光: 指定 mpls 编号, 如 800")
    ap.add_argument("--head-mb", type=int, help="蓝光: 喂给 MediaInfo 的数据量(MB)")
    ap.add_argument("--duration", type=float, help="取不到时长时手动指定(秒)")
    ap.add_argument("--tmpdir", help="临时文件目录, 默认 ISO 所在目录")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--ffmpeg"); ap.add_argument("--ffprobe")
    ap.add_argument("--7z", dest="sevenz"); ap.add_argument("--mediainfo")
    a = ap.parse_args(argv)

    if a.gui or not a.iso:
        return run_gui(a.iso)

    cfg = load_config() if a.use_config else dict(DEFAULTS)
    if a.outdir:
        cfg["out_mode"], cfg["out_dir"] = "dir", a.outdir
    if a.grid:
        m = re.match(r"^(\d+)\s*[xX*]\s*(\d+)$", a.grid)
        if not m:
            sys.exit("--grid 格式应为 列x行, 例如 2x3")
        cfg["grid_cols"], cfg["grid_rows"] = int(m.group(1)), int(m.group(2))
    for src, key in (("comment", "comment"), ("comment_color", "comment_color"), ("exists", "exist_mode"),
                     ("ext", "extra_exts"), ("preroll", "preroll"), ("width", "thumb_width"), ("quality", "jpeg_quality"), ("font_scale", "font_scale"),
                     ("fmt", "sheet_fmt"), ("playlist", "playlist"), ("head_mb", "head_mb"),
                     ("duration", "duration"), ("tmpdir", "tmp_dir"), ("ffmpeg", "ffmpeg"),
                     ("ffprobe", "ffprobe"), ("sevenz", "sevenz"), ("mediainfo", "mediainfo")):
        v = getattr(a, src)
        if v is not None:
            cfg[key] = v
    if a.seek_time:
        cfg["seek_mode"] = "time"
    if a.seek_bytes:
        cfg["seek_mode"] = "bytes"
    if a.full:
        cfg["mediainfo_mode"] = "full"
    if a.all:
        cfg["mediainfo_mode"] = "all"
    if a.mi_mode:
        cfg["mediainfo_mode"] = a.mi_mode
    if a.no_mediainfo:
        cfg["do_mediainfo"] = False
    if a.no_save_mediainfo:
        cfg["save_mediainfo"] = False
    if a.no_thumbs:
        cfg["make_sheet"] = False
    for k in [x.strip() for x in a.hide.split(",") if x.strip()]:
        if "show_" + k in cfg:
            cfg["show_" + k] = False
    for flag, key in ((a.tonemap, "tonemap"), (a.keep_thumbs, "keep_thumbs"),
                      (a.debug, "debug")):
        if flag:
            cfg[key] = True

    if a.skip_existing:
        cfg["exist_mode"] = "skip"
    if a.recursive:
        cfg["recursive"] = True
    files = collect_inputs(a.iso, cfg["recursive"], media_exts(cfg["extra_exts"]), strict=False)
    if not files:
        print("没有找到可处理的文件 (目录是否需要 -r? 扩展名可用 --ext 追加)")
        return 1
    fails = 0
    for i, f in enumerate(files, 1):
        print(f"\n===== [{i}/{len(files)}] {Path(f).name} =====")
        try:
            r = process_iso(f, cfg)
            if a.print_mediainfo and r["report"]:
                print("\n" + r["report"] + "\n")
        except Exception as e:
            fails += 1
            print("失败:", e)
            if cfg["debug"]:
                traceback.print_exc()
    print(f"\n完成: {len(files) - fails} 成功, {fails} 失败")
    return 1 if fails else 0


# ============================================================ GUI
class QWriter:
    def __init__(self, q):
        self.q = q

    def write(self, s):
        if s:
            self.q.put(("log", s))
        return len(s or "")

    def flush(self):
        pass


def run_gui(initial=()):
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    dnd_ok = False
    DND_FILES = None
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD
        root = TkinterDnD.Tk()
        dnd_ok = True
    except Exception:
        root = tk.Tk()

    cfg = load_config()
    root.title("DVD / 蓝光 ISO 截图 + MediaInfo")
    root.geometry(cfg.get("geometry") or "1180x760")
    root.minsize(900, 560)
    q = queue.Queue()
    V = {}
    state = {"running": False, "worker": None}
    reports = {}
    mono = ("Consolas", 10) if os.name == "nt" else ("DejaVu Sans Mono", 10)

    def var(key):
        if key in V:  # 同一设置的多个控件(如单选按钮组)必须共用同一个变量
            return V[key]
        d, val = DEFAULTS[key], cfg.get(key, DEFAULTS[key])
        if isinstance(d, bool):
            v = tk.BooleanVar(value=bool(val))
        elif isinstance(d, int):
            v = tk.IntVar(value=int(val))
        elif isinstance(d, float):
            v = tk.DoubleVar(value=float(val))
        else:
            v = tk.StringVar(value=str(val))
        V[key] = v
        return v

    def collect():
        out = dict(DEFAULTS)
        for k, v in V.items():
            try:
                out[k] = v.get()
            except Exception:
                out[k] = DEFAULTS[k]
        out["geometry"] = root.geometry()
        out["last_dir"] = cfg.get("last_dir", "")
        return out

    # ---------- 布局: 左 文件列表 / 右 设置页
    pw = ttk.PanedWindow(root, orient="horizontal")
    pw.pack(fill="both", expand=True, padx=6, pady=6)
    left = ttk.Frame(pw)
    right = ttk.Frame(pw)
    pw.add(left, weight=2)
    pw.add(right, weight=3)

    hint = "把 ISO / 视频文件 / 文件夹拖到这里" if dnd_ok else "点 [添加文件] 选择文件   (pip install tkinterdnd2 后可拖拽)"
    ttk.Label(left, text=hint, foreground="#555").pack(anchor="w", pady=(0, 4))

    tb = ttk.Frame(left)
    tb.pack(fill="x")
    tree_fr = ttk.Frame(left)
    tree_fr.pack(fill="both", expand=True, pady=4)
    tree = ttk.Treeview(tree_fr, columns=("name", "type", "status"), show="headings", selectmode="extended")
    for col, txt, wd in (("name", "文件", 300), ("type", "类型", 70), ("status", "状态", 80)):
        tree.heading(col, text=txt)
        tree.column(col, width=wd, anchor="w" if col == "name" else "center", stretch=(col == "name"))
    sb = ttk.Scrollbar(tree_fr, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    prog = ttk.Progressbar(left, mode="determinate")
    prog.pack(fill="x", pady=(2, 0))
    status = tk.StringVar(value="就绪")
    ttk.Label(left, textvariable=status).pack(anchor="w")

    # ---------- 右侧 Notebook
    nb = ttk.Notebook(right)
    nb.pack(fill="both", expand=True)

    def tab(title):
        f = ttk.Frame(nb, padding=10)
        nb.add(f, text=title)
        return f

    def check(parent, text, key, row, col=0, span=2):
        ttk.Checkbutton(parent, text=text, variable=var(key)).grid(row=row, column=col, columnspan=span,
                                                                  sticky="w", pady=2)

    def spin(parent, text, key, lo, hi, row, inc=1, col=0, width=7):
        ttk.Label(parent, text=text).grid(row=row, column=col, sticky="w", pady=2, padx=(0, 6))
        ttk.Spinbox(parent, from_=lo, to=hi, increment=inc, textvariable=var(key),
                    width=width).grid(row=row, column=col + 1, sticky="w", pady=2)

    def entry(parent, text, key, row, browse=None, width=44):
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=3, padx=(0, 6))
        ttk.Entry(parent, textvariable=var(key), width=width).grid(row=row, column=1, sticky="we", pady=3)
        if browse:
            def pick():
                p = filedialog.askdirectory() if browse == "dir" else filedialog.askopenfilename()
                if p:
                    V[key].set(p)
            ttk.Button(parent, text="浏览", width=6, command=pick).grid(row=row, column=2, padx=4)

    # -- 截图
    t1 = tab("截图")
    check(t1, "生成联系表截图", "make_sheet", 0)
    spin(t1, "列数", "grid_cols", 1, 12, 1)
    spin(t1, "行数", "grid_rows", 1, 12, 2)
    spin(t1, "单格宽度(px)", "thumb_width", 160, 3840, 3, inc=40)
    ttk.Label(t1, text="输出格式").grid(row=4, column=0, sticky="w", pady=2)
    ttk.Combobox(t1, textvariable=var("sheet_fmt"), values=["jpg", "png"], width=6,
                 state="readonly").grid(row=4, column=1, sticky="w")
    spin(t1, "JPEG 质量", "jpeg_quality", 50, 100, 5)
    lf = ttk.LabelFrame(t1, text="取帧方式 (仅 DVD; 蓝光始终按时间)", padding=6)
    lf.grid(row=6, column=0, columnspan=3, sticky="we", pady=8)
    for i, (val, txt) in enumerate((("auto", "自动: 先按字节(--seek-bytes), 仍黑屏再按时间"),
                                    ("bytes", "只按字节位置  (--seek-bytes, 不依赖时间戳, 更稳)"),
                                    ("time", "只按时间 seek  (--seek-time)"))):
        ttk.Radiobutton(lf, text=txt, value=val, variable=var("seek_mode")).grid(row=i, column=0, sticky="w")
    check(t1, "HDR → SDR 色调映射 (4K 蓝光截图发灰时)", "tonemap", 7)
    check(t1, "保留单张截图 (<文件名>_thumbs 文件夹)", "keep_thumbs", 8)
    spin(t1, "预解码秒数", "preroll", 0, 120, 9)
    ttk.Label(t1, text="防 HDTV/TS 白色马赛克: 先 seek 到目标前 N 秒的关键帧, 再解码到目标时间。\n"
                       "关键帧间隔很长 (>10 秒) 的视频可加大。", foreground="#666").grid(
        row=10, column=0, columnspan=3, sticky="w", pady=(2, 0))

    # -- 文件
    t0 = tab("文件")
    check(t0, "添加文件夹时递归子文件夹", "recursive", 0, span=3)
    entry(t0, "追加扩展名", "extra_exts", 1, width=30)
    ttk.Label(t0, text="逗号或空格分隔, 如  .mkv, .rmvb   (ISO 始终支持)", foreground="#666").grid(
        row=2, column=0, columnspan=3, sticky="w")
    ttk.Label(t0, text="默认已支持:").grid(row=3, column=0, sticky="nw", pady=(10, 0))
    ttk.Label(t0, text=" ".join(sorted(DEFAULT_VIDEO_EXTS)), wraplength=420, justify="left",
              foreground="#444").grid(row=3, column=1, columnspan=2, sticky="w", pady=(10, 0))
    t0.columnconfigure(1, weight=1)

    # -- 联系表内容
    t2 = tab("联系表内容")
    for i, (k, txt) in enumerate((("show_filename", "显示文件名"),
                                  ("show_fileinfo", "显示文件信息行 (类型/大小/时长/平均码率)"),
                                  ("show_video", "显示视频信息 (编码/分辨率/帧率/码率)"),
                                  ("show_audio", "显示音频信息"), ("show_subs", "显示字幕信息"),
                                  ("show_timestamp", "每张截图左下角显示时间"))):
        check(t2, txt, k, i)
    spin(t2, "文字缩放", "font_scale", 0.5, 3.0, 6, inc=0.1)
    entry(t2, "注释 (最后一行)", "comment", 7, width=40)
    entry(t2, "注释颜色", "comment_color", 8, width=14)
    ttk.Label(t2, text="注释显示在信息区最后一行, 可写广告 / 备注; 想换行写 \\n; 留空则不显示。\n"
                       "颜色可写名字 (red) 或 #RRGGBB。", foreground="#666").grid(
        row=9, column=0, columnspan=3, sticky="w")

    # -- MediaInfo
    t3 = tab("MediaInfo")
    top = ttk.Frame(t3)
    top.pack(fill="x")
    ttk.Checkbutton(top, text="读取 MediaInfo", variable=var("do_mediainfo")).grid(row=0, column=0, sticky="w")
    ttk.Checkbutton(top, text="同时生成 txt 文件", variable=var("save_mediainfo")).grid(row=0, column=1,
                                                                                  sticky="w", padx=10)
    mrow = ttk.Frame(t3)
    mrow.pack(fill="x", pady=4)
    ttk.Label(mrow, text="模式:").pack(side="left")
    for val, txt in (("simple", "精简"), ("full", "完整"), ("all", "完整(折叠)+精简"),
                     ("mi_normal", "MediaInfo原生标准"), ("mi_full", "MediaInfo原生Full")):
        ttk.Radiobutton(mrow, text=txt, value=val, variable=var("mediainfo_mode")).pack(side="left", padx=4)
    mrow2 = ttk.Frame(t3)
    mrow2.pack(fill="x")
    ttk.Label(mrow2, text="(原生模式才用到)  蓝光读取量(MB):").pack(side="left")
    ttk.Spinbox(mrow2, from_=16, to=2048, increment=16, textvariable=var("head_mb"),
                width=6).pack(side="left", padx=4)
    brow = ttk.Frame(t3)
    brow.pack(fill="x", pady=2)
    mi_text = tk.Text(t3, wrap="none", font=mono, height=10)
    msy = ttk.Scrollbar(t3, orient="vertical", command=mi_text.yview)
    msx = ttk.Scrollbar(t3, orient="horizontal", command=mi_text.xview)
    mi_text.configure(yscrollcommand=msy.set, xscrollcommand=msx.set)
    msx.pack(side="bottom", fill="x")
    msy.pack(side="right", fill="y")
    mi_text.pack(fill="both", expand=True)

    # -- 输出
    t4 = tab("输出")
    ttk.Radiobutton(t4, text="输出到 ISO 所在目录", value="iso_dir", variable=var("out_mode")).grid(
        row=0, column=0, columnspan=3, sticky="w")
    ttk.Radiobutton(t4, text="输出到指定目录", value="dir", variable=var("out_mode")).grid(
        row=1, column=0, columnspan=3, sticky="w")
    entry(t4, "指定目录", "out_dir", 2, "dir")
    entry(t4, "临时目录", "tmp_dir", 3, "dir")
    ttk.Label(t4, text="(临时目录留空 = ISO 所在目录; 用完自动删除, 避免系统盘空间不足)",
              foreground="#666").grid(row=4, column=0, columnspan=3, sticky="w")
    lf2 = ttk.LabelFrame(t4, text="同名输出文件已存在时 (联系表 / MediaInfo txt 各自判断)", padding=6)
    lf2.grid(row=5, column=0, columnspan=3, sticky="we", pady=8)
    for i, (val, txt) in enumerate((("overwrite", "覆盖"), ("skip", "跳过 (批量续跑)"),
                                    ("rename", "自动改名, 文件名后加 (1)(2)…"))):
        ttk.Radiobutton(lf2, text=txt, value=val, variable=var("exist_mode")).grid(row=i, column=0, sticky="w")
    t4.columnconfigure(1, weight=1)

    # -- 高级
    t5 = tab("高级")
    entry(t5, "蓝光播放列表编号", "playlist", 0, width=10)
    entry(t5, "手动指定时长(秒)", "duration", 1, width=10)
    entry(t5, "ffmpeg 路径", "ffmpeg", 2, "file")
    entry(t5, "ffprobe 路径", "ffprobe", 3, "file")
    entry(t5, "7z 路径", "sevenz", 4, "file")
    entry(t5, "mediainfo 路径", "mediainfo", 5, "file")
    ttk.Label(t5, text="(路径留空 = 自动从 PATH / 常见位置查找)", foreground="#666").grid(
        row=6, column=0, columnspan=3, sticky="w")
    check(t5, "调试: 日志里打印 ffmpeg 完整命令", "debug", 7, span=3)

    def reset_defaults():
        if messagebox.askyesno("恢复默认", "把所有设置恢复为默认值?"):
            for k, v in V.items():
                if k not in ("geometry", "last_dir"):
                    v.set(DEFAULTS[k])
    ttk.Button(t5, text="恢复默认设置", command=reset_defaults).grid(row=8, column=0, sticky="w", pady=10)
    t5.columnconfigure(1, weight=1)

    # -- 日志
    t6 = tab("日志")
    log = tk.Text(t6, wrap="word", font=mono, state="disabled")
    lsb = ttk.Scrollbar(t6, orient="vertical", command=log.yview)
    log.configure(yscrollcommand=lsb.set)
    lsb.pack(side="right", fill="y")
    log.pack(fill="both", expand=True)

    def log_add(s):
        log.configure(state="normal")
        log.insert("end", s)
        log.see("end")
        log.configure(state="disabled")

    # ---------- 文件列表操作
    def add_paths(paths):
        exts = media_exts(V["extra_exts"].get())
        found = collect_inputs(list(paths), bool(V["recursive"].get()), exts, strict=True)
        added = 0
        for f in found:
            iid = str(f)
            if tree.exists(iid):
                continue
            if f.suffix.lower() == ".iso":
                try:
                    typ = "DVD" if scan_dvd(f) else "蓝光"
                except Exception:
                    typ = "?"
            else:
                typ = "视频"
            tree.insert("", "end", iid=iid, values=(f.name, typ, "等待"))
            added += 1
        if paths and not found:
            status.set("没有可添加的文件 (扩展名不支持? 可在 设置-文件 里追加; 目录是否要勾选递归?)")
        elif added:
            status.set(f"已添加 {added} 个, 共 {len(tree.get_children())} 个")
            cfg["last_dir"] = str(Path(str(list(paths)[0]).strip("{}")).parent)

    def add_files():
        exts = sorted(media_exts(V["extra_exts"].get()))
        ps = filedialog.askopenfilenames(
            title="选择 ISO / 视频文件", initialdir=cfg.get("last_dir") or None,
            filetypes=[("ISO 和视频", " ".join("*" + e for e in exts)), ("ISO 镜像", "*.iso"),
                       ("所有文件", "*.*")])
        if ps:
            add_paths(list(ps))

    def add_folder():
        p = filedialog.askdirectory(initialdir=cfg.get("last_dir") or None)
        if p:
            add_paths([p])

    def remove_sel():
        for i in tree.selection():
            tree.delete(i)
            reports.pop(i, None)

    def clear_all():
        for i in tree.get_children():
            tree.delete(i)
        reports.clear()
        mi_text.delete("1.0", "end")

    if dnd_ok:
        for w in (root, tree):
            w.drop_target_register(DND_FILES)
            w.dnd_bind("<<Drop>>", lambda e: add_paths(list(root.tk.splitlist(e.data))))

    # ---------- 运行
    def set_running(on):
        state["running"] = on
        for b in (b_start, b_start_sel, b_mi):
            b.configure(state="disabled" if on else "normal")
        b_stop.configure(state="normal" if on else "disabled")

    def worker(items, c):
        CANCEL.clear()
        w = QWriter(q)
        with contextlib.redirect_stdout(w), contextlib.redirect_stderr(w):
            for k, iid in enumerate(items):
                if CANCEL.is_set():
                    q.put(("status", iid, "已停止"))
                    continue
                q.put(("status", iid, "处理中"))
                print(f"\n===== [{k + 1}/{len(items)}] {Path(iid).name} =====")
                try:
                    r = process_iso(iid, c)
                    if r.get("report"):
                        q.put(("report", iid, r["report"]))
                    q.put(("status", iid, "已跳过" if r.get("skipped") else "完成"))
                except Cancelled:
                    print("已停止")
                    q.put(("status", iid, "已停止"))
                except Exception as e:
                    print("失败:", e)
                    if c.get("debug"):
                        traceback.print_exc()
                    q.put(("status", iid, "失败"))
                q.put(("progress", k + 1, len(items)))
        q.put(("done",))

    def start(selected=False, mi_only=False):
        if state["running"]:
            return
        items = list(tree.selection()) if (selected or mi_only) else list(tree.get_children())
        if mi_only:
            items = items[:1]
        if not items:
            messagebox.showinfo("提示", "请先添加 ISO" if not (selected or mi_only) else "请先在列表里选中文件")
            return
        c = collect()
        save_config(c)
        if mi_only:
            c.update(make_sheet=False, do_mediainfo=True, save_mediainfo=False, exist_mode="overwrite")
        for i in items:
            tree.set(i, "status", "等待")
        prog.configure(maximum=len(items), value=0)
        set_running(True)
        status.set("处理中 ...")
        t = threading.Thread(target=worker, args=(items, c), daemon=True)
        state["worker"] = t
        t.start()
        if not mi_only:
            nb.select(t6)
        else:
            nb.select(t3)

    def stop():
        CANCEL.set()
        status.set("正在停止 (等当前这一步结束) ...")

    def show_report(iid):
        mi_text.delete("1.0", "end")
        if iid in reports:
            mi_text.insert("1.0", reports[iid])

    def on_select(_e=None):
        sel = tree.selection()
        if sel:
            show_report(sel[0])

    tree.bind("<<TreeviewSelect>>", on_select)

    def poll():
        try:
            while True:
                m = q.get_nowait()
                if m[0] == "log":
                    log_add(m[1])
                elif m[0] == "status":
                    if tree.exists(m[1]):
                        tree.set(m[1], "status", m[2])
                elif m[0] == "report":
                    reports[m[1]] = m[2]
                    sel = tree.selection()
                    if (sel and sel[0] == m[1]) or not sel or len(tree.get_children()) == 1:
                        show_report(m[1])
                elif m[0] == "progress":
                    prog.configure(value=m[1])
                    status.set(f"进度 {m[1]}/{m[2]}")
                elif m[0] == "done":
                    set_running(False)
                    status.set("全部完成" if not CANCEL.is_set() else "已停止")
        except queue.Empty:
            pass
        root.after(100, poll)

    def copy_mi():
        root.clipboard_clear()
        root.clipboard_append(mi_text.get("1.0", "end").rstrip())
        status.set("MediaInfo 已复制到剪贴板")

    def save_mi():
        sel = tree.selection()
        init = (Path(sel[0]).stem + ".mediainfo.txt") if sel else "mediainfo.txt"
        p = filedialog.asksaveasfilename(initialfile=init, defaultextension=".txt",
                                         filetypes=[("文本", "*.txt")])
        if p:
            Path(p).write_text(mi_text.get("1.0", "end").rstrip() + "\n", encoding="utf-8")
            status.set(f"已保存: {p}")

    def open_out():
        sel = tree.selection() or tree.get_children()
        if not sel:
            return
        d, _ = out_dirs(Path(sel[0]), collect())
        try:
            os.startfile(str(d))
        except AttributeError:
            subprocess.Popen(["xdg-open", str(d)])

    # ---------- 按钮
    def btn(parent, text, cmd, **kw):
        b = ttk.Button(parent, text=text, command=cmd, **kw)
        b.pack(side="left", padx=2)
        return b
    btn(tb, "添加文件", add_files)
    btn(tb, "添加文件夹", add_folder)
    btn(tb, "移除选中", remove_sel)
    btn(tb, "清空", clear_all)
    tb2 = ttk.Frame(left)
    tb2.pack(fill="x", pady=(2, 0))
    b_start = btn(tb2, "▶ 开始(全部)", lambda: start())
    b_start_sel = btn(tb2, "开始(选中)", lambda: start(selected=True))
    b_stop = btn(tb2, "■ 停止", stop, state="disabled")
    btn(tb2, "打开输出目录", open_out)
    b_mi = ttk.Button(brow, text="读取选中文件的 MediaInfo", command=lambda: start(mi_only=True))
    b_mi.pack(side="left", padx=2)
    ttk.Button(brow, text="复制", command=copy_mi).pack(side="left", padx=2)
    ttk.Button(brow, text="另存为…", command=save_mi).pack(side="left", padx=2)
    ttk.Button(log.master, text="清空日志", command=lambda: (log.configure(state="normal"),
                                                         log.delete("1.0", "end"),
                                                         log.configure(state="disabled"))).pack(side="bottom")

    def on_close():
        c = collect()
        save_config(c)
        CANCEL.set()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)

    if initial:
        add_paths(list(initial))
    poll()
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(cli(sys.argv[1:]))
