from kinopoisk_rec_sys.api_client import KinopoiskApiClient
from kinopoisk_rec_sys.scylla import KinopoiskScyllaDB


class KinopoiskSearch:
    def __init__(self):
        self._api = KinopoiskApiClient()
        self._scylla = KinopoiskScyllaDB()

    def collect_genres(self):
        genres = self._api.get_possible_genres()
        self._scylla.insert_collection(genres)


if __name__ == '__main__':
    k = KinopoiskSearch()
    k.collect_genres()
