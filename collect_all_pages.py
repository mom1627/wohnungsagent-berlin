"""Follow real public pagination, including Livewire-rendered offer cards."""
import asyncio
import re
import hashlib
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
              "stop_reason":None,"expected_total":None,"unknown_provider_links":[],"listings":results,
              "linked_offer_cards_seen":0,"duplicate_offer_links":0}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale="de-DE",user_agent=UA)
        try:
            print("Discovery stage: finder_navigation",flush=True)
            response = await page.goto(FINDER,wait_until="domcontentloaded",timeout=45000)
            if not response or response.status != 200:
                raise RuntimeError("finder_http_error")
            # The consent dialog appears after page load and intercepts Next.
            # Save the default essential-only selection, never accept all.
            result["last_stage"] = "essential_cookie_choice"
            cookies = page.locator("#accept-selected-cookies")
            try:
                await cookies.wait_for(state="visible",timeout=6000)
            except Exception:
                pass
            if await cookies.count() and await cookies.is_visible():
                await cookies.click(timeout=10000)
            for number in range(1,max_pages+1):
                if urlsplit(page.url).hostname not in {"www.inberlinwohnen.de","inberlinwohnen.de"}:
                    raise RuntimeError("finder_unexpected_redirect")
                result["last_stage"] = "offer_cards"
                await page.locator(".list__details a[href]").filter(has_text="Alle Details").first.wait_for(state="attached",timeout=20000)
                # Couple page identity and cards in one observation. Livewire
                # replaces pagination and card markup in separate phases.
                snapshot = await page.locator("body").evaluate("""body=>({
                    page:Number(new URL(location.href).searchParams.get('page')||1),
                    range:body.innerText.match(/Zeige\\s+(\\d+)\\s+bis/)?.[1]||null,
                    cards:[...body.querySelectorAll('.list__details')].map(e=>({
                      text:e.textContent.replace(/\\s+/g,' ').trim(),
                      links:[...e.querySelectorAll('a[href]')].filter(a=>a.textContent.trim()==='Alle Details').map(a=>a.href)
                    }))
                })""")
                cards = snapshot["cards"]
                signature = tuple(link for card in cards for link in card["links"])
                diagnostic = {"expected_page":number,"observed_page":snapshot["page"],
                    "range_start":snapshot["range"],"card_count":len(cards),
                    "signature":hashlib.sha256(repr(signature).encode()).hexdigest()[:12]}
                result.setdefault("page_diagnostics",[]).append(diagnostic)
                print("Discovery observation:",diagnostic,flush=True)
                if snapshot["page"] != number or snapshot["range"] != str((number-1)*10+1):
                    result["stop_reason"] = "page_identity_mismatch"
                    break
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
                        result["linked_offer_cards_seen"] += 1
                        provider = provider_for(link)
                        if not provider:
                            if link not in result["unknown_provider_links"]:
                                result["unknown_provider_links"].append(link)
                            continue
                        key = canonical_offer(link)
                        if key in seen:
                            result["duplicate_offer_links"] += 1
                            continue
                        seen.add(key)
                        results.append({"url":link,"provider":provider,"source":FINDER,
                                        "source_page":number,"source_text":card["text"]})
                next_button = page.get_by_role("button",name=re.compile(r"^Vor(?:\s|$)")).first
                if not await next_button.count() or not await next_button.is_enabled():
                    result["complete"] = True
                    result["stop_reason"] = "last_page"
                    break
                result["last_stage"] = "next_button_click"
                # Native keyboard activation also works while the Livewire
                # layout moves the button; do not require pointer stability.
                await next_button.press("Enter",timeout=10000)
                result["last_stage"] = "next_page_wait"
                navigation = await page.wait_for_function(
                    """state => { const links=[...document.querySelectorAll('.list__details a[href]')]
                    .filter(a=>a.textContent.trim()==='Alle Details').map(a=>a.href);
                    const current=Number(new URL(location.href).searchParams.get('page')||1);
                    const range=document.body.innerText.match(/Zeige\\s+(\\d+)\\s+bis/);
                    const ready=current===state.page && range && Number(range[1])===(state.page-1)*10+1
                      && links.length>0 && JSON.stringify(links)!==JSON.stringify(state.links);
                    return ready ? {url:location.href} : false; }""",
                    arg={"links":list(signature),"page":number+1},timeout=35000)
                target = await navigation.json_value()
                if urlsplit(target["url"]).hostname not in {"www.inberlinwohnen.de","inberlinwohnen.de"}:
                    raise RuntimeError("finder_unexpected_navigation")
                # The site can restore page 1 after its transient Livewire update.
                # Open the exact public URL produced by the normal Next action;
                # never invent query state or call internal endpoints.
                response = await page.goto(target["url"],wait_until="domcontentloaded",timeout=45000)
                if not response or response.status != 200: raise RuntimeError("finder_next_page_http_error")
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

