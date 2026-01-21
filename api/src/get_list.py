import asyncio

import playwright
from playwright.async_api import async_playwright


async def run(context, list_id):
    page = await context.new_page()
    p = 1
    results = []

    while True:
        await page.goto(
            f"{list_id}/page/{p}/",
            wait_until="domcontentloaded",
        )
        items = page.locator(".poster")
        count = await items.count()
        if count <= 1:
            break

        for i in range(count - 1):
            title = await items.nth(i).text_content()

            href = items.nth(i).locator("a")
            res = await href.get_attribute("href")
            results.append({"title": title.strip() if title else None, "film_id": res})
        p += 1

    return results


async def get_list(list_id: str):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            device_scale_factor=1,
        )
        result = await run(context, list_id)
        await browser.close()
        return result
