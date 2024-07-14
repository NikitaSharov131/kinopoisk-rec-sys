import attrs
from typing import List
from datetime import datetime
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, management, columns
from cassandra.cqlengine import models
from cassandra.cqlengine.query import BatchQuery


class Genre(models.Model):
    __table_name__ = 'genre'
    name = columns.Text(primary_key=True)
    slug = columns.Text()


class User(models.Model):
    __table_name__ = 'user'
    id = columns.UUID(primary_key=True)
    name = columns.Text()


class RecommendedMovie(models.Model):
    __table_name__ = 'recommended_movie'
    user_id = columns.Text(primary_key=True)
    id = columns.Integer(primary_key=True)
    description = columns.Text()
    kp_url = columns.Text()
    name = columns.Text()
    # rating = columns.Map(key_type=columns.Text, value_type=columns.Float)
    movieLength = columns.Integer()
    year = columns.Integer()
    # votes = columns.Map(key_type=columns.Text, value_type=columns.Float)
    # genres = columns.List(value_type=columns.Map(key_type=columns.Text, value_type=columns.Text))


class KinopoiskScyllaDB:
    scylla_models = [Genre, User, RecommendedMovie]
    ks_name = 'kinopoisk'
    connection_name = 'kinopoisk-connection'

    def __init__(self):
        session = Cluster().connect()
        connection.register_connection(self.connection_name, session=session)
        management.create_keyspace_simple(self.ks_name, connections=[self.connection_name], replication_factor=1)
        self._init_model()

    def _init_model(self):
        for model in self.scylla_models:
            model.__connection__ = self.connection_name
            model.__keyspace__ = self.ks_name
            management.sync_table(model, keyspaces=[self.ks_name], connections=[self.connection_name])

    def insert_collection(self, collection: List[attrs.Factory], scylla_model: models.BaseModel):
        with BatchQuery(timestamp=datetime.now(), connection=self.connection_name) as b:
            for element in collection:
                scylla_model.batch(b).create(**attrs.asdict(element))

    def _drop_table(self, model: models.BaseModel):
        management.drop_table(keyspaces=[self.ks_name], connections=[self.connection_name], model=model)

    def get_collection_elements(self, model: models.BaseModel):
        for element in model.objects.all():
            yield element


if __name__ == '__main__':
    k = KinopoiskScyllaDB()
    k._drop_table(RecommendedMovie)
