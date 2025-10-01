import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
import json
from datetime import datetime

class PlaywrightManager:
    def __init__(self, headless=True):
        self.headless = headless
        self._playwright = None
        self.browser = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=self.headless, args=["--no-sandbox"])
        return self

    async def new_context_page(self):
        context = await self.browser.new_context()
        page = await context.new_page()
        return context, page

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

# helper to capture XHRs while loading a page (useful to find JSON endpoints)
async def capture_xhr(page, url, wait_for=5):
    xhr_responses = []

    def on_response(response):
        try:
            if response.request.resource_type == "xhr":
                xhr_responses.append({
                    "url": response.url,
                    "status": response.status,
                })
        except Exception:
            pass

    page.on("response", on_response)
    await page.goto(url, wait_until="networkidle")
    # optionally wait a bit to capture late XHRs
    await page.wait_for_timeout(wait_for * 1000)
    return xhr_responses
