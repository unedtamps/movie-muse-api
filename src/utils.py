async def fetch_html(session, url):
    try:
        response = await session.get(url, timeout=30)
        if response.status_code == 200:
            return response.text
        print(f"Failed with status: {response.status_code}")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
