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
      7-Zip 是可选的: 只有「蓝光 ISO」的 隐藏字幕检测 / MediaInfo 原生模式 才会用到, 没有也能正常截图和出精简/完整报告
      GUI 拖拽需 pip install tkinterdnd2 (没装也能用按钮添加)
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
import time
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
    "tonemap_mode": "auto",     # HDR→SDR: off 关 / on 强制 / auto 识别到 HDR 才映射
    "keep_thumbs": False,
    "sheet_fmt": "jpg", "jpeg_quality": 92, "make_sheet": True,
    # 联系表内容
    "show_filename": False, "show_fileinfo": True, "show_video": True,
    "show_audio": True, "show_subs": True, "show_timestamp": True, "font_scale": 1.0,
    # MediaInfo
    # simple 精简(BDInfo风格) / full 完整 / all 完整(spoiler折叠)+精简 / mi_normal,mi_full MediaInfo命令行原生
    "do_mediainfo": True, "mediainfo_mode": "simple",
    "save_mediainfo": True, "head_mb": 128,
    # 输出
    "out_mode": "iso_dir", "out_dir": "", "tmp_dir": "",
    "exist_mode": "overwrite",      # 同名输出已存在时: overwrite 覆盖 / skip 跳过 / rename 自动改名 (1)
    "comment": "", "comment_color": "#8CC8FF", "font_path": "",   # 联系表信息区最后一行的注释 (可写广告/备注)
    # 输出文件名后缀: 留空 = 无后缀 (GUI); 命令行不写 = 默认后缀, 写 "" 才是无后缀
    "sheet_suffix": "_sheet", "mi_suffix": ".mediainfo",
    "sheet_prefix": "", "mi_prefix": "",          # 文件名前缀, 如 media_ -> media_xxx.mkv.txt
    # 联系表外观
    "bg_color": "#18181C", "text_color": "#EBEBEB", "name_color": "#FFDC78", "ts_color": "#FFFFFF",
    # 图片水印 (透明 PNG) 和 文字水印: 放在整张联系表上, 大小/位置都按联系表宽高的比例算, 所以不随图片大小变化
    # 位置: tl tc tr / cl cc cr / bl bc br 九宫格, 或 custom (用 x/y 百分比: 0=贴左/上边, 100=贴右/下边)
    "wm_enable": False, "wm_path": "", "wm_scale": 0.15, "wm_opacity": 100, "wm_pos": "tr", "wm_x": 100.0, "wm_y": 0.0,
    "tx_enable": False, "tx_text": "", "tx_color": "#FFFFFF", "tx_size": 0.03, "tx_opacity": 100, "tx_stroke": True,
    "tx_pos": "br", "tx_x": 100.0, "tx_y": 100.0,
    "detect_cc": True,             # 检测隐藏字幕 (EIA-608/708, 用 mediainfo 命令行)
    "bd_mode": "auto",             # 蓝光读取方式: auto (libbluray 读不到正常时长时自动改直读 m2ts) / direct (总是直读 m2ts) / libbluray
    "shot_timeout": 30,            # 单张截图最长等待秒数, 超时强行结束并清除中间文件 (冷门编码/损坏的视频会一直卡住)
    "deinterlace": True,           # 反交错: 隔行视频截图去拉丝
    "enhance_shots": True,         # 加强截图: 有 1~2 张画面单调(黑/白/绿屏等)或失败, 就在附近关键帧重截; 超过 2 张则判断为视频可能损坏, 不重截
    # 高级
    "recursive": False, "extra_exts": "", "preroll": 10,
    "top_n": 1,                    # DVD/蓝光 ISO: 最多截取时长最长的前 N 个标题
    # 过滤 (rclone 风格): 每行一条 "+ 模式" 包含 / "- 模式" 排除, 按顺序, 第一条匹配的生效
    "filter_rules": "", "min_size": "", "max_size": "", "min_age": "", "max_age": "", "filter_ignore_case": True,
    "playlist": "", "duration": "", "debug": False,
    "ffmpeg": "", "ffprobe": "", "sevenz": "", "mediainfo": "",
    # 界面记忆
    "geometry": "", "win_state": "normal", "sash": 0, "last_dir": "", "pending": [],     # pending: 上次没处理完/失败的队列 (崩溃恢复, 仅 GUI)
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
        if data.get("tonemap") is True and "tonemap_mode" not in data:
            cfg["tonemap_mode"] = "on"
        if str(data.get("wm_path") or "").strip() and "wm_enable" not in data:   # 旧版: 填了图片路径就是启用
            cfg["wm_enable"] = True
    except Exception:
        pass
    return cfg


def save_config(cfg):
    """原子写入 (先写临时文件再替换), 断电/崩溃时不会留下写了一半的 json"""
    try:
        data = {k: cfg.get(k, v) for k, v in DEFAULTS.items()}
        path = config_path()
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    except Exception as e:
        print("保存设置失败:", e)


# ============================================================ 通用
class Cancelled(BaseException):     # 不继承 Exception: 这样中间的 "except Exception" 吞不掉「用户点了停止」
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


def _child(p, name):
    """不区分大小写地找子项 (Linux 上 BDMV / bdmv 都能找到)"""
    try:
        for x in Path(p).iterdir():
            if x.name.upper() == name.upper():
                return x
    except OSError:
        pass
    return None


def disc_root(p):
    """文件夹是不是解压出来的 DVD / 蓝光? 返回 ("bd"|"dvd", 光盘根目录) 或 None.
    也认直接拖进来的 BDMV / VIDEO_TS 文件夹本身 (根目录取其上一级)"""
    p = Path(p)
    if not p.is_dir():
        return None
    name = p.name.upper()
    bdmv = p if name == "BDMV" else _child(p, "BDMV")
    if bdmv and bdmv.is_dir():
        st = _child(bdmv, "STREAM")
        if st and st.is_dir() and any(x.suffix.lower() == ".m2ts" for x in st.iterdir()):
            return "bd", (p.parent if name == "BDMV" else p)
    vts = p if name == "VIDEO_TS" else _child(p, "VIDEO_TS")
    if vts and vts.is_dir():
        if any(re.match(r"^VTS_\d\d_[1-9]\.VOB$", x.name, re.I) for x in vts.iterdir()):
            return "dvd", (p.parent if name == "VIDEO_TS" else p)
    return None


def media_kind(p):
    """路径 -> 'iso' / 'bdfolder' / 'dvdfolder' / 'file' / 'dir' / None"""
    p = Path(p)
    if p.is_dir():
        r = disc_root(p)
        return {"bd": "bdfolder", "dvd": "dvdfolder"}[r[0]] if r else "dir"
    if p.is_file():
        return "iso" if p.suffix.lower() == ".iso" else "file"
    return None


def _pattern_has_wild(p):
    return any(ch in str(p) for ch in "*?[")


def expand_pattern(pat, recursive, exts):
    """通配符 (如 D:/常用/*.iso 或 D:/常用/*): 非递归只看那个目录, -r 递归子目录.
    只写 * 或 *.* 这种没指定扩展名的, 按已知视频扩展名过滤; 写了具体扩展名 (*.iso / *.xyz) 就照写的来"""
    import fnmatch
    pat = str(pat)
    d, name = os.path.split(pat)
    if _pattern_has_wild(d):                    # 目录部分也带通配符: 交给 glob
        import glob
        hits = glob.glob(pat, recursive=bool(recursive))
        return [Path(h) for h in hits]
    d = d or "."
    explicit_ext = bool(re.search(r"\.[A-Za-z0-9]+$", name))
    base = Path(d)
    if not base.is_dir():
        return []
    out = []

    def want(x):
        if not fnmatch.fnmatch(x.name.lower(), name.lower()):
            return False
        return x.is_dir() or explicit_ext or x.suffix.lower() in exts

    def walk(dirp, depth):
        try:
            items = sorted(dirp.iterdir(), key=_natural)
        except OSError:
            return
        for x in items:
            if x.is_dir():
                if disc_root(x):
                    if want(x) or name in ("*", "*.*"):
                        out.append(x)
                elif recursive:
                    walk(x, depth + 1)
            elif x.is_file() and want(x):
                out.append(x)
    walk(base, 0)
    return out


def scan_dir_items(folder, recursive, exts):
    """扫描一个普通目录: 返回其中的视频文件 + 解压的 DVD/蓝光文件夹 (后者作为整体, 不进入内部)"""
    out = []

    def walk(dirp, top):
        try:
            items = sorted(dirp.iterdir(), key=_natural)
        except OSError:
            return
        for x in items:
            if x.is_dir():
                if disc_root(x):
                    out.append(x)            # 光盘文件夹: 即使不递归, 直接子目录里的光盘也算
                elif recursive:
                    walk(x, False)
            elif x.is_file() and x.suffix.lower() in exts:
                out.append(x)
    walk(folder, True)
    return out


INPUT_ROOT = {}      # 条目的绝对路径 -> 它是从哪个根目录收集来的 (过滤规则里以 / 开头的"锚定"规则要用)


def collect_inputs(paths, recursive, exts, strict=True, disc_folders=True):
    """文件/目录/通配符 -> 条目列表 (去重, 自然排序).
    目录若本身就是解压的 DVD/蓝光, 作为一个条目返回 (disc_folders=False 时当普通目录展开).
    strict: 单独给的文件也必须是已知扩展名"""
    out, seen = [], set()

    def add(f, root=None):
        k = str(Path(f).resolve())
        INPUT_ROOT.setdefault(k, str(root if root is not None else Path(f).parent))
        if k not in seen:
            seen.add(k)
            out.append(Path(f))

    for p in paths:
        p = Path(str(p).strip("{}"))
        if _pattern_has_wild(p) and not p.exists():
            for f in expand_pattern(p, recursive, exts):
                if f.is_dir() and not disc_root(f):
                    for g in scan_dir_items(f, recursive, exts):
                        add(g, f)
                else:
                    add(f, f.parent)
            continue
        if p.is_dir():
            r = disc_root(p)
            if r and disc_folders:
                add(r[1], r[1].parent)
            else:
                for f in scan_dir_items(p, recursive, exts) if not r else \
                        sorted((x for x in (p.rglob("*") if recursive else p.iterdir())
                                if x.is_file() and x.suffix.lower() in exts), key=_natural):
                    add(f, p)
        elif p.is_file() and (not strict or p.suffix.lower() in exts):
            add(p, p.parent)
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


def _kill(p):
    try:
        p.kill()
        p.communicate(timeout=5)
    except Exception:
        pass


def run(cmd, timeout=None, **kw):
    """subprocess.run 的升级版: 点「停止」(CANCEL) 立刻强行结束子进程并抛 Cancelled;
    超过 timeout 秒也强行结束并抛 subprocess.TimeoutExpired (冷门编码 / 损坏文件会让 ffmpeg 一直卡着)"""
    p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, encoding="utf-8", errors="replace", creationflags=CREATE_NO_WINDOW, **kw)
    t0 = time.time()
    while True:
        try:
            out, err = p.communicate(timeout=0.25)
            return subprocess.CompletedProcess(cmd, p.returncode, out, err)
        except subprocess.TimeoutExpired:
            pass
        if CANCEL.is_set():
            _kill(p)
            raise Cancelled()
        if timeout is not None and time.time() - t0 > timeout:
            _kill(p)
            raise subprocess.TimeoutExpired(cmd, timeout)


def fmt_size(n):
    """联系表里的大小: >= 1GB 用 GB, 否则用 MB, 都保留两位小数: 1.50GB / 222.11MB / 11.00MB"""
    n = float(n or 0)
    return f"{n / 1024 ** 3:.2f}GB" if round(n / 1024 ** 2, 2) >= 1024 else f"{n / 1024 ** 2:.2f}MB"


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
    try:
        r = run(cmd, timeout=300)
    except subprocess.TimeoutExpired:
        print("ffprobe 读取超过 300 秒, 已强制结束")
        return None
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


_FILTER_CACHE = {}


def has_filter(ffmpeg, name):
    """当前 ffmpeg 有没有某个滤镜 (HDR 色调映射需要 zscale 和 tonemap)"""
    if ffmpeg not in _FILTER_CACHE:
        try:
            _FILTER_CACHE[ffmpeg] = run([ffmpeg, "-hide_banner", "-filters"]).stdout or ""
        except Exception:
            _FILTER_CACHE[ffmpeg] = ""
    return re.search(r"\s" + re.escape(name) + r"\s", _FILTER_CACHE[ffmpeg]) is not None


def hdr_kind(probe):
    """首个视频流是 HDR 吗: 返回 'pq' (HDR10/HDR10+/DV 的 PQ 基础层) / 'hlg' / None"""
    for s in (probe or {}).get("streams", []):
        if s.get("codec_type") == "video" and not (s.get("disposition") or {}).get("attached_pic"):
            trc = (s.get("color_transfer") or "").lower()
            if trc == "smpte2084":
                return "pq"
            if trc == "arib-std-b67":
                return "hlg"
            return None
    return None


MONO_STD = 6.0      # 缩小后三个通道的最大标准差低于它 = 画面单调 (纯黑/纯白/纯绿/纯色)


def frame_score(path):
    """画面丰富度: 纯色画面 ≈ 0, 有内容的画面一般 > 15. 读不了就当正常"""
    try:
        from PIL import Image, ImageStat
        im = Image.open(path).convert("RGB").resize((64, 36))
        return max(ImageStat.Stat(im).stddev)
    except Exception:
        return 99.0


def _capture_enhanced(grab, grab_bytes, byte_time, ffmpeg, pre, url, duration, n, outdir, order, stats, shot_timeout=30,
                      t_offset=0.0):
    """加强截图: 先每个位置截一张; 只有 1~2 张单调/失败时才在附近关键帧 (上下各最多 2 个) 重截,
    都单调就取最丰富的一张; 超过 2 张单调/失败 → 大概率视频本身有问题, 不重截, 只告警"""
    def shot(method, frac, t, out):
        if method == "bytes":
            f = min(max(frac, 0.0), 0.995)
            ok, err, pts = grab_bytes(f, out)
            return ok, (byte_time(f, pts) if ok else t), err
        t2 = min(max(t, 0), max(duration - 1, 0))
        ok, err = grab(t2, out)
        return ok, t2, err

    def keyframes_near(t0):
        """目标时间附近的关键帧 (I 帧) 时间: 用 ffmpeg 从目标前 30 秒起往后找"""
        ss = max(t0 - 30, 0)
        cmd = [ffmpeg, "-hide_banner", "-loglevel", "info"] + pre + [
            "-ss", f"{ss + t_offset:.3f}", "-i", url, "-map", "0:v:0", "-an", "-t", "90",
            "-vf", "select='eq(pict_type\\,I)',showinfo", "-frames:v", "60", "-f", "null", "-"]
        try:
            r = run(cmd, timeout=shot_timeout * 2)
            return sorted(ss + float(m) for m in re.findall(r"pts_time:\s*(-?[\d.]+)", r.stderr or ""))
        except (subprocess.TimeoutExpired, OSError, ValueError):
            return []

    R = []
    for i in range(n):
        check_cancel()
        frac0 = (i + 1) / (n + 1)
        t0 = duration * frac0
        out = outdir / f"thumb_{i + 1:02d}.jpg"
        ok, t_used, err = shot(order[0], frac0, t0, out)
        sc = frame_score(out) if ok else -1.0
        R.append({"i": i, "frac": frac0, "t0": t0, "out": out, "ok": ok, "t": t_used, "score": sc})
        tag = "ok" if ok and sc >= MONO_STD else ("失败: " + err[-120:] if not ok else "画面单调")
        print(f"  [{i + 1}/{n}] {fmt_t(t_used if ok else t0)} {tag}")

    def bad_of(rs):
        return [r for r in rs if (not r["ok"]) or r["score"] < MONO_STD]
    bad = bad_of(R)
    st = stats if stats is not None else {}
    st.update(total=n, bad_initial=len(bad), warn="")
    if len(bad) > 2:
        st["warn"] = f"{len(bad)}/{n} 张截图画面单调或失败, 视频可能已损坏"
        print(f"!! {st['warn']} (超过 2 张, 不再重新截图)")
    elif bad:
        for r in bad:
            check_cancel()
            i = r["i"]
            cands = []
            if len(order) > 1:
                cands.append((order[1], r["frac"], r["t0"]))
            if order[0] == "time":
                kfs = keyframes_near(r["t0"])
                if kfs:
                    idx = min(range(len(kfs)), key=lambda k: abs(kfs[k] - r["t0"]))
                    for d in (-1, 1, -2, 2):
                        if 0 <= idx + d < len(kfs):
                            cands.append(("time", r["frac"], kfs[idx + d]))
                else:
                    cands += [("time", r["frac"], r["t0"] + d) for d in (-2, 2, -4, 4)]
            else:
                cands += [("bytes", r["frac"] + d * 0.004, r["t0"]) for d in (-1, 1, -2, 2)]
            print(f"  [{i + 1}/{n}] 画面单调/失败, 在附近关键帧重截 (最多 {len(cands)} 次) ...")
            best_sc, best_t, best_path = (r["score"], r["t"], r["out"]) if r["ok"] else (-1.0, r["t0"], None)
            for k, (m, fr, tt) in enumerate(cands):
                check_cancel()
                cand = outdir / f"thumb_{i + 1:02d}_c{k}.jpg"
                ok, t_used, _e = shot(m, fr, tt, cand)
                if not ok:
                    continue
                sc = frame_score(cand)
                if sc > best_sc:
                    best_sc, best_t, best_path = sc, t_used, cand
                if sc >= MONO_STD:
                    break
            if best_path is not None and best_path != r["out"]:
                shutil.copyfile(best_path, r["out"])
            for k in range(len(cands)):
                try:
                    (outdir / f"thumb_{i + 1:02d}_c{k}.jpg").unlink()
                except OSError:
                    pass
            if best_path is not None:
                r.update(ok=True, t=best_t, score=best_sc)
                print(f"  [{i + 1}/{n}] 最终取 {fmt_t(best_t)}" + ("" if best_sc >= MONO_STD else " (附近也都是单调画面, 只能选这张)"))
    st["bad_final"] = len(bad_of(R))
    return [(r["t"], r["out"]) for r in R if r["ok"]]


def make_thumbs(ffmpeg, pre, url, duration, n, width, outdir, tonemap, dvd=False,
                dvd_range=None, seek_mode="auto", debug=False, preroll=10, enhance=False, stats=None,
                shot_timeout=30, deinterlace=True, t_offset=0.0):
    """dvd_range = (ISO路径, 标题集起始字节, 结束字节), 用于不依赖时间戳的"按字节偏移"取帧"""
    outdir.mkdir(parents=True, exist_ok=True)
    vf = []
    if deinterlace:    # 反交错 (去拉丝): 只处理解码器标记为隔行的帧 (HDTV 1080i / DVD), 逐行的帧原样通过
        vf.append("yadif=mode=0:deint=interlaced")
    vf += ["scale='trunc(iw*sar/2)*2':ih", "setsar=1"]   # 按 SAR 还原画面比例 (DVD / 1440x1080 等非方形像素)
    timeouts = [0]

    def run_shot(cmd, out):
        """单张截图最多 shot_timeout 秒: 超时就强行结束 ffmpeg 并删掉写了一半的图; 连续超时 3 次判定视频无法解码, 放弃"""
        try:
            return run(cmd, timeout=shot_timeout)
        except subprocess.TimeoutExpired:
            timeouts[0] += 1
            try:
                out.unlink()
            except OSError:
                pass
            print(f"   单张截图超过 {shot_timeout} 秒, 已强行结束并清除中间文件 ({timeouts[0]}/3)")
            if timeouts[0] >= 3:
                raise RuntimeError(f"截图连续 {timeouts[0]} 次超过 {shot_timeout} 秒, 视频可能已损坏或编码太冷门, 放弃截图")
            return subprocess.CompletedProcess(cmd, -9, "", f"超时 (>{shot_timeout}s), 已强行结束")
    if tonemap:   # tonemap: "tags" 按流里的标签 / "pq" 流没标签时按 PQ BT.2020 处理
        # 流里本来就有 HDR 标签: 直接按标签映射; 没标签却强制映射: 先用 setparams 补上 PQ/BT.2020 标签
        first = ("setparams=color_primaries=bt2020:color_trc=smpte2084:colorspace=bt2020nc:range=tv,"
                 "zscale=t=linear:npl=100" if tonemap == "pq" else "zscale=t=linear:npl=100")
        vf.append(first + ",format=gbrpf32le,zscale=p=bt709,"
                  "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    vf.append(f"scale={width}:-2")
    vf = ",".join(vf)

    def grab(t, out):
        # 防白色马赛克: 先 seek 到目标前 preroll 秒(落在关键帧), 再从那里一路解码到目标时间,
        # 这样目标帧一定是从完整的参考帧链解出来的, 而不是从非关键帧起解码 (TS/HDTV 常见)
        roll = min(float(preroll), t + t_offset)
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "warning"] + pre
        cmd += ["-probesize", "100M", "-analyzeduration", "100M",
                "-ss", f"{t + t_offset - roll:.3f}", "-i", url, "-ss", f"{roll:.3f}",
                "-map", "0:v:0", "-frames:v", "1", "-vf", vf, "-q:v", "2", "-update", "1", str(out)]
        r = run_shot(cmd, out)
        if debug:
            print("   $ " + " ".join(cmd))
            print("   " + clean_err(r.stderr).replace("\n", "\n   "))
        return (out.exists() and out.stat().st_size > 0), clean_err(r.stderr)

    def grab_bytes(frac, out):
        """从 ISO 内标题集的 frac 位置(按字节)开始读, 跳过开头 10 帧(此处可能缺参考帧)后取一帧;
        返回 (ok, err, 帧的原始 PTS 秒)"""
        # dvd_range = [(文件路径, 起始字节, 结束字节), ...]: ISO 里的 VOB 区段, 或 DVD 文件夹里的各个 VOB 文件
        total = sum(e - b for _, b, e in dvd_range)
        pos = min(int(total * frac), total - 1)
        for path, b0, e0 in dvd_range:
            if pos < e0 - b0:
                break
            pos -= e0 - b0
        st = b0 + pos
        st -= (st - b0) % SEC
        u = f"subfile,,start,{st},end,{e0},,:{path}"
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "info", "-copyts", "-probesize", "50M",
               "-i", u, "-map", "0:v:0", "-frames:v", "1",
               "-vf", "select=gte(n\\,10),showinfo," + vf, "-q:v", "2", "-update", "1", str(out)]
        r = run_shot(cmd, out)
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

    if enhance:
        return _capture_enhanced(grab, grab_bytes, byte_time, ffmpeg, pre, url, duration, n, outdir, order, stats,
                                 shot_timeout, t_offset)

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
_M2TS_CACHE = {}


def list_m2ts(sevenz, iso):
    """BDMV/STREAM 里每个 m2ts 的 (路径, 大小). 只是让 7-Zip 列出 ISO 的目录, 不解压任何内容; 同一个 ISO 只列一次"""
    try:
        key = (str(iso), os.path.getmtime(iso), os.path.getsize(iso))
    except OSError:
        key = None
    if key and key in _M2TS_CACHE:
        return list(_M2TS_CACHE[key])
    t0 = time.time()
    res = _list_m2ts_uncached(sevenz, iso)
    if key:
        _M2TS_CACHE[key] = list(res)
    print(f"7-Zip 列出 ISO 里的文件: {time.time() - t0:.1f} 秒 (只读目录, 不解压)")
    return res


def _list_m2ts_uncached(sevenz, iso):
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
                check_cancel()
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
# ============================================================ 蓝光: 绕过 libbluray 直接读 m2ts
# 动机: 有些 UHD 蓝光上 ffmpeg 的 bluray: 协议读不到整段时长 (只读到 0~1 秒), 也就没法按时间跳转, 截图全落在开头.
# 蓝光文件夹: 直接用 BDMV/STREAM 里的 m2ts 文件. 蓝光 ISO: 用 7-Zip 取到 m2ts 大小, 再到 UDF 结构里找它在 ISO 里的位置, 用 subfile 直读.
def parse_mpls(data):
    """播放列表 -> [(片段名, 入点, 出点)], 入出点单位 1/45000 秒"""
    if not data or data[:4] != b"MPLS":
        return []
    try:
        p = int.from_bytes(data[8:12], "big")
        n = int.from_bytes(data[p + 6:p + 8], "big")
        p += 10
        items = []
        for _ in range(n):
            ln = int.from_bytes(data[p:p + 2], "big")
            clip = data[p + 2:p + 7].decode("ascii", "ignore")
            items.append((clip, int.from_bytes(data[p + 14:p + 18], "big"), int.from_bytes(data[p + 18:p + 22], "big")))
            p += 2 + ln
        return items
    except Exception:
        return []


def parse_clpi_langs(data):
    """片段信息 CLPI -> {PID: 语言代码}: 蓝光的音轨/字幕语言记在这里 (m2ts 自己的 PMT 里常常没有)"""
    if not data or data[:4] != b"HDMV":
        return {}
    langs = {}
    try:
        p = int.from_bytes(data[12:16], "big") + 4          # ProgramInfo, 跳过 length(4)
        nps = data[p + 1]
        p += 2
        for _ in range(nps):
            p += 6                                           # SPN_program_sequence_start(4) + program_map_PID(2)
            nst = data[p]
            p += 2                                           # number_of_streams + number_of_groups
            for _s in range(nst):
                pid = int.from_bytes(data[p:p + 2], "big")
                ln = data[p + 2]
                info = data[p + 3:p + 3 + ln]
                p += 3 + ln
                if not info:
                    continue
                ct = info[0]
                if ct in (0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0xA1, 0xA2):    # 音频: 格式/采样率(1) + 语言(3)
                    lg = info[2:5]
                elif ct in (0x90, 0x91):                                             # PG / IG 字幕
                    lg = info[1:4]
                elif ct == 0x92:                                                     # 文字字幕: 字符编码(1) + 语言(3)
                    lg = info[2:5]
                else:
                    continue
                code = lg.decode("ascii", "ignore").strip("\x00 ")
                if len(code) == 3 and code.isalpha():
                    langs[pid] = code.lower()
    except Exception:
        pass
    return langs


def read_bd_file(is_folder, root, rel, sevenz):
    """读 BDMV 里的小文件 (mpls / clpi). 文件夹直接读; ISO 用 7z -so 取"""
    try:
        if is_folder:
            q = Path(root)
            for part in rel.split("/"):
                q = _child(q, part)
                if q is None:
                    return None
            return q.read_bytes()
        if sevenz:
            for name in (rel, rel.replace("/", "\\")):
                r = subprocess.run([sevenz, "e", "-so", str(root), name], capture_output=True, timeout=60,
                                   stdin=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
                if r.returncode == 0 and r.stdout:
                    return r.stdout
    except Exception:
        pass
    return None


def _udf_partition_start(f):
    f.seek(256 * SEC)
    d = f.read(SEC)
    if len(d) < SEC or int.from_bytes(d[0:2], "little") != 2:         # 卷描述符指针 AVDP
        return None
    vlen, vloc = int.from_bytes(d[16:20], "little"), int.from_bytes(d[20:24], "little")
    f.seek(vloc * SEC)
    vds = f.read(min(max(vlen, SEC), 64 * SEC))
    for i in range(0, len(vds) - SEC + 1, SEC):
        if int.from_bytes(vds[i:i + 2], "little") == 5:               # 分区描述符
            return int.from_bytes(vds[i + 188:i + 192], "little")
    return None


def _udf_extents(b, is_efe, ps, size):
    """File Entry / Extended File Entry -> [(起始字节, 长度)]; 不支持的 (续接/稀疏/内嵌) 返回 None"""
    adt = int.from_bytes(b[34:36], "little") & 7
    if is_efe:
        lea, lad, base = int.from_bytes(b[208:212], "little"), int.from_bytes(b[212:216], "little"), 216
    else:
        lea, lad, base = int.from_bytes(b[168:172], "little"), int.from_bytes(b[172:176], "little"), 176
    base += lea
    if base + lad > len(b) or adt not in (0, 1):
        return None
    step = 8 if adt == 0 else 16
    out, left = [], size
    for i in range(0, lad - step + 1, step):
        v = int.from_bytes(b[base + i:base + i + 4], "little")
        ln, typ = v & 0x3FFFFFFF, v >> 30
        if ln == 0:
            break
        if typ != 0:
            return None
        lbn = int.from_bytes(b[base + i + 4:base + i + 8], "little")
        take = min(ln, left)
        out.append(((ps + lbn) * SEC, take))
        left -= take
        if left <= 0:
            break
    if left > 0 or not out:
        return None
    merged = [list(out[0])]
    for st, ln in out[1:]:                      # 相邻的区段合并
        if merged[-1][0] + merged[-1][1] == st:
            merged[-1][1] += ln
        else:
            merged.append([st, ln])
    return [(a, b2) for a, b2 in merged]


def udf_find_extents(iso, size):
    """在 UDF 里找「大小恰好等于 size」的那个文件的数据位置. 不解析目录树 (蓝光的目录在元数据分区里, 绕过它):
    直接扫描分区开头附近 (和结尾处的元数据镜像) 的 File Entry, 按文件大小匹配, 再用 m2ts 的同步字节 0x47 校验"""
    try:
        total = os.path.getsize(iso)
        with open(iso, "rb") as f:
            ps = _udf_partition_start(f)
            if ps is None:
                return None
            base = ps * SEC
            regions = [(base, min(total, base + 256 * 1024 * 1024)),
                       (base + 256 * 1024 * 1024, min(total, base + 2048 * 1024 * 1024)),
                       (max(base, total - 256 * 1024 * 1024), total)]
            for lo, hi in regions:
                pos = lo
                while pos < hi:
                    check_cancel()
                    f.seek(pos)
                    buf = f.read(min(8 * 1024 * 1024, hi - pos))
                    if not buf:
                        break
                    for o in range(0, len(buf) - SEC + 1, SEC):
                        if buf[o + 1] == 1 and buf[o] in (5, 10) and \
                                int.from_bytes(buf[o + 56:o + 64], "little") == size:
                            ext = _udf_extents(buf[o:o + SEC], buf[o] == 10, ps, size)
                            if not ext:
                                continue
                            f.seek(ext[0][0])
                            d = f.read(400)
                            if len(d) >= 197 and ((d[4] == 0x47 and d[196] == 0x47) or (d[0] == 0x47 and d[188] == 0x47)):
                                return ext
                    pos += len(buf)
    except OSError:
        return None
    return None


def _bd_stream_files(is_folder, root, sevenz):
    """{片段名: (路径或ISO内路径, 大小)}"""
    if is_folder:
        st = _child(_child(root, "BDMV"), "STREAM")
        return {x.stem: (x, x.stat().st_size) for x in st.iterdir() if x.suffix.lower() == ".m2ts"} if st else {}
    if not sevenz:
        return {}
    return {Path(pth.replace("\\", "/")).stem: (pth, sz) for pth, sz in list_m2ts(sevenz, root)}


def bd_main_clip(is_folder, root, playlist, sevenz):
    """主片段名 (如 '00000'): 知道播放列表就取它的第一个片段, 否则取最大的 m2ts"""
    if playlist is not None:
        mp = parse_mpls(read_bd_file(is_folder, root, f"BDMV/PLAYLIST/{int(playlist):05d}.mpls", sevenz))
        if mp:
            return mp[0][0]
    files = _bd_stream_files(is_folder, root, sevenz)
    return max(files, key=lambda k: files[k][1]) if files else None


def bd_pid_langs(is_folder, root, playlist, sevenz):
    clip = bd_main_clip(is_folder, root, playlist, sevenz)
    if not clip:
        return None
    return parse_clpi_langs(read_bd_file(is_folder, root, f"BDMV/CLIPINF/{clip}.clpi", sevenz)) or None


def bd_direct_source(is_folder, root, playlist, sevenz, tmpdir, ffprobe=None):
    """蓝光直读 m2ts, 返回 dict(pre, url, cleanup, duration) 或 None"""
    try:
        if playlist is None and ffprobe:                       # 没指定播放列表: 取最长的那个
            lst = list_bd_titles(ffprobe, root)
            playlist = lst[0][0] if lst else None
        clips, dur, rng1 = [], None, None
        if playlist is not None:
            mp = parse_mpls(read_bd_file(is_folder, root, f"BDMV/PLAYLIST/{int(playlist):05d}.mpls", sevenz))
            if mp:
                clips = [c for c, _, _ in mp]
                dur = sum((o - i) / 45000.0 for _, i, o in mp)
                if len(mp) == 1:
                    rng1 = (mp[0][1] / 45000.0, mp[0][2] / 45000.0)      # 单片段播放列表: 用到的入点/出点 (秒)
        files = _bd_stream_files(is_folder, root, sevenz)
        if not files:
            return None
        if not clips:
            clips = [max(files, key=lambda k: files[k][1])]
        if any(c not in files for c in clips):
            return None
        if is_folder:
            paths = [files[c][0].resolve().as_posix() for c in clips]
            if len(paths) == 1:
                return {"pre": [], "url": paths[0], "cleanup": None, "duration": dur, "range": rng1}
            lines = ["ffconcat version 1.0"] + ["file '" + q.replace("'", "'\\''") + "'" for q in paths]
            lst = Path(tempfile.mkdtemp(dir=tmpdir)) / "clips.ffconcat"
            lst.write_text("\n".join(lines), encoding="utf-8")
            return {"pre": ["-f", "concat", "-safe", "0"], "url": str(lst), "cleanup": lst.parent, "duration": dur,
                    "range": None}
        isop = Path(root).resolve().as_posix()
        segs = []
        for c in clips:
            ext = udf_find_extents(root, files[c][1])
            if not ext:
                print(f"在 ISO 的 UDF 结构里没找到 {c}.m2ts 的位置")
                return None
            segs += [(isop, a, a + ln) for a, ln in ext]
        if len(segs) == 1:
            return {"pre": [], "url": f"subfile,,start,{segs[0][1]},end,{segs[0][2]},,:{segs[0][0]}",
                    "cleanup": None, "duration": dur, "range": rng1}
        lines = ["ffconcat version 1.0"] + [
            "file '" + f"subfile,,start,{a},end,{b},,:{pth}".replace("'", "'\\''") + "'" for pth, a, b in segs]
        lst = Path(tempfile.mkdtemp(dir=tmpdir)) / "clips.ffconcat"
        lst.write_text("\n".join(lines), encoding="utf-8")
        return {"pre": ["-f", "concat", "-safe", "0", "-protocol_whitelist", "file,subfile,concat"],
                "url": str(lst), "cleanup": lst.parent, "duration": dur, "range": None}
    except Cancelled:
        raise
    except Exception as e:
        print("蓝光直读 m2ts 失败:", e)
        return None


def do_mediainfo_bd_folder(mediainfo, root, raw_mode):
    """蓝光文件夹: 直接对 BDMV/STREAM 里最大的 m2ts 跑 mediainfo (整个文件, 数据是准的)"""
    st = _child(_child(root, "BDMV"), "STREAM")
    m2 = max((x for x in st.iterdir() if x.suffix.lower() == ".m2ts"), key=lambda x: x.stat().st_size)
    txt, mj = None, None
    if raw_mode in ("normal", "full"):
        txt = run([mediainfo] + (["--Full"] if raw_mode == "full" else []) + [str(m2)]).stdout
    try:
        mj = json.loads(run([mediainfo, "--Full", "--Output=JSON", str(m2)]).stdout)
    except Exception:
        mj = None
    return txt, mj, m2.name, m2.stat().st_size


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


def scan_dvd_folder(root):
    """解压出来的 DVD 文件夹: 结构和 scan_dvd 一样, 只是位置是文件路径(Path)而不是 ISO 里的扇区号"""
    vt = _child(root, "VIDEO_TS") if Path(root).name.upper() != "VIDEO_TS" else Path(root)
    if not vt or not vt.is_dir():
        return None
    vts = {}
    for x in vt.iterdir():
        m = re.match(r"^VTS_(\d\d)_(\d)\.(VOB|IFO|BUP)$", x.name, re.I)
        if not m or not x.is_file():
            continue
        n, part, ext = int(m.group(1)), int(m.group(2)), m.group(3).upper()
        e = vts.setdefault(n, {"ifo": None, "vobs": []})
        if ext == "IFO" and part == 0:
            e["ifo"] = (x, x.stat().st_size)
        elif ext == "VOB" and part >= 1:
            e["vobs"].append((part, x, x.stat().st_size, x.name))
    for e in vts.values():
        e["vobs"].sort(key=lambda v: v[0])
    return {k: v for k, v in vts.items() if v["vobs"]}


def scan_dvd_any(path):
    """ISO 文件 或 DVD 文件夹 -> scan 结果 (不是 DVD 返回 None)"""
    path = Path(path)
    if path.is_dir():
        r = disc_root(path)
        return scan_dvd_folder(r[1]) if r and r[0] == "dvd" else None
    return scan_dvd(path)


def path_size(p):
    """文件大小; 文件夹则为其中所有文件之和"""
    p = Path(p)
    if p.is_file():
        return p.stat().st_size
    total = 0
    for dp, _dn, fn in os.walk(p):
        for f in fn:
            try:
                total += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return total


def read_range(iso, loc, size):
    if isinstance(loc, Path):           # DVD 文件夹里的文件
        with open(loc, "rb") as f:
            return f.read(size)
    with open(iso, "rb") as f:
        f.seek(loc * SEC)
        return f.read(size)


def dvd_pick_main(vts):
    n = max(vts, key=lambda k: sum(v[2] for v in vts[k]["vobs"]))
    return n, vts[n]


def dvd_source(iso, vobs, tmpdir):
    """返回 (ffmpeg前置参数, url, 需清理的目录, 区段列表[(路径,起,止)...]).
    ISO: VOB 在 ISO 内连续时用单个 subfile, 否则 concat; DVD 文件夹: 单个 VOB 直接用, 多个用 concat"""
    if isinstance(vobs[0][1], Path):
        segs = [(v[1].resolve().as_posix(), 0, v[2]) for v in vobs]
        if len(segs) == 1:
            return [], segs[0][0], None, segs
        lines = ["ffconcat version 1.0"] + ["file '" + sp.replace("'", "'\\''") + "'" for sp, _, _ in segs]
        lst = Path(tempfile.mkdtemp(dir=tmpdir)) / "vobs.ffconcat"
        lst.write_text("\n".join(lines), encoding="utf-8")
        return ["-f", "concat", "-safe", "0"], str(lst), lst.parent, segs
    path = iso.resolve().as_posix()
    contiguous = all(vobs[i + 1][1] == vobs[i][1] + (vobs[i][2] + SEC - 1) // SEC
                     for i in range(len(vobs) - 1))
    if contiguous:
        start = vobs[0][1] * SEC
        end = vobs[-1][1] * SEC + vobs[-1][2]
        return [], f"subfile,,start,{start},end,{end},,:{path}", None, [(path, start, end)]
    lines = ["ffconcat version 1.0"]
    for _, lba, size, _n in vobs:
        u = f"subfile,,start,{lba * SEC},end,{lba * SEC + size},,:{path}".replace("'", "'\\''")
        lines.append(f"file '{u}'")
    lst = Path(tempfile.mkdtemp(dir=tmpdir)) / "vobs.ffconcat"
    lst.write_text("\n".join(lines), encoding="utf-8")
    segs = [(path, lba * SEC, lba * SEC + size) for _, lba, size, _n in vobs]
    return (["-f", "concat", "-safe", "0", "-protocol_whitelist", "file,subfile,concat"],
            str(lst), lst.parent, segs)


def dvd_css_scan(iso, vobs):
    """抽样检查第一个 VOB 里视频 PES 包的加扰标志位. 返回 (被加扰包数, 视频包总数)"""
    lba, size = vobs[0][1], vobs[0][2]
    nsec = size // SEC
    scr = tot = 0
    folder = isinstance(lba, Path)
    with open(lba if folder else iso, "rb") as f:
        for i in range(2000):
            f.seek((i * nsec // 2000 if folder else lba + i * nsec // 2000) * SEC)
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
            fr = to_f(t.get("FrameRate_Original")) or to_f(t.get("FrameRate"))
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
    parts = [kind, f"{size_label} {fmt_size(path_size(iso))}"]
    if duration:
        parts.append("时长 " + fmt_t(duration))
    if inner:
        parts.append("主流 " + Path(inner.replace("\\", "/")).name)
    if extra:
        parts.append(extra)
    if css_enc:
        parts.append("[!] VOB 被 CSS 加密, 无法截图")
    info = {"name": iso.name, "fileinfo": "  |  ".join(parts), "video": [], "audio": [], "subs": None, "cc": None}
    if brief:  # 联系表里的视频/音频/字幕行直接用 BDInfo 风格的精简文本
        ls = brief.splitlines()
        info["video"] = [l for l in ls if l.startswith("VIDEO:")][:2]
        info["audio"] = [l for l in ls if l.startswith("AUDIO:")][:8]
        sub = [l for l in ls if l.startswith("Subtitle:")]
        info["subs"] = sub[0] if sub else None
        cc = [l for l in ls if l.startswith("隐藏字幕:")]
        info["cc"] = cc[0] if cc else None
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
    if c["show_subs"] and info.get("cc"):
        lines.append(info["cc"])
    return lines


def simple_report(info):
    return "\n".join([info["name"], info["fileinfo"]] + info["video"] + info["audio"]
                     + ([info["subs"]] if info["subs"] else []) + ([info["cc"]] if info.get("cc") else []))


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
    is_zh = code in _MI_ZH_CODES or (code in ("und", "") and re.search(r"中文|国语|國語|普通话|普通話|粤语|粵語|广东话|廣東話|chinese|mandarin|cantonese", t))
    if is_zh:
        if code in ("zh-tw", "cht", "zh-hant") or re.search(r"繁|台|taiwan|traditional|\bcht\b", t):
            return "中文-台湾"
        if code in ("zh-hk", "yue") or re.search(r"港|hong ?kong|\bhk\b|粤|粵|cantonese", t):
            return "中文-香港"
        return "中文"
    if code in ("und", "mis", "zxx", ""):
        return ""
    return _MI_LANG_NAMES.get(code, code.upper())


def _mi_lang_en(lang, title=""):
    """精简版的音频(/视频)轨语言: 中文(含台湾/香港/粤语...)统一写 Chinese, 免得被误会成有中文字幕;
    字幕行和完整模式仍用 _mi_lang (中文 / 中文-台湾 / 中文-香港)"""
    n = _mi_lang(lang, title)
    return "Chinese" if n.startswith("中文") else n


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


def _mi_fps(s, orig=None):
    """帧率. 优先用 mediainfo 的「原始帧率」(orig); 没有就用 ffprobe 实测的 avg_frame_rate
    (隔行 1080i 的 r_frame_rate / VUI 常给出场率 59.94, 而真实帧率是 29.97), 最后才用 r_frame_rate"""
    def fmt(x):
        return f"{x:.3f}".rstrip("0").rstrip(".") + " fps"
    if orig:
        return fmt(float(orig))
    for key in ("avg_frame_rate", "r_frame_rate"):
        v = s.get(key) or ""
        try:
            a, b = v.split("/")
            a, b = float(a), float(b)
            if a > 0 and b > 0:
                return fmt(a / b)
        except Exception:
            continue
    return ""


def _mi_orig_fps(mj):
    """mediainfo JSON 里第一个视频轨的「原始帧率」: 字段名是 FrameRate_Original (界面里显示为 原始帧率 / Original frame rate)"""
    for t in (mj or {}).get("media", {}).get("track", []):
        if t.get("@type") == "Video":
            for key in ("FrameRate_Original", "FrameRate_Original_String", "OriginalFrameRate"):
                m = re.search(r"\d+(?:\.\d+)?", str(t.get(key) or ""))
                if m and float(m.group()) > 0:
                    return float(m.group())
            return None
    return None


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
        proc = run(cmd, timeout=60)
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


def _mi_full_video(s, head, container_dur, extra, enc, interlaced, video_fallback, orig_fps=None):
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
    fps = _mi_fps(s, orig_fps)
    if fps:
        r, a = _mi_f(s.get("r_frame_rate")), _mi_f(s.get("avg_frame_rate"))
        # r = 2a 是场率/帧率的差别 (隔行), 不算可变帧率
        mode = "Constant" if (r and a and (abs(r - a) < 0.01 or abs(r - 2 * a) < 0.02)) else "Variable"
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


def _mi_build_full(label, data, streams, extra, enc, first_video, video_fallback, orig_fps=None):
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
            sections.append(_mi_full_video(s, head, container_dur, extra, enc, inter, video_fallback, orig_fps))
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


_CC_RE = re.compile(r"EIA-?[67]0[8]|CEA-?[67]0[8]|DTVCC|SCTE.?128|Line.?21|ATSC.?A/53", re.I)


def mi_cc_tracks(mj):
    """mediainfo JSON 里的隐藏字幕轨 (EIA-608/708 等, 混流在视频里, ffmpeg 读不出来)"""
    out = []
    for t in (mj or {}).get("media", {}).get("track", []):
        if t.get("@type") == "Text" and _CC_RE.search(
                " ".join(str(t.get(k, "")) for k in ("Format", "MuxingMode", "MuxingMode_MoreInfo", "CodecID"))):
            out.append(t)
    return out


def cc_label(t):
    lang = t.get("Language")
    name = _mi_lang(lang, t.get("Title", "") or "") if lang else ""
    if name:
        return name
    fmt = str(t.get("Format") or "CC")
    m = re.search(r"-(\d+)\s*$", str(t.get("ID", "")))      # ID "256 (0x100)-4" -> 服务号 4
    return f"{fmt}#{m.group(1)}" if m else fmt


def _mi_cc_full(tracks):
    secs = []
    for i, t in enumerate(tracks, 1):
        L = [f"Text (隐藏字幕) #{i}"]
        for key, label in (("ID", "ID"), ("MenuID", "Menu ID"), ("Format", "Format"),
                           ("MuxingMode", "Muxing mode"), ("MuxingMode_MoreInfo", "Muxing mode, more info"),
                           ("Duration", "Duration"), ("Language", "Language")):
            if t.get(key):
                val = t[key]
                if key == "Duration":
                    try:
                        val = _mi_dur_h(float(val))
                    except Exception:
                        pass
                L.append(_mi_kv(label, val))
        secs.append("\n".join(L))
    return "\n\n".join(secs)


def get_media_info_src(label, ffprobe, pre, url, lang_mj=None, duration_override=None, file_path=None, cc_mj=None,
                       show_cc=True, pid_langs=None):
    """对 bluray:/subfile 源生成 (精简文本, 完整文本, ffprobe JSON). 识别不到视频/音频时抛 MediaInfoError"""
    cmd = [ffprobe, "-v", "error", "-probesize", "50M", "-analyzeduration", "50M"] + pre + \
          ["-print_format", "json", "-show_streams", "-show_chapters", "-show_format", url]
    try:
        proc = run(cmd, timeout=300)
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
    if pid_langs:       # 蓝光: 用 CLPI 里的语言补上 (m2ts 自己的 PMT 里常常没有语言, 会显示成 Unknown)
        for s in streams:
            if s.get("codec_type") in ("audio", "subtitle"):
                try:
                    lg = pid_langs.get(int(str(s.get("id", "")), 16))
                except ValueError:
                    continue
                if lg and (s.get("tags") or {}).get("language") in (None, "", "und"):
                    s.setdefault("tags", {})["language"] = lg
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
    orig_fps = _mi_orig_fps(cc_mj) or _mi_orig_fps(lang_mj)   # mediainfo 的原始帧率 (比 ffprobe 的 r_frame_rate 准)
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
            if (s.get("codec_name") or "").lower() == "prores":      # ProRes 显示 Codec ID: Apple ProRes Video (apch)
                ctag = (s.get("codec_tag_string") or "").strip()
                if not ctag or ctag.startswith("[0]"):               # mkv 等容器里没有 fourcc: 按档位推
                    ctag = {"proxy": "apco", "lt": "apcs", "standard": "apcn", "hq": "apch",
                            "4444": "ap4h", "4444xq": "ap4x"}.get(str(s.get("profile") or "").lower().replace(" ", ""), "")
                if ctag:
                    codec += f" ({ctag})"
            etag = _mi_enc_tag(s, enc) if is_first else ""
            if etag:
                codec += f" ({etag})"
            lines.append("VIDEO: " + _mi_join([
                codec, _mi_resolution(s, inter), _mi_fps(s, orig_fps if is_first else None), _mi_aspect(s),
                _mi_kbps(s, video_fallback, approx=True), _mi_profile(s), _mi_video_bitdepth(s)
            ] + _mi_hdr_list(s, extra if is_first else {})))
        elif ctype == "audio":
            kbps = _mi_kbps(s)
            lines.append("AUDIO: " + _mi_join([
                _mi_audio_codec(s), _mi_lang_en(lang, title), kbps,
                _mi_channels(s), _mi_samplerate(s), _mi_bitdepth(s)
            ]))
        elif ctype == "subtitle":
            subs.append(_mi_lang(lang, title) or "Unknown")
    if subs:
        lines.append("Subtitle: " + " / ".join(subs))
    cc_tracks = mi_cc_tracks(cc_mj) if show_cc else []     # 关掉隐藏字幕检测时, cc_mj 仍用来取原始帧率
    if cc_tracks:     # ffmpeg 看不到的隐藏字幕 (EIA-608/708): 用 mediainfo 的结果
        counts = {}                       # 按格式统计条数: 有3条EIA-708字幕, 有1条EIA-608字幕
        for t in cc_tracks:
            fm = str(t.get("Format") or "CC").strip()
            counts[fm] = counts.get(fm, 0) + 1
        lines.append("隐藏字幕: " + ", ".join(f"有{n}条{fm}字幕" for fm, n in counts.items()))
    n_chapters = len(data.get("chapters") or [])
    if n_chapters > 0:
        lines.append(f"章节： {n_chapters}")

    try:
        full_text = _mi_build_full(label, data, streams, extra, enc, first_video, video_fallback, orig_fps)
        if cc_tracks:
            full_text += "\n\n" + _mi_cc_full(cc_tracks)
    except Exception as e:
        full_text = "完整信息生成失败: " + str(e)
    return "\n".join(lines), full_text, data


SPOILER_OPEN = '[spoiler title="Mediainfo" open="no" style="default" icon="plus" anchor_in_url="no"]'
SPOILER_CLOSE = "[/spoiler]"


def format_all(brief, full):
    """完整版放进 spoiler 折叠块, 后面空一行再接简洁版"""
    return f"{SPOILER_OPEN}\n{full.rstrip()}\n{SPOILER_CLOSE}\n\n{brief.rstrip()}"


# ============================================================ 联系表
FONT_PATH = [""]       # 用户指定的字体文件 (设置里 / --font)
_FONT_WARNED = [False]
_CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af\uff00-\uffef]")

_FONT_CANDIDATES = [
    # Windows
    r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyh.ttf", r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\YuGothM.ttc", r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc",
    # Linux (Colab: apt-get install -y fonts-noto-cjk  或  fonts-wqy-zenhei)
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "/usr/share/fonts/wenquanyi/wqy-zenhei/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
    # macOS
    "/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc", "/Library/Fonts/Arial Unicode.ttf",
]


def _fc_cjk_fonts():
    """用 fontconfig 找系统里支持中文的字体 (Linux/macOS)"""
    try:
        r = subprocess.run(["fc-list", ":lang=zh", "-f", "%{file}\n"], capture_output=True, text=True, timeout=10)
        fs = [x.strip() for x in (r.stdout or "").splitlines() if x.strip()]
    except Exception:
        return []
    fs.sort(key=lambda x: (0 if re.search(r"CJK|Noto|WenQuanYi|wqy|Source ?Han|Heiti|PingFang", x, re.I) else 1, x))
    out = []
    for x in fs:
        if x.lower().endswith((".ttf", ".ttc", ".otf")) and x not in out:
            out.append(x)
    return out


def font_supports_cjk(font):
    """字体里有没有 "中/あ" 的真实字形 (没有的话会画成和未定义字符一样的方块)"""
    try:
        blank = bytes(font.getmask("\u0378"))   # 未分配的码位 -> 方块/空白 (.notdef)
        return bytes(font.getmask("中")) != blank and bytes(font.getmask("あ")) != blank
    except Exception:
        return False


def load_font(size):
    from PIL import ImageFont
    cands = ([FONT_PATH[0]] if FONT_PATH[0] else []) + _FONT_CANDIDATES
    for f in cands:
        if f and os.path.isfile(f):
            try:
                ft = ImageFont.truetype(f, size)
                if font_supports_cjk(ft):
                    return ft
            except Exception:
                continue
    for f in _fc_cjk_fonts():
        try:
            ft = ImageFont.truetype(f, size)
            if font_supports_cjk(ft):
                return ft
        except Exception:
            continue
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try:
            f2 = ImageFont.truetype(f, size)
            _font_warn()
            return f2
        except Exception:
            continue
    _font_warn()
    return ImageFont.load_default()


def _font_warn():
    if not _FONT_WARNED[0]:
        _FONT_WARNED[0] = True
        print("!! 没找到支持中文/日文的字体, 中文会显示成方块。解决办法任选其一:\n"
              "   - Linux/Colab:  apt-get install -y fonts-noto-cjk   (装完重跑)\n"
              "   - 或用 --font /路径/某字体.ttf (GUI: 联系表内容 → 字体文件) 指定一个中文字体")


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


def _rgb(v, default):
    """颜色字符串 (名字 / #RRGGBB) -> (r,g,b); 空或写错用 default"""
    try:
        from PIL import ImageColor
        v = str(v or "").strip()
        return ImageColor.getrgb(v)[:3] if v else default
    except Exception:
        return default


WM_POS = {"tl": (0, 0), "tc": (.5, 0), "tr": (1, 0), "cl": (0, .5), "cc": (.5, .5), "cr": (1, .5),
          "bl": (0, 1), "bc": (.5, 1), "br": (1, 1)}


def wm_xy(pos, px, py, W, H, w, h):
    """水印左上角坐标: 九宫格预设 / 自定义百分比 (0=贴左(上)边, 100=贴右(下)边), 边距按联系表宽度的比例"""
    m = max(6, int(W * 0.015))
    if pos == "custom":
        fx, fy = float(px) / 100.0, float(py) / 100.0
    else:
        fx, fy = WM_POS.get(pos, (1, 0))
    fx, fy = min(max(fx, 0.0), 1.0), min(max(fy, 0.0), 1.0)
    return int(m + max(W - w - 2 * m, 0) * fx), int(m + max(H - h - 2 * m, 0) * fy)


def _apply_overlays(sheet, st):
    """整张联系表上的图片水印和文字水印 (大小和位置都按联系表宽高的比例)"""
    from PIL import Image, ImageDraw
    W, H = sheet.size
    wmp = str(st.get("wm_path") or "").strip()
    if st.get("wm_enable") and wmp:
        try:
            im0 = Image.open(wmp).convert("RGBA")
            tw = max(8, int(W * float(st.get("wm_scale") or 0.15)))
            th = max(1, int(im0.height * tw / im0.width))
            if th > H * 0.5:
                th = int(H * 0.5)
                tw = max(1, int(im0.width * th / im0.height))
            im = im0.resize((tw, th), getattr(Image, "Resampling", Image).LANCZOS)
            op = max(0.0, min(100.0, float(st.get("wm_opacity", 100)))) / 100.0
            if op < 1.0:
                im.putalpha(im.getchannel("A").point(lambda v: int(v * op)))
            x, y = wm_xy(st.get("wm_pos", "tr"), st.get("wm_x", 100), st.get("wm_y", 0), W, H, tw, th)
            sheet.paste(im, (x, y), im)
        except Exception as e:
            print("图片水印加载失败:", e)
    text = str(st.get("tx_text") or "").replace("\\n", "\n").strip()
    if st.get("tx_enable") and text:
        try:
            size = max(10, int(W * float(st.get("tx_size") or 0.03)))
            font = load_font(size)
            col = _rgb(st.get("tx_color"), (255, 255, 255))
            al = int(255 * max(0.0, min(100.0, float(st.get("tx_opacity", 100)))) / 100.0)
            sw = max(1, size // 14) if st.get("tx_stroke", True) else 0
            layer = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
            dl = ImageDraw.Draw(layer)
            bb = dl.multiline_textbbox((0, 0), text, font=font, stroke_width=sw, align="center")
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            x, y = wm_xy(st.get("tx_pos", "br"), st.get("tx_x", 100), st.get("tx_y", 100), W, H, tw, th)
            dl.multiline_text((x - bb[0], y - bb[1]), text, font=font, fill=col + (al,), align="center",
                              stroke_width=sw, stroke_fill=(0, 0, 0, al))
            sheet = Image.alpha_composite(sheet.convert("RGBA"), layer).convert("RGB")
        except Exception as e:
            print("文字水印绘制失败:", e)
    return sheet


def make_sheet(files, outpath, cols, rows, lines, show_ts=True, quality=92, font_scale=1.0,
               comment="", comment_color="#8CC8FF", style=None, warn=""):
    """style: bg_color text_color name_color ts_color 以及 wm_* / tx_* 水印设置 (都可省略)"""
    from PIL import Image, ImageDraw
    st = style or {}
    bg = _rgb(st.get("bg_color"), (24, 24, 28))
    c_text = _rgb(st.get("text_color"), (235, 235, 235))
    c_name = _rgb(st.get("name_color"), (255, 220, 120))
    c_ts = _rgb(st.get("ts_color"), (255, 255, 255))
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
    wwrapped = wrap(d0, "[!] " + str(warn), font, sheet_w - margin * 2) if warn else []   # 视频可能损坏的警告 (红色)
    nlines = len(wrapped) + len(wwrapped) + len(cwrapped)
    head_h = (margin * 2 + line_h * nlines) if nlines else margin
    sheet_h = head_h + rows * h + (rows - 1) * gap + margin

    sheet = Image.new("RGB", (sheet_w, sheet_h), bg)
    d = ImageDraw.Draw(sheet)
    y = margin
    for i, ln in enumerate(wrapped):
        d.text((margin, y), ln, font=font, fill=c_name if i == 0 else c_text)
        y += line_h
    for ln in wwrapped:
        d.text((margin, y), ln, font=font, fill=(255, 110, 110))
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
            d.text((x + 8, yy + h - int(fs * 1.9)), fmt_t(t), font=tfont, fill=c_ts,
                   stroke_width=2, stroke_fill=(0, 0, 0))
    sheet = _apply_overlays(sheet, st)
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


def _ensure_orig_fps(mediainfo, path, mj):
    """JSON 里没带「原始帧率」时, 用 --Inform 单独问一次 mediainfo, 补进第一个视频轨 (保险)"""
    if not mj or _mi_orig_fps(mj):
        return mj
    try:
        out = run([mediainfo, "--Inform=Video;%FrameRate_Original%\\n", str(path)]).stdout or ""
        m = re.search(r"\d+(?:\.\d+)?", out)
        if m and float(m.group()) > 0:
            for t in mj.get("media", {}).get("track", []):
                if t.get("@type") == "Video":
                    t["FrameRate_Original"] = m.group()
                    break
    except Exception:
        pass
    return mj


def detect_cc_json(kindp, path, c, mediainfo, sevenz, tmpdir):
    """隐藏字幕检测: 对源跑一次 mediainfo 拿 JSON (文件=整个文件, 蓝光文件夹=最大的 m2ts, 蓝光 ISO=7z 读开头一段)"""
    if not mediainfo:
        return None
    try:
        if kindp == "file":
            return _ensure_orig_fps(mediainfo, path, json.loads(
                run([mediainfo, "--Full", "--Output=JSON", str(path)]).stdout))
        if kindp == "bdfolder":
            mj = do_mediainfo_bd_folder(mediainfo, path, "simple")[1]
            st = _child(_child(path, "BDMV"), "STREAM")
            m2 = max((x for x in st.iterdir() if x.suffix.lower() == ".m2ts"), key=lambda x: x.stat().st_size)
            return _ensure_orig_fps(mediainfo, m2, mj)
        if kindp == "iso" and sevenz and c.get("detect_cc"):    # 读 ISO 开头要用 7z, 比较慢, 只在开了隐藏字幕检测时做
            return do_mediainfo_bd(sevenz, mediainfo, path, int(c["head_mb"]), "simple", tmpdir)[1]
    except Exception as e:
        print("隐藏字幕检测失败:", e)
    return None


MI_MODES = ("simple", "full", "all", "mi_normal", "mi_full")


def list_bd_titles(ffprobe, iso):
    """蓝光: 让 ffmpeg 的 bluray 协议列出可用播放列表 (它自己会去重/过滤), 返回 [(mpls编号, 秒)] 按时长降序"""
    try:
        r = run([ffprobe, "-hide_banner", "-v", "info", "-i", bd_src(iso)], timeout=300)
    except Exception:
        return []
    log = (r.stderr or "") + (r.stdout or "")
    seen, out = set(), []
    for m in re.finditer(r"playlist\s+(\d+)\.mpls\s+\((\d+):(\d{2}):(\d{2})\)", log):
        pl = int(m.group(1))
        if pl not in seen:
            seen.add(pl)
            out.append((pl, int(m.group(2)) * 3600 + int(m.group(3)) * 60 + int(m.group(4))))
    out.sort(key=lambda x: (-x[1], x[0]))
    return out


def bd_has_audio(ffprobe, iso, pl):
    """蓝光某个播放列表有没有音轨: True / False / None (读不出来, 不确定)"""
    try:
        r = run([ffprobe, "-v", "error", "-playlist", str(pl), "-show_entries", "stream=codec_type",
                 "-of", "csv=p=0", bd_src(iso)], timeout=120)
    except subprocess.TimeoutExpired:
        return None
    kinds = set((r.stdout or "").split())
    if "video" not in kinds and "audio" not in kinds:
        return None
    return "audio" in kinds


def list_dvd_titles(dvd, mediainfo, iso, tmpdir):
    """DVD: 每个标题集(VTS) 一个标题, 返回 [(vts号, 时长秒或None, 总字节)] 按时长(没有就按大小)降序"""
    out, noaudio = [], []
    for n, vt in dvd.items():
        size = sum(v[2] for v in vt["vobs"])
        dur, has_audio = None, None
        if mediainfo and vt["ifo"]:
            try:
                _, mj, dur = do_mediainfo_dvd(mediainfo, iso, n, vt, "simple", tmpdir)
                if mj:
                    has_audio = any(t.get("@type") == "Audio" for t in mj.get("media", {}).get("track", []))
            except Exception:
                dur = None
        if has_audio is False:          # 没有音轨的标题集多半是菜单 / 片头, 取最长标题时跳过
            noaudio.append(n)
            continue
        out.append((n, dur, size))
    if noaudio:
        print("跳过没有音频的标题集 (可能是菜单): " + ", ".join(f"VTS_{x:02d}" for x in noaudio))
    if not out and noaudio:             # 全都没音频 (极少见): 别什么都不剩, 退回不过滤
        out = [(n, None, sum(v[2] for v in dvd[n]["vobs"])) for n in noaudio]
    if out and all(x[1] for x in out):
        out.sort(key=lambda x: (-x[1], -x[2]))
    else:
        out.sort(key=lambda x: -x[2])
    return out


def process_iso(iso, cfg):
    """处理一个文件. DVD/蓝光 ISO 且 top_n>1 时, 依次处理时长最长的前 N 个标题 (输出名加 [1][2]...)"""
    c = {**DEFAULTS, **cfg}
    iso = Path(iso)
    try:
        top = max(1, int(c.get("top_n") or 1))
    except Exception:
        top = 1
    kindp = media_kind(iso)
    if kindp not in ("iso", "bdfolder", "dvdfolder"):
        return _process_iso_one(iso, c)
    if kindp != "iso":
        iso = disc_root(iso)[1]
    dvd = scan_dvd_any(iso)
    if top <= 1 and not dvd:      # 蓝光 N=1: 直接用 ffmpeg/libbluray 默认选的主标题(最长的)
        return _process_iso_one(iso, c)

    ffmpeg = find_tool("ffmpeg", c["ffmpeg"] or None)
    ffprobe = find_tool("ffprobe", c["ffprobe"] or None)
    mediainfo = find_tool("mediainfo", c["mediainfo"] or None, [r"C:\Program Files\MediaInfo\MediaInfo.exe"])
    tmpdir = out_dirs(iso, c)[1]
    tmpdir.mkdir(parents=True, exist_ok=True)
    titles = []
    if dvd:
        for n, dur, size in list_dvd_titles(dvd, mediainfo, iso, tmpdir)[:top]:
            titles.append({"_vts": n, "label": f"VTS_{n:02d}  " + (fmt_t(dur) if dur else f"{size / 1024 ** 3:.2f} GB")})
    elif ffmpeg and ffprobe and check_bluray_protocol(ffmpeg):
        cands = list_bd_titles(ffprobe, iso)
        skipped = []
        for pl, sec in cands[:40]:
            if len(titles) >= top:
                break
            if bd_has_audio(ffprobe, iso, pl) is False:      # 没有音轨的播放列表多半是菜单, 跳过
                skipped.append(f"{pl:05d}.mpls")
                continue
            titles.append({"_playlist": pl, "_dur": sec, "label": f"{pl:05d}.mpls  {fmt_t(sec)}"})
        if skipped:
            print("跳过没有音频的播放列表 (可能是菜单): " + ", ".join(skipped))
        if not titles:
            titles = [{"_playlist": pl, "_dur": sec, "label": f"{pl:05d}.mpls  {fmt_t(sec)}"} for pl, sec in cands[:top]]
    if not titles:
        print("没能列出该 ISO 的标题 (蓝光需要 ffmpeg 带 libbluray), 只处理主标题")
        return _process_iso_one(iso, c)

    total = len(titles)
    if total > 1 or top > 1:
        print(f"取时长最长的 {total} 个标题: " + " | ".join(t["label"] for t in titles))
    merged = {"report": None, "sheet": None, "sheets": [], "report_path": None, "report_paths": [], "skipped": True}
    reports, errors = [], 0
    for i, t in enumerate(titles, 1):
        check_cancel()
        if total > 1:
            print(f"\n--- 标题 [{i}/{total}] {t['label']} ---")
        cc = {**c, **{k: v for k, v in t.items() if k != "label"}}
        if total > 1:
            cc["_idx"] = i
        try:
            r = _process_iso_one(iso, cc)
        except Cancelled:
            raise
        except Exception as e:
            errors += 1
            print(f"标题 [{i}] 失败: {e}")
            continue
        merged["skipped"] = merged["skipped"] and r.get("skipped", False)
        if r.get("report"):
            reports.append(f"===== [{i}] {t['label']} =====\n{r['report']}" if total > 1 else r["report"])
        if r.get("sheet"):
            merged["sheets"].append(r["sheet"])
        if r.get("report_path"):
            merged["report_paths"].append(r["report_path"])
    if errors == total:
        raise RuntimeError("所有标题都处理失败")
    merged["report"] = "\n\n".join(reports) if reports else None
    merged["sheet"] = merged["sheets"][0] if merged["sheets"] else None
    merged["report_path"] = merged["report_paths"][0] if merged["report_paths"] else None
    return merged


def _process_iso_one(iso, cfg):
    """处理单个文件/单个标题. 返回 dict(report, sheet, report_path, skipped). 失败抛 RuntimeError"""
    c = {**DEFAULTS, **cfg}
    iso = Path(iso)
    kindp = media_kind(iso)
    if kindp is None:
        raise RuntimeError(f"找不到文件: {iso}")
    if kindp == "dir":
        raise RuntimeError("这是普通文件夹, 不是解压的 DVD/蓝光 (请展开成文件处理)")
    if kindp in ("bdfolder", "dvdfolder"):
        iso = disc_root(iso)[1]       # 拖的是 BDMV / VIDEO_TS 本身时, 取它的上一级
    outdir, tmpdir = out_dirs(iso, c)
    outdir.mkdir(parents=True, exist_ok=True)
    tmpdir.mkdir(parents=True, exist_ok=True)
    FONT_PATH[0] = str(c.get("font_path") or "").strip()
    is_iso = kindp in ("iso", "bdfolder", "dvdfolder")   # 光盘源: ISO 或解压出来的文件夹
    is_folder = kindp in ("bdfolder", "dvdfolder")
    src_word = "文件夹" if is_folder else "ISO"
    # ISO 去掉 .iso 扩展名; 普通视频保留扩展名 (xxx.mkv.jpg), 避免 a.mkv / a.mp4 重名; 文件夹用文件夹名
    base = iso.stem if kindp == "iso" else iso.name
    tag = f"[{c['_idx']}]" if c.get("_idx") else ""      # 多标题模式: 名字_sheet[1].jpg ...
    ssuf, msuf = str(c["sheet_suffix"]), str(c["mi_suffix"])   # 留空 = 无后缀
    spre, mpre = str(c["sheet_prefix"]), str(c["mi_prefix"])   # 前缀, 默认无
    sheet_path = outdir / f"{spre}{base}{ssuf}{tag}.{'png' if c['sheet_fmt'] == 'png' else 'jpg'}"
    mi_path = outdir / f"{mpre}{base}{msuf}{tag}.txt"
    preview = c.get("_preview_out")                       # GUI 预览: 输出到指定临时文件
    if preview:
        sheet_path = Path(preview)
    res = {"report": None, "sheet": None, "report_path": None, "skipped": False}

    exist = c["exist_mode"] if c["exist_mode"] in ("overwrite", "skip", "rename") else "overwrite"
    if preview:
        exist = "overwrite"
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
    if c.get("_playlist") is not None:
        playlist = int(c["_playlist"])
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

    dvd = scan_dvd_any(iso) if is_iso else None
    kind = "DVD-Video" if dvd else ("Blu-ray" if is_iso else iso.suffix[1:].upper() + " 视频文件")
    label = iso.name if is_iso else str(iso.resolve())
    probe, mj, raw, inner, extra = None, None, None, None, None
    if c.get("_playlist") is not None:
        inner = f"{int(c['_playlist']):05d}.mpls"
    brief = full = None
    pre, url, cleanup, rng, css_enc = [], None, None, None, False
    t_offset = 0.0
    header = ""

    def run_brief(lang_mj=None, dur=None, cc_mj=None, pid_langs=None):
        nonlocal brief, full, probe
        try:
            brief, full, probe = get_media_info_src(label, ffprobe, pre, url, lang_mj, dur,
                                                    None if is_iso else url, cc_mj, bool(c["detect_cc"]), pid_langs)
        except MediaInfoError as e:
            print("ffprobe 读取流信息失败:", e)

    try:
        if dvd:
            n, vt = (c["_vts"], dvd[c["_vts"]]) if c.get("_vts") in dvd else dvd_pick_main(dvd)
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
            header = (f"{src_word}{' ' * (15 - len(src_word))}: {iso.name}\n类型           : DVD-Video\n"
                      f"主标题集       : VTS_{n:02d} ({len(vt['vobs'])} 个 VOB, {total / 1024 ** 3:.2f} GiB)\n"
                      + (f"时长           : {fmt_t(duration)}\n" if duration else "") + "\n")
        elif not is_iso:
            # ---- 普通视频文件: 直接用文件路径
            if not ffmpeg:
                raise RuntimeError("找不到 ffmpeg")
            url = str(iso.resolve())
            m2_langs = None
            if iso.suffix.lower() == ".m2ts" and iso.parent.name.upper() == "STREAM":
                # 直接拿蓝光里的 m2ts 来截图: 旁边的 CLIPINF/xxxxx.clpi 里有音轨/字幕语言, 补上 (否则字幕语言全是 Unknown)
                cl = _child(_child(iso.parent.parent, "CLIPINF"), iso.stem + ".clpi")
                if cl:
                    try:
                        m2_langs = parse_clpi_langs(cl.read_bytes()) or None
                    except OSError:
                        m2_langs = None
            if ffprobe and want_brief:
                run_brief(cc_mj=detect_cc_json("file", iso, c, mediainfo, sevenz, tmpdir), pid_langs=m2_langs)
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
                    kind_s = "bdfolder" if is_folder else "iso"
                    hint = c.get("_dur")                       # 多标题模式下, ffmpeg 自己列出的这个播放列表的时长
                    bd_mode = c["bd_mode"] if c.get("bd_mode") in ("auto", "direct", "libbluray") else "auto"
                    cc_json = detect_cc_json(kind_s, iso, c, mediainfo, sevenz, tmpdir) if want_brief else None
                    pid_langs = bd_pid_langs(is_folder, iso, playlist, sevenz) if want_brief else None
                    dsrc, bad = None, False
                    if bd_mode == "direct":
                        dsrc = bd_direct_source(is_folder, iso, playlist, sevenz, tmpdir, ffprobe)
                        if dsrc is None:
                            print("直接读 m2ts 没成功, 退回 libbluray")
                    if dsrc is None:
                        if want_brief:
                            run_brief(cc_mj=cc_json, pid_langs=pid_langs)
                        else:
                            probe = get_probe(ffprobe, pre, url)
                        if duration is None and probe:
                            try:
                                duration = float(probe["format"]["duration"])
                            except Exception:
                                pass
                        bad = (duration is None or duration < 5 or bool(hint and duration < 0.6 * hint))
                        if bad and bd_mode == "auto":
                            print(f"libbluray 读到的时长不正常 ({fmt_t(duration or 0)}), 改为直接读 m2ts "
                                  "(UHD 蓝光上 libbluray 常读不到时长、也没法按时间跳转)")
                            dsrc = bd_direct_source(is_folder, iso, playlist, sevenz, tmpdir, ffprobe)
                            if dsrc is None:
                                print("直接读 m2ts 也没成功" + ("; 改用播放列表里的时长" if hint else ""))
                    if dsrc:
                        pre, url, cleanup = dsrc["pre"], dsrc["url"], dsrc["cleanup"]
                        probe = brief = full = None
                        duration = float(c["duration"]) if str(c["duration"]).strip() else None
                        run_brief(cc_mj=cc_json, pid_langs=pid_langs)
                        if duration is None and probe:
                            try:
                                duration = float(probe["format"]["duration"])
                            except Exception:
                                pass
                        if (duration is None or duration < 5) and dsrc.get("duration"):
                            duration = dsrc["duration"]           # 用 MPLS 里的入点/出点算出来的
                        elif dsrc.get("range") and duration:      # 播放列表只用了这个 m2ts 的一部分: 截图只在这一段里取
                            r_in, r_out = dsrc["range"]
                            if r_out - r_in < duration - 5:
                                try:
                                    st0 = float((probe or {}).get("format", {}).get("start_time") or 0)
                                except (TypeError, ValueError):
                                    st0 = 0.0
                                t_offset = max(r_in - st0, 0.0)
                                duration = r_out - r_in
                                print(f"播放列表只用了该 m2ts 的一部分 ({fmt_t(duration)}), 截图限定在这一段里")
                        print("(已直接读取 m2ts)")
                    elif bad and hint:
                        duration = float(hint)
                    print(f"时长: {fmt_t(duration)}" if duration else "ffprobe 读取时长失败")
            # 只有 MediaInfo 原生模式, 或 ffprobe 读不了时, 才走 mediainfo (ISO 用 7z 读主 m2ts 开头一段, 文件夹直接读整个 m2ts)
            need_old = want_raw or (brief is None and want_brief)
            if need_old and is_folder and mediainfo:
                raw, mj, inner, msize = do_mediainfo_bd_folder(mediainfo, iso, raw_mode)
                header = (f"{src_word}{' ' * (15 - len(src_word))}: {iso.name}\n类型           : Blu-ray\n"
                          f"主视频流       : {inner}\n"
                          f"该文件实际大小 : {msize} bytes ({msize / 1024 ** 3:.2f} GiB)\n"
                          + (f"播放列表时长   : {fmt_t(duration)} (ffprobe/libbluray)\n" if duration else "") + "\n")
            elif need_old and sevenz and mediainfo and not is_folder:
                raw, mj, inner, msize = do_mediainfo_bd(sevenz, mediainfo, iso, int(c["head_mb"]),
                                                        raw_mode, tmpdir)
                header = (f"{src_word}{' ' * (15 - len(src_word))}: {iso.name}\n类型           : Blu-ray\n"
                          f"主视频流       : {inner}\n"
                          f"该文件实际大小 : {msize} bytes ({msize / 1024 ** 3:.2f} GiB)\n"
                          + (f"播放列表时长   : {fmt_t(duration)} (ffprobe/libbluray)\n" if duration else "")
                          + "注意: 下面的 MediaInfo 只分析了文件开头一段, 其中的 Duration / Overall bitrate "
                            "/ File size 不代表整盘, 以上方信息为准。\n\n")
            elif need_old:
                print("缺少 7z 或 mediainfo, 蓝光的 MediaInfo 原生读取已跳过")
        check_cancel()

        info = collect_info(iso, kind, duration, inner, mj, probe, extra, css_enc, brief,
                            {"iso": "ISO 大小", "bdfolder": "文件夹大小", "dvdfolder": "文件夹大小"}.get(kindp, "文件大小"))

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
            tm_mode = c["tonemap_mode"] if c["tonemap_mode"] in ("off", "on", "auto") else "auto"
            kind_hdr = hdr_kind(probe)
            tonemap = None
            if tm_mode == "on" or (tm_mode == "auto" and kind_hdr):
                tonemap = "tags" if kind_hdr else "pq"
                if tm_mode == "auto":
                    print(f"检测到 HDR ({'HLG' if kind_hdr == 'hlg' else 'HDR10/PQ'}) → 自动映射为 SDR 截图")
                if not (has_filter(ffmpeg, "zscale") and has_filter(ffmpeg, "tonemap")):
                    print("!! 当前 ffmpeg 缺少 zscale/tonemap 滤镜, 无法做 HDR→SDR, 截图可能发灰 "
                          "(换 gyan.dev full 构建; Linux 用发行版自带的 ffmpeg 一般有)")
                    tonemap = None
            shot_stats = {}
            kw = dict(tonemap=tonemap, dvd=bool(dvd), dvd_range=rng, enhance=bool(c["enhance_shots"]), stats=shot_stats,
                      shot_timeout=float(c["shot_timeout"] or 30), deinterlace=bool(c["deinterlace"]),
                      t_offset=t_offset,
                      seek_mode=c["seek_mode"], debug=c["debug"],
                      preroll=float(c["preroll"]))
            if c["keep_thumbs"]:
                files = make_thumbs(*args, outdir=outdir / f"{base}_thumbs", **kw)
                ok = make_sheet(files, sheet_path, cols, rows, lines, c["show_timestamp"],
                                c["jpeg_quality"], c["font_scale"], c["comment"], c["comment_color"], c,
                                warn=shot_stats.get("warn", ""))
            else:
                with tempfile.TemporaryDirectory(dir=tmpdir) as td:
                    files = make_thumbs(*args, outdir=Path(td), **kw)
                    ok = make_sheet(files, sheet_path, cols, rows, lines, c["show_timestamp"],
                                    c["jpeg_quality"], c["font_scale"], c["comment"], c["comment_color"], c,
                                warn=shot_stats.get("warn", ""))
            if ok:
                res["sheet"] = str(sheet_path)
            if shot_stats.get("warn"):
                res["warn"] = shot_stats["warn"]
        return res
    finally:
        if cleanup:
            shutil.rmtree(cleanup, ignore_errors=True)


# ============================================================ 命令行
def build_cli_command(cfg, files, script=None):
    """把当前设置翻译成等价的命令行 (只写和默认值不同的项). files 为空时用 xxx.mkv 占位"""
    c, d = {**DEFAULTS, **cfg}, DEFAULTS
    a = []

    def val(key, flag, fmt=str):
        if str(c.get(key, "")) != str(d[key]) and str(c.get(key, "")).strip() != "":
            a.extend([flag, fmt(c[key])])

    if c["out_mode"] == "dir" and str(c["out_dir"]).strip():
        a.extend(["-d", str(c["out_dir"])])
    if (c["grid_cols"], c["grid_rows"]) != (d["grid_cols"], d["grid_rows"]):
        a.extend(["--grid", f"{c['grid_cols']}x{c['grid_rows']}"])
    val("thumb_width", "-w")
    if c["seek_mode"] == "bytes":
        a.append("--seek-bytes")
    elif c["seek_mode"] == "time":
        a.append("--seek-time")
    val("tonemap_mode", "--tonemap")
    val("preroll", "--preroll")
    val("sheet_fmt", "--fmt")
    val("jpeg_quality", "--quality")
    val("font_scale", "--font-scale")
    hide = [k for k in ("filename", "fileinfo", "video", "audio", "subs", "timestamp")
            if not c["show_" + k] and d["show_" + k]]
    show = [k for k in ("filename", "fileinfo", "video", "audio", "subs", "timestamp")
            if c["show_" + k] and not d["show_" + k]]
    if hide:
        a.extend(["--hide", ",".join(hide)])
    if show:
        a.extend(["--show", ",".join(show)])
    if str(c["comment"]).strip():
        a.extend(["--comment", str(c["comment"])])
        val("comment_color", "--comment-color")
    val("font_path", "--font")
    if not c["make_sheet"]:
        a.append("--no-thumbs")
    if not c["do_mediainfo"]:
        a.append("--no-mediainfo")
    else:
        val("mediainfo_mode", "--mi-mode")
        if not c["save_mediainfo"]:
            a.append("--no-save-mediainfo")
    val("head_mb", "--head-mb")
    val("top_n", "--top")
    for key, flag in (("bg_color", "--bg-color"), ("text_color", "--text-color"),
                      ("name_color", "--name-color"), ("ts_color", "--ts-color")):
        val(key, flag)
    def pos_args(flag, kp, kx, ky):
        if c[kp] == "custom":
            a.extend([flag, f"{float(c[kx]):g},{float(c[ky]):g}"])
        elif c[kp] != d[kp]:
            a.extend([flag, str(c[kp])])
    if c["wm_enable"] and str(c["wm_path"]).strip():
        a.extend(["--watermark", str(c["wm_path"])])
        val("wm_scale", "--wm-scale")
        val("wm_opacity", "--wm-opacity")
        pos_args("--wm-pos", "wm_pos", "wm_x", "wm_y")
    if c["tx_enable"] and str(c["tx_text"]).strip():
        a.extend(["--tx-text", str(c["tx_text"])])
        val("tx_color", "--tx-color")
        val("tx_size", "--tx-size")
        val("tx_opacity", "--tx-opacity")
        pos_args("--tx-pos", "tx_pos", "tx_x", "tx_y")
        if not c["tx_stroke"]:
            a.append("--tx-no-stroke")
    if not c["detect_cc"]:
        a.append("--no-cc")
    if not c["enhance_shots"]:
        a.append("--no-enhance")
    if not c["deinterlace"]:
        a.append("--no-deinterlace")
    val("shot_timeout", "--shot-timeout")
    val("bd_mode", "--bd-mode")
    # 后缀: 命令行不写 = 默认后缀; 写 "" = 无后缀 (所以和默认不同时, 即使是空串也要写出来)
    try:
        for sign, pat in parse_rules_text(c.get("filter_rules", "")):
            a.extend(["--filter", f"{sign} {pat}"])
    except ValueError:
        pass
    for key, flag in (("min_size", "--min-size"), ("max_size", "--max-size"),
                      ("min_age", "--min-age"), ("max_age", "--max-age")):
        val(key, flag)
    if not c.get("filter_ignore_case", True):
        a.append("--case-sensitive")
    val("sheet_prefix", "--sheet-prefix")
    val("mi_prefix", "--mi-prefix")
    if c["sheet_suffix"] != d["sheet_suffix"]:
        a.extend(["--sheet-suffix", str(c["sheet_suffix"])])
    if c["mi_suffix"] != d["mi_suffix"]:
        a.extend(["--mi-suffix", str(c["mi_suffix"])])
    val("exist_mode", "--exists")
    if c["keep_thumbs"]:
        a.append("--keep-thumbs")
    if c["recursive"]:
        a.append("-r")
    val("extra_exts", "--ext")
    val("playlist", "--playlist")
    val("duration", "--duration")
    val("tmp_dir", "--tmpdir")
    val("ffmpeg", "--ffmpeg")
    val("ffprobe", "--ffprobe")
    val("sevenz", "--7z")
    val("mediainfo", "--mediainfo")
    if c["debug"]:
        a.append("--debug")

    script = script or str(Path(__file__).resolve())
    parts = ["python", script] + [str(f) for f in (files or ["xxx.mkv"])] + a
    if os.name == "nt":
        return subprocess.list2cmdline(parts)
    import shlex
    return " ".join(shlex.quote(x) for x in parts)


# ============================================================ 过滤规则 (rclone 风格)
def _glob_to_re(pat):
    """rclone 的通配符 -> 正则: * 不跨 /, ** 可跨 /, ? 单个字符, [a-z] [!a-z], {a,b}, \\ 转义"""
    i, n, out = 0, len(pat), []
    while i < n:
        ch = pat[i]
        if ch == "*":
            if pat[i:i + 3] == "**/":
                out.append("(?:.*/)?")
                i += 3
            elif pat[i:i + 2] == "**":
                out.append(".*")
                i += 2
            else:
                out.append("[^/]*")
                i += 1
        elif ch == "?":
            out.append("[^/]")
            i += 1
        elif ch == "[":
            j = pat.find("]", i + 2 if pat[i + 1:i + 2] in ("!", "^") else i + 1)
            if j == -1:
                out.append(re.escape(ch))
                i += 1
            else:
                body = pat[i + 1:j]
                neg = body[:1] in ("!", "^")
                body = (body[1:] if neg else body).replace("\\", "\\\\")
                out.append("[" + ("^" if neg else "") + body + "]")
                i = j + 1
        elif ch == "{":
            j = pat.find("}", i + 1)
            if j == -1:
                out.append(re.escape(ch))
                i += 1
            else:
                out.append("(?:" + "|".join(_glob_to_re(a) for a in pat[i + 1:j].split(",")) + ")")
                i = j + 1
        elif ch == "\\" and i + 1 < n:
            out.append(re.escape(pat[i + 1]))
            i += 2
        else:
            out.append(re.escape(ch))
            i += 1
    return "".join(out)


class _Rule:
    def __init__(self, sign, pat, flags=0):
        self.sign, self.pat = sign, pat
        p = pat.strip()
        self.anchored = p.startswith("/")          # 以 / 开头: 相对根目录; 否则在任意层级匹配 (路径末尾)
        if self.anchored:
            p = p[1:]
        self.dir_only = p.endswith("/")            # 以 / 结尾: 只匹配目录 (及其下所有内容)
        p = p.rstrip("/")
        core = _glob_to_re(p)
        prefix = "^" if self.anchored else "^(?:.*/)?"
        self.re = re.compile(prefix + core + "$", flags)
        self.re_under = re.compile(prefix + core + "/.+$", flags)

    def matches(self, full, rel, is_dir):
        t = rel if self.anchored else full
        if self.dir_only:
            return bool(self.re_under.search(t)) or (is_dir and bool(self.re.search(t)))
        # 普通模式: 路径本身, 或它的任何一级上层目录 (目录被排除/包含 = 其下所有内容)
        parts = t.split("/")
        for k in range(1, len(parts) + 1):
            if self.re.search("/".join(parts[:k])):
                return True
        return False


def parse_rule_line(line):
    """一行 rclone --filter 语法 -> ("+"|"-", 模式) / ("!", None) 清空 / None 忽略 (空行和注释)"""
    ln = line.strip()
    if not ln or ln.startswith(("#", ";")):
        return None
    if ln == "!":
        return ("!", None)
    if len(ln) > 2 and ln[0] in "+-" and ln[1] in " \t":
        return (ln[0], ln[2:].strip())
    raise ValueError(f"无法识别的过滤规则: {line!r}  (每行应为 '+ 模式' 或 '- 模式', 和 rclone --filter 一样)")


def parse_rules_text(text):
    out = []
    for line in str(text or "").splitlines():
        r = parse_rule_line(line)
        if r is None:
            continue
        if r[0] == "!":
            out.clear()
        else:
            out.append(r)
    return out


def parse_size(v):
    """1.5G / 700M / 100k / 123456 -> 字节 (二进制进位, 和 rclone 一样); 空 -> None"""
    v = str(v or "").strip()
    if not v:
        return None
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([kKmMgGtT]?)(?:i?[bB])?$", v)
    if not m:
        raise ValueError(f"无法识别的大小: {v!r}  (例: 500M, 1.5G, 100k)")
    return float(m.group(1)) * 1024 ** ("kmgt".index(m.group(2).lower()) + 1 if m.group(2) else 0)


def parse_age(v):
    """1d / 2w / 1h30m / 3M(月) / 1y -> 秒; 空 -> None"""
    v = str(v or "").strip()
    if not v:
        return None
    unit = {"ms": 0.001, "s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "M": 2592000, "y": 31536000}
    toks = re.findall(r"(\d+(?:\.\d+)?)(ms|s|m|h|d|w|M|y)", v)
    if not toks or "".join(a + b for a, b in toks) != v:
        raise ValueError(f"无法识别的时间: {v!r}  (例: 7d, 2w, 1h30m, 3M=三个月, 1y)")
    return sum(float(a) * unit[b] for a, b in toks)


class Filter:
    """rclone 风格过滤: 规则按顺序, 第一条匹配的生效; 有 + 规则时, 没匹配到任何规则的默认排除 (等于末尾隐含 - **);
    之后再看大小/时间"""

    def __init__(self, rules=(), min_size=None, max_size=None, min_age=None, max_age=None, ignore_case=True):
        flags = re.IGNORECASE if ignore_case else 0
        self.rules = [_Rule(sg, pt, flags) for sg, pt in rules]
        self.has_include = any(r.sign == "+" for r in self.rules)
        self.min_size, self.max_size = min_size, max_size
        self.min_age, self.max_age = min_age, max_age

    def active(self):
        return bool(self.rules) or any(x is not None for x in (self.min_size, self.max_size, self.min_age, self.max_age))

    def test(self, path):
        """返回 (是否保留, 原因)"""
        path = Path(path)
        try:
            rp = path.resolve()
        except OSError:
            rp = path
        full = rp.as_posix()
        root = INPUT_ROOT.get(str(rp))
        try:
            rel = rp.relative_to(Path(root).resolve()).as_posix() if root else path.name
        except ValueError:
            rel = path.name
        is_dir = path.is_dir()
        for r in self.rules:
            if r.matches(full, rel, is_dir):
                if r.sign == "-":
                    return False, f"被排除规则匹配: - {r.pat}"
                break
        else:
            if self.has_include:
                return False, "没有匹配任何包含规则 (+)"
        if self.min_size is not None or self.max_size is not None:
            sz = path_size(path)
            if self.min_size is not None and sz < self.min_size:
                return False, f"小于 --min-size ({sz / 1024 ** 2:.1f} MiB)"
            if self.max_size is not None and sz > self.max_size:
                return False, f"大于 --max-size ({sz / 1024 ** 2:.1f} MiB)"
        if self.min_age is not None or self.max_age is not None:
            try:
                age = time.time() - os.path.getmtime(path)
            except OSError:
                age = 0
            if self.min_age is not None and age < self.min_age:
                return False, "比 --min-age 新"
            if self.max_age is not None and age > self.max_age:
                return False, "比 --max-age 旧"
        return True, ""


def make_filter(c, extra_rules=()):
    """从设置 (filter_rules 文本 + min/max 大小/时间 + 忽略大小写) 加上额外规则(命令行) 生成 Filter; 写错抛 ValueError"""
    rules = parse_rules_text(c.get("filter_rules", "")) + list(extra_rules)
    return Filter(rules, parse_size(c.get("min_size")), parse_size(c.get("max_size")),
                  parse_age(c.get("min_age")), parse_age(c.get("max_age")),
                  bool(c.get("filter_ignore_case", True)))


def resolve_disc_folders(entries, mode, recursive, exts, ask=input):
    """命令行: 遇到解压的 DVD/蓝光文件夹时询问: y 按整盘处理 / a 此后都按整盘 / n 当普通文件夹批量处理.
    mode: ask(默认, 询问) / yes / no. 普通文件夹和文件不问"""
    out = []
    for e in entries:
        k = media_kind(e)
        if k not in ("bdfolder", "dvdfolder"):
            out.append(e)
            continue
        ans = "y" if mode == "yes" else ("n" if mode == "no" else None)
        while ans is None:
            what = "蓝光 (BDMV)" if k == "bdfolder" else "DVD (VIDEO_TS)"
            try:
                r = ask(f"识别到 {what} 文件夹: {e}\n  按整盘处理? [y]es 是 / [a]ll 是且以后都是 / [n]o 当普通文件夹批量处理 (默认 y): ")
            except EOFError:
                r = "y"
            r = r.strip().lower()
            if r in ("", "y", "yes"):
                ans = "y"
            elif r in ("a", "all"):
                ans, mode = "y", "yes"
            elif r in ("n", "no"):
                ans = "n"
        if ans == "y":
            out.append(e)
        else:
            out.extend(collect_inputs([e], recursive, exts, strict=False, disc_folders=False))
    seen, uniq = set(), []
    for f in out:
        key = str(Path(f).resolve())
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq


class _RuleAction(argparse.Action):
    """--include/--exclude/--filter 以及 *-from 文件: 全部累积到同一个列表, 保持命令行里的先后顺序 (rclone 同款)"""

    def __call__(self, parser, ns, values, option_string=None):
        rules = list(getattr(ns, "rules", None) or [])

        def push(r):
            if r is None:
                return
            if r[0] == "!":
                rules.clear()
            else:
                rules.append(r)
        try:
            if option_string == "--include":
                push(("+", values))
            elif option_string == "--exclude":
                push(("-", values))
            elif option_string == "--filter":
                push(parse_rule_line(values))
            else:
                for line in Path(values).read_text(encoding="utf-8-sig").splitlines():
                    if option_string == "--filter-from":
                        push(parse_rule_line(line))
                    else:
                        ln = line.strip()
                        if ln and not ln.startswith(("#", ";")):
                            push(("+" if option_string == "--include-from" else "-", ln))
        except (ValueError, OSError) as e:
            parser.error(f"{option_string}: {e}")
        ns.rules = rules


def parse_pos(v):
    """--wm-pos / --tx-pos: tl tc tr cl cc cr bl bc br, 或 'x,y' (百分比) -> (pos, x, y)"""
    v = str(v).strip().lower()
    if v in WM_POS:
        return v, 100.0, 0.0
    m = re.match(r"^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$", v)
    if not m:
        raise ValueError(f"位置应为 tl tc tr / cl cc cr / bl bc br 之一, 或 'x,y' 百分比 (如 80,5): {v!r}")
    return "custom", float(m.group(1)), float(m.group(2))


def cli(argv):
    ap = argparse.ArgumentParser(description="DVD/蓝光 ISO: 联系表 + MediaInfo (不挂载). 不带参数则打开 GUI")
    ap.add_argument("iso", nargs="*", help="ISO / 视频文件 / 目录, 可多个")
    ap.add_argument("-r", "--recursive", action="store_true", help="目录递归子文件夹")
    ap.add_argument("--ext", help="追加要识别的视频扩展名, 如 .mkv,.rmvb")
    ap.add_argument("--preroll", type=float, help="预解码秒数 (默认 10, 防 HDTV 白色马赛克; 关键帧间隔很长时加大)")
    ap.add_argument("--gui", action="store_true", help="打开 GUI (可同时带 ISO 预加入列表)")
    ap.add_argument("--use-config", action="store_true", help=f"以 GUI 保存的设置 ({CONFIG_NAME}) 为基础")
    ap.add_argument("-d", "--dir", "-o", "--outdir", dest="outdir", metavar="DIR",
                    help="输出目录 (联系表和 MediaInfo txt 都放这里; 不存在会自动创建), 默认与源文件同目录")
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
    ap.add_argument("--show", default="", help="联系表显示项 (默认关闭的才需要), 同 --hide 的取值, 如 filename")
    ap.add_argument("--hide", default="", help="联系表隐藏项, 逗号分隔: filename,fileinfo,video,audio,subs,timestamp")
    ap.add_argument("--fmt", choices=["jpg", "png"])
    ap.add_argument("--quality", type=int)
    ap.add_argument("--font-scale", type=float)
    ap.add_argument("--tonemap", nargs="?", const="on", choices=["off", "on", "auto"],
                    help="HDR→SDR 色调映射: off 关 / on 强制 / auto 识别到 HDR 才映射 (默认 auto); 只写 --tonemap = on")
    ap.add_argument("--keep-thumbs", action="store_true", help="保留单张截图")
    ap.add_argument("--skip-existing", action="store_true", help="同名输出已存在则跳过 (= --exists skip)")
    ap.add_argument("--exists", choices=["overwrite", "skip", "rename"],
                    help="同名输出已存在时: overwrite 覆盖(默认) / skip 跳过 / rename 自动改名加 (1)")
    ap.add_argument("--comment", help="联系表信息区最后一行的注释 (可写广告/备注, \\n 换行)")
    ap.add_argument("--comment-color", help="注释颜色, 如 red / #FF8800")
    ap.add_argument("--check-font", action="store_true", help="检查会用哪个字体、是否支持中文/日文, 然后退出")
    ap.add_argument("--font", help="联系表用的字体文件 (.ttf/.ttc/.otf), 需支持中文; 默认自动查找系统字体")
    fg = ap.add_argument_group("过滤 (和 rclone 一样: 规则按命令行里的先后顺序, 第一条匹配的生效; "
                               "有 --include 时没匹配到任何规则的默认排除; * 不跨目录, ** 跨目录, ? {a,b} [a-z] 都支持; "
                               "以 / 开头=相对根目录, 以 / 结尾=只匹配目录, 不以 / 开头=在任意层级匹配)")
    for opt, hlp in (("--include", "只处理匹配的, 如 --include '*.iso'"),
                     ("--exclude", "排除匹配的, 如 --exclude '*sample*' / --exclude 'extras/'"),
                     ("--filter", "一条规则 '+ 模式' (包含) 或 '- 模式' (排除), '!' 清空之前的规则"),
                     ("--include-from", "从文件读取包含规则 (每行一个模式, # 开头为注释)"),
                     ("--exclude-from", "从文件读取排除规则"),
                     ("--filter-from", "从文件读取 '+ 模式' / '- 模式' 规则")):
        fg.add_argument(opt, action=_RuleAction, dest="rules", default=None, metavar="规则/文件", help=hlp)
    fg.add_argument("--min-size", help="只处理不小于这个大小的, 如 500M / 1.5G (ISO=文件大小, 光盘文件夹=整个文件夹)")
    fg.add_argument("--max-size", help="只处理不大于这个大小的")
    fg.add_argument("--min-age", help="只处理比这个更旧的 (修改时间), 如 1d / 2w / 1h30m / 3M(月) / 1y")
    fg.add_argument("--max-age", help="只处理比这个更新的 (修改时间)")
    fg.add_argument("--case-sensitive", action="store_true", help="规则区分大小写 (默认不区分, Windows 文件名本来就不分)")
    fg.add_argument("--dry-run", action="store_true", help="只列出哪些会处理 / 哪些被排除 (及原因), 不实际处理")
    ap.add_argument("--max", type=int, metavar="N", help="最多处理 N 个 (展开通配符/目录之后, 按顺序取前 N 个)")
    ap.add_argument("--disc-folder", choices=["ask", "yes", "no"], default="ask",
                    help="遇到解压出来的 DVD/蓝光文件夹: ask 询问 y/a/n (默认) / yes 都按整盘 / no 都当普通文件夹")
    ap.add_argument("--sheet-suffix", help='联系表文件名后缀, 默认 "_sheet"; 写 "" (空) = 不加后缀, 如 xxx.mkv.jpg')
    ap.add_argument("--mi-suffix", help='MediaInfo 文件名后缀, 默认 ".mediainfo"; 写 "" (空) = 不加后缀, 如 xxx.mkv.txt')
    ap.add_argument("--sheet-prefix", help="联系表文件名前缀, 默认无, 如 pic_ -> pic_xxx.mkv_sheet.jpg")
    ap.add_argument("--mi-prefix", help="MediaInfo 文件名前缀, 默认无, 如 media_ -> media_xxx.mkv.mediainfo.txt "
                                        "(配合 --mi-suffix \"\" 就是 media_xxx.mkv.txt)")
    ap.add_argument("--bg-color", help="联系表背景色, 如 #18181C / black")
    ap.add_argument("--text-color", help="信息文字颜色")
    ap.add_argument("--name-color", help="信息区第一行(文件名/类型行)的颜色")
    ap.add_argument("--ts-color", help="截图上时间戳的颜色")
    ap.add_argument("--watermark", help="图片水印 (透明 PNG), 放在整张联系表上, 默认右上角")
    ap.add_argument("--wm-scale", type=float, help="水印宽度占整张联系表宽度的比例, 默认 0.15 (随图片大小等比变化)")
    ap.add_argument("--wm-opacity", type=int, help="水印不透明度 0-100, 默认 100")
    ap.add_argument("--wm-pos", help="水印位置: tl tc tr / cl cc cr / bl bc br (默认 tr 右上), 或 'x,y' 百分比 "
                                     "(0=贴左/上边, 100=贴右/下边), 如 --wm-pos 80,5")
    ap.add_argument("--tx-text", help="文字水印的内容 (\\n 换行), 放在整张联系表上, 默认右下角")
    ap.add_argument("--tx-color", help="文字水印颜色, 默认 #FFFFFF")
    ap.add_argument("--tx-size", type=float, help="文字水印字号, 占联系表宽度的比例, 默认 0.03")
    ap.add_argument("--tx-opacity", type=int, help="文字水印不透明度 0-100, 默认 100")
    ap.add_argument("--tx-pos", help="文字水印位置, 同 --wm-pos, 默认 br 右下")
    ap.add_argument("--tx-no-stroke", action="store_true", help="文字水印不描黑边")
    ap.add_argument("--no-cc", action="store_true", help="不检测隐藏字幕 (EIA-608/708)")
    ap.add_argument("--bd-mode", choices=["auto", "direct", "libbluray"],
                    help="蓝光读取方式: auto (默认, libbluray 读不到正常时长时自动改直读 m2ts) / direct (总是直读 m2ts) / libbluray")
    ap.add_argument("--no-deinterlace", action="store_true", help="关闭反交错 (默认开: 隔行视频截图自动去拉丝)")
    ap.add_argument("--shot-timeout", type=float, metavar="秒",
                    help="单张截图最长等待秒数, 超时强行结束并清除中间文件 (默认 30); 连续 3 次超时判定视频无法解码, 放弃")
    ap.add_argument("--no-enhance", action="store_true",
                    help="关闭加强截图 (默认开: 1~2 张单调/失败的在附近关键帧重截, 超过 2 张判断为视频可能损坏并告警)")
    ap.add_argument("--top", type=int, metavar="N",
                    help="DVD/蓝光 ISO: 取时长最长的前 N 个标题各出一张联系表 (默认 1; N>1 时输出名加 [1][2]…)")
    ap.add_argument("--playlist", type=int, help="蓝光: 指定 mpls 编号, 如 800")
    ap.add_argument("--head-mb", type=int, help="蓝光: 喂给 MediaInfo 的数据量(MB)")
    ap.add_argument("--duration", type=float, help="取不到时长时手动指定(秒)")
    ap.add_argument("--tmpdir", help="临时文件目录, 默认 ISO 所在目录")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--ffmpeg"); ap.add_argument("--ffprobe")
    ap.add_argument("--7z", dest="sevenz"); ap.add_argument("--mediainfo")
    a = ap.parse_args(argv)

    if a.check_font:
        FONT_PATH[0] = (a.font or "").strip()
        _FONT_WARNED[0] = True  # 下面自己输出结果, 不重复提示
        f = load_font(20)
        path = getattr(f, "path", None)
        ok = font_supports_cjk(f) if path else False
        print("使用字体:", path or "(PIL 内置字体)")
        print("支持中文/日文:", "是, 联系表里的中文不会再是方块" if ok else
              "否, 中文会显示成方块\n  Linux/Colab:  apt-get install -y fonts-noto-cjk\n  或  --font /路径/某中文字体.ttf")
        found = _fc_cjk_fonts()
        print("系统中文字体 (fc-list :lang=zh):", ("\n  " + "\n  ".join(found[:8])) if found else "无")
        return 0 if ok else 1
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
    for src, key in (("min_size", "min_size"), ("max_size", "max_size"), ("min_age", "min_age"), ("max_age", "max_age"),
                     ("sheet_suffix", "sheet_suffix"), ("mi_suffix", "mi_suffix"), ("sheet_prefix", "sheet_prefix"),
                     ("mi_prefix", "mi_prefix"), ("bg_color", "bg_color"),
                     ("text_color", "text_color"), ("name_color", "name_color"), ("ts_color", "ts_color"),
                     ("watermark", "wm_path"), ("wm_scale", "wm_scale"), ("wm_opacity", "wm_opacity"),
                     ("tx_text", "tx_text"), ("tx_color", "tx_color"), ("tx_size", "tx_size"), ("tx_opacity", "tx_opacity"),
                     ("top", "top_n"), ("comment", "comment"), ("comment_color", "comment_color"), ("font", "font_path"), ("exists", "exist_mode"),
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
    for k in [x.strip() for x in a.show.split(",") if x.strip()]:
        if "show_" + k in cfg:
            cfg["show_" + k] = True
    for k in [x.strip() for x in a.hide.split(",") if x.strip()]:
        if "show_" + k in cfg:
            cfg["show_" + k] = False
    for flag, key in ((a.keep_thumbs, "keep_thumbs"),
                      (a.debug, "debug")):
        if flag:
            cfg[key] = True

    if a.tonemap:
        cfg["tonemap_mode"] = a.tonemap
    if a.skip_existing:
        cfg["exist_mode"] = "skip"
    if a.recursive:
        cfg["recursive"] = True
    exts = media_exts(cfg["extra_exts"])
    entries = collect_inputs(a.iso, cfg["recursive"], exts, strict=False)
    files = resolve_disc_folders(entries, a.disc_folder, cfg["recursive"], exts)
    if a.case_sensitive:
        cfg["filter_ignore_case"] = False
    if a.watermark:
        cfg["wm_enable"] = True
    if a.tx_text:
        cfg["tx_enable"] = True
    if a.tx_no_stroke:
        cfg["tx_stroke"] = False
    if a.no_cc:
        cfg["detect_cc"] = False
    if a.no_enhance:
        cfg["enhance_shots"] = False
    if a.no_deinterlace:
        cfg["deinterlace"] = False
    if a.bd_mode:
        cfg["bd_mode"] = a.bd_mode
    if a.shot_timeout:
        cfg["shot_timeout"] = a.shot_timeout
    try:
        for opt, (kp, kx, ky) in ((a.wm_pos, ("wm_pos", "wm_x", "wm_y")), (a.tx_pos, ("tx_pos", "tx_x", "tx_y"))):
            if opt:
                cfg[kp], cfg[kx], cfg[ky] = parse_pos(opt)
    except ValueError as e:
        print("位置参数有误:", e)
        return 2
    try:
        flt = make_filter(cfg, a.rules or [])
    except ValueError as e:
        print("过滤规则有误:", e)
        return 2
    excluded = []
    if flt.active():
        kept = []
        for f in files:
            ok, why = flt.test(f)
            (kept if ok else excluded).append(f if ok else (f, why))
        files = kept
        print(f"过滤: 保留 {len(files)} 个, 排除 {len(excluded)} 个")
    if a.max and a.max > 0 and len(files) > a.max:
        print(f"共 {len(files)} 个, 只处理前 {a.max} 个 (--max)")
        files = files[:a.max]
    if a.dry_run:
        for f in files:
            print("+", f)
        for f, why in excluded:
            print("-", f, f"({why})")
        print(f"[dry-run] 会处理 {len(files)} 个, 排除 {len(excluded)} 个, 未实际处理")
        return 0
    if not files:
        print("没有可处理的文件 (目录是否需要 -r? 扩展名可用 --ext 追加; 或者都被过滤规则排除了)")
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
    from tkinter import colorchooser, filedialog, messagebox, ttk

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
    root.minsize(900, 560)

    def safe_geometry(g):
        """上次的 窗口大小+位置: 位置落在现有屏幕 (含多显示器的虚拟桌面) 之外时只保留大小, 让系统自己摆; 无效值用默认"""
        m = re.match(r"^(\d+)x(\d+)(?:([+-]-?\d+)([+-]-?\d+))?$", str(g or "").strip())
        if not m:
            return "1180x760"
        w, h = int(m.group(1)), int(m.group(2))
        if w < 600 or h < 400:
            return "1180x760"
        if not m.group(3):
            return f"{w}x{h}"
        x, y = int(m.group(3)), int(m.group(4))
        vx, vy, vw, vh = root.winfo_vrootx(), root.winfo_vrooty(), root.winfo_vrootwidth(), root.winfo_vrootheight()
        if vw <= 1 or vh <= 1:
            vx, vy, vw, vh = 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()
        if x + w < vx + 120 or x > vx + vw - 120 or y < vy - 5 or y > vy + vh - 80:
            return f"{w}x{h}"            # 位置跑到屏幕外了 (比如拔掉了副屏)
        return f"{w}x{h}{x:+d}{y:+d}"
    root.geometry(safe_geometry(cfg.get("geometry")))
    last_normal = [cfg.get("geometry") or ""]   # 最近一次「正常(非最大化)」状态下的 大小+位置
    q = queue.Queue()
    V = {}
    state = {"running": False, "worker": None, "pending_ready": False, "photo": None, "preview": None}
    reports = {}
    disc_on = {}      # 解压出来的 DVD/蓝光文件夹: iid -> 是否按整盘处理 (☑/☐)
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
        try:
            out["win_state"] = "zoomed" if root.state() == "zoomed" else "normal"
        except Exception:
            out["win_state"] = cfg.get("win_state", "normal")
        out["geometry"] = last_normal[0] or cfg.get("geometry", "")
        try:
            out["sash"] = int(pw.sashpos(0))
        except Exception:
            out["sash"] = int(cfg.get("sash") or 0)
        out["last_dir"] = cfg.get("last_dir", "")
        out["pending"] = pending_snapshot()
        try:
            out["filter_rules"] = filter_text.get("1.0", "end").strip()
        except Exception:
            out["filter_rules"] = cfg.get("filter_rules", "")
        return out

    def pending_snapshot():
        """没处理完 / 失败 / 中断的条目, 写进 json, 下次打开可以载入"""
        res = []
        try:
            for iid in tree.get_children():
                st = tree.set(iid, "status")
                if st in ("完成", "已跳过", "已过滤", "完成(疑似损坏)"):
                    continue
                res.append({"path": iid, "disc": disc_on.get(iid), "status": st})
        except Exception:
            pass
        return res

    def persist():
        if state["pending_ready"]:
            save_config(collect())

    # ---------- 布局: 左 文件列表 / 右 设置页
    pw = ttk.PanedWindow(root, orient="horizontal")
    pw.pack(fill="both", expand=True, padx=6, pady=6)
    left = ttk.Frame(pw)
    right = ttk.Frame(pw)
    pw.add(left, weight=2)
    pw.add(right, weight=3)

    def restore_window():
        try:
            if int(cfg.get("sash") or 0) > 150:
                pw.sashpos(0, int(cfg["sash"]))
        except Exception:
            pass
        if cfg.get("win_state") == "zoomed":
            try:
                root.state("zoomed")
            except Exception:
                try:
                    root.attributes("-zoomed", True)
                except Exception:
                    pass
    root.after(200, restore_window)

    _sv = [None]

    def on_root_configure(e):
        if e.widget is not root:
            return
        try:
            if root.state() == "normal":
                g = root.geometry()
                m = re.match(r"^(\d+)x(\d+)", g)
                if m and int(m.group(1)) >= 600 and int(m.group(2)) >= 400:   # 还没显示出来时是 1x1, 不能存
                    last_normal[0] = g
        except Exception:
            return
        if _sv[0]:                                 # 拖动/缩放结束 1 秒后落盘, 崩溃/被结束进程也不会丢
            root.after_cancel(_sv[0])
        _sv[0] = root.after(1000, lambda: persist())
    root.bind("<Configure>", on_root_configure, add="+")

    hint = "把 ISO / 视频文件 / 文件夹拖到这里" if dnd_ok else "点 [添加文件] 选择文件   (pip install tkinterdnd2 后可拖拽)"
    ttk.Label(left, text=hint, foreground="#555").pack(anchor="w", pady=(0, 4))

    tb = ttk.Frame(left)
    tb.pack(fill="x")
    tbx = ttk.Frame(left)
    tbx.pack(fill="x", pady=(3, 0))
    tree_fr = ttk.Frame(left)
    tree_fr.pack(fill="both", expand=True, pady=4)
    tree = ttk.Treeview(tree_fr, columns=("name", "type", "disc", "status"), show="headings", selectmode="extended")
    for col, txt, wd in (("name", "文件", 190), ("type", "类型", 82), ("disc", "整盘", 40), ("status", "状态", 78)):
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

    def color_row(parent, text, key, row):
        """颜色: 输入框 (名字或 #RRGGBB) + 色块 + [选色…] (Windows 上是和画图一样的系统颜色对话框)"""
        v = var(key)
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=3, padx=(0, 6))
        fr = ttk.Frame(parent)
        fr.grid(row=row, column=1, columnspan=2, sticky="w")
        ttk.Entry(fr, textvariable=v, width=12).pack(side="left")
        sw = tk.Label(fr, width=4, relief="solid", bd=1)
        sw.pack(side="left", padx=6)

        def hexof():
            return "#%02x%02x%02x" % _rgb(v.get(), (200, 200, 200))

        def refresh(*_):
            try:
                sw.configure(bg=hexof())
            except Exception:
                pass

        def pick():
            r = colorchooser.askcolor(color=hexof(), parent=root, title=text)
            if r and r[1]:
                v.set(r[1].upper())
        ttk.Button(fr, text="选色…", width=7, command=pick).pack(side="left")
        v.trace_add("write", refresh)
        refresh()

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
    lf3 = ttk.LabelFrame(t1, text="HDR → SDR 色调映射 (HDR 截图发灰时)", padding=6)
    lf3.grid(row=7, column=0, columnspan=3, sticky="we", pady=4)
    for i, (val, txt) in enumerate((("auto", "自动: 识别到 HDR (HDR10/HLG) 才映射, SDR 片源不动"),
                                    ("on", "始终映射"), ("off", "关闭"))):
        ttk.Radiobutton(lf3, text=txt, value=val, variable=var("tonemap_mode")).grid(row=i, column=0, sticky="w")
    check(t1, "保留单张截图 (<文件名>_thumbs 文件夹)", "keep_thumbs", 8)
    spin(t1, "预解码秒数", "preroll", 0, 120, 9)
    check(t1, "开启反交错 (隔行视频截图去拉丝)", "deinterlace", 15)
    spin(t1, "单张截图超时(秒)", "shot_timeout", 5, 600, 16)
    ttk.Label(t1, foreground="#666", justify="left", text=(
        "超时会强行结束 ffmpeg 并清除中间文件 (冷门编码 / 损坏的视频会一直卡住); 连续 3 次超时就放弃这个视频。\n"
        "点「停止」也会立刻强行结束正在截图的 ffmpeg。")).grid(row=17, column=0, columnspan=3, sticky="w")
    check(t1, "加强截图 (默认开)", "enhance_shots", 13)
    ttk.Label(t1, foreground="#666", justify="left", text=(
        "有 1~2 张画面单调 (黑/白/绿屏等) 或截图失败时, 在附近的关键帧 (上下各最多 2 个) 重新截;\n"
        "附近也都单调就取最丰富的一张。超过 2 张单调/失败, 大概率是视频损坏, 不重截, "
        "联系表上会加一行红字提醒。")).grid(row=14, column=0, columnspan=3, sticky="w")
    spin(t1, "ISO 取最长的前 N 个标题", "top_n", 1, 50, 11)
    ttk.Label(t1, text="仅 DVD / 蓝光 ISO: DVD 按标题集(VTS)、蓝光按播放列表(mpls) 取时长最长的 N 个,\n"
                       "每个各出一张联系表 + MediaInfo; N>1 时输出名加 [1] [2]…。默认 1 = 只取主标题。",
              foreground="#666").grid(row=12, column=0, columnspan=3, sticky="w", pady=(2, 0))
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
                                  ("show_fileinfo", "显示文件信息行 (类型/大小/时长)"),
                                  ("show_video", "显示视频信息 (编码/分辨率/帧率/码率)"),
                                  ("show_audio", "显示音频信息"), ("show_subs", "显示字幕信息"),
                                  ("show_timestamp", "每张截图左下角显示时间"))):
        check(t2, txt, k, i)
    spin(t2, "文字缩放", "font_scale", 0.5, 3.0, 6, inc=0.1)
    entry(t2, "注释 (最后一行)", "comment", 7, width=40)
    color_row(t2, "注释颜色", "comment_color", 8)
    entry(t2, "字体文件", "font_path", 10, "file", width=40)
    ttk.Label(t2, text="字体留空 = 自动找系统中文字体 (Windows 微软雅黑等)。", foreground="#666").grid(
        row=11, column=0, columnspan=3, sticky="w")
    ttk.Label(t2, text="注释显示在信息区最后一行, 可写广告 / 备注; 想换行写 \\n; 留空则不显示。\n"
                       "颜色可写名字 (red) 或 #RRGGBB。", foreground="#666").grid(
        row=9, column=0, columnspan=3, sticky="w")

    # -- 过滤 (rclone 风格)
    t9 = tab("过滤")
    ttk.Label(t9, text="过滤规则: 每行一条, 和 rclone 的 --filter 一样。运行时, 列表里不满足的会被跳过 (状态显示「已过滤」)。",
              foreground="#444").pack(anchor="w")
    filter_text = tk.Text(t9, height=8, wrap="none", font=mono)
    filter_text.pack(fill="x", pady=4)
    filter_text.insert("1.0", str(cfg.get("filter_rules", "")))
    ttk.Label(t9, justify="left", foreground="#666", text=(
        "+ 模式   只要匹配的 (有 + 规则时, 没匹配到任何规则的默认排除)        - 模式   排除匹配的\n"
        "规则按从上到下的顺序, 第一条匹配的生效; # 开头是注释; 单独一行 ! 清空前面的规则。\n"
        "模式: * 不跨目录  ** 跨目录  ? 单个字符  [a-z] [!a-z]  {a,b} 二选一  \\ 转义\n"
        "      不以 / 开头 = 在任意层级匹配;  /开头 = 相对添加的那个文件夹;  以 / 结尾 = 只匹配目录 (及其下所有内容)\n"
        "例:   - *sample*           排除名字带 sample 的\n"
        "      - extras/            排除所有叫 extras 的文件夹里的东西\n"
        "      + *.{iso,mkv}        只要 iso 和 mkv        (这行单独写时, 其他类型自动被排除)")).pack(anchor="w")
    ffr = ttk.Frame(t9)
    ffr.pack(fill="x", pady=(8, 0))
    entry(ffr, "最小大小", "min_size", 0, width=10)
    entry(ffr, "最大大小", "max_size", 1, width=10)
    entry(ffr, "至少这么旧 (min-age)", "min_age", 2, width=10)
    entry(ffr, "至多这么旧 (max-age)", "max_age", 3, width=10)
    ttk.Label(ffr, text="大小: 500M / 1.5G / 100k    时间: 1d / 2w / 1h30m / 3M(月) / 1y (按修改时间); 留空 = 不限。",
              foreground="#666").grid(row=4, column=0, columnspan=3, sticky="w")
    ttk.Checkbutton(ffr, text="规则忽略大小写 (默认; Windows 文件名本来就不分大小写)",
                    variable=var("filter_ignore_case")).grid(row=5, column=0, columnspan=3, sticky="w", pady=4)
    ttk.Button(ffr, text="检查列表 (把会被跳过的标出来)", command=lambda: check_list()).grid(
        row=6, column=0, columnspan=2, sticky="w", pady=4)
    ffr.columnconfigure(1, weight=1)

    # -- 外观 (颜色 / 水印)
    t8 = tab("外观")
    color_row(t8, "背景色", "bg_color", 0)
    color_row(t8, "信息文字颜色", "text_color", 1)
    color_row(t8, "第一行颜色 (文件名/类型行)", "name_color", 2)
    color_row(t8, "时间戳颜色", "ts_color", 3)
    ttk.Label(t8, text="(注释文字颜色在「联系表内容」里设置)  颜色框可手输名字或 #RRGGBB, 也可点「选色…」。",
              foreground="#666").grid(row=4, column=0, columnspan=3, sticky="w", pady=(0, 6))

    def reset_colors():
        for k in ("bg_color", "text_color", "name_color", "ts_color", "comment_color"):
            V[k].set(DEFAULTS[k])
    ttk.Button(t8, text="颜色恢复默认", command=reset_colors).grid(row=5, column=0, sticky="w", pady=4)
    POS_LABELS = [("tr", "右上"), ("tl", "左上"), ("tc", "上中"), ("cr", "右中"), ("cc", "正中"),
                  ("cl", "左中"), ("br", "右下"), ("bl", "左下"), ("bc", "下中"), ("custom", "自定义")]

    def pos_row(parent, row, kp, kx, ky):
        """位置: 九宫格预设 + 自定义 (x% / y%: 0 = 贴左/上边, 100 = 贴右/下边, 按联系表宽高的比例, 不随图片大小变化)"""
        code = var(kp)
        names, inv = dict(POS_LABELS), {t: c for c, t in POS_LABELS}
        ttk.Label(parent, text="位置").grid(row=row, column=0, sticky="w", pady=2, padx=(0, 6))
        fr = ttk.Frame(parent)
        fr.grid(row=row, column=1, columnspan=2, sticky="w")
        lab = tk.StringVar(value=names.get(code.get(), "右上"))
        cb = ttk.Combobox(fr, textvariable=lab, values=[t for _, t in POS_LABELS], state="readonly", width=8)
        cb.pack(side="left")
        ttk.Label(fr, text="   x%").pack(side="left")
        sx = ttk.Spinbox(fr, from_=0, to=100, increment=1, textvariable=var(kx), width=5)
        sx.pack(side="left")
        ttk.Label(fr, text=" y%").pack(side="left")
        sy = ttk.Spinbox(fr, from_=0, to=100, increment=1, textvariable=var(ky), width=5)
        sy.pack(side="left")

        def upd(*_):
            lab.set(names.get(code.get(), "右上"))
            st = "normal" if code.get() == "custom" else "disabled"
            sx.configure(state=st)
            sy.configure(state=st)
        cb.bind("<<ComboboxSelected>>", lambda e: code.set(inv.get(lab.get(), "tr")))
        code.trace_add("write", upd)
        upd()

    lfw = ttk.LabelFrame(t8, labelwidget=ttk.Checkbutton(t8, text="水印 (透明 PNG 图片)", variable=var("wm_enable")),
                         padding=8)
    lfw.grid(row=6, column=0, columnspan=3, sticky="we", pady=(8, 4))
    entry(lfw, "图片", "wm_path", 0, "file", width=36)
    spin(lfw, "大小 (占联系表宽度)", "wm_scale", 0.03, 0.8, 1, inc=0.01)
    spin(lfw, "不透明度 0-100", "wm_opacity", 0, 100, 2, inc=5)
    pos_row(lfw, 3, "wm_pos", "wm_x", "wm_y")
    lfw.columnconfigure(1, weight=1)
    lft = ttk.LabelFrame(t8, labelwidget=ttk.Checkbutton(t8, text="文字 (自定义文字水印)", variable=var("tx_enable")),
                         padding=8)
    lft.grid(row=7, column=0, columnspan=3, sticky="we", pady=4)
    entry(lft, "文字", "tx_text", 0, width=36)
    color_row(lft, "颜色", "tx_color", 1)
    spin(lft, "字号 (占联系表宽度)", "tx_size", 0.01, 0.3, 2, inc=0.005)
    spin(lft, "不透明度 0-100", "tx_opacity", 0, 100, 3, inc=5)
    check(lft, "描边 (黑色, 更清晰)", "tx_stroke", 4, span=3)
    pos_row(lft, 5, "tx_pos", "tx_x", "tx_y")
    lft.columnconfigure(1, weight=1)
    ttk.Label(t8, foreground="#666", justify="left", text=(
        "水印放在整张联系表上, 大小和位置都按联系表的宽高比例算, 改单格宽度(-w)时不会错位。\n"
        "位置选「自定义」时用 x%/y%: 0 = 贴左/上边, 100 = 贴右/下边。文字换行写 \\n。\n"
        "勾选标题上的「水印」「文字」才会生效, 两个可以同时开。")).grid(row=8, column=0, columnspan=3, sticky="w")
    t8.columnconfigure(1, weight=1)

    # -- 预览
    t7 = tab("预览")
    pbar = ttk.Frame(t7)
    pbar.pack(fill="x")
    b_prev = ttk.Button(pbar, text="生成预览 (用当前所有设置, 对选中的/第一个文件)", command=lambda: preview())
    b_prev.pack(side="left")
    fit_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(pbar, text="适应窗口", variable=fit_var, command=lambda: render_preview()).pack(side="left", padx=10)
    pv_status = tk.StringVar(value="")
    ttk.Label(pbar, textvariable=pv_status, foreground="#666").pack(side="left")
    pv_fr = ttk.Frame(t7)
    pv_fr.pack(fill="both", expand=True, pady=(6, 0))
    canvas = tk.Canvas(pv_fr, bg="#2b2b2b", highlightthickness=0)
    pvy = ttk.Scrollbar(pv_fr, orient="vertical", command=canvas.yview)
    pvx = ttk.Scrollbar(pv_fr, orient="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=pvy.set, xscrollcommand=pvx.set)
    pvx.pack(side="bottom", fill="x")
    pvy.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    _pv_after = [None]

    def on_canvas_cfg(_e=None):
        if _pv_after[0]:
            root.after_cancel(_pv_after[0])
        _pv_after[0] = root.after(150, lambda: render_preview())
    canvas.bind("<Configure>", on_canvas_cfg)

    # -- MediaInfo
    t3 = tab("MediaInfo")
    top = ttk.Frame(t3)
    top.pack(fill="x")
    ttk.Checkbutton(top, text="读取 MediaInfo", variable=var("do_mediainfo")).grid(row=0, column=0, sticky="w")
    ttk.Checkbutton(top, text="同时生成 txt 文件", variable=var("save_mediainfo")).grid(row=0, column=1,
                                                                                  sticky="w", padx=10)
    ttk.Checkbutton(top, text="检测隐藏字幕 (EIA-608/708, ffmpeg 读不到, 需要 mediainfo)",
                    variable=var("detect_cc")).grid(row=1, column=0, columnspan=3, sticky="w")
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
    entry(t4, "联系表文件名前缀", "sheet_prefix", 6, width=20)
    entry(t4, "联系表文件名后缀", "sheet_suffix", 7, width=20)
    entry(t4, "MediaInfo 文件名前缀", "mi_prefix", 8, width=20)
    entry(t4, "MediaInfo 文件名后缀", "mi_suffix", 9, width=20)
    ttk.Label(t4, text="文件名 = 前缀 + 原名 + 后缀 (+ 扩展名)。前缀默认无, 如填 media_ → media_xxx.mkv.mediainfo.txt;\n"
                       "后缀留空 = 不加: 如 xxx.mkv.jpg / xxx.mkv.txt (默认 _sheet 和 .mediainfo)。\n"
                       "ISO 取多个标题时, 序号 [1] [2]… 仍会加在最后 (如 xxx[1].jpg)。",
              foreground="#666").grid(row=10, column=0, columnspan=3, sticky="w")
    t4.columnconfigure(1, weight=1)

    # -- 高级
    t5 = tab("高级")
    ttk.Label(t5, text="蓝光读取方式").grid(row=9, column=0, sticky="w", pady=3)
    ttk.Combobox(t5, textvariable=var("bd_mode"), values=["auto", "direct", "libbluray"], width=12,
                 state="readonly").grid(row=9, column=1, sticky="w")
    ttk.Label(t5, foreground="#666", justify="left", text=(
        "auto: 默认, libbluray 读不到正常时长时 (常见于 UHD 蓝光) 自动改为直接读 m2ts;  direct: 总是直接读 m2ts;\n"
        "libbluray: 总是用 ffmpeg 的 bluray: 协议。蓝光 ISO 直读 m2ts 需要 7-Zip。")).grid(
        row=10, column=0, columnspan=3, sticky="w")
    entry(t5, "蓝光播放列表编号", "playlist", 0, width=10)
    entry(t5, "手动指定时长(秒)", "duration", 1, width=10)
    entry(t5, "ffmpeg 路径", "ffmpeg", 2, "file")
    entry(t5, "ffprobe 路径", "ffprobe", 3, "file")
    entry(t5, "7z 路径 (可选)", "sevenz", 4, "file")
    entry(t5, "mediainfo 路径", "mediainfo", 5, "file")
    ttk.Label(t5, text="(路径留空 = 自动从 PATH / 常见位置查找)", foreground="#666").grid(
        row=6, column=0, columnspan=3, sticky="w")
    check(t5, "调试: 日志里打印 ffmpeg 完整命令", "debug", 7, span=3)

    def reset_defaults():
        if messagebox.askyesno("恢复默认设置",
                               "确定要把所有设置恢复为默认值吗?\n\n"
                               "包括 截图 / 外观 / 水印 / 过滤规则 / 输出 / 高级 里的全部设置 (文件列表不受影响)。\n"
                               "此操作无法撤销。", icon="warning", default="no"):
            for k, v in V.items():
                if k not in ("geometry", "last_dir"):
                    v.set(DEFAULTS[k])
            filter_text.delete("1.0", "end")
            status.set("已恢复默认设置")
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
    def add_paths(paths, restore=None, quiet=False):
        exts = media_exts(V["extra_exts"].get())
        found = collect_inputs(list(paths), bool(V["recursive"].get()), exts, strict=True)
        added = 0
        for f in found:
            iid = str(f)
            if tree.exists(iid):
                continue
            k = media_kind(f)
            disc = ""
            if k == "iso":
                try:
                    typ = "DVD" if scan_dvd(f) else "蓝光"
                except Exception:
                    typ = "?"
            elif k == "dvdfolder":
                typ, disc = "DVD文件夹", "☑"
            elif k == "bdfolder":
                typ, disc = "蓝光文件夹", "☑"
            else:
                typ = "视频"
            st = "等待"
            if restore and iid in restore:
                if restore[iid].get("disc") is False and disc:
                    disc = "☐"
                if restore[iid].get("status") in ("失败", "处理中") or re.match(r"^完成\(\d+失败\)$", str(restore[iid].get("status", ""))):
                    st = "待重试"
            tree.insert("", "end", iid=iid, values=(f.name, typ, disc, st))
            if disc:
                disc_on[iid] = (disc == "☑")
            added += 1
        if not quiet:
            if paths and not found:
                status.set("没有可添加的文件 (扩展名不支持? 可在 设置-文件 里追加; 目录是否要勾选递归?)")
            elif added:
                status.set(f"已添加 {added} 个, 共 {len(tree.get_children())} 个")
                cfg["last_dir"] = str(Path(str(list(paths)[0]).strip("{}")).parent)
        persist()

    def on_tree_click(e):
        """点「整盘」列的 ☑/☐ 切换: ☑ 按整盘(一个DVD/蓝光)处理, ☐ 当普通文件夹批量处理其中的视频文件"""
        if tree.identify_region(e.x, e.y) != "cell" or tree.identify_column(e.x) != "#3":
            return None
        iid = tree.identify_row(e.y)
        if iid in disc_on and not state["running"]:
            disc_on[iid] = not disc_on[iid]
            tree.set(iid, "disc", "☑" if disc_on[iid] else "☐")
            status.set("按整盘处理" if disc_on[iid] else
                       "取消勾选: 当普通文件夹批量处理其中的视频文件 (需勾选「文件」页的递归才会进入子目录)")
            persist()
            return "break"
        return None
    tree.bind("<Button-1>", on_tree_click, add="+")

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
            disc_on.pop(i, None)
        persist()

    def remove_status(kind):
        """移除成功 (完成 / 已跳过) 或 失败 (失败 / 部分失败 / 待重试) 的行"""
        if state["running"]:
            return
        n = 0
        for iid in list(tree.get_children()):
            st = tree.set(iid, "status")
            hit = (st in ("完成", "已跳过", "完成(疑似损坏)") if kind == "ok"
                   else (st in ("失败", "待重试") or bool(re.match(r"^完成\(\d+失败\)$", st))))
            if hit:
                tree.delete(iid)
                reports.pop(iid, None)
                disc_on.pop(iid, None)
                n += 1
        status.set(f"已移除 {n} 个{'成功' if kind == 'ok' else '失败'}的")
        persist()

    def clear_all():
        for i in tree.get_children():
            tree.delete(i)
        reports.clear()
        disc_on.clear()
        mi_text.delete("1.0", "end")
        persist()

    if dnd_ok:
        for w in (root, tree):
            w.drop_target_register(DND_FILES)
            w.dnd_bind("<<Drop>>", lambda e: add_paths(list(root.tk.splitlist(e.data))))

    # ---------- 运行
    def set_running(on):
        state["running"] = on
        for b in (b_start, b_start_sel, b_mi, b_prev):
            b.configure(state="disabled" if on else "normal")
        b_stop.configure(state="normal" if on else "disabled")

    def expand_job(iid, c):
        """一行 -> 要处理的路径列表. 光盘文件夹取消 ☑ 时, 按普通文件夹批量处理其中的视频文件"""
        k = media_kind(iid)
        if k in ("bdfolder", "dvdfolder") and not disc_on.get(iid, True):
            return collect_inputs([iid], bool(c["recursive"]), media_exts(c["extra_exts"]),
                                  strict=False, disc_folders=False)
        return [Path(iid)]

    def worker(jobs, c):
        CANCEL.clear()
        w = QWriter(q)
        with contextlib.redirect_stdout(w), contextlib.redirect_stderr(w):
            for k, (iid, paths) in enumerate(jobs):
                if CANCEL.is_set():
                    q.put(("status", iid, "已停止"))
                    continue
                print(f"\n===== [{k + 1}/{len(jobs)}] {Path(iid).name} =====")
                if not paths:
                    print("没有可处理的文件 (取消整盘后是普通文件夹批量: 需要勾选递归才会进入子目录; 扩展名可在 设置-文件 追加)")
                    q.put(("status", iid, "无文件"))
                    q.put(("progress", k + 1, len(jobs)))
                    continue
                q.put(("status", iid, "处理中"))
                fails, stopped, reps, skipped, warned = 0, False, [], True, False
                for j, pth in enumerate(paths, 1):
                    if CANCEL.is_set():
                        stopped = True
                        break
                    if len(paths) > 1:
                        print(f"\n--- [{j}/{len(paths)}] {Path(pth).name}")
                        q.put(("status", iid, f"处理中 {j}/{len(paths)}"))
                    try:
                        r = process_iso(pth, c)
                        skipped = skipped and bool(r.get("skipped"))
                        warned = warned or bool(r.get("warn"))
                        if r.get("report"):
                            reps.append((f"===== {Path(pth).name} =====\n" if len(paths) > 1 else "") + r["report"])
                    except Cancelled:
                        print("已停止")
                        stopped = True
                        break
                    except Exception as e:
                        fails += 1
                        skipped = False
                        print("失败:", e)
                        if c.get("debug"):
                            traceback.print_exc()
                if reps:
                    q.put(("report", iid, "\n\n".join(reps)))
                if stopped:
                    final = "已停止"
                elif fails and fails == len(paths):
                    final = "失败"
                elif fails:
                    final = f"完成({fails}失败)"
                else:
                    final = "已跳过" if skipped else ("完成(疑似损坏)" if warned else "完成")
                q.put(("status", iid, final))
                q.put(("progress", k + 1, len(jobs)))
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
        try:
            flt = make_filter(c)
        except ValueError as e:
            messagebox.showerror("过滤规则有误", str(e))
            return
        jobs = [(i, expand_job(i, c)) for i in items]
        if mi_only:
            jobs = [(jobs[0][0], jobs[0][1][:1])]
        for i in items:
            tree.set(i, "status", "等待")
        if flt.active() and not mi_only:        # 过滤规则: 不满足的直接跳过 (只读 MediaInfo 的单个文件不过滤)
            kept_jobs, nskip = [], 0
            for iid, paths in jobs:
                kept = [pth for pth in paths if flt.test(pth)[0]]
                if paths and not kept:
                    tree.set(iid, "status", "已过滤")
                    nskip += 1
                else:
                    kept_jobs.append((iid, kept if paths else paths))
            jobs = kept_jobs
            log_add(f"\n[过滤] 按规则跳过 {nskip} 项, 处理 {len(jobs)} 项\n")
            if not jobs:
                status.set("所有项目都被过滤规则排除了")
                persist()
                return
        prog.configure(maximum=len(jobs), value=0)
        set_running(True)
        status.set("处理中 ...")
        t = threading.Thread(target=worker, args=(jobs, c), daemon=True)
        state["worker"] = t
        t.start()
        if not mi_only:
            nb.select(t6)
        else:
            nb.select(t3)

    def check_list():
        """按当前过滤规则检查列表: 会被跳过的标成「将跳过」"""
        c = collect()
        try:
            flt = make_filter(c)
        except ValueError as e:
            messagebox.showerror("过滤规则有误", str(e))
            return
        skip = 0
        for iid in tree.get_children():
            paths = expand_job(iid, c)
            res = [flt.test(pth) for pth in paths] if flt.active() else [(True, "")]
            bad = bool(paths) and not any(ok for ok, _ in res)
            cur = tree.set(iid, "status")
            if bad:
                skip += 1
                tree.set(iid, "status", "将跳过")
                log_add(f"[过滤] {Path(iid).name}: {res[0][1]}\n")
            elif cur in ("将跳过", "已过滤"):
                tree.set(iid, "status", "等待")
        status.set(f"检查完成: 共 {len(tree.get_children())} 个, 将跳过 {skip} 个" if flt.active()
                   else "没有填写过滤规则")

    # ---------- 预览: 用当前所有设置, 对选中的 (没选就第一个) 文件生成一张联系表, 显示在「预览」页
    def preview():
        if state["running"]:
            return
        sel = list(tree.selection()) or list(tree.get_children())
        if not sel:
            messagebox.showinfo("提示", "请先添加文件 (然后选中一个再预览)")
            return
        c = collect()
        paths = expand_job(sel[0], c)
        if not paths:
            messagebox.showinfo("提示", "这一项没有可处理的文件")
            return
        pvdir = Path(tempfile.mkdtemp(prefix="bdtool_pv_"))     # 预览用的临时目录, 生成并读进内存后立刻删除
        out = pvdir / "preview.png"
        c.update(make_sheet=True, do_mediainfo=False, save_mediainfo=False, top_n=1, keep_thumbs=False,
                 exist_mode="overwrite", _preview_out=str(out))
        pv_status.set(f"正在生成预览: {Path(paths[0]).name} …")
        set_running(True)
        nb.select(t7)

        def pw():
            CANCEL.clear()
            wr = QWriter(q)
            with contextlib.redirect_stdout(wr), contextlib.redirect_stderr(wr):
                print(f"\n===== 预览: {Path(paths[0]).name} =====")
                try:
                    process_iso(paths[0], c)
                    if out.exists():
                        from PIL import Image
                        im = Image.open(out)
                        im.load()                      # 读进内存, 之后磁盘上的临时图就可以删了
                        q.put(("preview", im))
                    else:
                        q.put(("preview_err", "没有生成图片, 详见日志"))
                except Cancelled:
                    q.put(("preview_err", "已停止"))
                except Exception as e:
                    print("失败:", e)
                    q.put(("preview_err", str(e)))
                finally:
                    shutil.rmtree(pvdir, ignore_errors=True)
            q.put(("pdone",))
        threading.Thread(target=pw, daemon=True).start()

    def render_preview():
        im0 = state.get("preview")
        if im0 is None:
            return
        try:
            import base64
            import io

            im = im0.convert("RGB")
            cw, ch = canvas.winfo_width(), canvas.winfo_height()
            if fit_var.get() and cw > 40 and ch > 40:
                sc = min(cw / im.width, ch / im.height, 1.0)
                if sc < 1.0:
                    im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))))
            buf = io.BytesIO()
            im.save(buf, "PNG")
            state["photo"] = tk.PhotoImage(data=base64.b64encode(buf.getvalue()))
            canvas.delete("all")
            canvas.create_image(0, 0, anchor="nw", image=state["photo"])
            canvas.configure(scrollregion=(0, 0, im.width, im.height))
        except Exception as e:
            pv_status.set(f"预览显示失败: {e}")

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
                        persist()          # 每次状态变化都落盘, 断电/崩溃后下次能恢复队列
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
                    persist()
                elif m[0] == "preview":
                    state["preview"] = m[1]
                    pv_status.set("预览已生成 (所有设置都已应用)")
                    render_preview()
                elif m[0] == "preview_err":
                    pv_status.set("预览失败: " + m[1][:120])
                elif m[0] == "pdone":
                    set_running(False)
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

    def copy_cmd():
        sel = list(tree.selection()) or list(tree.get_children())
        cmd = build_cli_command(collect(), sel or ["xxx.mkv"])
        root.clipboard_clear()
        root.clipboard_append(cmd)
        root.update()
        log_add("\n[命令行]\n" + cmd + "\n")
        status.set("命令行已复制到剪贴板" + ("" if sel else " (列表为空, 用 xxx.mkv 占位)"))

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
    ttk.Button(tbx, text="移除成功", command=lambda: remove_status("ok")).pack(side="left", padx=2)
    ttk.Button(tbx, text="移除失败", command=lambda: remove_status("fail")).pack(side="left", padx=2)
    tb2 = ttk.Frame(left)
    tb2.pack(fill="x", pady=(2, 0))
    b_start = btn(tb2, "▶ 开始(全部)", lambda: start())
    b_start_sel = btn(tb2, "开始(选中)", lambda: start(selected=True))
    b_stop = btn(tb2, "■ 停止", stop, state="disabled")
    btn(tb2, "打开输出目录", open_out)
    bar = ttk.Frame(right)
    bar.pack(side="bottom", fill="x", before=nb, pady=(4, 0))
    ttk.Button(bar, text="复制命令行", command=copy_cmd).pack(side="right")
    b_mi = ttk.Button(brow, text="读取选中文件的 MediaInfo", command=lambda: start(mi_only=True))
    b_mi.pack(side="left", padx=2)
    ttk.Button(brow, text="复制", command=copy_mi).pack(side="left", padx=2)
    ttk.Button(brow, text="另存为…", command=save_mi).pack(side="left", padx=2)
    ttk.Button(log.master, text="清空日志", command=lambda: (log.configure(state="normal"),
                                                         log.delete("1.0", "end"),
                                                         log.configure(state="disabled"))).pack(side="bottom")

    def on_close():
        c = collect()
        state["pending_ready"] = True
        save_config(c)
        CANCEL.set()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)

    # ---------- 崩溃/断电/失败后的队列恢复: 上次没处理完的 (含失败/中断) 问一下是否载入
    pend = [x for x in (cfg.get("pending") or []) if isinstance(x, dict) and x.get("path")
            and os.path.exists(str(x["path"]))]
    if pend:
        nbad = sum(1 for x in pend if x.get("status") in ("失败", "处理中")
                   or re.match(r"^完成\(\d+失败\)$", str(x.get("status", ""))))
        if messagebox.askyesno("载入上次的队列",
                               f"上次有 {len(pend)} 个文件没处理完 (其中失败/中断 {nbad} 个)。\n是否载入到列表?"):
            add_paths([x["path"] for x in pend], restore={str(x["path"]): x for x in pend}, quiet=True)
            status.set(f"已载入上次未完成的 {len(tree.get_children())} 个文件")
    state["pending_ready"] = True
    persist()          # 用户选了"否"时, 这里会把旧队列清掉

    if initial:
        add_paths(list(initial))
    poll()
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(cli(sys.argv[1:]))
