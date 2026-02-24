import asyncio
from typing import Optional

from bs4 import BeautifulSoup

from src.film import get_film_by_id
from src.utils import fetch_html

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
    return raw_href[raw_href.find("/film/"):]


def parse_diary(html: str):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(".griditem")

    for row in rows:
        component = row.select_one(".react-component")
        viewing_data = row.select_one(".poster-viewingdata")
        if not component or not viewing_data:
            continue

        film_a = component.get("data-item-link")
        rating_el = viewing_data.select_one(".rating")
        like_icon = bool(viewing_data.select_one(".icon-liked"))

        yield {
            "film_href": film_a,
            "rating": rating_el.get_text(strip=True) if rating_el else None,
            "liked": like_icon,
        }


async def scrape_user(session, user_id: str, page: int):
    datas = []
    diary_url = f"https://letterboxd.com{user_id}films/page/{page}/"

    html = await fetch_html(session, diary_url)
    if not html:
        return []

    for entry in parse_diary(html):
        film_id = clean_film_url(entry["film_href"])
        if not film_id:
            continue

        data = {
            "user_id": user_id,
            "film_id": film_id,
            "rating": convert_stars_to_number(entry["rating"]),
            "liked": entry["liked"],
        }
        datas.append(data)

    return datas


async def get_user_diary_page(session, user_id: str, page: int):
    formatted_uid = f"/{user_id}/"
    return await scrape_user(session, formatted_uid, page)


def parse_favorites(html: str):
    soup = BeautifulSoup(html, "html.parser")
    favorites = soup.select("#favourites .favourite-production-poster-container > div")

    for film in favorites:
        film_id = film.get("data-item-link")
        if film_id:
            yield film_id


async def get_user_favorites_handler(session, user_id: str):
    formatted_uid = f"/{user_id}/"
    html = await fetch_html(session, f"https://letterboxd.com{formatted_uid}")
    if not html:
        return []

    film_ids = list(parse_favorites(html))
    
    # Fetch all film details concurrently
    tasks = [get_film_by_id(film_id) for film_id in film_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and None results
    datas = [
        result for result in results 
        if not isinstance(result, Exception) and result is not None
    ]
    
    return datas
