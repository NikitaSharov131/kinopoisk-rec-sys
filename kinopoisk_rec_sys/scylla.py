import attrs
from typing import List
from datetime import datetime
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection, management, models, statements, operators
from cassandra.cqlengine.query import BatchQuery
from kinopoisk_rec_sys.models import ScyllaGenre, ScyllaUser, ScyllaRecommendedMovie


class KinopoiskScyllaDB:
    scylla_models = [ScyllaGenre, ScyllaUser, ScyllaRecommendedMovie]
    ks_name = 'kinopoisk'
    connection_name = 'kinopoisk-connection'

    def __init__(self):
        self._session = Cluster().connect()
        connection.register_connection(self.connection_name, session=self._session)
        management.create_keyspace_simple(self.ks_name, connections=[self.connection_name], replication_factor=1)
        self._init_model()

    def _init_model(self):
        for model in self.scylla_models:
            model.__connection__ = self.connection_name
            model.__keyspace__ = self.ks_name
            management.sync_table(model, keyspaces=[self.ks_name], connections=[self.connection_name])

    def insert_collection(self, collection: List[attrs.Factory], model: models.BaseModel):
        model.__keyspace__, model.__connection__ = self.ks_name, self.connection_name
        with BatchQuery(timestamp=datetime.now(), connection=self.connection_name) as b:
            for element in collection:
                model.batch(b).create(**element)

    def _drop_table(self, model: models.BaseModel):
        management.drop_table(keyspaces=[self.ks_name], connections=[self.connection_name], model=model)

    def get_collection_elements(self, model: models.BaseModel):
        model.__keyspace__, model.__connection__ = self.ks_name, self.connection_name
        for element in model.objects.all():
            yield element

    def filter_collection(self, model: models.BaseModel, column, column_value):
        model.__keyspace__, model.__connection__ = self.ks_name, self.connection_name
        condition = statements.WhereClause(field=column, operator=operators.EqualsOperator(),
                                           value=column_value)
        for element in model.objects.filter(condition).all():
            yield element


if __name__ == '__main__':
    k = KinopoiskScyllaDB()
    k._drop_table(ScyllaRecommendedMovie)

