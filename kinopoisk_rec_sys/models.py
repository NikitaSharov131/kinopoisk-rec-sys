from cassandra.cqlengine import models, columns
from attrs import define, AttrsInstance, fields
from typing import List, Optional
from datetime import datetime, timedelta


class ScyllaGenre(models.Model):
    __table_name__ = 'genre'
    name = columns.Text(primary_key=True)
    slug = columns.Text()


class ScyllaUser(models.Model):
    __table_name__ = 'user'
    id = columns.Integer(primary_key=True)
    name = columns.Text()
    preferred_genre = columns.Text()
    chat_id = columns.Integer()
    min_movies_rating = columns.Float()


class ScyllaRecommendedMovie(models.Model):
    __table_name__ = 'recommended_movie'
    user_id = columns.Integer(primary_key=True)
    id = columns.Integer(primary_key=True)
    description = columns.Text()
    kp_url = columns.Text()
    name = columns.Text()
    genres = columns.List(value_type=columns.Map(key_type=columns.Text, value_type=columns.Text))
    # rating = columns.Map(key_type=columns.Text, value_type=columns.Float)
    movieLength = columns.Integer()
    year = columns.Integer()
    # votes = columns.Map(key_type=columns.Text, value_type=columns.Float)


@define(frozen=True)
class Rating:
    kp: float
    imdb: Optional[float] = None
    filmCritics: Optional[float] = None
    russianFilmCritics: Optional[float] = None


@define(frozen=True)
class Votes:
    kp: int
    imdb: int
    filmCritics: int
    russianFilmCritics: int


@define(frozen=True)
class Genre:
    name: str
    slug: str = None


@define(kw_only=True)
class User:
    id: str = None
    name: str = None
    preferred_genre: Genre.name = None
    chat_id: str = None
    min_movies_rating: Rating = None


@define(frozen=True, kw_only=True)
class Movie(AttrsInstance):
    id: int
    name: str
    alternativeName: str
    enName: str
    year: int
    description: str
    shortDescription: str
    status: str
    rating: Rating
    votes: Votes
    movieLength: int
    ratingMpaa: str
    genres: List[Genre]


@define(frozen=True, kw_only=True)
class RecommendedMovie(Movie):
    user_id: User.id
    kp_url: str


@define()
class MovieQuery(AttrsInstance):
    type: str = "movie"
    page: int = 1
    limit: int = 50
    isSeries: str = "false"
    selectFields: List = [f.name for f in fields(Movie) if f.name not in ("kp_url")]


@define(frozen=True)
class PossibleValues(AttrsInstance):
    field: str


class NewMovieQuery(MovieQuery):
    createdAt: str = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
    updatedAt: str = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
