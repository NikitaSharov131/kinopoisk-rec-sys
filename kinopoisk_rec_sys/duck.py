import duckdb
import pyarrow
from pyarrow import parquet
from typing import List, Dict
import os
from pathlib import Path
from datetime import datetime
import random
from client import Movie
import attrs

parquet_folder = Path(os.path.join(Path(os.getcwd()).parent, 'parquet'))


def write_parquet_file(table: pyarrow.Table):
    parquet_file = f"{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}_{random.randint(0, 10000)}"
    parquet.write_table(table, Path(os.path.join(parquet_folder, f'{parquet_file}.parquet')))


class KinopoiskDuckDb:

    def __init__(self):
        if self._duck_is_alive and self._is_data_present:
            self._define_tables()

    def _define_tables(self):
        ...

    @property
    def _duck_is_alive(self):
        return True

    @property
    def _is_data_present(self):
        return True

    @staticmethod
    def create_parquet(movies: List[Movie]):
        struct = pyarrow.array([attrs.asdict(m) for m in movies])
        parquet_file = pyarrow.Table.from_struct_array(struct)
        write_parquet_file(parquet_file)

    def fetch_movies(self):
        cursor = duckdb.connect()
        print(cursor.execute('SELECT 42').fetchall())


if __name__ == '__main__':
    k = KinopoiskDuckDb()
    k.fetch_movies()
