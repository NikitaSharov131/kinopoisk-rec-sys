from kinopoisk_rec_sys.api_client import KinopoiskApiClient, Genre, User, Rating
from kinopoisk_rec_sys.scylla import KinopoiskScyllaDB
from models import ScyllaGenre, ScyllaRecommendedMovie, ScyllaUser
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

    def get_recs(self, user: User, recs_history: List[int] = None):
        recs = self._api.get_movie(user, recs_history)
        user.min_movies_rating = user.min_movies_rating.kp
        self._scylla.insert_collection([user], ScyllaUser)
        user.min_movies_rating = Rating(kp=user.min_movies_rating)
        self._scylla.insert_collection(recs, ScyllaRecommendedMovie)
        return recs

    def is_user_exist(self, user_id):
        return [u for u in self._scylla.filter_collection(ScyllaUser, 'id', user_id)]

    def recommended_movie(self, user_id):
        recs = self._scylla.filter_collection(ScyllaRecommendedMovie, 'user_id', user_id)
        return set(rec.id for rec in recs)


if __name__ == '__main__':
    k = KinopoiskSearch()

