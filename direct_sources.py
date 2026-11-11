"""Independent discovery through providers' ordinary public search pages."""
import asyncio
import json
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from lxml import html

from collect_inberlinwohnen import UA
from provider_registry import canonical_offer, provider_for
from public_access import check_robots


@dataclass(frozen=True)
class Source:
    provider: str
    url: str
    cards: str
    link: str
    offer_path: str
    next_link: str
    empty: str
    price_before_label: bool = False


SOURCES = (
    Source("degewo", "https://www.degewo.de/immosuche",
           "//*[contains(@class,'c-teaser--apartment')]",
           ".//a[contains(@href,'/immosuche/details/')]", r"/immosuche/details/[^/]+/?",
           "//a[contains(@class,'c-pagination__link--next')]",
           r"\b0 Ergebnisse\b|keine Immobilien gefunden", True),
    Source("gesobau", "https://www.gesobau.de/mieten/wohnungssuche/",
           "//article[contains(@class,'basicTeaser') and contains(@class,' apartment')]",
           ".//a[contains(@href,'/wohnungssuche/detailseite/')]", r"/mieten/wohnungssuche/detailseite/[^/]+/?",
           "//nav[contains(@class,'solr-pagination')]//li[last()]/a[not(normalize-space(text()))]",
           r"\b0 freie Wohnungen\b|keine Ergebnisse"),
    Source("wbm", "https://www.wbm.de/wohnungen-berlin/angebote/",
           "//*[contains(@class,'openimmo-search-list-item')]",
           ".//a[contains(@class,'immo-button-cta')]", r"/wohnungen-berlin/angebote/details/.+",
           "//a[@rel='next']", r"\b0 Mietwohnungen\b|derzeit keine (?:freien |verfügbaren )?(?:Mietwohnungen|Wohnungen|Wohnungsangebote)", True),
    Source("berlinovo", "https://www.berlinovo.de/de/wohnungen/suche",
           "//article[contains(@class,'node--type-apartment')]",
           ".//a[starts-with(@href,'/wohnung-id/')]", r"/wohnung-id/[\d-]+/?",
           "//a[@rel='next']", r"\b0 Ergebnisse gefunden\b|keine Ergebnisse"),
)

def public_url(source, url, *, detail=False):
    try:
        parsed = urlsplit(url)
        if provider_for(url) != source.provider:
            return False
        pattern = source.offer_path if detail else re.escape(urlsplit(source.url).path.rstrip("/")) + "/?"
        return bool(re.fullmatch(pattern, parsed.path))
    except (ValueError, TypeError, AttributeError):
        return False


def card_record(source, card, page_number):
    url = card.get("url")
    text = " ".join((card.get("text") or "").split())
    if not url or not text or not public_url(source, url, detail=True):
        return None
    # These two observed layouts display their explicit warm-rent label after the value.
    if source.price_before_label:
        text = re.sub(r"([\d.]+,\d{2}\s*€)\s*Warmmiete\b", r"Warmmiete \1", text, flags=re.I)
    return {"url": url, "provider": source.provider, "source": source.url,
            "source_page": page_number, "source_text": text[:10000],
            "title": (card.get("title") or "").strip(), "candidate_origin": "direct_provider"}


class SourceFailure(Exception):
    pass


class SourceRedirect(HTTPRedirectHandler):
    def __init__(self, source, robots):
        self.source, self.robots = source, robots

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not public_url(self.source, newurl):
            raise SourceFailure("unexpected_redirect")
        check_robots(newurl, self.robots)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_page(source, url, robots):
    if not public_url(source, url):
        raise SourceFailure("unexpected_search_link")
    check_robots(url, robots)
    with build_opener(SourceRedirect(source, robots)).open(
            Request(url, headers={"User-Agent": UA}), timeout=12) as response:
        body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise SourceFailure("response_too_large")
        return html.fromstring(body, base_url=response.geturl())


async def public_page(source, url, robots):
    for attempt in range(2):
        try:
            return await asyncio.to_thread(fetch_page, source, url, robots)
        except HTTPError as exc:
            # Rate limits and access denials are reported without another request.
            if exc.code not in {500, 502, 503, 504} or attempt:
                raise SourceFailure(f"http_{exc.code}") from None
        except (URLError, TimeoutError):
            if attempt:
                raise SourceFailure("network_error_or_timeout") from None
        await asyncio.sleep(2 ** attempt)


def node_text(element):
    return " ".join(" ".join(element.xpath(".//text()[not(ancestor::script or ancestor::style)]")).split())


def read_cards(source, document):
    for element in document.xpath(source.cards):
        links = element.xpath(source.link)
        if not links:
            yield {}
            continue
        title = element.xpath(".//h2|.//h3|.//h4|.//*[contains(@class,'field--name-title')]")
        yield {"url": urljoin(document.base_url, links[0].get("href")), "text": node_text(element),
               "title": node_text(title[0]) if title else ""}


async def collect_source(source, *, max_pages=30):
    report = {"source": source.url, "complete": False, "stop_reason": "page_limit",
              "pages_checked": 0, "count": 0, "listings": []}
    try:
        url, visited, seen, robots = source.url, set(), set(), {}
        for number in range(1, max_pages + 1):
            if url in visited:
                raise SourceFailure("pagination_cycle")
            visited.add(url)
            document = await public_page(source, url, robots)
            cards = list(read_cards(source, document))
            records = [record for card in cards if (record := card_record(source, card, number))]
            if not records:
                body = node_text(document)
                if re.search(r"verify you are human|checking your browser|automated traffic", body, re.I):
                    raise SourceFailure("manual_security_check")
                if cards or number > 1 or not re.search(source.empty, body, re.I):
                    raise SourceFailure("listing_layout_unrecognized")
            page_records = {canonical_offer(record["url"]): record for record in records}
            new_keys = page_records.keys() - seen
            if records and not new_keys:
                raise SourceFailure("pagination_repeated_results")
            for key, record in page_records.items():
                if key in new_keys:
                    report["listings"].append(record)
            seen.update(new_keys)
            report["pages_checked"] += 1
            links = list(dict.fromkeys(urljoin(document.base_url, a.get("href"))
                                       for a in document.xpath(source.next_link) if a.get("href")))
            if len(links) > 1:
                raise SourceFailure("ambiguous_next_page")
            if not links:
                report.update(complete=True, stop_reason="last_page" if records else "no_open_offers")
                break
            url = links[0]
            await asyncio.sleep(0.5)
    except (SourceFailure, PermissionError) as exc:
        report["stop_reason"] = str(exc)
    except Exception as exc:
        report["stop_reason"] = type(exc).__name__
    report["count"] = len(report["listings"])
    return report


async def collect_direct():
    async def run(source):
        try:
            async with asyncio.timeout(210):
                return await collect_source(source)
        except Exception as exc:
            return {"source": source.url, "complete": False, "stop_reason": type(exc).__name__,
                    "pages_checked": 0, "count": 0, "listings": []}

    results = await asyncio.gather(*(run(source) for source in SOURCES))
    for source, result in zip(SOURCES, results):
        print(json.dumps({"event": "source_result", "provider": source.provider,
                          **{k: v for k, v in result.items() if k != "listings"}}), flush=True)
    return dict(zip((source.provider for source in SOURCES), results))
