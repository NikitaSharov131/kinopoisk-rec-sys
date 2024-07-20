import json

import telebot
from telebot import types
import os
from search import KinopoiskSearch
from models import User, Rating, RecommendedMovie
import uuid
from functools import lru_cache
from typing import List

bot = telebot.TeleBot(os.environ.get("TOKEN"))

start_command = '/start'
movie_command = '/movie'
commands = [start_command, movie_command]
welcome = ('Привет! Давай выберем жанры фильмов, которые тебе нравятся.'
           '\nЯ повторно не посоветую тебе уже ранее порекомендованный фильм.')


@lru_cache(maxsize=None)
def get_genres():
    return KinopoiskSearch().collect_genres()


def show_rec_movie(message, user, recs, recs_hist: List[int] = None):
    if message.text == 'Еще!' or message.text == 'Да!':
        if not recs:
            recs = KinopoiskSearch().get_recs(user, recs_hist)
            recs_hist = KinopoiskSearch().recommended_movie(user.id)
        bot.send_message(message.chat.id, string_rec_repr(recs.pop()), parse_mode='Markdown')
        markup = types.ReplyKeyboardMarkup()
        markup.add(types.KeyboardButton("Еще!"), types.KeyboardButton("Конец"), types.KeyboardButton("Сменить жанр"))
        bot.send_message(message.chat.id, "Хочешь еще?", reply_markup=markup)
        bot.register_next_step_handler(message, show_rec_movie, user, recs, recs_hist)
    elif message.text == 'Сменить жанр':
        markup = create_genre_markup()
        bot.send_message(message.chat.id, welcome, reply_markup=markup)
        bot.register_next_step_handler(message, process_genre, user)
    else:
        bot.send_message(message.chat.id, "Я закончил присылать рекомендации,"
                                          " если хочешь посмотреть их снова, пиши /start ",
                         reply_markup=json.dumps({'hide_keyboard': True}))
        return


def string_rec_repr(rec: RecommendedMovie):
    return f" Картина: [{rec.name}]({rec.kp_url}) \nДата выхода {rec.year} \nРейтинг {rec.rating.kp}"


def process_user_rating(message, user):
    rating = message.text.replace(",", ".")
    if rating.replace(".", "").isdigit() and (0 < float(rating) < 10):
        user.min_movies_rating = Rating(kp=round(float(rating), 2))
        recs = KinopoiskSearch().get_recs(user)
        bot.send_message(message.chat.id, string_rec_repr(recs.pop()), parse_mode='Markdown')
        markup = types.ReplyKeyboardMarkup()
        markup.add(types.KeyboardButton("Еще!"), types.KeyboardButton("Конец"), types.KeyboardButton("Сменить жанр"))
        bot.send_message(message.chat.id, "Хочешь еще?", reply_markup=markup)
        bot.register_next_step_handler(message, show_rec_movie, user, recs)
    else:
        msg = bot.reply_to(message, 'Пожалуйста, укажи рейтинг корректно '
                                    '(это должно быть число в диапазоне от 0 до 10) ')
        bot.register_next_step_handler(msg, process_user_rating, user)
        return


def create_genre_markup():
    markup = types.ReplyKeyboardMarkup()
    genres = get_genres()
    for i in range(0, len(genres) - 1, 2):
        markup.add(types.KeyboardButton(genres[i].name), types.KeyboardButton(genres[i + 1].name))
    return markup


def process_genre(message, user):
    if message.text in [g.name for g in get_genres()]:
        user.preferred_genre = message.text
        reply = "Отлично, введи минимально допустимый рейтинг фильма (0 - 10):"
        bot.send_message(message.chat.id, reply, reply_markup=json.dumps({'hide_keyboard': True}))
        bot.register_next_step_handler(message, process_user_rating, user)
    else:
        markup = create_genre_markup()
        bot.send_message(message.chat.id, "Пожалуйста, укажи жанр из доступных...", reply_markup=markup)
        bot.register_next_step_handler(message, process_genre, user)
        return


@bot.message_handler(content_types='text')
def handle_text(message):
    if message.text not in commands:
        reply_message = 'Привет! Для того чтобы начать начать получать рекомендации от меня, введи /start'
        bot.send_message(message.chat.id, reply_message)
    elif message.text == start_command:
        handle_start(message)


@bot.message_handler(commands=['movie'])
def handle_movie(message, user: User, history_recs: List = None):
    if user:
        reply = (f'Привет, {user.name}. Рад, что ты снова тут.'
                 f'\nЯ отправляю тебе рекомендации из жанра "{user.preferred_genre}".'
                 f'\nМинимальный рейтинг {round(user.min_movies_rating.kp, 2)}. Продолжим?')
        markup = types.ReplyKeyboardMarkup()
        markup.add(types.KeyboardButton("Да!"), types.KeyboardButton("Сменить жанр"))
        bot.send_message(message.chat.id, reply, reply_markup=markup)
        bot.register_next_step_handler(message, show_rec_movie, user, [], history_recs)
    else:
        handle_text(message)


def is_user_id_exist(user_id):
    user = KinopoiskSearch().is_user_exist(user_id)
    if user:
        user = User(**user.pop())
        user.min_movies_rating = Rating(kp=user.min_movies_rating)
        return user


@bot.message_handler(commands=['start'])
def handle_start(message):
    user = User(id=message.from_user.id if message.from_user.id else uuid.uuid4(),
                name=message.from_user.username, chat_id=message.chat.id)
    if hist_user := is_user_id_exist(user.id):
        history_recs = KinopoiskSearch().recommended_movie(user.id)
        handle_movie(message, hist_user, history_recs)
        return
    markup = create_genre_markup()
    bot.send_message(message.chat.id, welcome, reply_markup=markup)
    bot.register_next_step_handler(message, process_genre, user)


bot.infinity_polling()
