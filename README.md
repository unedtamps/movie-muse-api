# Letterboxd Scraper & API

> ⚠️ **Unofficial API** - This is an unofficial Letterboxd API and is not affiliated with or endorsed by Letterboxd.
>
> 🚧 **Under Development** - This project is actively being developed. APIs and features may change without notice.

A REST API for accessing Letterboxd film data, user activity, and recommendations.

## Features

* **Film Search:** Search for films by name
* **Film Details:** Get comprehensive film metadata (genres, cast, synopsis, ratings, etc.)
* **User Data:** Access user diaries and favorites
* **Lists:** Fetch films from user lists, watchlists, actor/director filmographies
* **Recommendations:** Get film recommendations based on user preferences or seed films

## API Usage

Start the local server:

```bash
python3 main.py
```

The API will be available at `http://localhost:5000`.

### Swagger Documentation

Access the interactive API documentation at `http://localhost:5000/apidocs/`.

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/film/<id>` | GET | Get film details by ID |
| `/search` | GET | Search films by name |
| `/diary/<user_id>` | GET | Get user diary entries |
| `/favorites/<user_id>` | GET | Get user favorites |
| `/get_list` | GET | Fetch films from a list |
| `/recommend/personalize/<user_id>` | GET | Personalized recommendations |
| `/recommend/seed` | POST | Recommendations based on seed films |

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional):
```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_SLOW_HOST=localhost
export REDIS_SLOW_PORT=6378
```

## Docker

Run with Docker Compose:

```bash
docker-compose up
```

## Model

Download the recommendation model from [Hugging Face](https://huggingface.co/wolfgag/model-movie-muse/tree/main) and place it in the `/model` directory.
