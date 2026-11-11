"""WohnungsAgent Berlin: conservative listing screening and deduplication.
Input: JSON array of listings from permitted sources. No scraping or applications.
"""
import argparse
import datetime as dt
import json
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from berlin_location import district_name
MAX_WARM = 550.0

def canonical_url(url):
    parts = urlsplit(url.strip())
    if parts.scheme not in ("https", "http") or not parts.netloc:
        raise ValueError("Valid listing URL required")
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path.rstrip("/"), "", ""))

def eligible(item):
    """Unknown costs, WBS eligibility, availability or fees are not auto-approved."""
    try:
        rent = float(item["warm_rent_eur"])
        rooms = float(item["rooms"])
        area = str(item["district"]).casefold()
        url = canonical_url(item["url"])
        wbs = item["wbs_100_eligible"] is True
        available = item["application_open"] is True
        upfront = float(item.get("cooperative_entry_eur", 0))
        cap = float(item.get("max_cooperative_entry_eur", 500))
    except (KeyError, ValueError, TypeError):
        return False
    return (0 < rent <= MAX_WARM and rooms in (1, 2) and
            (area == "berlin" or district_name(area) is not None) and wbs and available and
            upfront <= cap and bool(url))

def run(listings, db_path):
    with sqlite3.connect(db_path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS seen (url TEXT PRIMARY KEY, first_seen TEXT NOT NULL)")
        fresh = []
        for item in listings:
            if not eligible(item):
                continue
            url = canonical_url(item["url"])
            cursor = db.execute("INSERT OR IGNORE INTO seen VALUES (?, ?)",
                                (url, dt.datetime.now(dt.timezone.utc).isoformat()))
            if cursor.rowcount:
                fresh.append(item)
        db.commit()
    return fresh

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="JSON array of verified listings")
    parser.add_argument("--db", type=Path, default=Path("seen.sqlite3"))
    args = parser.parse_args()
    listings = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(listings, list):
        parser.error("Input must be a JSON array")
    print(json.dumps(run(listings, args.db), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
