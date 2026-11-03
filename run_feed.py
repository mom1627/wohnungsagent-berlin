"""Manual/scheduled source screening.

The GitHub Actions runner is ephemeral. Persist deduplication separately
before enabling notifications; this script intentionally reports candidates
without sending notifications or applications.
"""
import json
import os
import sys
from agent import eligible, canonical_url
from sources import load_feed

def main():
    url = os.environ.get("HOUSING_FEED_URL")
    if not url:
        print("No authorized feed configured; nothing to check.")
        return
    listings = load_feed(url)
    seen = set()
    matches = []
    for item in listings:
        if eligible(item):
            key = canonical_url(item["url"])
            if key not in seen:
                seen.add(key)
                matches.append(item)
    print(json.dumps({"candidate_count": len(matches), "candidates": matches},
                     ensure_ascii=False, indent=2))
    print("No applications submitted; candidates require source verification.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Feed screening failed: {exc}", file=sys.stderr)
        sys.exit(1)
