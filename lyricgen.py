#!/usr/bin/env python3
"""lyricgen — turn a song clip into a TikTok "speed song" lyric video.

Pipeline:
  transcribe  media -> vocals separated -> word-level timestamps (words.json + lyrics.txt)
  align       re-map timestamps after you hand-correct lyrics.txt
  render      b-roll clips + words.json -> 1080x1920 MP4 with one word on screen at a time
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import io
import zipfile
import random
import re
import shutil
import subprocess
import sys
import tarfile
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
FONTS = ROOT / "fonts"
BROLL = ROOT / "broll"
PROJECTS = ROOT / "projects"
INTER_ZIP = "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip"
RELEASES = "https://github.com/k2-fsa/sherpa-onnx/releases/download"
SEPARATOR = MODELS / "UVR-MDX-NET-Voc_FT.onnx"
ASR_DIR = MODELS / "sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"

W, H, FPS = 1080, 1920, 30
PUNCT_BREAK = {".", ",", "?", "!", ";", ":", "…"}
LINE_GAP = 0.55  # seconds of silence that starts a new lyric line
MAX_LINE_WORDS = 9
MAX_WORD_HOLD = 1.1  # a word disappears after this long if nobody sings


# ---------------------------------------------------------------- utils

def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def ffmpeg(*args: str) -> None:
    run(["ffmpeg", "-v", "error", "-y", *args])


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return float(out.strip())


def norm(word: str) -> str:
    w = unicodedata.normalize("NFKD", word.lower())
    w = "".join(c for c in w if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9']", "", w)


# ---------------------------------------------------------------- setup

def cmd_setup(_: argparse.Namespace) -> None:
    MODELS.mkdir(exist_ok=True)
    if not SEPARATOR.exists():
        print("downloading vocal separator (67 MB)…")
        urllib.request.urlretrieve(f"{RELEASES}/source-separation-models/{SEPARATOR.name}", SEPARATOR)
    if not ASR_DIR.exists():
        print("downloading Parakeet TDT v3 ASR (670 MB)…")
        tmp = MODELS / "asr.tar.bz2"
        urllib.request.urlretrieve(f"{RELEASES}/asr-models/{ASR_DIR.name}.tar.bz2", tmp)
        with tarfile.open(tmp) as t:
            t.extractall(MODELS, filter="data")
        tmp.unlink()
    FONTS.mkdir(exist_ok=True)
    if not any(FONTS.glob("*.ttf")):
        print("downloading Inter Display fonts…")
        with urllib.request.urlopen(INTER_ZIP, timeout=120) as r:
            z = zipfile.ZipFile(io.BytesIO(r.read()))
        for n in z.namelist():
            if re.search(r"InterDisplay-(Black|SemiBold)\.ttf$", n):
                (FONTS / Path(n).name).write_bytes(z.read(n))
    print("models + fonts ready")


# ---------------------------------------------------------------- transcribe

def separate_vocals(media: Path, work: Path) -> Path:
    import numpy as np
    import sherpa_onnx as so
    import soundfile as sf

    stereo = work / "audio44.wav"
    ffmpeg("-i", str(media), "-vn", "-ac", "2", "-ar", "44100", str(stereo))
    cfg = so.OfflineSourceSeparationConfig(
        model=so.OfflineSourceSeparationModelConfig(
            uvr=so.OfflineSourceSeparationUvrModelConfig(model=str(SEPARATOR)), num_threads=4
        )
    )
    audio, sr = sf.read(stereo, dtype="float32", always_2d=True)
    out = so.OfflineSourceSeparation(cfg).process(sample_rate=sr, samples=np.ascontiguousarray(audio.T))
    vocals44 = work / "vocals44.wav"
    sf.write(vocals44, np.asarray(out.stems[0].data).T, out.sample_rate)
    vocals16 = work / "vocals16k.wav"
    ffmpeg("-i", str(vocals44), "-ac", "1", "-ar", "16000", str(vocals16))
    return vocals16


def asr_tokens(wav: Path) -> tuple[list[str], list[float]]:
    import sherpa_onnx as so
    import soundfile as sf

    rec = so.OfflineRecognizer.from_transducer(
        encoder=str(ASR_DIR / "encoder.int8.onnx"),
        decoder=str(ASR_DIR / "decoder.int8.onnx"),
        joiner=str(ASR_DIR / "joiner.int8.onnx"),
        tokens=str(ASR_DIR / "tokens.txt"),
        model_type="nemo_transducer",
        num_threads=4,
    )
    audio, sr = sf.read(wav, dtype="float32")
    stream = rec.create_stream()
    stream.accept_waveform(sr, audio)
    rec.decode_stream(stream)
    return list(stream.result.tokens), list(stream.result.timestamps)


def tokens_to_words(tokens: list[str], stamps: list[float]) -> list[dict]:
    words: list[dict] = []
    for tok, ts in zip(tokens, stamps):
        if tok.strip() in PUNCT_BREAK:
            if words:
                words[-1]["text"] += tok.strip()
                words[-1]["break"] = True
            continue
        if tok.startswith(" ") or not words:
            words.append({"text": tok.strip(), "start": round(ts, 3), "break": False})
        else:
            words[-1]["text"] += tok
    return words


def assign_lines(words: list[dict]) -> None:
    line, count = 0, 0
    for i, w in enumerate(words):
        if i > 0:
            prev = words[i - 1]
            gap = w["start"] - prev["start"]
            hard = prev.get("break") and prev["text"][-1] in ".?!…"
            soft = prev.get("break") and count >= 4
            if hard or soft or gap > LINE_GAP + 0.4 or count >= MAX_LINE_WORDS:
                line, count = line + 1, 0
        w["line"] = line
        count += 1


def finish_timings(words: list[dict], total: float) -> None:
    for i, w in enumerate(words):
        nxt = words[i + 1]["start"] if i + 1 < len(words) else total
        w["end"] = round(min(nxt, w["start"] + MAX_WORD_HOLD), 3)
        w.pop("break", None)


def write_project(proj: Path, words: list[dict], total: float) -> None:
    (proj / "words.json").write_text(
        json.dumps({"duration": total, "words": words}, ensure_ascii=False, indent=1)
    )
    lines: dict[int, list[str]] = {}
    for w in words:
        lines.setdefault(w["line"], []).append(w["text"])
    (proj / "lyrics.txt").write_text("\n".join(" ".join(v) for v in lines.values()) + "\n")


def cmd_transcribe(a: argparse.Namespace) -> None:
    media = Path(a.media).resolve()
    proj = Path(a.project)
    work = proj / "work"
    work.mkdir(parents=True, exist_ok=True)
    suffix = media.suffix if media.suffix.lower() in {".mp4", ".mov", ".m4a", ".mp3", ".wav"} else ".mp4"
    shutil.copy(media, proj / ("source" + suffix))
    total = probe_duration(media)
    print("1/2 separating vocals…")
    vocals = separate_vocals(media, work)
    print("2/2 transcribing with word timestamps…")
    tokens, stamps = asr_tokens(vocals)
    words = tokens_to_words(tokens, stamps)
    assign_lines(words)
    finish_timings(words, total)
    (work / "asr_words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1))
    write_project(proj, words, total)
    print(f"{len(words)} words -> {proj/'lyrics.txt'}  (fix it by hand, then run `align`)")


# ---------------------------------------------------------------- align

def cmd_align(a: argparse.Namespace) -> None:
    """Map hand-corrected lyrics.txt onto the original ASR timings."""
    proj = Path(a.project)
    asr = json.loads((proj / "work" / "asr_words.json").read_text())
    total = json.loads((proj / "words.json").read_text())["duration"]
    new: list[dict] = []
    for li, line in enumerate((proj / "lyrics.txt").read_text().splitlines()):
        for tok in line.split():
            new.append({"text": tok, "line": li})

    src = [norm(w["text"]) for w in asr]
    dst = [norm(w["text"]) for w in new]
    sm = difflib.SequenceMatcher(a=src, b=dst, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "delete":
            continue
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            for k in range(j2 - j1):
                new[j1 + k]["start"] = asr[i1 + k]["start"]
            continue
        # replace with different word count, or insert: spread over the available span
        t0 = asr[i1]["start"] if i1 < len(asr) else (asr[-1]["end"] if asr else 0.0)
        if i2 > i1:
            t1 = asr[i2 - 1]["end"]
        else:
            t1 = asr[i1]["start"] if i1 < len(asr) else total
            t0 = asr[i1 - 1]["start"] + 0.12 if i1 > 0 else max(0.0, t1 - 0.3 * (j2 - j1))
        span = max(t1 - t0, 0.12 * (j2 - j1))
        weights = [max(len(norm(n["text"])), 1) for n in new[j1:j2]]
        acc = 0.0
        for k, wgt in enumerate(weights):
            new[j1 + k]["start"] = round(t0 + span * acc / sum(weights), 3)
            acc += wgt
    new.sort(key=lambda w: w["start"])
    finish_timings(new, total)
    (proj / "words.json").write_text(json.dumps({"duration": total, "words": new}, ensure_ascii=False, indent=1))
    print(f"aligned {len(new)} words")


# ---------------------------------------------------------------- render

STYLES = {
    # word colour (ASS &HBBGGRR), accent for the last word of each line, show full line at bottom?
    "damso": {"word": "&H00FF2A1E", "accent": "&H00FF2A1E", "font": "Inter Display Black", "size": 140,
              "subtitle": False, "upper": True, "dim": -0.10},
    "bello": {"word": "&H00FFFFFF", "accent": "&H00E0329B", "font": "Inter Display Black", "size": 128,
              "subtitle": True, "upper": True, "dim": -0.12},
    "cream": {"word": "&H00C8DCF2", "accent": "&H00C8DCF2", "font": "Inter Display Black", "size": 170,
              "subtitle": False, "upper": True, "dim": -0.06},
}


def ass_time(t: float) -> str:
    t = max(t, 0.0)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ass_escape(text: str) -> str:
    return text.replace("\\", "").replace("{", "(").replace("}", ")")


def build_ass(words: list[dict], style: dict, offset: float, end: float) -> str:
    st = style
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,{st['font']},{st['size']},{st['word']},&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,0,3,5,60,60,0,1
Style: Line,Inter Display SemiBold,52,&H00FFFFFF,&H000000FF,&H59000000,&H59000000,0,0,0,0,100,100,0,0,3,12,0,1,40,140,470,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    last_in_line = {}
    for i, w in enumerate(words):
        last_in_line[w["line"]] = i
    for i, w in enumerate(words):
        s, e = w["start"] - offset, w["end"] - offset
        if e <= 0 or s >= end - offset:
            continue
        text = re.sub(r"[.,!?;:…]+$", "", w["text"])
        if st["upper"]:
            text = text.upper()
        colour = st["accent"] if last_in_line[w["line"]] == i else st["word"]
        pop = r"{\c" + colour + r"&\fscx118\fscy118\t(0,90,\fscx100\fscy100)}"
        events.append(f"Dialogue: 1,{ass_time(s)},{ass_time(e)},Word,,0,0,0,,{pop}{ass_escape(text)}")
    if st["subtitle"]:
        lines: dict[int, list[dict]] = {}
        for w in words:
            lines.setdefault(w["line"], []).append(w)
        groups = list(lines.values())
        for gi, ws in enumerate(groups):
            s, e = ws[0]["start"] - offset, ws[-1]["end"] - offset + 0.15
            if gi + 1 < len(groups):
                e = min(e, groups[gi + 1][0]["start"] - offset)
            if e <= 0 or s >= end - offset:
                continue
            text = " ".join(x["text"] for x in ws).rstrip(".,;:")
            events.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Line,,0,0,0,,{ass_escape(text.lower())}")
    return head + "\n".join(events) + "\n"


def build_broll(clips: list[Path], cut_points: list[float], length: float, out: Path, dim: float, seed: int) -> None:
    """Cut the b-roll into segments that switch on lyric line changes."""
    rng = random.Random(seed)
    durations = {c: probe_duration(c) for c in clips}
    bounds = [0.0] + [t for t in cut_points if 0.4 < t < length - 0.4] + [length]
    inputs, filters = [], []
    order = clips[:]
    for k in range(len(bounds) - 1):
        seg = bounds[k + 1] - bounds[k]
        if k % len(order) == 0:
            rng.shuffle(order)
        clip = order[k % len(order)]
        start = rng.uniform(0, max(durations[clip] - seg - 0.05, 0))
        inputs += ["-ss", f"{start:.3f}", "-t", f"{seg + 0.05:.3f}", "-i", str(clip)]
        filters.append(
            f"[{k}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"setsar=1,fps={FPS},trim=duration={seg:.3f},setpts=PTS-STARTPTS[v{k}]"
        )
    n = len(bounds) - 1
    filters.append("".join(f"[v{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0,"
                   f"eq=brightness={dim}:saturation=0.85,vignette=PI/5[out]")
    ffmpeg(*inputs, "-filter_complex", ";".join(filters), "-map", "[out]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out))


def render(proj: Path, style_name: str, clips: list[Path], start: float | None = None,
           end: float | None = None, seed: int = 7, cut_every: float | None = None,
           out: Path | None = None) -> Path:
    data = json.loads((proj / "words.json").read_text())
    words = data["words"]
    source = next(proj.glob("source.*"))
    start = start or 0.0
    end = end or data["duration"]
    length = end - start
    style = STYLES[style_name]
    clips = clips or [source.resolve()]

    work = proj / "work"
    work.mkdir(exist_ok=True)
    if cut_every:
        cuts = [t * cut_every for t in range(1, int(length / cut_every) + 1)]
    else:  # switch clip on every new lyric line
        cuts = sorted({w["start"] - start for i, w in enumerate(words)
                       if i == 0 or w["line"] != words[i - 1]["line"]})
    bg = work / f"broll_{style_name}.mp4"
    print(f"[{style_name}] building b-roll from {len(clips)} clip(s)…")
    build_broll(clips, cuts, length, bg, style["dim"], seed)

    ass = work / f"{style_name}.ass"
    ass.write_text(build_ass(words, style, start, end))
    out = out or proj / f"{proj.name}_{style_name}.mp4"
    fonts = f":fontsdir={FONTS}" if FONTS.exists() else ""
    print(f"[{style_name}] burning lyrics + audio…")
    ffmpeg("-i", str(bg), "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(source),
           "-filter_complex", f"[0:v]ass={ass}{fonts}[v]", "-map", "[v]", "-map", "1:a:0",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out))
    print("->", out)
    return out


def cmd_render(a: argparse.Namespace) -> None:
    clips = [Path(c).resolve() for c in a.broll] if a.broll else []
    if a.broll_dir:
        clips += list_clips(Path(a.broll_dir))
    for st in a.style:
        render(Path(a.project), st, clips, a.start, a.end, a.seed, a.cut_every)


# ---------------------------------------------------------------- online sources (optional)

def http_json(url: str, headers: dict | None = None) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": "lyricgen/1.0", **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def fetch_lyrics(artist: str, title: str) -> str | None:
    """Official lyrics from LRCLIB (free, no key). Returns None if unreachable/not found."""
    q = urllib.parse.urlencode({"artist_name": artist, "track_name": title})
    try:
        hits = http_json(f"https://lrclib.net/api/search?{q}")
    except Exception as e:  # network blocked, timeout…
        print(f"  lyrics: LRCLIB unreachable ({e.__class__.__name__}) -> keeping the transcription")
        return None
    for h in hits if isinstance(hits, list) else []:
        if h.get("plainLyrics"):
            return h["plainLyrics"]
    print("  lyrics: not found on LRCLIB -> keeping the transcription")
    return None


def match_excerpt(asr_words: list[dict], official: str) -> list[str] | None:
    """Find which lines of the full official lyrics are sung in the clip."""
    lines = [l.strip() for l in official.splitlines() if l.strip() and not l.strip().startswith("[")]
    flat, owner = [], []
    for li, line in enumerate(lines):
        for tok in line.split():
            flat.append(norm(tok))
            owner.append(li)
    src = [norm(w["text"]) for w in asr_words]
    blocks = [b for b in difflib.SequenceMatcher(a=src, b=flat, autojunk=False).get_matching_blocks()
              if b.size >= 2]
    matched = sum(b.size for b in blocks)
    if not blocks or matched < 0.35 * len(src):
        print(f"  lyrics: official text doesn't match the clip well ({matched}/{len(src)} words) -> skipped")
        return None
    first, last = owner[blocks[0].b], owner[blocks[-1].b + blocks[-1].size - 1]
    print(f"  lyrics: matched {matched}/{len(src)} words, using official lines {first + 1}-{last + 1}")
    return lines[first:last + 1]


def list_clips(folder: Path) -> list[Path]:
    return sorted(p.resolve() for p in folder.rglob("*") if p.suffix.lower() in {".mp4", ".mov", ".webm", ".m4v"})


def fetch_broll(queries: list[str], per_query: int = 4) -> list[Path]:
    """Download portrait stock clips from Pexels (needs PEXELS_API_KEY). Cached in broll/."""
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        print("  b-roll: no PEXELS_API_KEY -> using local broll/ folder or the source video")
        return []
    clips: list[Path] = []
    for q in queries:
        folder = BROLL / re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")
        folder.mkdir(parents=True, exist_ok=True)
        cached = list_clips(folder)
        if len(cached) >= per_query:
            clips += cached[:per_query]
            continue
        params = urllib.parse.urlencode({"query": q, "orientation": "portrait", "per_page": per_query * 2})
        try:
            res = http_json(f"https://api.pexels.com/videos/search?{params}", {"Authorization": key})
        except Exception as e:
            print(f"  b-roll: Pexels unreachable ({e.__class__.__name__}) for '{q}'")
            clips += cached
            continue
        got = cached[:]
        for v in res.get("videos", []):
            if len(got) >= per_query:
                break
            files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4"
                     and (f.get("height") or 0) > (f.get("width") or 0) and (f.get("height") or 0) <= 1920]
            if not files:
                continue
            best = max(files, key=lambda f: f["height"])
            dest = folder / f"pexels_{v['id']}.mp4"
            if not dest.exists():
                req = urllib.request.Request(best["link"], headers={"User-Agent": "lyricgen/1.0"})
                with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as fh:
                    shutil.copyfileobj(r, fh)
            got.append(dest)
        print(f"  b-roll: {len(got)} clip(s) for '{q}'")
        clips += got
    return clips


# ---------------------------------------------------------------- make (all-in-one)

DEFAULT_BROLL = ["night drive city", "dubai night", "sports car night", "city lights night"]


def slug(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "clip"


def write_caption(proj: Path, artist: str | None, title: str | None) -> None:
    tags = ["#paroles", "#lyrics", "#speedsongs", "#rapfr", "#pourtoi"]
    if artist:
        tags.insert(0, "#" + slug(artist).replace("-", ""))
    if title:
        tags.insert(1, "#" + slug(title).replace("-", ""))
    head = " – ".join(x for x in [title, artist] if x) or proj.name
    (proj / "caption.txt").write_text(f"{head} 🎧\n{' '.join(tags)}\n")


def cmd_make(a: argparse.Namespace) -> None:
    name = a.name or slug(" ".join(x for x in [a.artist, a.title] if x) or Path(a.media).stem)
    proj = PROJECTS / name
    cmd_transcribe(argparse.Namespace(media=a.media, project=str(proj)))

    if a.artist and a.title:
        official = fetch_lyrics(a.artist, a.title)
        if official:
            (proj / "official_lyrics.txt").write_text(official)
            asr = json.loads((proj / "work" / "asr_words.json").read_text())
            lines = match_excerpt(asr, official)
            if lines:
                (proj / "lyrics.txt").write_text("\n".join(lines) + "\n")
                cmd_align(argparse.Namespace(project=str(proj)))

    clips: list[Path] = []
    if a.broll_dir:
        clips = list_clips(Path(a.broll_dir))
    if not clips and not a.no_stock:
        clips = fetch_broll(a.broll_query or DEFAULT_BROLL, a.clips_per_query)
    if not clips and BROLL.exists():
        clips = list_clips(BROLL)
    if not clips:
        print("  b-roll: none found -> the source video is used as background")

    outs = [render(proj, st, clips, a.start, a.end, a.seed) for st in a.style]
    write_caption(proj, a.artist, a.title)
    print("\nDONE")
    for o in outs:
        print("  video  :", o)
    print("  caption:", proj / "caption.txt")
    print("  lyrics :", proj / "lyrics.txt", "(edit + `align` + `render` if a word is wrong)")


# ---------------------------------------------------------------- main

def main() -> None:
    p = argparse.ArgumentParser(prog="lyricgen", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(required=True)

    s = sub.add_parser("setup", help="download models + fonts")
    s.set_defaults(fn=cmd_setup)

    s = sub.add_parser("make", help="ALL-IN-ONE: clip -> finished videos + caption")
    s.add_argument("media", help="video or audio of the song excerpt (the sound is kept)")
    s.add_argument("--artist")
    s.add_argument("--title")
    s.add_argument("--name", help="project folder name (default: artist-title)")
    s.add_argument("--style", nargs="+", choices=sorted(STYLES), default=["damso", "bello"])
    s.add_argument("--broll-dir", help="folder of your own background clips")
    s.add_argument("--broll-query", nargs="+", help=f"Pexels searches (default: {DEFAULT_BROLL})")
    s.add_argument("--clips-per-query", type=int, default=3)
    s.add_argument("--no-stock", action="store_true", help="never download stock clips")
    s.add_argument("--start", type=float)
    s.add_argument("--end", type=float)
    s.add_argument("--seed", type=int, default=7)
    s.set_defaults(fn=cmd_make)

    s = sub.add_parser("transcribe", help="media -> words.json + lyrics.txt")
    s.add_argument("media")
    s.add_argument("project")
    s.set_defaults(fn=cmd_transcribe)

    s = sub.add_parser("align", help="re-time hand-corrected lyrics.txt")
    s.add_argument("project")
    s.set_defaults(fn=cmd_align)

    s = sub.add_parser("render", help="render the lyric video(s)")
    s.add_argument("project")
    s.add_argument("--style", nargs="+", choices=sorted(STYLES), default=["damso"])
    s.add_argument("--broll", nargs="*", help="background clips")
    s.add_argument("--broll-dir", help="folder of background clips")
    s.add_argument("--cut-every", type=float, help="switch clip every N s (default: on each lyric line)")
    s.add_argument("--start", type=float)
    s.add_argument("--end", type=float)
    s.add_argument("--seed", type=int, default=7)
    s.set_defaults(fn=cmd_render)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
