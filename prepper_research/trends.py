"""Google Trends (pytrends), US, past 5 years. Cached to cache/trends.csv; skips cleanly if blocked."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "cache" / "trends.csv"
TERMS = ["prepping", "emergency preparedness", "power outage", "bug out bag", "food storage"]

if OUT.exists():
    print("cached"); sys.exit(0)
try:
    from pytrends.request import TrendReq
    py = TrendReq(hl="en-US", tz=300, timeout=(10, 30), retries=2, backoff_factor=1)
    py.build_payload(TERMS, timeframe="today 5-y", geo="US")
    df = py.interest_over_time()
    if df.empty:
        raise RuntimeError("empty response")
    df.to_csv(OUT)
    print(f"ok rows={len(df)}")
except Exception as e:
    (ROOT / "cache" / "trends_error.txt").write_text(repr(e))
    print(f"Trends skipped: {e!r}")
