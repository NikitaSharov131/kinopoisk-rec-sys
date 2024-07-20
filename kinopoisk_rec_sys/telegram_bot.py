import json
import os
import uuid
from functools import lru_cache
from typing import List

import attrs
import requests
import telebot
from models import Genre, Rating, RecommendedMovie, User
from telebot import types

bot = telebot.TeleBot(os.environ.get("TOKEN_BOT"))

start_command = "/start"
movie_command = "/movie"
commands = [start_command, movie_command]
welcome = (
    "Привет! Давай выберем жанры фильмов, которые тебе нравятся."
    "\nЯ повторно не посоветую тебе уже ранее порекомендованный фильм."
)

kp_rec_sys_base_url = f'http://{os.environ.get("REC_SYS_ENDPOINT")}:8000'


def get(endpoint, query_params: dict = None):
    url = f"{kp_rec_sys_base_url}/{endpoint}"
    response = requests.get(url, params=query_params)
    try:
        response.raise_for_status()
    except requests.RequestException as exc:
        raise exc
    return response.json()


@lru_cache(maxsize=None)
def get_genres():
    response = get("genres")
    return [Genre(**genre) for genre in response["genres"]]


def is_user_exist(user: User):
    response = get(f"user/{user.id}")
    return [User(**u) for u in response.get("user_id")]


def get_recs(user: User):
    url = f"{kp_rec_sys_base_url}/recs"
    user.min_movies_rating = user.min_movies_rating.kp
    response = requests.post(url, data=json.dumps(attrs.asdict(user)))
    user.min_movies_rating = Rating(kp=user.min_movies_rating)
    return [RecommendedMovie(**r) for r in response.json().get("recs")]


def get_recommended_movie(user: User):
    response = get(f"recs/{user.id}")
    return response.json()


def swipe_next_movie(message, recs: List):
    bot.send_message(
        message.chat.id, string_rec_repr(recs.pop()), parse_mode="Markdown"
    )
    markup = types.ReplyKeyboardMarkup()
    markup.add(
        types.KeyboardButton("Еще!"),
        types.KeyboardButton("Конец"),
        types.KeyboardButton("Сменить жанр"),
    )
    bot.send_message(message.chat.id, "Хочешь еще?", reply_markup=markup)
    return message


def show_rec_movie(message, user, recs):
    if message.text == "Еще!" or message.text == "Да!":
        if not recs:
            recs = get_recs(user)
        swipe_next_movie(message, recs)
        bot.register_next_step_handler(message, show_rec_movie, user, recs)
    elif message.text == "Сменить жанр":
        markup = create_genre_markup()
        bot.send_message(message.chat.id, welcome, reply_markup=markup)
        bot.register_next_step_handler(message, process_genre, user)
    else:
        bot.send_message(
            message.chat.id,
            "Я закончил присылать рекомендации,"
            " если хочешь посмотреть их снова, пиши /start ",
            reply_markup=json.dumps({"hide_keyboard": True}),
        )
        return


def string_rec_repr(rec: RecommendedMovie):
    return f" Картина: [{rec.name}]({rec.kp_url}) \nДата выхода {rec.year} \nРейтинг {rec.rating}"


def process_user_rating(message, user):
    rating = message.text.replace(",", ".")
    if rating.replace(".", "").isdigit() and (0 < float(rating) < 10):
        user.min_movies_rating = Rating(kp=round(float(rating), 2))
        recs = get_recs(user)
        swipe_next_movie(message, recs)
        bot.register_next_step_handler(message, show_rec_movie, user, recs)
    else:
        msg = bot.reply_to(
            message,
            "Пожалуйста, укажи рейтинг корректно "
            "(это должно быть число в диапазоне от 0 до 10) ",
        )
        bot.register_next_step_handler(msg, process_user_rating, user)
        return


def create_genre_markup():
    markup = types.ReplyKeyboardMarkup()
    genres = get_genres()
    for i in range(0, len(genres) - 1, 2):
        markup.add(
            types.KeyboardButton(genres[i].name),
            types.KeyboardButton(genres[i + 1].name),
        )
    return markup


def process_genre(message, user):
    if message.text in [g.name for g in get_genres()]:
        user.preferred_genre = message.text
        reply = "Отлично, введи минимально допустимый рейтинг фильма (0 - 10):"
        bot.send_message(
            message.chat.id, reply, reply_markup=json.dumps({"hide_keyboard": True})
        )
        bot.register_next_step_handler(message, process_user_rating, user)
    else:
        markup = create_genre_markup()
        bot.send_message(
            message.chat.id,
            "Пожалуйста, укажи жанр из доступных...",
            reply_markup=markup,
        )
        bot.register_next_step_handler(message, process_genre, user)
        return


@bot.message_handler(content_types="text")
def handle_text(message):
    if message.text not in commands:
        reply_message = "Привет! Для того чтобы начать начать получать рекомендации от меня, введи /start"
        bot.send_message(message.chat.id, reply_message)
    elif message.text == start_command:
        handle_start(message)


@bot.message_handler(commands=["movie"])
def handle_movie(message, user: User):
    if user:
        reply = (
            f"Привет, {user.name}. Рад, что ты снова тут."
            f'\nЯ отправляю тебе рекомендации из жанра "{user.preferred_genre}".'
            f"\nМинимальный рейтинг {round(user.min_movies_rating.kp, 2)}. Продолжим?"
        )
        markup = types.ReplyKeyboardMarkup()
        markup.add(types.KeyboardButton("Да!"), types.KeyboardButton("Сменить жанр"))
        bot.send_message(message.chat.id, reply, reply_markup=markup)
        bot.register_next_step_handler(message, show_rec_movie, user, [])
    else:
        handle_text(message)


@bot.message_handler(commands=["start"])
def handle_start(message):
    user = User(
        id=message.from_user.id if message.from_user.id else uuid.uuid4(),
        name=message.from_user.username,
        chat_id=message.chat.id,
    )
    if hist_user := is_user_exist(user):
        hist_user = hist_user.pop()
        hist_user.min_movies_rating = Rating(kp=hist_user.min_movies_rating)
        handle_movie(message, hist_user)
        return
    markup = create_genre_markup()
    bot.send_message(message.chat.id, welcome, reply_markup=markup)
    bot.register_next_step_handler(message, process_genre, user)


bot.infinity_polling()
