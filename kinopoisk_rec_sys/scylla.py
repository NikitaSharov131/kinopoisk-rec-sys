from cassandra.cluster import Cluster
from uuid import uuid4
from cassandra.cqlengine import connection, management, columns
from cassandra.cqlengine.models import Model
import attrs
from typing import List
from cassandra.cqlengine.query import BatchQuery
from datetime import datetime


class Genre(Model):
    __table_name__ = 'genre'
    name = columns.Text(primary_key=True)
    slug = columns.Text()


class User(Model):
    __table_name__ = 'user'
    id = columns.UUID(primary_key=True)
    name = columns.Text()


class KinopoiskScyllaDB:
    models = [Genre, User]
    ks_name = 'kinopoisk'
    connection_name = 'kinopoisk-connection'

    def __init__(self):
        session = Cluster().connect()
        connection.register_connection(self.connection_name, session=session)
        management.create_keyspace_simple(self.ks_name, connections=[self.connection_name], replication_factor=1)
        self._init_model()

    def _init_model(self):
        for model in self.models:
            model.__connection__ = self.connection_name
            model.__keyspace__ = self.ks_name
            management.sync_table(model, keyspaces=[self.ks_name], connections=[self.connection_name])

    def insert_collection(self, collection: List[attrs.Factory]):
        with BatchQuery(timestamp=datetime.now(), connection=self.connection_name) as b:
            for element in collection:
                row = attrs.asdict(element)
                row['uuid'] = uuid4()
                Genre.batch(b).create(**row)

    def _drop_table(self, model: Model):
        management.drop_table(keyspaces=[self.ks_name], connections=[self.connection_name], model=model)

    def get_collection_elements(self):
        return


if __name__ == '__main__':
    k = KinopoiskScyllaDB()
    k.get_collection_elements()
