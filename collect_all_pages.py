"""Follow real public pagination, including Livewire-rendered offer cards."""
import asyncio
import re
from urllib.parse import urlsplit
from provider_registry import provider_for, canonical_offer
from collect_inberlinwohnen import FINDER, UA
from public_access import check_robots

CARD_JS = """els => els.map(e => ({text:e.textContent.replace(/\\s+/g,' ').trim(),
 links:[...e.querySelectorAll('a[href]')].filter(a=>a.textContent.trim()==='Alle Details').map(a=>a.href)}))"""

async def collect_async(max_pages=200):
    from playwright.async_api import async_playwright
    print("Discovery stage: robots_check",flush=True)
    try:
        check_robots(FINDER,{})
    except Exception as exc:
        return {"source":FINDER,"count":0,"pages_checked":0,"complete":False,
                "stop_reason":"robots_check_"+type(exc).__name__,"listings":[],
                "expected_total":None,"unknown_provider_links":[]}
    print("Discovery stage: robots_verified",flush=True)
    results, seen, signatures = [], set(), set()
    result = {"source":FINDER,"count":0,"pages_checked":0,"complete":False,
              "stop_reason":None,"expected_total":None,"unknown_provider_links":[],"listings":results}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="de-DE",user_agent=UA)
        try:
            print("Discovery stage: finder_navigation",flush=True)
            response = await page.goto(FINDER,wait_until="domcontentloaded",timeout=45000)
            if not response or response.status != 200:
                raise RuntimeError("finder_http_error")
            for number in range(1,max_pages+1):
                if urlsplit(page.url).hostname not in {"www.inberlinwohnen.de","inberlinwohnen.de"}:
                    raise RuntimeError("finder_unexpected_redirect")
                await page.locator(".list__details").first.wait_for(state="attached",timeout=20000)
                cards = await page.locator(".list__details").evaluate_all(CARD_JS)
                signature = tuple(link for card in cards for link in card["links"])
                if signature in signatures:
                    result["stop_reason"] = "repeated_page"
                    break
                signatures.add(signature)
                result["pages_checked"] += 1
                print("Discovery page:",number,flush=True)
                body = await page.locator("body").inner_text()
                total = re.search(r"von\s+([\d.]+)\s+Angeboten",body)
                if total:
                    result["expected_total"] = int(total.group(1).replace(".",""))
                for card in cards:
                    for link in card["links"]:
                        provider = provider_for(link)
                        if not provider:
                            if link not in result["unknown_provider_links"]:
                                result["unknown_provider_links"].append(link)
                            continue
                        key = canonical_offer(link)
                        if key in seen:
                            continue
                        seen.add(key)
                        results.append({"url":link,"provider":provider,"source":FINDER,
                                        "source_page":number,"source_text":card["text"]})
                next_button = page.get_by_role("button",name=re.compile(r"^Vor(?:\s|$)")).first
                if not await next_button.count() or not await next_button.is_enabled():
                    result["complete"] = True
                    result["stop_reason"] = "last_page"
                    break
                await next_button.click()
                await page.wait_for_function(
                    """old => JSON.stringify([...document.querySelectorAll('.list__details a[href]')]
                    .filter(a=>a.textContent.trim()==='Alle Details').map(a=>a.href)) !== JSON.stringify(old)""",
                    arg=list(signature),timeout=25000)
                await page.wait_for_timeout(300)
            else:
                result["stop_reason"] = "page_limit_reached"
        except Exception as exc:
            result["complete"] = False
            result["stop_reason"] = "collection_error_"+type(exc).__name__
        finally:
            await browser.close()
    result["count"] = len(results)
    return result

def collect(max_pages=200):
    return asyncio.run(collect_async(max_pages))

