import random
import re
from typing import Optional

import aiohttp
from selectolax.parser import HTMLParser

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}


def convert_stars_to_number(star_str: Optional[str]) -> Optional[float]:
    if not star_str:
        return None
    return star_str.count("★") + star_str.count("½") * 0.5


def clean_film_url(raw_href: Optional[str]) -> Optional[str]:
    if not raw_href or "/film/" not in raw_href:
        return None
    return raw_href[raw_href.find("/film/") :]


async def fetch(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status != 200:
                return None
            return await r.text()
    except Exception:
        return None


def parse_diary(html: str):
    tree = HTMLParser(html)
    rows = tree.css(".diary-entry-row")

    for row in rows:
        film_a = row.css_first(".name a")
        rating_el = row.css_first(".rating")

        yield {
            "film_href": film_a.attributes.get("href") if film_a else None,
            "rating": rating_el.text(strip=True) if rating_el else None,
            "liked": bool(row.css_first(".icon-liked")),
            "reviewed": bool(row.css_first(".icon-review")),
        }


def parse_review(html: str) -> Optional[str]:
    tree = HTMLParser(html)
    body = tree.css_first(".js-review-body")
    if not body:
        return None

    text = body.text()
    return re.sub(r"^\s+", "", text)


async def scrape_user(session, user_id: str, page):
    datas = []

    diary_url = f"https://letterboxd.com{user_id}diary/films/page/{page}/"

    html = await fetch(session, diary_url)

    if not html:
        return {}

    for entry in parse_diary(html):
        film_id = clean_film_url(entry["film_href"])
        if not film_id:
            continue

        review_text = None

        if entry["reviewed"]:
            review_url = f"https://letterboxd.com{entry['film_href']}"
            review_html = await fetch(session, review_url)
            if review_html:
                review_text = parse_review(review_html)

        data = {
            "user_id": user_id,
            "film_id": film_id,
            "rating": convert_stars_to_number(entry["rating"]),
            "liked": entry["liked"],
            "review": review_text,
        }
        datas.append(data)
    return datas


async def get_user_diary_page(session: aiohttp.ClientSession, user_id: str, page: int):
    formatted_uid = f"/{user_id}/"
    return await scrape_user(session, formatted_uid, page)
