import os

import attrs
import requests
from functools import cached_property
from typing import List, Set, Dict
from kinopoisk_rec_sys.models import Rating, Genre, PossibleValues, User, MovieQuery


def _assign_rating(rating: Rating):
    return {rating_kind: f"{rating_value}-10" for rating_value, rating_kind in
            zip([rating.kp, rating.imdb], ["rating.kp", "rating.imdb"]) if rating_value}


class KinopoiskApiClient:
    movie_meta = []

    def __init__(self):
        self._api_key = os.environ.get('KP_KEY')
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

    def get_movie(self, user: User, id_recommended: Set[int] = None) -> List[Dict]:
        endpoint = 'movie'
        query = attrs.asdict(MovieQuery())
        query['genres.name'] = user.preferred_genre
        if id_recommended:
            query['id'] = [f"!{kp_id}" for kp_id in id_recommended]
        query = {**query, **_assign_rating(user.min_movies_rating)}
        movies = []
        if raw_movies := self._get(endpoint, query):
            for movie in raw_movies.get("docs"):
                movie["rating"] = movie.get("rating", {}).get("kp")
                movies.append({**movie, **{"kp_url": f"{self.base_kp_url}/{movie.get('id')}",
                                           "user_id": user.id}})
        return movies
