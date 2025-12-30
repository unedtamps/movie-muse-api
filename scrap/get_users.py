import csv
import os
import asyncio
import httpx
from bs4 import BeautifulSoup

DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "users.csv")
POPULAR_PAGES = 256

BASE_URL = "https://letterboxd.com"


def load_existing(csv_path: str) -> set[str]:
    seen = set()
    if not os.path.exists(csv_path):
        return seen

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("user_id"):
                seen.add(row["user_id"])
    return seen


async def fetch_page(client: httpx.AsyncClient, path : str, page: int) -> str | None:
    url = f"{BASE_URL}/members/popular{path}page/{page}/"
    try:
        r = await client.get(url, timeout=30)
        r.raise_for_status()
        return r.text
    except httpx.HTTPError as e:
        print(f"[FETCH FAIL] {url} | {type(e).__name__}")
        return None


def extract_users(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    users = []
    for name in soup.select(".name"):
        if name:
            users.append(name["href"])
    return users


async def run():
    os.makedirs(DATA_DIR, exist_ok=True)
    paths = ["/this/week/", "/this/month/", "/this/year/", "/"]

    seen = load_existing(CSV_PATH)
    print(f"Loaded {len(seen)} existing rows")

    file_exists = os.path.exists(CSV_PATH)

    async with httpx.AsyncClient(
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
        },
        follow_redirects=True,
    ) as client:

      with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(f, fieldnames=["user_id"])
        if not file_exists:
            writer.writeheader()
        
        for path in paths:
            for page in range(1, POPULAR_PAGES + 1):
                html = await fetch_page(client,path, page)
                if not html:
                    continue

                user_ids = extract_users(html)

                for user_id in user_ids:
                    if user_id in seen:
                        continue
                    print(f"Write {user_id}")
                    writer.writerow({"user_id": user_id})
                    seen.add(user_id)

                print(f"Completed popular {path} page {page}")


if __name__ == "__main__":
    asyncio.run(run())