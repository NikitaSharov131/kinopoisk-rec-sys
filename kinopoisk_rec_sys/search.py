from kinopoisk_rec_sys.api_client import KinopoiskApiClient


class KinopoiskSearch:
    def __init__(self):
        self._api = KinopoiskApiClient()

    def start_search(self):
        movies = self._api.get_movie()
        print(movies)



if __name__ == '__main__':
    k = KinopoiskSearch()
    k.start_search()
