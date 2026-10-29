"""Turn raw.json (from collect.py) into videos.csv, new_channels.csv and tables.md. Costs 0 quota."""
import csv
import json
import re
import statistics as st
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from classify import classify, is_english

ROOT = Path(__file__).resolve().parent
TODAY = datetime(2026, 10, 28, tzinfo=timezone.utc)
NEW_SINCE = datetime(2025, 10, 28, tzinfo=timezone.utc)
WINDOW_ORDER = ["yoy90", "prev90", "last90"]
WINDOW_LABEL = {"yoy90": "2025-07-30→10-28", "prev90": "2026-05-01→07-29", "last90": "2026-07-30→10-28"}
STRONG_SUBS = 100_000

raw = json.loads((ROOT / "raw.json").read_text())
videos, channels, searches = raw["videos"], raw["channels"], raw["searches"]


def dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def seconds(iso):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


# ---- one row per video -------------------------------------------------------
hits = defaultdict(list)  # videoId -> [(window, query, rank)]
for key, s in searches.items():
    w, q = key.split("|", 1)
    for rank, vid in enumerate(s["ids"], 1):
        hits[vid].append((w, q, rank))

rows = {}
for vid, v in videos.items():
    sn, stt, cd = v["snippet"], v["statistics"], v["contentDetails"]
    ch = channels.get(sn["channelId"], {})
    cs = ch.get("statistics", {})
    dur = seconds(cd.get("duration"))
    text = (sn["title"] + " " + sn.get("description", "")).lower()
    pub = dt(sn["publishedAt"])
    hidden = cs.get("hiddenSubscriberCount", False)
    rows[vid] = {
        "video_id": vid,
        "window": hits[vid][0][0],
        "queries": ";".join(sorted({q for _, q, _ in hits[vid]})),
        "title": sn["title"],
        "url": f"https://www.youtube.com/watch?v={vid}",
        "published": sn["publishedAt"][:10],
        "age_days": max((TODAY - pub).days, 1),
        "duration_s": dur,
        "is_short": int(dur <= 180 or "#short" in text),
        "views": int(stt.get("viewCount", 0)),
        "likes": int(stt["likeCount"]) if "likeCount" in stt else "",
        "comments": int(stt["commentCount"]) if "commentCount" in stt else "",
        "channel_id": sn["channelId"],
        "channel": sn["channelTitle"],
        "subscribers": "" if hidden else int(cs.get("subscriberCount", 0)),
        "channel_created": ch.get("snippet", {}).get("publishedAt", "")[:10],
        "channel_videos": int(cs.get("videoCount", 0)) if cs else "",
        "description": sn.get("description", "")[:500].replace("\n", " "),
        "category": classify(sn["title"], sn.get("description", "")),
        "english": int(is_english(sn["title"], sn)),
    }
    r = rows[vid]
    r["views_per_day"] = round(r["views"] / r["age_days"], 1)
    r["ratio"] = round(r["views"] / r["subscribers"], 2) if r["subscribers"] else ""

with open(ROOT / "videos.csv", "w", newline="") as f:
    cols = list(next(iter(rows.values())).keys())
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in sorted(rows.values(), key=lambda r: (r["window"], -r["views"])):
        w.writerow(r)

out = []


def table(headers, data):
    out.append("| " + " | ".join(headers) + " |")
    out.append("|" + "|".join("---" for _ in headers) + "|")
    for d in data:
        out.append("| " + " | ".join(str(x) for x in d) + " |")
    out.append("")


def fmt(n):
    return f"{n:,.0f}"


# ---- step 4: per window x query ---------------------------------------------
CORE = {v for v, r in rows.items() if r["category"] == "core_prep" and r["english"]}


def stats(ids, core_only=True):
    rs = [rows[i] for i in ids if i in rows and (i in CORE or not core_only)]
    if not rs:
        return dict(n=0, over50k=0, median=0, shorts=0, chans=0, median_vpd=0)
    return dict(
        n=len(rs),
        over50k=sum(r["views"] > 50_000 for r in rs),
        median=st.median(r["views"] for r in rs),
        shorts=sum(r["is_short"] for r in rs) / len(rs),
        chans=len({r["channel_id"] for r in rs}),
        median_vpd=st.median(r["views_per_day"] for r in rs),
    )


out.append("### 0. What the searches actually return (share of unique videos, all 16 queries) — measured; "
           "categories are keyword-classified (≈90% precision on an 80-video hand audit — estimated)\n")
mix = []
for w in WINDOW_ORDER:
    rs = [r for r in rows.values() if r["window"] == w]
    n = len(rs)
    c = lambda f: sum(1 for r in rs if f(r))
    mix.append([w, n, f"{c(lambda r: r['category'] == 'core_prep' and r['english'])/n:.0%}",
                f"{c(lambda r: r['category'] == 'bushcraft')/n:.0%}", f"{c(lambda r: r['category'] == 'off_topic')/n:.0%}",
                f"{c(lambda r: not r['english'])/n:.0%}",
                f"{sum(r['views'] for r in rs if r['category'] == 'bushcraft')/max(sum(r['views'] for r in rs), 1):.0%}"])
table(["Window", "Unique videos", "Core prep (English)", "Wilderness/bushcraft", "Off-topic", "Non-English",
       "Bushcraft share of views"], mix)
out.append("**All tables below use core-prep English videos only** unless stated.\n")

summary = {}
for w in WINDOW_ORDER:
    ids = sorted({v for k, s in searches.items() if k.startswith(w + "|") for v in s["ids"]})
    rs = [rows[i] for i in ids if i in CORE]
    total = sum(r["views"] for r in rs)
    top5 = sum(sorted((r["views"] for r in rs), reverse=True)[:5]) / max(total, 1)
    summary[w] = dict(stats(ids), total=total, top5=top5)

out.append("### 4a. Window totals (unique core-prep videos across all 16 queries) — measured\n")
table(["Window", "Unique videos", ">50K views", "Median views", "Total views", "Median views/day",
       "Shorts share", "Distinct channels", "Top-5 videos' share of total views"],
      [[f"{w} ({WINDOW_LABEL[w]})", s["n"], s["over50k"], fmt(s["median"]), fmt(s["total"]),
        fmt(s["median_vpd"]), f"{s['shorts']:.0%}", s["chans"], f"{s['top5']:.0%}"]
       for w, s in summary.items()])

per_q = {}
for key, s in searches.items():
    w, q = key.split("|", 1)
    per_q[(q, w)] = stats(s["ids"])
queries = list(dict.fromkeys(k.split("|", 1)[1] for k in searches))
out.append("### 4b. Per query: core-prep videos inside each top-50 result set — measured (YoY = last90 median ÷ yoy90 median)\n")
data = []
for q in queries:
    a, b, c = per_q[(q, "yoy90")], per_q[(q, "prev90")], per_q[(q, "last90")]
    yoy = c["median"] / a["median"] if a["median"] else float("nan")
    data.append([q,
                 f"{a['over50k']} / {b['over50k']} / {c['over50k']}",
                 f"{fmt(a['median'])} / {fmt(b['median'])} / {fmt(c['median'])}",
                 f"{yoy:.2f}×",
                 f"{a['shorts']:.0%} / {b['shorts']:.0%} / {c['shorts']:.0%}",
                 f"{a['chans']} / {b['chans']} / {c['chans']}",
                 f"{a['n']} / {b['n']} / {c['n']}"])
table(["Query", ">50K (yoy/prev/last)", "Median views (yoy/prev/last)", "YoY median",
       "Shorts share", "Distinct channels", "Core-prep videos of 50 (yoy/prev/last)"], data)
qup = sum(per_q[(q, "last90")]["median"] > per_q[(q, "yoy90")]["median"] for q in queries)
q50 = sum(per_q[(q, "last90")]["over50k"] > per_q[(q, "yoy90")]["over50k"] for q in queries)
out.append(f"Queries where last-90 median beats year-ago median: **{qup}/16**; "
           f"where last-90 >50K count beats year-ago: **{q50}/16** (measured).\n")

# ---- themes (used by steps 5-7) ----------------------------------------------
THEMES = [
    ("what to buy / stockpile lists", r"\bbuy\b|before it'?s too late|stock ?up|stockpil|hoard|disappear\w* from|"
                                      r"run out first|\bshortage|must[- ]have|worth gold|dollar tree|walmart|costco|"
                                      r"sam'?s club|hobby lobby|\bitems\b|\bthings (to|every|you)|\d+ (foods|items|"
                                      r"tools|things|groceries|appliances)"),
    ("scenario / fiction", r"what (would|will) happen|what if|\bhow (long )?would you survive|\bfiction|"
                           r"\bstory\b|\bstories\b|\bdays? (to|without)\b|\bhours? without\b|\b\d+ (year|day)s?\b.*surviv|"
                           r"surviv\w* .*\b\d+ (year|day)s?\b|what happens (if|when)|\bscenario|\bhypothetical|"
                           r"\bgo dark first|\branked\b"),
    ("grid / power", r"\bgrid\b|power outage|blackout|\bemp\b|solar flare|\bgenerator|power station|"
                     r"backup power|power (is|goes) out|lose power|without power|no power|ecoflow|froze an entire"),
    ("specific disasters", r"hurricane|earthquake|wildfire|tornado|flood|tsunami|volcan|typhoon|"
                           r"evacuat|blizzard|\bquake\b|\bfault\b|new madrid|\bfire\b"),
    ("government / news-driven", r"\bfema\b|\bgovernment\b|\bwarn|\bofficial|\bnews\b|\bbreaking\b|\balert\b|"
                                 r"\bdhs\b|\bpentagon\b|\bwar\b|\bnuclear\b|\bnato\b|\brussia|\bchina|\biran\b|"
                                 r"\bmilitary\b|\btrump\b|\bcongress\b|\bpresident\b|\bcollapse\b|\bcrisis\b|\beconom|"
                                 r"\buk\b|britain|white house"),
    ("food storage", r"\bfood\b|pantry|canning|\bcanned\b|freeze[- ]?dr|\brice\b|\bbeans\b|"
                     r"long[- ]term storage|mylar|\bmre\b|water storage|\bstorage\b|famine"),
    ("bug-out / go-bag / kits", r"bug ?out|go[- ]?bag|72[- ]?h|\bedc\b|every ?day carry|get home bag|"
                                r"emergency kit|survival kit|first ?aid|\bifak\b|\bkit\b|emegencykit"),
    ("gear reviews", r"\breview\b|\bgear\b|\btest(ed|ing)?\b|\bvs\.?\b|\bbest\b|\bunboxing|\bknife\b|"
                     r"\bflashlight|\bfilter\b|\btent\b|\bstove\b|\bgadget|\bamazon\b|\btool\b|\bradio\b"),
    ("bunkers / off-grid / homestead", r"off[- ]?grid|homestead|\bbunker|\bcabin\b|\bshelter\b|\bsurvival\b"),
]


def theme(title):
    t = title.lower()
    for name, pat in THEMES:
        if re.search(pat, t):
            return name
    return "other / unclassified"


# ---- step 5: new entrants ------------------------------------------------------
FACELESS = r"\bai\b|animat|narrat|documentar|explained|\bwhat if\b|stories|\bstory\b|compilation|\bfacts\b|" \
           r"\btop \d+|\bhistory\b|cinematic|\bsimulat|faceless|minecraft|\bvoice ?over|\bnews\b|\bpodcast\b"
ON_CAMERA = r"\bi\b|\bi'm\b|\bmy\b|\bme\b|\bwe\b|\bour\b|\bvlog|\bfamily\b|homestead|\bwife\b|\bhusband\b|" \
            r"\bkids\b|\bjoin me\b|\bwith me\b|\bi'?ve\b|\bshowing you\b"


def faceless_guess(title, desc, chdesc):
    t = " ".join([title, desc, chdesc]).lower()
    f, o = len(re.findall(FACELESS, t)), len(re.findall(ON_CAMERA, t))
    if f > o:
        return "faceless (guess)"
    if o > f:
        return "on-camera (guess)"
    return "unclear (guess)"


# Hand-judged from channel + video descriptions (still a guess: no video was watched). Overrides the heuristic.
MANUAL_FACELESS = {
    "UC672i5aQ_l5XrKSYZM75A9A": "faceless: re-cut clips of military podcasts (manual guess)",
    "FAK_NETWORK": "faceless: product B-roll Shorts from one seller (manual guess)",
    "UCyXAbzVT0HzkuhntnxaP1Ow": "faceless: animated scenarios (manual guess)",
    "UC4txvlt0VzrbwdFfzfeSiRQ": "faceless: facts + voice-over (manual guess)",
    "UCLp9A7kQlD3ma75fGwPJlTw": "unclear (manual guess)",
    "UChcEGagsoreavgb1jmKDhhg": "faceless: narrated listicles (manual guess, low confidence)",
    "UCEYdflFM96OJDEMtNdG7WLw": "faceless: animated survival story (manual guess)",
    "UC19O5ANzU-Zsi-rT8tAuO1A": "faceless: narrated document breakdowns (manual guess)",
    "UCAbcCunwVOr2yZpOTlC7NlA": "unclear: 'Bob' mascot/persona (manual guess)",
    "UCJg9vswGbZoRTXGG1D94o8g": "on-camera: lifestyle creator (manual guess)",
    "UCE81eiSO8oNur9phe57qxMQ": "faceless: data/ranking explainer (manual guess)",
    "UCw55hwfi1-iaro-x4cBR-4g": "on-camera: personal vlog (manual guess)",
}


def entity(cid):
    """Channels run by one first-aid-kit seller (same WhatsApp number / name) are counted as one entrant."""
    ch = channels.get(cid, {}).get("snippet", {})
    if "8613378436948" in ch.get("description", "") or ch.get("title", "").lower().startswith("first aid kit"):
        return "FAK_NETWORK"
    return cid


last90 = [r for v, r in rows.items() if r["window"] == "last90" and v in CORE]
by_ch = defaultdict(list)
for r in last90:
    if r["channel_created"] and dt(r["channel_created"] + "T00:00:00Z") >= NEW_SINCE:
        by_ch[entity(r["channel_id"])].append(r)
new = []
for cid, rs in by_ch.items():
    rs.sort(key=lambda r: -r["views"])
    if rs[0]["views"] <= 100_000:
        continue
    best = rs[0]
    chdesc = channels.get(best["channel_id"], {}).get("snippet", {}).get("description", "")
    members = sorted({r["channel_id"] for r in rs})
    subs = [rows_ch["subscribers"] for rows_ch in {r["channel_id"]: r for r in rs}.values()]
    new.append({
        "channel": best["channel"].strip() + (f" (network of {len(members)} channels)" if len(members) > 1 else ""),
        "channel_id": ";".join(members),
        "channel_url": f"https://www.youtube.com/channel/{best['channel_id']}",
        "subscribers": sum(x for x in subs if x != ""),
        "created": min(r["channel_created"] for r in rs),
        "uploads": sum(int(channels[c]["statistics"].get("videoCount", 0)) for c in members),
        "found_videos_last90": len(rs), "found_views_last90": sum(r["views"] for r in rs),
        "best_title": best["title"], "best_views": best["views"], "best_url": best["url"],
        "best_is_short": best["is_short"], "theme": theme(best["title"]),
        "faceless_guess": MANUAL_FACELESS.get(cid) or faceless_guess(best["title"], best["description"], chdesc),
        "channel_description": chdesc[:300].replace("\n", " "),
    })
new.sort(key=lambda r: -r["found_views_last90"])
with open(ROOT / "new_channels.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(new[0].keys()) if new else ["channel"])
    w.writeheader()
    w.writerows(new)

out.append(f"### 5. New entrants — channels created on/after 2025-10-28 with a >100K-view core-prep video in the last 90 days\n")
out.append(f"Qualifying channels found: **{len(new)}** (measured). Ranked by summed views of their videos in our "
           f"last-90 sample. The 'First aid kit…' channels (same name, one shared WhatsApp contact) and are merged into one "
           f"row (subs/uploads summed). Faceless/on-camera is judged from titles + descriptions only — a guess.\n")
table(["#", "Channel", "Subs", "Created", "Uploads", "Best video", "Views", "Short?", "Faceless? (guess)"],
      [[i, n["channel"].replace("|", "/"), fmt(n["subscribers"]) if n["subscribers"] != "" else "hidden", n["created"], n["uploads"],
        f"[{n['best_title'][:70].replace('|', '/')}]({n['best_url']})", fmt(n["best_views"]),
        "Y" if n["best_is_short"] else "N", n["faceless_guess"]]
       for i, n in enumerate(new[:15], 1)])

# ---- step 6: outliers ----------------------------------------------------------
outl = [r for r in last90 if r["subscribers"] and r["views"] > 5 * r["subscribers"]]
outl.sort(key=lambda r: -r["views"])
out.append(f"### 6. Outliers — last-90 core-prep videos with views > 5× channel subscribers\n")
out.append(f"Outliers: **{len(outl)}** of {len(last90)} last-90 videos ({len(outl)/len(last90):.0%}), measured. "
           f"Top 20 ranked by views (ranking by raw ratio is dominated by <100-sub channels).\n")
table(["#", "Title", "Views", "Subs", "Ratio", "Short?", "Theme"],
      [[i, f"[{r['title'][:75].replace('|', '/')}]({r['url']})", fmt(r["views"]), fmt(r["subscribers"]),
        f"{r['ratio']:.0f}×", "Y" if r["is_short"] else "N", theme(r["title"])]
       for i, r in enumerate(outl[:20], 1)])

# ---- step 7: themes ------------------------------------------------------------
pool = {r["video_id"]: r for r in outl}
for n in new:
    for r in by_ch[n["channel_id"]]:
        pool[r["video_id"]] = r
th = defaultdict(list)
for r in pool.values():
    th[theme(r["title"])].append(r)
all_th = defaultdict(list)
for r in last90:
    all_th[theme(r["title"])].append(r)

out.append("### 7. Topic clusters — outlier + new-entrant videos, last 90 days (themes are keyword-assigned, "
           "one theme per video, first match wins)\n")
data = []
for name, rs in sorted(th.items(), key=lambda kv: -sum(r["views"] for r in kv[1])):
    a = all_th[name]
    strong = {r["channel_id"] for r in a if r["subscribers"] and r["subscribers"] >= STRONG_SUBS}
    ratios = [r["ratio"] for r in a if r["ratio"] != ""]
    data.append([name, len(rs), fmt(sum(r["views"] for r in rs)), len({r["channel_id"] for r in rs}),
                 f"{sum(r['is_short'] for r in rs)/len(rs):.0%}",
                 len(a), f"{sum(1 for x in ratios if x > 5)/len(a):.0%}",
                 f"{st.median(ratios):.2f}×" if ratios else "–", len(strong),
                 f"[{max(rs, key=lambda r: r['views'])['title'][:55].replace('|', '/')}]"
                 f"({max(rs, key=lambda r: r['views'])['url']})"])
table(["Theme", "Outlier+new videos", "Their views", "Channels", "Shorts share",
       "All last-90 videos in theme", "Outlier rate", "Median views/subs", "Channels ≥100K subs in theme",
       "Top video"], data)

# ---- gap inputs: per subtopic (query), last 90 days, core-prep only -----------
out.append("### 9a. Gap inputs per subtopic — last 90 days, core-prep videos in each query's top 50 — measured\n")
newc = {c for n in new for c in n["channel_id"].split(";")}
data = []
for q in queries:
    rs = [rows[i] for i in searches[f"last90|{q}"]["ids"] if i in CORE]
    if not rs:
        continue
    tot = sum(r["views"] for r in rs)
    chv = defaultdict(int)
    for r in rs:
        chv[r["channel_id"]] += r["views"]
    rat = [r["ratio"] for r in rs if r["ratio"] != ""]
    yoy = per_q[(q, "yoy90")]["median"]
    data.append([q, len(rs), fmt(st.median(r["views"] for r in rs)),
                 f"{per_q[(q, 'last90')]['median']/yoy:.2f}×" if yoy else "–",
                 f"{sum(1 for x in rat if x > 5)/len(rs):.0%}",
                 len({r["channel_id"] for r in rs if r["subscribers"] and r["subscribers"] >= STRONG_SUBS}),
                 f"{max(chv.values())/tot:.0%}" if tot else "–",
                 len({r["channel_id"] for r in rs} & newc),
                 f"{sum(r['is_short'] for r in rs)/len(rs):.0%}"])
table(["Subtopic (query)", "Core videos", "Median views", "YoY median", "Outlier rate (>5× subs)",
       "Channels ≥100K subs", "Top channel's view share", "New-entrant channels", "Shorts share"], data)

(ROOT / "tables.md").write_text("\n".join(out))
json.dump({"summary": summary, "qup": qup, "q50": q50, "n_new": len(new), "n_outl": len(outl),
           "n_last90": len(last90)}, open(ROOT / "cache" / "analysis_summary.json", "w"), indent=1, default=str)
print("\n".join(out))
