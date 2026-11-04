"""Verify complete traversal, repeated pages, caps and partial failure reporting."""
import sys
import types
import unittest
from unittest.mock import patch
from collect_all_pages import collect_async

class Node:
    def __init__(self, page, kind): self.page, self.kind = page, kind
    @property
    def first(self): return self
    def filter(self, **kwargs): return self
    async def wait_for(self, **kwargs): pass
    async def evaluate_all(self, script):
        if self.page.index == self.page.fail_at: raise TimeoutError()
        number = 0 if self.page.repeat else self.page.index
        return [{"text":"source text", "links":[f"https://www.gewobag.de/offer/{number}"]}]
    async def evaluate(self, script):
        return {"page":self.page.index+1,"range":str(self.page.index*10+1),"cards":await self.evaluate_all(script)}
    async def inner_text(self): return "Zeige 1 bis 10 von 30 Angeboten"
    async def count(self): return int(self.page.index < 2)
    async def is_enabled(self): return self.page.index < 2
    async def is_visible(self): return False
    async def click(self, **kwargs): self.page.index += 1
    async def press(self, key, **kwargs):
        assert key == "Enter"
        self.page.index += 1
        self.page.url = "https://www.inberlinwohnen.de/wohnungsfinder?page="+str(self.page.index+1)

class Page:
    url = "https://www.inberlinwohnen.de/wohnungsfinder"
    def __init__(self, repeat=False, fail_at=None): self.index, self.repeat, self.fail_at = 0, repeat, fail_at
    async def goto(self, *args, **kwargs): return types.SimpleNamespace(status=200)
    async def close(self): pass
    def locator(self, selector): return Node(self, selector)
    def get_by_role(self, *args, **kwargs): return Node(self, "next")
    async def wait_for_function(self, *args, **kwargs):
        page=self
        class Handle:
            async def json_value(self): return {"url":page.url+"?page="+str(page.index+1)}
        return Handle()
    async def wait_for_timeout(self, *args): pass

class Browser:
    def __init__(self, page): self.page = page
    async def new_context(self, **kwargs): return self
    async def new_page(self, **kwargs): return self.page
    async def close(self): pass

class Playwright:
    def __init__(self, page): self.page, self.chromium = page, self
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def launch(self, **kwargs): return Browser(self.page)

class PaginationTests(unittest.IsolatedAsyncioTestCase):
    async def collect(self, page, **kwargs):
        module = types.ModuleType("playwright.async_api")
        module.async_playwright = lambda: Playwright(page)
        with patch.dict(sys.modules, {"playwright":types.ModuleType("playwright"), "playwright.async_api":module}), patch("collect_all_pages.check_robots"):
            return await collect_async(**kwargs)
    async def test_all_pages(self):
        result = await self.collect(Page())
        self.assertTrue(result["complete"])
        self.assertEqual(result["pages_checked"], 3)
        self.assertEqual(result["count"], 3)
    async def test_repeated_page_is_incomplete(self):
        result = await self.collect(Page(repeat=True))
        self.assertFalse(result["complete"])
        self.assertEqual(result["stop_reason"], "repeated_page")
    async def test_page_cap_is_incomplete(self):
        result = await self.collect(Page(), max_pages=1)
        self.assertFalse(result["complete"])
        self.assertEqual(result["stop_reason"], "page_limit_reached")
    async def test_partial_results_survive_failure(self):
        result = await self.collect(Page(fail_at=1))
        self.assertFalse(result["complete"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["stop_reason"], "collection_error_TimeoutError")
