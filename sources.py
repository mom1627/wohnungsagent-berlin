"""Read housing listings from an explicitly configured, authorized JSON feed.

No scraping, login, CAPTCHA handling, or automatic applications.
Expected feed: JSON array of listings with agent.py fields.
"""
import json
import os
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

MAX_BYTES = 2_000_000

def load_feed(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Feed URL must use HTTPS")
    # Restrict feed hosts to explicit operator-approved allowlist.
    hosts = [h.strip().lower() for h in os.environ.get("FEED_ALLOWED_HOSTS", "").split(",") if h.strip()]
    if parsed.hostname.lower() not in hosts:
        raise ValueError("Feed host is not in FEED_ALLOWED_HOSTS")
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "WohnungsAgentBerlin/0.1"})
    with urlopen(req, timeout=20) as response:
        if urlsplit(response.geturl()).hostname.lower() not in hosts:
            raise ValueError("Feed redirect left approved hosts")
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Feed too large")
    items = json.loads(data.decode("utf-8"))
    if not isinstance(items, list):
        raise ValueError("Feed must be a JSON array")
    return items
