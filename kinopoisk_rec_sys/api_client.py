import os

import attrs
import requests
from attrs import define, AttrsInstance, fields
from datetime import datetime, timedelta
from functools import cached_property
from typing import List


@define(frozen=True)
class Rating:
    kp: int
    imdb: int
    filmCritics: int
    russianFilmCritics: int


@define(frozen=True)
class Votes:
    kp: int
    imdb: int
    filmCritics: int
    russianFilmCritics: int


@define(frozen=True)
class Genre:
    name: str


@define(frozen=True)
class Movie(AttrsInstance):
    id: int
    name: str
    alternativeName: str
    enName: str
    type: str
    typeNumber: int
    year: int
    description: str
    shortDescription: str
    status: str
    rating: Rating
    votes: Votes
    movieLength: int
    ratingMpaa: str
    ageRating: int
    genres: List[Genre] = None


@define(frozen=True)
class MovieQuery(AttrsInstance):
    type: str = "movie"
    page: int = 1
    limit: int = 250
    isSeries: str = "false"
    selectFields: List = [f.name for f in fields(Movie)]


class NewMovieQuery(MovieQuery):
    createdAt: str = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
    updatedAt: str = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")


class KinopoiskApiClient:
    movie_meta = []

    def __init__(self):
        self._api_key = os.environ.get('kp_key')
        self._api_version = 'v1.4'
        self.base_url = 'https://api.kinopoisk.dev'

    @cached_property
    def _session(self):
        session = requests.session()
        session.headers = {'X-API-KEY': self._api_key}
        return session

    def _get(self, endpoint):
        url = f"{self.base_url}/{self._api_version}/{endpoint}"
        response = self._session.get(url, params=attrs.asdict(MovieQuery()))
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            self._session.close()
            raise exc
        return response.json()

    def get_movie_details(self, movie_id):
        endpoint = f"movie/{movie_id}"
        return self._get(endpoint)

    def get_movie(self) -> List[Movie]:
        endpoint = 'movie'
        movies = []
        if raw_movies := self._get(endpoint):
            movies.extend([Movie(**movie) for movie in raw_movies.get("docs")])
            return movies

    def get_top_rated_movies(self, page=1):
        endpoint = 'movie/top_rated'
        return self._get(endpoint)

    def get_popular_movies(self, page=1):
        endpoint = 'movie/popular'
        params = {'page': page}
        return self._get(endpoint)


# Usage example
if __name__ == "__main__":
    unpack_fields(Movie)
    print(1)
