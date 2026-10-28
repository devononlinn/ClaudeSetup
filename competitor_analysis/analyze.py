#!/usr/bin/env python3
"""Sound-design and colour analysis of analog-horror YouTube videos.

Pipeline per video (see README.md for setup):
  1. yt-dlp: 480p video + English auto-captions (VTT) into a temp folder.
  2. Demucs htdemucs --two-stems=vocals -> voice / non-voice.
  3. librosa onsets on the non-voice stem, filtered against the music/ambience bed,
     then each hit is measured (time, duration, peak dB vs voice) and categorised.
  4. Each hit is mapped to the caption word it lands on (+/-0.3 s) and POS-tagged.
  5. Frames every 0.5 s: red share, brightness, other strong hue, flashes, colour shifts,
     coincidence with sound hits (+/-0.2 s); 6 representative stills saved.
  6. report.md, hits.csv, color.csv, frames/ and competitor_sound_color.zip.

Usage:
  python analyze.py --picks picks.json --out OUT_DIR [--work TMP_DIR] [--keep-video]
  python analyze.py --report-only --out OUT_DIR      # rebuild report from cached JSON
"""
import argparse
import csv
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import numpy as np
import librosa
import scipy.ndimage as ndi

SR = 22050
HOP = 512
FRAME_FPS = 2  # one frame every 0.5 s
WORD_TOL = 0.3
AV_TOL = 0.2

CATEGORIES = ["low boom/hit", "whoosh", "riser", "sting/stab", "glitch/static",
              "foley", "drone/bed change"]


def run(cmd, **kw):
    print("+", " ".join(cmd), file=sys.stderr)
    return subprocess.run(cmd, check=True, **kw)


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-9))


# ---------------------------------------------------------------- download / separate

def download(vid, work):
    url = f"https://www.youtube.com/watch?v={vid}"
    run(["yt-dlp", "-f", "bv*[height<=480]+ba/b[height<=480]", "--merge-output-format", "mp4",
         "--write-auto-subs", "--sub-langs", "en.*,en", "--sub-format", "vtt",
         "-o", os.path.join(work, f"{vid}.%(ext)s"), url])
    video = os.path.join(work, f"{vid}.mp4")
    subs = sorted(glob.glob(os.path.join(work, f"{vid}*.vtt")))
    # prefer the plain auto "en" track over translated variants
    subs.sort(key=lambda p: (not p.endswith(".en.vtt"), len(p)))
    return video, (subs[0] if subs else None)


def separate(video, vid, work):
    wav = os.path.join(work, f"{vid}.wav")
    stem_dir = os.path.join(work, "htdemucs", vid)
    voc, rest = os.path.join(stem_dir, "vocals.wav"), os.path.join(stem_dir, "no_vocals.wav")
    if not (os.path.exists(voc) and os.path.exists(rest)):
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vn", "-ac", "2", "-ar", "44100", wav])
        run([sys.executable, "-m", "demucs", "-n", "htdemucs", "--two-stems=vocals", "-o", work, wav])
    return voc, rest


# ---------------------------------------------------------------- audio analysis

def frame_rms(y):
    return librosa.feature.rms(y=y, frame_length=2048, hop_length=HOP)[0]


def voice_reference_db(voc_rms):
    """Median RMS (dBFS) of frames where the narrator is actually speaking."""
    d = db(voc_rms)
    active = d[d > d.max() - 30]
    return float(np.median(active)) if active.size else float(d.max())


def bed_envelope(rms, sr=SR, win_s=3.0):
    """Slow 'bed' level: rolling 30th percentile, so transients don't lift it."""
    n = max(3, int(win_s * sr / HOP) | 1)
    return ndi.percentile_filter(rms, 30, size=n, mode="nearest")


def classify(seg, sr, dur, attack, peak_pos):
    S = np.abs(librosa.stft(seg, n_fft=2048, hop_length=HOP)) + 1e-12
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    P = S ** 2
    tot = P.sum()
    low = P[freqs < 150].sum() / tot
    high = P[freqs > 4000].sum() / tot
    flat = float(np.median(librosa.feature.spectral_flatness(S=S)))
    cent = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
    cent_slope = (np.polyfit(np.arange(len(cent)), cent, 1)[0] * len(cent) / max(cent.mean(), 1)
                  if len(cent) > 2 else 0.0)
    # abrupt gating / stutter (level jumps >6 dB between 23 ms frames) -> glitch
    env = db(librosa.feature.rms(y=seg, frame_length=512, hop_length=128)[0])
    flips = float(np.mean(np.abs(np.diff(env)) > 6)) if len(env) > 2 else 0.0
    feats = dict(low=round(float(low), 3), high=round(float(high), 3), flat=round(flat, 3),
                 cent=round(float(cent.mean())), cent_slope=round(float(cent_slope), 2),
                 attack=round(attack, 3), peak_pos=round(peak_pos, 2), am=round(float(flips), 2))
    if dur >= 1.2 and peak_pos > 0.6 and (cent_slope > 0.2 or attack > 0.5):
        cat = "riser"
    elif flat > 0.15 and (flips > 0.05 or (high > 0.4 and attack < 0.03)):
        cat = "glitch/static"
    elif low > 0.45 and attack < 0.2:
        cat = "low boom/hit"
    elif 0.25 <= dur <= 2.5 and flat > 0.08 and 0.25 <= peak_pos <= 0.75 and attack > 0.08:
        cat = "whoosh"
    elif dur < 0.45 and attack < 0.06 and low < 0.45:
        cat = "foley"
    elif attack < 0.1:
        cat = "sting/stab"
    elif low > 0.45:
        cat = "low boom/hit"
    else:
        cat = "whoosh" if flat > 0.08 else "sting/stab"
    return cat, feats


def analyse_audio(voc_path, rest_path):
    voc, _ = librosa.load(voc_path, sr=SR, mono=True)
    rest, _ = librosa.load(rest_path, sr=SR, mono=True)
    n = min(len(voc), len(rest))
    voc, rest = voc[:n], rest[:n]
    t_of = lambda i: i * HOP / SR

    vr, rr, mr = frame_rms(voc), frame_rms(rest), frame_rms(voc + rest)
    vref = voice_reference_db(vr)
    bed = bed_envelope(rr)
    rr_db, bed_db = db(rr), db(bed)
    bed_raw_db = bed_db
    # the 3 s percentile lags at the edges of a bed dropout; a slower 70th percentile stops the
    # bed itself from reading as a "hit" there
    slow = db(ndi.percentile_filter(rr, 70, size=int(8 * SR / HOP) | 1, mode="nearest")) - 3
    bed_db = np.maximum(bed_db, slow)

    # Hits = stretches that rise >3 dB over the slow bed and peak >=6 dB over it (steady music
    # and ambience stay near the bed and are ignored). librosa onsets split a stretch that holds
    # several hits; a stretch with no onset (slow riser, sub boom) still counts from its start.
    oenv = librosa.onset.onset_strength(y=rest, sr=SR, hop_length=HOP)
    onsets = librosa.onset.onset_detect(onset_envelope=oenv, sr=SR, hop_length=HOP,
                                        backtrack=True, delta=0.25, wait=int(0.25 * SR / HOP))
    over = rr_db - bed_db
    min_gap = int(0.25 * SR / HOP)
    hits = []
    for s, e in runs(over > 3):
        if over[s:e].max() < 6:
            continue
        cuts = [s] + [int(o) for o in onsets if s + min_gap < o < e - 2]
        cuts = [c for k, c in enumerate(cuts) if k == 0 or c - cuts[k - 1] >= min_gap]
        for k, i0 in enumerate(cuts):
            end = min(cuts[k + 1] if k + 1 < len(cuts) else e, i0 + int(8 * SR / HOP))
            ipk = i0 + int(np.argmax(rr_db[i0:end]))
            if over[ipk] < 6:
                continue
            dur = t_of(end - i0)
            attack = t_of(ipk - i0)
            seg = rest[i0 * HOP: max(end, i0 + 4) * HOP]
            cat, feats = classify(seg, SR, dur, attack, (ipk - i0) / max(end - i0, 1))
            hits.append(dict(time=round(t_of(i0), 2), duration=round(dur, 2),
                             peak_dbfs=round(float(rr_db[ipk]), 1),
                             level_vs_voice_db=round(float(rr_db[ipk] - vref), 1),
                             above_bed_db=round(float(over[ipk]), 1),
                             category=cat, **feats))

    # ---- bed events: dropouts, changes, silences
    sec = int(SR / HOP)  # frames per second (approx)
    bed_med = float(np.median(bed_raw_db))
    events = []
    low_bed = bed_raw_db < bed_med - 10
    for s, e in runs(low_bed):
        if (e - s) / sec >= 1:
            events.append(dict(type="bed dropout", time=round(t_of(s), 2), duration=round(t_of(e - s), 2)))
    # bed change: the bed's timbre (chroma + MFCC, hit frames masked out) over the 4 s after a
    # point differs from the 4 s before it; also the bed coming back after a dropout.
    quiet = over < 3
    feat = np.vstack([librosa.feature.mfcc(y=rest, sr=SR, hop_length=HOP, n_mfcc=13)[1:] / 20,
                      librosa.feature.chroma_stft(y=rest, sr=SR, hop_length=HOP) * 2])
    feat = feat[:, : len(quiet)]
    w4 = 4 * sec
    cand = []
    for j in range(w4, feat.shape[1] - w4, sec // 2):
        a, b = quiet[j - w4:j], quiet[j:j + w4]
        if a.sum() < sec or b.sum() < sec or bed_raw_db[j - w4:j + w4].min() < bed_med - 10:
            continue
        d = np.linalg.norm(feat[:, j - w4:j][:, a].mean(1) - feat[:, j:j + w4][:, b].mean(1))
        cand.append((j, d))
    if cand:
        ds = np.array([d for _, d in cand])
        thr = max(np.median(ds) + 4 * np.median(np.abs(ds - np.median(ds))), 0.8)
        peaks = [j for k, (j, d) in enumerate(cand) if d > thr and
                 d == max(dd for jj, dd in cand[max(0, k - 4):k + 5])]
        for j in peaks:
            events.append(dict(type="bed change", time=round(t_of(j), 2), duration=0))
    for e in [e for e in events if e["type"] == "bed dropout"]:
        events.append(dict(type="bed change", time=round(e["time"] + e["duration"], 2), duration=0))
    for e in [e for e in events if e["type"] == "bed change"]:
        if any(abs(e["time"] - h["time"]) < 1 for h in hits):
            continue
        j = min(int(e["time"] * SR / HOP) + sec, len(bed_db) - 1)
        hits.append(dict(time=e["time"], duration=1.0, peak_dbfs=round(float(bed_db[j]), 1),
                         level_vs_voice_db=round(float(max(bed_db[j], vref - 60) - vref), 1),
                         above_bed_db=0.0, category="drone/bed change"))
    mix_db = db(mr)
    silent = mix_db < max(mix_db.max() - 50, -60)
    for s, e in runs(silent):
        if (e - s) / sec > 1:
            events.append(dict(type="silence", time=round(t_of(s), 2), duration=round(t_of(e - s), 2)))
    hits.sort(key=lambda h: h["time"])
    events.sort(key=lambda e: e["time"])
    return dict(duration=round(n / SR, 2), voice_ref_dbfs=round(vref, 1),
                bed_median_vs_voice_db=round(bed_med - vref, 1), hits=hits, bed_events=events)


def runs(mask):
    mask = np.concatenate([[False], mask, [False]])
    d = np.diff(mask.astype(int))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


# ---------------------------------------------------------------- captions / words

TS = r"(\d+):(\d\d):(\d\d)\.(\d+)"


def ts(m):
    h, mi, s, ms = m
    return int(h) * 3600 + int(mi) * 60 + int(s) + int(ms) / 10 ** len(ms)


def parse_vtt_words(path):
    """Word-level timings from a YouTube auto-caption VTT (uses the inline <t><c> tags)."""
    words = []
    if not path:
        return words
    txt = open(path, encoding="utf-8").read()
    for block in txt.split("\n\n"):
        m = re.search(TS + r" --> " + TS, block)
        if not m:
            continue
        start = ts(m.groups()[:4])
        for line in block.splitlines()[1:]:
            if "<c>" not in line and not re.search(r"<\d", line):
                continue
            # first word has the cue start, others carry <hh:mm:ss.mmm>
            parts = re.split(r"<(" + r"\d+:\d\d:\d\d\.\d+" + r")>", line)
            t = start
            for k, p in enumerate(parts):
                if k % 2 == 1:
                    t = ts(re.match(TS, p).groups())
                    continue
                w = re.sub(r"<[^>]+>", "", p).strip()
                for ww in w.split():
                    words.append((t, ww))
    # fallback for VTTs without inline timings: spread each cue's words evenly
    if not words:
        for block in txt.split("\n\n"):
            m = re.search(TS + r" --> " + TS, block)
            if not m:
                continue
            a, b = ts(m.groups()[:4]), ts(m.groups()[4:])
            ws = " ".join(re.sub(r"<[^>]+>", "", l) for l in block.splitlines()[1:]).split()
            for k, w in enumerate(ws):
                words.append((a + (b - a) * k / max(len(ws), 1), w))
    words = sorted(set(words))
    out = []
    for k, (t, w) in enumerate(words):
        end = words[k + 1][0] if k + 1 < len(words) else t + 0.5
        out.append(dict(start=round(t, 2), end=round(min(end, t + 1.5), 2), word=w,
                        gap_after=round(end - t, 2)))
    return out


NUMBER_WORDS = set("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                   "fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty "
                   "hundred thousand first second third fourth fifth sixth seventh eighth ninth tenth "
                   "number rule".split())


def tag_words(words):
    if not words:
        return words
    try:
        import nltk
        tags = [t for _, t in nltk.pos_tag([w["word"] for w in words])]
    except Exception:
        tags = ["?"] * len(words)
    for w, t in zip(words, tags):
        lw = re.sub(r"[^a-z0-9]", "", w["word"].lower())
        kinds = []
        if t == "CD" or lw.isdigit() or lw in NUMBER_WORDS:
            kinds.append("number")
        if t.startswith("NN"):
            kinds.append("noun")
        if t.startswith("VB"):
            kinds.append("verb")
        # auto-captions have no punctuation: treat a pause >= 0.6 s after the word as a sentence end
        if w["word"].endswith((".", "!", "?")) or w["gap_after"] >= 0.6:
            kinds.append("sentence end")
        w["pos"] = t
        w["kinds"] = kinds
    return words


def word_at(words, t, tol=WORD_TOL):
    best, bd = None, None
    for w in words:
        if w["start"] - tol <= t <= w["end"] + tol:
            d = 0 if w["start"] <= t <= w["end"] else min(abs(t - w["start"]), abs(t - w["end"]))
            if bd is None or d < bd:
                best, bd = w, d
    return best


# ---------------------------------------------------------------- visuals

def read_frames(video, width=160):
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0", video],
                           capture_output=True, text=True, check=True).stdout.strip().split(",")
    w0, h0 = int(probe[0]), int(probe[1])
    h = int(round(h0 * width / w0 / 2)) * 2
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", video, "-vf",
                        f"fps={FRAME_FPS},scale={width}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True)
    arr = np.frombuffer(p.stdout, np.uint8)
    return arr.reshape(-1, h, width, 3)


def rgb_to_hsv(f):
    f = f.astype(np.float32) / 255
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mx, mn = f.max(-1), f.min(-1)
    d = mx - mn + 1e-9
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-9), 0)
    return h, s, mx


HUE_NAMES = [(15, "red"), (45, "orange"), (70, "yellow"), (160, "green"), (200, "cyan"),
             (260, "blue"), (300, "purple"), (345, "magenta"), (360, "red")]


def hue_name(h):
    for lim, n in HUE_NAMES:
        if h < lim:
            return n
    return "red"


def analyse_frames(frames):
    rows = []
    for i, f in enumerate(frames):
        h, s, v = rgb_to_hsv(f)
        sat = (s > 0.5) & (v > 0.25)
        red = sat & ((h < 15) | (h >= 345))
        other = sat & ~red
        row = dict(time=i / FRAME_FPS, red_share=float(red.mean()),
                   brightness=float((0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]).mean() / 255),
                   sat_share=float(sat.mean()), other_hue="", other_share=0.0)
        if other.any():
            hist, edges = np.histogram(h[other], bins=12, range=(0, 360))
            k = int(np.argmax(hist))
            row["other_hue"] = hue_name((edges[k] + edges[k + 1]) / 2)
            row["other_share"] = float(hist[k] / h.size)
        # tint: mean chroma direction, used for colour-shift detection
        m = f.reshape(-1, 3).mean(0) / 255
        row["tint"] = (float(m[0] - m[1]), float(m[2] - m[1]))
        rows.append(row)
    # flashes and colour shifts
    for i, r in enumerate(rows):
        r["flash"] = ""
        r["color_shift"] = ""
        if i == 0:
            continue
        p = rows[i - 1]
        db_ = r["brightness"] - p["brightness"]
        if abs(db_) > 0.25 * max(p["brightness"], 0.04) and abs(db_) > 0.03:
            r["flash"] = "bright up" if db_ > 0 else "bright down"
        dr = r["red_share"] - p["red_share"]
        if abs(dr) > 0.25 * max(p["red_share"], 0.02) and abs(dr) > 0.02:
            r["flash"] = (r["flash"] + "+" if r["flash"] else "") + ("red up" if dr > 0 else "red down")
        lo = max(0, i - 4)
        ref = np.median([rows[j]["tint"] for j in range(lo, i)], axis=0)
        if np.linalg.norm(np.array(r["tint"]) - ref) > 0.06:
            r["color_shift"] = f"tint->{r['other_hue'] or ('red' if r['red_share'] > 0.05 else 'neutral')}"
    # a shift is only reported at its first frame
    for i in range(len(rows) - 1, 0, -1):
        if rows[i]["color_shift"] and rows[i - 1]["color_shift"]:
            rows[i]["color_shift"] = ""
    return rows


def pick_stills(rows, n=6):
    """6 frames that show the video's colour use: reddest, strongest other hue, biggest flash,
    then the most saturated frame from each third of the video."""
    chosen, why = [], []
    spread = max(4, len(rows) // 12)
    def add(i, reason, gap=4):
        if i is not None and all(abs(i - c) > gap for c in chosen):
            chosen.append(i); why.append(reason)
    idx = range(len(rows))
    add(max(idx, key=lambda i: rows[i]["red_share"]), "max red")
    add(max(idx, key=lambda i: rows[i]["other_share"]), "strongest non-red hue")
    fl = [i for i in idx if rows[i]["flash"]]
    if fl:
        add(max(fl, key=lambda i: abs(rows[i]["brightness"] - rows[i - 1]["brightness"])), "biggest flash")
    for part in np.array_split(np.arange(len(rows)), 3):
        if len(part):
            add(int(max(part, key=lambda i: rows[i]["sat_share"])), "most saturated in its third", spread)
    for i in sorted(idx, key=lambda i: -rows[i]["sat_share"]):
        if len(chosen) >= n:
            break
        add(i, "saturated filler", spread)
    for i in np.linspace(0, len(rows) - 1, 12).astype(int):  # still short: spread evenly
        if len(chosen) >= n:
            break
        add(int(i), "typical frame", spread)
    return list(zip(chosen, why))[:n]


def save_stills(video, rows, picks, frames_dir, label):
    out = []
    for k, (i, why) in enumerate(picks):
        t = rows[i]["time"]
        r = rows[i]
        name = f"{label}_{k + 1}_{int(t // 60):02d}m{t % 60:04.1f}s.jpg"
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
             "-q:v", "3", os.path.join(frames_dir, name)])
        out.append(dict(file=name, time=t, why=why, red=round(r["red_share"], 3),
                        brightness=round(r["brightness"], 2), other=f"{r['other_hue']} {r['other_share']:.0%}"))
    return out


# ---------------------------------------------------------------- per-video

def analyse_video(v, work, frames_dir, keep_video=False):
    vid = v["id"]
    vdir = os.path.join(work, vid)
    os.makedirs(vdir, exist_ok=True)
    video = os.path.join(vdir, f"{vid}.mp4")
    subs = sorted(glob.glob(os.path.join(vdir, f"{vid}*.vtt")))
    if not os.path.exists(video):
        video, sub = download(vid, vdir)
    else:
        sub = subs[0] if subs else None
    voc, rest = separate(video, vid, vdir)
    audio = analyse_audio(voc, rest)
    words = tag_words(parse_vtt_words(sub))
    for h in audio["hits"]:
        w = word_at(words, h["time"])
        h["word"] = w["word"] if w else ""
        h["word_kinds"] = ",".join(w["kinds"]) if w else ""
    rows = analyse_frames(read_frames(video))
    hit_times = np.array([h["time"] for h in audio["hits"]]) if audio["hits"] else np.array([])
    for r in rows:
        r["on_hit"] = bool(hit_times.size and np.min(np.abs(hit_times - r["time"])) <= AV_TOL + 0.25)
        # +0.25 s: frames are 0.5 s apart, so an accent can sit anywhere within half a sample
    stills = save_stills(video, rows, pick_stills(rows), frames_dir, v["label"])
    if not keep_video:
        for p in glob.glob(os.path.join(vdir, "*.mp4")) + glob.glob(os.path.join(vdir, "*.wav")):
            os.remove(p)
        shutil.rmtree(os.path.join(vdir, "htdemucs"), ignore_errors=True)
    res = dict(meta=v, audio=audio, words=len(words), frames=rows, stills=stills,
               captions=bool(sub))
    res["summary"] = summarise(res)
    return res


def summarise(res):
    a, rows = res["audio"], res["frames"]
    mins = a["duration"] / 60
    hits = [h for h in a["hits"] if h["category"] != "drone/bed change"]
    allh = a["hits"]
    mix = {c: sum(h["category"] == c for h in allh) for c in CATEGORIES}
    keyed = [h for h in hits if h.get("word_kinds")]
    on_word = [h for h in hits if h.get("word")]
    accents = [r for r in rows if r["flash"] or r["color_shift"]]
    q = np.array_split(np.array([r["red_share"] for r in rows]), 4) if rows else []
    hit_times = np.array([h["time"] for h in hits])
    frame_t = np.array([r["time"] for r in accents])
    hits_with_visual = (sum(np.min(np.abs(frame_t - t)) <= AV_TOL + 0.25 for t in hit_times)
                        if frame_t.size else 0)
    kinds = {}
    for h in keyed:
        for k in h["word_kinds"].split(","):
            kinds[k] = kinds.get(k, 0) + 1
    return dict(
        minutes=round(mins, 2),
        hits=len(hits), hits_per_min=round(len(hits) / mins, 1) if mins else 0,
        category_mix=mix,
        mean_level_vs_voice_db=round(float(np.mean([h["level_vs_voice_db"] for h in hits])), 1) if hits else None,
        median_level_vs_voice_db=round(float(np.median([h["level_vs_voice_db"] for h in hits])), 1) if hits else None,
        pct_hits_on_any_word=round(100 * len(on_word) / len(hits)) if hits else 0,
        pct_hits_on_key_words=round(100 * len(keyed) / len(hits)) if hits else 0,
        key_word_kinds=kinds,
        red_mean=round(float(np.mean([r["red_share"] for r in rows])), 4) if rows else 0,
        red_by_quarter=[round(float(x.mean()), 4) for x in q],
        pct_frames_red_over_5=round(100 * np.mean([r["red_share"] > 0.05 for r in rows]), 1) if rows else 0,
        brightness_mean=round(float(np.mean([r["brightness"] for r in rows])), 3) if rows else 0,
        top_other_hues=top_hues(rows),
        flashes_per_min=round(sum(bool(r["flash"]) for r in rows) / mins, 1) if mins else 0,
        color_shifts_per_min=round(sum(bool(r["color_shift"]) for r in rows) / mins, 1) if mins else 0,
        pct_visual_accents_on_hit=round(100 * np.mean([r["on_hit"] for r in accents])) if accents else 0,
        pct_hits_with_visual_accent=round(100 * hits_with_visual / len(hits)) if hits else 0,
        bed_dropouts=sum(e["type"] == "bed dropout" for e in a["bed_events"]),
        silences_over_1s=sum(e["type"] == "silence" for e in a["bed_events"]),
        bed_changes=sum(e["type"] == "bed change" for e in a["bed_events"]),
    )


def top_hues(rows):
    acc = {}
    for r in rows:
        if r["other_hue"] and r["other_share"] > 0.03:
            acc[r["other_hue"]] = acc.get(r["other_hue"], 0) + 1
    n = max(len(rows), 1)
    return {k: round(100 * c / n) for k, c in sorted(acc.items(), key=lambda x: -x[1])[:3]}


# ---------------------------------------------------------------- outputs

def write_csvs(results, out):
    with open(os.path.join(out, "hits.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["video", "time", "category", "level_vs_voice_db", "word",
                    "duration", "above_bed_db", "word_kinds", "channel", "title"])
        for r in results:
            for h in r["audio"]["hits"]:
                w.writerow([r["meta"]["id"], h["time"], h["category"], h["level_vs_voice_db"], h.get("word", ""),
                            h["duration"], h["above_bed_db"], h.get("word_kinds", ""),
                            r["meta"]["handle"], r["meta"]["title"]])
    with open(os.path.join(out, "color.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["video", "time", "red_share", "brightness", "other_hue", "other_share",
                    "flash", "color_shift", "coincides_with_hit"])
        for r in results:
            for fr in r["frames"]:
                w.writerow([r["meta"]["id"], fr["time"], round(fr["red_share"], 4), round(fr["brightness"], 3),
                            fr["other_hue"], round(fr["other_share"], 4), fr["flash"], fr["color_shift"],
                            int(fr["on_hit"])])


def fmt_t(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def video_section(r):
    m, s, a = r["meta"], r["summary"], r["audio"]
    L = [f"### {m['handle']} — {m['title']}",
         f"`{m['id']}` · {m['views']:,} views · {fmt_t(m['dur'])} · published {m['published']} · "
         f"captions: {'yes' if r['captions'] else 'NONE (word mapping skipped)'}", "",
         "| metric | value |", "|---|---|",
         f"| hits / min | {s['hits_per_min']} ({s['hits']} hits) |",
         f"| category mix | " + ", ".join(f"{k} {v}" for k, v in s["category_mix"].items() if v) + " |",
         f"| hit level vs voice (mean / median dB) | {s['mean_level_vs_voice_db']} / {s['median_level_vs_voice_db']} |",
         f"| music bed vs voice (median dB) | {a['bed_median_vs_voice_db']} |",
         f"| % hits on a key word (noun/verb/number/sentence end) | {s['pct_hits_on_key_words']}% "
         f"({', '.join(f'{k} {v}' for k, v in s['key_word_kinds'].items())}) |",
         f"| bed dropouts / bed changes / silences >1 s | {s['bed_dropouts']} / {s['bed_changes']} / {s['silences_over_1s']} |",
         f"| red share mean · by quarter | {s['red_mean']:.1%} · " + " → ".join(f"{x:.1%}" for x in s["red_by_quarter"]) + " |",
         f"| frames with >5% red | {s['pct_frames_red_over_5']}% |",
         f"| mean brightness | {s['brightness_mean']} |",
         f"| other strong hues (% of frames) | " + (", ".join(f"{k} {v}%" for k, v in s["top_other_hues"].items()) or "none") + " |",
         f"| flashes / min · colour shifts / min | {s['flashes_per_min']} · {s['color_shifts_per_min']} |",
         f"| visual accents landing on a sound hit | {s['pct_visual_accents_on_hit']}% |",
         f"| sound hits with a visual accent | {s['pct_hits_with_visual_accent']}% |", ""]
    loud = sorted([h for h in a["hits"] if h["category"] != "drone/bed change"],
                  key=lambda h: -h["level_vs_voice_db"])[:8]
    if loud:
        L += ["Loudest hits:", "", "| time | category | dB vs voice | dur | word |", "|---|---|---|---|---|"]
        L += [f"| {fmt_t(h['time'])} | {h['category']} | {h['level_vs_voice_db']} | {h['duration']} s | "
              f"{h.get('word', '')} {('(' + h['word_kinds'] + ')') if h.get('word_kinds') else ''} |" for h in sorted(loud, key=lambda h: h["time"])]
        L.append("")
    ev = [e for e in a["bed_events"] if e["type"] != "bed change"][:10]
    if ev:
        L += ["Bed dropouts / silences: " + "; ".join(f"{e['type']} at {fmt_t(e['time'])} ({e['duration']} s)" for e in ev), ""]
    L += ["Stills: " + ", ".join(f"[{x['file']}](frames/{x['file']}) ({x['why']}; red {x['red']:.0%}, {x['other']})"
                                 for x in r["stills"]), ""]
    return "\n".join(L)


def cross_channel(results):
    by_ch = {}
    for r in results:
        by_ch.setdefault(r["meta"]["handle"], []).append(r)
    # tier by views: top third of videos vs the rest
    vs = sorted(results, key=lambda r: -r["meta"]["views"])
    k = max(1, len(vs) // 3)
    top, rest = vs[:k], vs[k:]
    keys = ["hits_per_min", "mean_level_vs_voice_db", "pct_hits_on_key_words", "red_mean",
            "pct_frames_red_over_5", "flashes_per_min", "color_shifts_per_min",
            "pct_hits_with_visual_accent", "pct_visual_accents_on_hit", "silences_over_1s", "bed_dropouts"]
    def avg(group, key):
        vals = [g["summary"][key] for g in group if g["summary"][key] is not None]
        return round(float(np.mean(vals)), 3) if vals else None
    def mix(group):
        tot = {c: 0 for c in CATEGORIES}
        for g in group:
            for c, n in g["summary"]["category_mix"].items():
                tot[c] += n
        n = max(sum(tot.values()), 1)
        return {c: round(100 * v / n) for c, v in tot.items()}
    def kinds(group):
        tot, n = {}, 0
        for g in group:
            n += g["summary"]["hits"]
            for kk, v in g["summary"]["key_word_kinds"].items():
                tot[kk] = tot.get(kk, 0) + v
        return {kk: round(100 * v / max(n, 1)) for kk, v in tot.items()}
    def redq(group):
        return [round(float(np.mean([g["summary"]["red_by_quarter"][i] for g in group if len(g["summary"]["red_by_quarter"]) == 4])), 4)
                for i in range(4)] if group else []

    L = ["## Cross-channel summary", "",
         f"Top performers = the top third of analysed videos by views ({len(top)} videos, "
         f"≥{top[-1]['meta']['views']:,} views): " + ", ".join(f"{t['meta']['handle']} `{t['meta']['id']}`" for t in top) + ".", "",
         "| metric | all | top performers | the rest |", "|---|---|---|---|"]
    for key in keys:
        L.append(f"| {key} | {avg(results, key)} | {avg(top, key)} | {avg(rest, key)} |")
    ma, mt, mr = mix(results), mix(top), mix(rest)
    L += ["", "Category mix (% of all hits):", "", "| category | all | top | rest |", "|---|---|---|---|"]
    L += [f"| {c} | {ma[c]}% | {mt[c]}% | {mr[c]}% |" for c in CATEGORIES]
    kt, kr = kinds(top), kinds(rest)
    L += ["", "Share of hits landing on each word kind:", "", "| word kind | top | rest |", "|---|---|---|"]
    L += [f"| {kk} | {kt.get(kk, 0)}% | {kr.get(kk, 0)}% |" for kk in ["noun", "verb", "number", "sentence end"]]
    rq_t, rq_r = redq(top), redq(rest)
    L += ["", f"Red share by quarter of runtime — top: {' → '.join(f'{x:.1%}' for x in rq_t)}; "
              f"rest: {' → '.join(f'{x:.1%}' for x in rq_r)}", ""]
    L += ["Per-channel averages:", "", "| channel | videos | views (sum) | hits/min | dB vs voice | % on key words | red mean | flashes/min | % hits w/ visual |",
          "|---|---|---|---|---|---|---|---|---|"]
    for ch, g in sorted(by_ch.items(), key=lambda x: -sum(r["meta"]["views"] for r in x[1])):
        L.append(f"| {ch} | {len(g)} | {sum(r['meta']['views'] for r in g):,} | {avg(g, 'hits_per_min')} | "
                 f"{avg(g, 'mean_level_vs_voice_db')} | {avg(g, 'pct_hits_on_key_words')}% | {avg(g, 'red_mean'):.1%} | "
                 f"{avg(g, 'flashes_per_min')} | {avg(g, 'pct_hits_with_visual_accent')}% |")
    L += ["", "### Common patterns", ""]
    L += [f"- Median hit density across all videos: {np.median([r['summary']['hits_per_min'] for r in results]):.1f} hits/min.",
          f"- Most-used hit types overall: " + ", ".join(f"{c} ({ma[c]}%)" for c in sorted(ma, key=lambda c: -ma[c])[:3]) + ".",
          f"- Typical hit level: {np.median([r['summary']['median_level_vs_voice_db'] for r in results if r['summary']['median_level_vs_voice_db'] is not None]):+.1f} dB relative to the narrator.",
          f"- {np.mean([r['summary']['pct_hits_on_key_words'] for r in results]):.0f}% of hits land on a noun, verb, number or sentence end.",
          f"- Red covers on average {np.mean([r['summary']['red_mean'] for r in results]):.1%} of the frame; "
          f"{np.mean([r['summary']['pct_frames_red_over_5'] for r in results]):.0f}% of frames have >5% red.", ""]
    L += ["### What the top performers do differently", ""]
    diffs = []
    for key in keys:
        a, b = avg(top, key), avg(rest, key)
        if a is None or b is None:
            continue
        rel = (a - b) / (abs(b) + 1e-6)
        diffs.append((abs(rel), key, a, b))
    for _, key, a, b in sorted(diffs, reverse=True)[:6]:
        L.append(f"- **{key}**: {a} vs {b} ({'higher' if a > b else 'lower'} in top performers).")
    for c in CATEGORIES:
        if abs(mt[c] - mr[c]) >= 8:
            L.append(f"- Use of **{c}**: {mt[c]}% of hits in top performers vs {mr[c]}% elsewhere.")
    L += ["", "### 10 rules to copy (data-derived drafts — review before use)", ""]
    L += draft_rules(top, rest, mt, kt, rq_t, avg)
    return "\n".join(L)


def draft_rules(top, rest, mt, kt, rq_t, avg):
    """Turns the top-performer numbers into concrete, copyable rules."""
    first = sorted(mt, key=lambda c: -mt[c])
    lvl = [h["level_vs_voice_db"] for r in top for h in r["audio"]["hits"] if h["category"] != "drone/bed change"]
    lvl_lo, lvl_hi = (np.percentile(lvl, 25), np.percentile(lvl, 75)) if lvl else (0, 0)
    num_hits = [h for r in top for h in r["audio"]["hits"] if "number" in h.get("word_kinds", "")]
    num_cat = max(CATEGORIES, key=lambda c: sum(h["category"] == c for h in num_hits)) if num_hits else first[0]
    end_hits = [h for r in top for h in r["audio"]["hits"] if "sentence end" in h.get("word_kinds", "")]
    end_cat = max(CATEGORIES, key=lambda c: sum(h["category"] == c for h in end_hits)) if end_hits else first[1]
    peak_q = int(np.argmax(rq_t)) + 1 if rq_t else 4
    hues = {}
    for r in top:
        for k, v in r["summary"]["top_other_hues"].items():
            hues[k] = hues.get(k, 0) + v
    hue = max(hues, key=hues.get) if hues else "blue"
    return [
        f"1. **Density:** aim for ~{avg(top, 'hits_per_min')} sound hits per minute (top performers) — "
        f"others average {avg(rest, 'hits_per_min')}.",
        f"2. **Hit palette:** lead with {first[0]} ({mt[first[0]]}% of hits), then {first[1]} ({mt[first[1]]}%) and {first[2]} ({mt[first[2]]}%).",
        f"3. **Level:** mix hits {lvl_lo:+.0f} to {lvl_hi:+.0f} dB relative to the narrator; never bury the voice.",
        f"4. **Numbers:** put a {num_cat} under every rule number / count word "
        f"({kt.get('number', 0)}% of top-performer hits land on numbers).",
        f"5. **Sentence ends:** close key sentences with a {end_cat} on the last word "
        f"({kt.get('sentence end', 0)}% of hits land on a sentence end).",
        f"6. **Word targeting:** land {avg(top, 'pct_hits_on_key_words'):.0f}% of hits on a noun, verb, number or sentence end, not between words.",
        f"7. **Silence:** use ~{avg(top, 'silences_over_1s'):.0f} silences >1 s and ~{avg(top, 'bed_dropouts'):.0f} bed dropouts per video, "
        f"right before the reveal hit.",
        f"8. **Red curve:** keep red sparse early and let it peak in quarter {peak_q} of the runtime "
        f"(top-performer red by quarter: {' → '.join(f'{x:.1%}' for x in rq_t)}).",
        f"9. **Flashes:** ~{avg(top, 'flashes_per_min')} flashes/min; tie {avg(top, 'pct_hits_with_visual_accent'):.0f}% of sound hits to a flash or colour change.",
        f"10. **Second colour:** use {hue} as the secondary accent hue against the red (most common non-red strong hue in top performers).",
    ]


def write_report(results, out):
    order = sorted(results, key=lambda r: (r["meta"]["handle"], -r["meta"]["views"]))
    L = ["# Competitor analog-horror videos: sound design & colour", "",
         "Method: Demucs htdemucs (2 stems) → librosa onsets on the non-voice stem, kept only when ≥6 dB over "
         "the rolling 30th-percentile bed; levels are peak RMS (2048-sample frames) relative to the narrator's median "
         "active RMS. Words from YouTube auto-captions (±0.3 s; sentence end = word followed by a ≥0.6 s pause, since "
         "auto-captions have no punctuation). Frames at 2 fps (160 px wide): red = hue <15° or ≥345°, S>0.5, V>0.25; "
         "flash = brightness or red share jumps >25% between consecutive samples; colour shift = mean tint moves away "
         "from the previous 2 s. Sound/visual coincidence uses ±0.2 s plus half the 0.5 s frame step. "
         "Category labels come from simple spectral/envelope rules, so treat them as approximate.", "",
         "## Per-video results", ""]
    for r in order:
        L.append(video_section(r))
    L.append(cross_channel(results))
    open(os.path.join(out, "report.md"), "w").write("\n".join(L) + "\n")


def make_zip(out):
    zp = os.path.join(out, "competitor_sound_color.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in ["report.md", "hits.csv", "color.csv"]:
            z.write(os.path.join(out, f), f)
        for f in sorted(glob.glob(os.path.join(out, "frames", "*"))):
            z.write(f, os.path.join("frames", os.path.basename(f)))
    return zp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks", help="picks.json from pick_videos.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", help="temp folder (default: a new temp dir)")
    ap.add_argument("--keep-video", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    frames_dir = os.path.join(out, "frames")
    cache = os.path.join(out, "cache")
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(cache, exist_ok=True)
    if not args.report_only:
        work = args.work or tempfile.mkdtemp(prefix="ahorror_")
        for ch in json.load(open(args.picks)):
            for n, v in enumerate(ch.get("top2", []), 1):
                cp = os.path.join(cache, f"{v['id']}.json")
                if os.path.exists(cp):
                    continue
                v = dict(v, handle=ch["handle"], label=f"{ch['handle'].lstrip('@')}_v{n}")
                try:
                    res = analyse_video(v, work, frames_dir, args.keep_video)
                except Exception as e:  # keep going; the report lists what failed
                    print(f"!! {v['id']} failed: {e}", file=sys.stderr)
                    continue
                json.dump(res, open(cp, "w"))
        if not args.work and not args.keep_video:
            shutil.rmtree(work, ignore_errors=True)
    results = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(cache, "*.json")))]
    if not results:
        sys.exit("no analysed videos")
    write_csvs(results, out)
    write_report(results, out)
    print(make_zip(out))


if __name__ == "__main__":
    main()
