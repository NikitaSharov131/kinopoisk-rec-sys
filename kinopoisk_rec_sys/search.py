from kinopoisk_rec_sys.api_client import KinopoiskApiClient, Genre, User, Rating
from kinopoisk_rec_sys.scylla import KinopoiskScyllaDB
from models import ScyllaGenre, RecommendedMovie
from typing import List


class KinopoiskSearch:

    def __init__(self):
        self._api = KinopoiskApiClient()
        self._scylla = KinopoiskScyllaDB()

    def collect_genres(self) -> List[Genre]:
        genres = self._scylla.get_collection_elements(ScyllaGenre)
        if not genres:
            genres = self._api.get_possible_genres()
            self._scylla.insert_collection(genres, ScyllaGenre)
        return [Genre(**genre) for genre in genres]

    def start_search(self):
        user = User(id="12312333123123", preferred_genres=[Genre(name="драма").name], min_movies_rating=Rating(kp=8.1))
        recommended_movies = self._api.get_movie(user)
        self._scylla.insert_collection(recommended_movies, RecommendedMovie)


if __name__ == '__main__':
    k = KinopoiskSearch()
    k.start_search()
