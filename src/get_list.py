import asyncio

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from src.utils import fetch_html


def parse_list_entries(html: str):
    """Parse film list entries from HTML.
    
    Handles multiple list layouts:
    - Numbered poster lists: ul.js-list-entries > li.posteritem
    - Grid layouts: ul.grid > li.griditem
    """
    soup = BeautifulSoup(html, "html.parser")
    
    entries = soup.select("ul.js-list-entries > li.posteritem")
    
    if not entries:
        entries = soup.select("ul.grid > li.griditem")
    
    for entry in entries:
        react_component = entry.select_one("div.react-component")
        if not react_component:
            continue
        
        film_id = react_component.get("data-item-link")
        title = react_component.get("data-item-name")
        
        if film_id and title:
            yield {
                "title": title.strip(),
                "film_id": film_id,
            }


async def fetch_list_page(session: AsyncSession, list_id: str, page: int):
    """Fetch a single page of a film list."""
    url = f"https://letterboxd.com{list_id}/page/{page}/"
    html = await fetch_html(session, url)
    if not html:
        return []
    
    return list(parse_list_entries(html))


async def get_list(list_id: str, page: int = None, limit: int = None):
    """Fetch films from a Letterboxd list.
    
    Args:
        list_id: The list URL path (e.g., "/user/list/top-10/")
        page: Specific page number to fetch. If None, fetches all pages.
        limit: Maximum number of films to return. If None, returns all.
    
    Returns:
        List of film dictionaries with 'title' and 'film_id'.
    """
    # Normalize list_id
    if not list_id.startswith("/"):
        list_id = f"/{list_id}"
    
    results = []
    current_page = page if page else 1
    
    async with AsyncSession(impersonate="chrome") as session:
        # Fetch single page if specified
        if page:
            results = await fetch_list_page(session, list_id, page)
            if limit:
                results = results[:limit]
            return results
        
        # Fetch all pages
        while True:
            if limit and len(results) >= limit:
                break
            
            entries = await fetch_list_page(session, list_id, current_page)
            
            if not entries:
                break
            
            results.extend(entries)
            current_page += 1
    
    # Apply limit if specified
    if limit:
        results = results[:limit]
    
    return results
