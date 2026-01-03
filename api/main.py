import asyncio

from flask import Flask, jsonify, request
from src.film import get_film_by_id
from src.get_list import get_list as fetch_list
from src.recomender import cache, get_ranked_cached
from src.users import get_user_diary_page

app = Flask(__name__)


@app.route("/film/<string:id>", methods=["GET"])
async def get_film(id):
    data = await get_film_by_id(f"/film/{id}")
    return jsonify(data)


@app.route("/diary/<string:user_id>", methods=["GET"])
async def get_dialy_user(user_id):
    page = request.args.get("page", default=1, type=int)
    data = await get_user_diary_page(user_id, page)
    return jsonify(data)


@app.route("/recommend/<string:user_id>", methods=["GET"])
async def get_recommend_user(user_id):
    k = request.args.get("k", default=1, type=int)

    data = await get_ranked_cached(user_id, k)
    return jsonify(data)


@app.route("/get_list", methods=["GET"])
async def get_list():

    list_id = request.args.get(
        "list_id", default="official-top-250-narrative-feature-films", type=str
    )
    if list_id.startswith("https://letterboxd.com"):
        list_id = list_id.replace("https://letterboxd.com", "")
        list_id = list_id.split("/")[1:4]
    else:
        list_id = list_id.split("/")[0:3]

    list_id = "/".join(list_id)

    data = await fetch_list(f"https://letterboxd.com/{list_id}")
    return jsonify(data)


if __name__ == "__main__":
    cache.init_app(app)
    app.run()
