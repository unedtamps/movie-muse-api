import re

from playwright.async_api import async_playwright

from src.film import get_film_by_id


def upscale_poster(url):
    pattern = r"-0-(\d+)-0-(\d+)-crop"
    new_pattern = "-0-230-0-345-crop"
    new_url = re.sub(pattern, new_pattern, url)
    return new_url


async def run(context, query):
    page = await context.new_page()
    results = []
    await page.add_init_script(
        """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
    )

    try:
        response = await page.goto(
            f"https://letterboxd.com/search/films/{query}",
            wait_until="domcontentloaded",
        )
        if response.status == 403:
            return results

        items = page.locator(".search-result")
        await items.first.wait_for(state="visible")

        count = await items.count()

        for i in range(count):
            data = items.nth(i).locator("article > div").first
            await data.wait_for(state="visible")
            title = await data.get_attribute("data-item-name")
            film_id = await data.get_attribute("data-item-link")
            poster_film = None
            film = await get_film_by_id(film_id)
            poster_film = film["poster"] if film else None
            results.append(
                {
                    "title": title.strip() if title else None,
                    "film_id": film_id,
                    "poster": poster_film,
                }
            )

    except Exception as e:
        print(e)
        return results

    return results


async def get_film_by_name(query):
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
        result = await run(context, query)
        await browser.close()
        return result
