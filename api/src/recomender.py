import asyncio
import pickle

import aiohttp
import numpy as np
from flask_caching import Cache
from src.users import get_user_diary_page

cache = Cache(
    config={
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_HOST": "localhost",
        "CACHE_REDIS_PORT": 6379,
        "CACHE_REDIS_DB": 0,
        "CACHE_DEFAULT_TIMEOUT": 3600,  # 1 hour
    }
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

with open("model/model.pkl", "rb") as f:
    obj = pickle.load(f)

model = obj["model"]
item_map = obj["item_map"]
user_map = obj["user_map"]
id_to_film = {idx: film_id for film_id, idx in item_map.items()}


def infer_user_vector(item_ids, ratings, item_factors):
    item_ids = np.asarray(item_ids, dtype=int)
    ratings = np.asarray(ratings, dtype=float)
    if len(item_ids) == 0:
        raise ValueError("No known items for user")
    if len(ratings) > 1:
        w = ratings - ratings.mean()
    else:
        w = np.ones_like(ratings)
    user_vec = (item_factors[item_ids] * w[:, None]).sum(axis=0)
    return user_vec


def process_film_id(film_id):
    film_id = film_id.split("/")
    film_id = "/".join(film_id[1:3])
    return f"/{film_id}/"


BATCH = 10


async def compute_ranked(user_id: str, k: int = 10) -> list[str]:
    seen = set()
    item_ids = []
    ratings = []

    page = 1
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        while True:
            tasks = [
                get_user_diary_page(session, user_id, page + i) for i in range(BATCH)
            ]
            pages = await asyncio.gather(*tasks)

            if all(not p for p in pages):
                break

            for data in pages:
                if not data:
                    continue

                for r in data:
                    fid = r.get("film_id")
                    fid = process_film_id(fid)
                    rating = r.get("rating")

                    if fid not in item_map:
                        continue

                    i = item_map[fid]
                    seen.add(i)

                    if rating is None or rating <= 0:
                        continue

                    item_ids.append(i)
                    ratings.append(float(rating))

            page += BATCH

    if len(item_ids) < 2:
        return []

    item_ids = np.asarray(item_ids, dtype=np.int32)
    ratings = np.asarray(ratings, dtype=np.float32)

    u_vec = infer_user_vector(item_ids, ratings, model.item_factors)

    scores = model.item_factors @ u_vec
    scores[list(seen)] = -np.inf

    topk = np.argpartition(scores, -k)[-k:]
    topk = topk[np.argsort(scores[topk])[::-1]]

    return [id_to_film[i] for i in topk]


PER_PAGE = 10


def paginate_ranked(ranked, page: int):
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    return ranked[start:end]


async def get_ranked_cached(user_id: str, page: int):
    key = f"ranked:{user_id}"

    ranked = cache.get(key)
    if ranked is not None:
        return paginate_ranked(ranked, page)

    ranked = await compute_ranked(user_id, 1000)
    cache.set(key, ranked)
    return paginate_ranked(ranked, page)
