import asyncio
import csv
import os
import re
import sqlite3

from playwright.async_api import async_playwright
DB_PATH = "data/database.db"

MAX_BATCH = 5
def read_users_films():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT film_id FROM user_reviews")
    rows = cur.fetchall()

    conn.close()
    films = []
    for row in rows:
        film_id = dict(row)['film_id']
        film_split = film_id.split("/")[1:3]
        film_id = "/".join(film_split)
        films.append(f"/{film_id}/")
    return list(set(films))


def init_schema(db_path=DB_PATH):
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute(
        """
    CREATE TABLE IF NOT EXISTS films (
        id TEXT PRIMARY KEY,
        name TEXT,
        year TEXT,
        director TEXT,
        tagline TEXT,
        synopsis TEXT,
        poster TEXT,
        casts TEXT,
        genres TEXT,
        themes TEXT,
        studio TEXT,
        countries TEXT,
        language TEXT,
        views TEXT,
        lists TEXT,
        likes TEXT,
        fans TEXT,
        ratings TEXT,
        duration TEXT
    )
    """
    )
    conn.commit()
    conn.close()


async def db_writer(queue: asyncio.Queue, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    SQL = """
    INSERT OR REPLACE INTO films (
        id,name,year,director,tagline,synopsis,poster,
        casts,genres,themes,studio,countries,language,
        views,lists,likes,fans,ratings,duration
    ) VALUES (
        :id,:name,:year,:director,:tagline,:synopsis,:poster,
        :casts,:genres,:themes,:studio,:countries,:language,
        :views,:lists,:likes,:fans,:ratings,:duration
    )
    """

    buffer = []
    COMMIT_EVERY = 25

    while True:
        item = await queue.get()
        if item is None:
            break

        buffer.append(item)

        if len(buffer) >= COMMIT_EVERY:
            print(f"Writing {len(buffer)} records to DB...")
            cur.executemany(SQL, buffer)
            conn.commit()
            buffer.clear()

        queue.task_done()

    if buffer:
        cur.executemany(SQL, buffer)
        conn.commit()

    conn.close()


async def safe_get_text(locator):
    try:
        if await locator.count() > 0:
            return await locator.text_content()
    except:
        pass
    return None


async def get_detail_val(page, label):
    try:
        xpath = f"//div[@id='tab-details']//h3[contains(., '{label}')]/following-sibling::div[1]"
        target = page.locator(xpath)

        if await target.count() == 0:
            return None

        links = await target.locator("a").all()
        if links:
            texts = await asyncio.gather(*[l.text_content() for l in links])
            return ", ".join(texts)

        return await target.text_content()
    except:
        return None


async def scrape_one(context, film_id, db_queue):
    page = await context.new_page()
    url = f"https://letterboxd.com{film_id}/"

    data = {
        "id": film_id,
        "name": None,
        "year": None,
        "director": None,
        "tagline": None,
        "synopsis": None,
        "poster": None,
        "casts": None,
        "genres": None,
        "themes": None,
        "studio": None,
        "countries": None,
        "language": None,
        "views": None,
        "lists": None,
        "likes": None,
        "fans": None,
        "ratings": None,
        "duration": None,
    }
    url = f"https://letterboxd.com{film_id}"

    try:
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
    except Exception as e:
        print(f"Gagal memuat URL {url}")
        return None

    head = page.locator(".details").first
    data["name"] = await safe_get_text(head.locator("h1").first)
    data["year"] = await safe_get_text(page.locator(".releasedate").first)
    data["director"] = await safe_get_text(page.locator(".contributor").first)
    data["tagline"] = await safe_get_text(page.locator(".tagline").first)
    data["synopsis"] = await safe_get_text(page.locator(".truncate").first)

    cast_locators = await page.locator(".cast-list .text-slug").all()
    casts = [await c.text_content() for c in cast_locators]
    data["casts"] = ", ".join(casts) if casts else None

    genre_elements = await page.locator("#tab-genres .text-sluglist").all()
    if len(genre_elements) > 0:
        g_links = await genre_elements[0].locator("a").all()
        data["genres"] = ", ".join([await l.text_content() for l in g_links])
    if len(genre_elements) > 1:
        t_links = await genre_elements[1].locator("a").all()
        data["themes"] = ", ".join([await l.text_content() for l in t_links])

    try:
        await page.wait_for_selector(
            ".production-statistic-list > div",
            timeout=5000
        )
        stats = await page.locator(".production-statistic-list > div").all()
        if len(stats) >= 3:
            data["views"] = (await stats[0].text_content()).strip().split()[0]
            data["lists"] = (await stats[1].text_content()).strip().split()[0]
            data["likes"] = (await stats[2].text_content()).strip().split()[0]
    except Exception:
        pass


    data["fans"] = await safe_get_text(
        page.locator(".ratings-histogram-chart > a").first
    )
    data["ratings"] = await safe_get_text(
        page.locator(".average-rating > a").first
    )

    try:
        slug = film_id.split("/")
        if len(slug) > 2:
            poster_img = page.locator(
                f'.poster-list [data-item-slug="{slug[2]}"] .film-poster'
            ).first
            img = poster_img.locator("img")
            data["poster"] = await img.get_attribute("src")
    except Exception:
        pass

    try:
        dur_el = page.locator(".text-footer").first
        if await dur_el.count() > 0:
            dur_text = await dur_el.text_content()
            import re

            match = re.search(r"(\d+)\s+mins", dur_text)
            if match:
                data["duration"] = match.group(1)
            else:
                parts = dur_text.strip().split()
                for p in parts:
                    if p.isdigit():
                        data["duration"] = p
                        break
    except Exception:
        pass

    data["studio"] = await get_detail_val(page, "Studios")
    data["countries"] = await get_detail_val(page, "Country")
    data["language"] = await get_detail_val(page, "Language")

    await page.close()
    await db_queue.put(data)


async def run():
    init_schema()

    film_ids = read_users_films()
    print(f"Loaded {len(film_ids)} from database")
    db_queue = asyncio.Queue(maxsize=200)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()

        db_task = asyncio.create_task(db_writer(db_queue))

        BATCH = 5
        for i in range(0, len(film_ids), BATCH):
            batch = film_ids[i : i + BATCH]
            print(f"Processing batch: {batch}")
            tasks = [scrape_one(context, fid, db_queue) for fid in batch]
            await asyncio.gather(*tasks)

        await db_queue.join()
        await db_queue.put(None)
        await db_task

        await browser.close()
if __name__ == "__main__":
    asyncio.run(run())
