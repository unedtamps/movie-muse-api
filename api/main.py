import asyncio

from flask import Flask, jsonify, request

from src.film import get_film_by_id
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



if __name__ == "__main__":
    app.run()
