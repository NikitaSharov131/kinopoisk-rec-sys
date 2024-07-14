import os

import attrs
import requests
from attrs import define, AttrsInstance, fields
from datetime import datetime, timedelta
from functools import cached_property
from typing import List, Optional


@define(frozen=True)
class Rating:
    kp: float
    imdb: Optional[float] = None
    filmCritics: Optional[float] = None
    russianFilmCritics: Optional[float] = None


@define(frozen=True)
class Votes:
    kp: int
    imdb: int
    filmCritics: int
    russianFilmCritics: int


@define(frozen=True)
class Genre:
    name: str
    slug: str = None


@define(frozen=True, kw_only=True)
class User:
    id: str
    preferred_genres: List[Genre.name]
    min_movies_rating: Rating


@define(frozen=True, kw_only=True)
class Movie(AttrsInstance):
    id: int
    name: str
    alternativeName: str
    enName: str
    year: int
    description: str
    shortDescription: str
    status: str
    rating: Rating
    votes: Votes
    movieLength: int
    ratingMpaa: str
    genres: List[Genre] = None


@define(frozen=True, kw_only=True)
class RecommendedMovie(Movie):
    user_id: User.id
    kp_url: str


@define()
class MovieQuery(AttrsInstance):
    type: str = "movie"
    page: int = 1
    limit: int = 10
    isSeries: str = "false"
    selectFields: List = [f.name for f in fields(Movie) if f.name not in ("kp_url")]


@define(frozen=True)
class PossibleValues(AttrsInstance):
    field: str


class NewMovieQuery(MovieQuery):
    createdAt: str = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
    updatedAt: str = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")


def _assign_rating(rating: Rating):
    return {rating_kind: f"{rating_value}-10" for rating_value, rating_kind in
            zip([rating.kp, rating.imdb], ["rating.kp", "rating.imdb"]) if rating_value}


class KinopoiskApiClient:
    movie_meta = []

    def __init__(self):
        self._api_key = os.environ.get('kp_key')
        self.base_url = 'https://api.kinopoisk.dev'
        self.base_kp_url = 'https://www.kinopoisk.ru/film/'

    def get_possible_genres(self) -> List[Genre]:
        endpoint = 'movie/possible-values-by-field'
        if genres := self._get(endpoint, attrs.asdict(PossibleValues(field='genres.name')), 'v1'):
            return [Genre(**genre) for genre in genres]

    @cached_property
    def _session(self):
        session = requests.session()
        session.headers = {'X-API-KEY': self._api_key, "accept": "application/json"}
        return session

    def _get(self, endpoint, query_params: dict, api_version: str = 'v1.4'):
        url = f"{self.base_url}/{api_version}/{endpoint}"
        response = self._session.get(url, params=query_params)
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            self._session.close()
            raise exc
        return response.json()

    def get_movie_details(self, movie_id):
        endpoint = f"movie/{movie_id}"
        return self._get(endpoint)

    def get_movie(self, user: User) -> List[RecommendedMovie]:
        endpoint = 'movie'
        query = attrs.asdict(MovieQuery())
        query['genres.name'] = user.preferred_genres
        query = {**query, **_assign_rating(user.min_movies_rating)}
        if raw_movies := self._get(endpoint, query):
            return [RecommendedMovie(**movie, **{"kp_url": f"{self.base_kp_url}/{movie.get('id')}", "user_id": user.id})
                    for movie in raw_movies.get("docs")]

    def get_top_rated_movies(self, page=1):
        endpoint = 'movie/top_rated'
        return self._get(endpoint)

    def get_popular_movies(self, page=1):
        endpoint = 'movie/popular'
        params = {'page': page}
        return self._get(endpoint)


# Usage example
if __name__ == "__main__":
    r = Rating(kp=10)
    t = r.kp.__class__.__name__
    print(t)
