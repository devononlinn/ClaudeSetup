"""Collect YouTube search/video/channel data for the prepper niche study.

Every API response is cached in ./cache/ keyed by request params, so reruns
cost 0 quota. A running quota ledger is written to cache/quota_ledger.json.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)
API = "https://www.googleapis.com/youtube/v3/"
KEY = os.environ.get("YT_API_KEY")  # if unset, the environment's proxy authenticates
BUDGET = 8000
COST = {"search": 100, "videos": 1, "channels": 1}

QUERIES = [
    "prepper", "prepping", "doomsday prep", "power grid failure", "grid down",
    "emergency preparedness", "bug out bag", "go bag", "72 hour kit",
    "food storage prepping", "garage prepper", "earthquake preparedness",
    "hurricane prep", "wildfire evacuation", "EMP prep", "off grid survival",
]
WINDOWS = {
    "last90": ("2026-07-30T00:00:00Z", "2026-10-29T00:00:00Z"),
    "yoy90": ("2025-07-30T00:00:00Z", "2025-10-29T00:00:00Z"),
    "prev90": ("2026-05-01T00:00:00Z", "2026-07-30T00:00:00Z"),
}

ledger_path = CACHE / "quota_ledger.json"
ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"spent": 0, "calls": []}


class QuotaExceeded(Exception):
    pass


def call(endpoint, params):
    key = hashlib.sha1(json.dumps([endpoint, params], sort_keys=True).encode()).hexdigest()[:16]
    path = CACHE / f"{endpoint}_{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    if ledger["spent"] + COST[endpoint] > BUDGET:
        raise QuotaExceeded(f"budget {BUDGET} would be exceeded")
    q = dict(params)
    if KEY:
        q["key"] = KEY
    r = requests.get(API + endpoint, params=q, timeout=60)
    ledger["spent"] += COST[endpoint]
    ledger["calls"].append({"endpoint": endpoint, "status": r.status_code, "cache": path.name})
    ledger_path.write_text(json.dumps(ledger, indent=1))
    data = r.json()
    if r.status_code != 200:
        reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "")
        if reason in ("quotaExceeded", "dailyLimitExceeded"):
            raise QuotaExceeded(reason)
        raise RuntimeError(f"{endpoint} {r.status_code}: {data}")
    path.write_text(json.dumps({"params": params, "response": data}))
    return {"params": params, "response": data}


def chunks(xs, n=50):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def main():
    searches = {}  # (window, query) -> [videoId, ...] in rank order
    incomplete = []
    try:
        for w, (after, before) in WINDOWS.items():
            for q in QUERIES:
                d = call("search", {
                    "part": "snippet", "q": q, "type": "video", "order": "viewCount",
                    "maxResults": 50, "regionCode": "US", "relevanceLanguage": "en",
                    "publishedAfter": after, "publishedBefore": before,
                })["response"]
                searches[f"{w}|{q}"] = {
                    "ids": [it["id"]["videoId"] for it in d.get("items", [])],
                    "totalResults": d.get("pageInfo", {}).get("totalResults"),
                }
    except QuotaExceeded as e:
        incomplete.append(f"search stopped: {e}")

    vids = sorted({v for s in searches.values() for v in s["ids"]})
    videos = {}
    try:
        for c in chunks(vids):
            d = call("videos", {"part": "snippet,statistics,contentDetails", "id": ",".join(c), "maxResults": 50})
            for it in d["response"].get("items", []):
                videos[it["id"]] = it
    except QuotaExceeded as e:
        incomplete.append(f"videos stopped: {e}")

    chans = sorted({v["snippet"]["channelId"] for v in videos.values()})
    channels = {}
    try:
        for c in chunks(chans):
            d = call("channels", {"part": "snippet,statistics", "id": ",".join(c), "maxResults": 50})
            for it in d["response"].get("items", []):
                channels[it["id"]] = it
    except QuotaExceeded as e:
        incomplete.append(f"channels stopped: {e}")

    (ROOT / "raw.json").write_text(json.dumps(
        {"searches": searches, "videos": videos, "channels": channels, "incomplete": incomplete}))
    print(f"searches={len(searches)} videos={len(videos)} channels={len(channels)} "
          f"quota_spent_total={ledger['spent']} incomplete={incomplete}")
    return 1 if incomplete else 0


if __name__ == "__main__":
    sys.exit(main())
