import asyncio
from .base_scraper import PlaywrightManager, capture_xhr
from bs4 import BeautifulSoup
import json
from datetime import date, timedelta

# Example high-level function: fetch a court page and return raw HTML + captured XHR endpoints
async def fetch_page_with_xhr(url, headless=True):
    async with PlaywrightManager(headless=headless) as pm:
        ctx, page = await pm.new_context_page()
        # capture XHRs while loading
        xhrs = []
        def on_response(response):
            try:
                if response.request.resource_type == "xhr":
                    xhrs.append({"url": response.url, "status": response.status})
            except Exception:
                pass
        page.on("response", on_response)
        await page.goto(url, wait_until="networkidle")
        # wait for extra XHRs
        await page.wait_for_timeout(2000)
        html = await page.content()
        await ctx.close()
    return html, xhrs

# naive parser example: extract text and paragraphs into a single block
def parse_causelist_simple(html):
    soup = BeautifulSoup(html, "html.parser")
    # many ecourts pages render cause lists in tables or <pre> elements. We'll gather relevant text blocks.
    container = soup.find(class_="cause-list") or soup.find("table") or soup.find("pre")
    if not container:
        # fallback: full text
        text = soup.get_text("\n", strip=True)
        return {"text": text}
    text = container.get_text("\n", strip=True)
    return {"text": text}
