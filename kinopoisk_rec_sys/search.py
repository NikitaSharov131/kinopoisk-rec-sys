from fastapi import FastAPI
from pydantic import BaseModel

from kinopoisk_rec_sys.api_client import KinopoiskApiClient, Rating
from kinopoisk_rec_sys.models import (ScyllaGenre, ScyllaRecommendedMovie,
                                      ScyllaUser)
from kinopoisk_rec_sys.scylla import KinopoiskScyllaDB

app = FastAPI()
api = KinopoiskApiClient()
scylla = KinopoiskScyllaDB()


class User(BaseModel):
    id: int
    name: str
    preferred_genre: str
    chat_id: int
    min_movies_rating: float


@app.get("/genres")
async def get_genres():
    genres = scylla.get_collection_elements(ScyllaGenre)
    if not [g for g in genres]:
        genres = api.get_possible_genres()
        scylla.insert_collection(genres, ScyllaGenre)
    return {"genres": genres}


@app.post("/recs")
async def get_recs(user: User):
    user.min_movies_rating = Rating(kp=user.min_movies_rating)
    recs = api.get_movie(user, recommended_movie(user.id))
    user.min_movies_rating = user.min_movies_rating.kp
    scylla.insert_collection([user.model_dump()], ScyllaUser)
    scylla.insert_collection(recs, ScyllaRecommendedMovie)
    return {"recs": recs}


@app.get("/user/{user_id}")
async def get_user_meta(user_id):
    return {
        "user_id": [u for u in scylla.filter_collection(ScyllaUser, "id", int(user_id))]
    }


@app.get("/recs/{user_id}")
def recommended_movie(user_id):
    recs = scylla.filter_collection(ScyllaRecommendedMovie, "user_id", int(user_id))
    return set(rec.id for rec in recs)
