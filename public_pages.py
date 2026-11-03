"""Conservative read-only extractor for explicitly configured public listing pages.

Only reads schema.org JSON-LD. No logins, scraping around access restrictions,
or automatic application submissions. Requires approved exact hostnames.
"""
import json
import os
from html.parser import HTMLParser
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

class JsonLdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.blocks = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script" and dict(attrs).get("type", "").lower() == "application/ld+json":
            self.active = True
            self.parts = []

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.active:
            self.blocks.append("".join(self.parts))
            self.active = False

def extract_jsonld(html):
    parser = JsonLdParser()
    parser.feed(html)
    objects = []
    for block in parser.blocks:
        try:
            value = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(value, list):
            objects.extend(value)
        else:
            objects.append(value)
    return objects

def fetch_public_page(url, approved_hosts):
    parts = urlsplit(url)
    hosts = {host.strip().lower() for host in approved_hosts.split(",") if host.strip()}
    if parts.scheme != "https" or parts.hostname not in hosts:
        raise ValueError("Public URL must use HTTPS and an explicitly approved host")
    req = Request(url, headers={"User-Agent": "WohnungsAgentBerlin/0.1 (read-only; contact repository owner)"})
    with urlopen(req, timeout=15) as response:
        final = urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname not in hosts:
            raise ValueError("Redirect outside approved hosts")
        data = response.read(1_000_001)
    if len(data) > 1_000_000:
        raise ValueError("Page exceeds size limit")
    return extract_jsonld(data.decode("utf-8", errors="replace"))

def main():
    urls = [u.strip() for u in os.environ.get("PUBLIC_LISTING_URLS", "").splitlines() if u.strip()]
    hosts = os.environ.get("PUBLIC_ALLOWED_HOSTS", "")
    if not urls:
        print("No public listing URLs configured; no pages accessed.")
        return
    for url in urls[:20]:
        try:
            blocks = fetch_public_page(url, hosts)
            print(json.dumps({"url": url, "structured_blocks": len(blocks),
                              "status": "metadata-only; no application submitted"}, ensure_ascii=False))
        except Exception as exc:
            print(json.dumps({"url": url, "error": str(exc)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
