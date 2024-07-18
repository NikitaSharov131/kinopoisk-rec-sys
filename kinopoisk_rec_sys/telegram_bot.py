import telebot
from telebot import types
import os
from search import KinopoiskSearch
from models import User
import uuid
from functools import lru_cache

bot = telebot.TeleBot(os.environ.get("TOKEN"))

welcome = """ Привет! Я могу помочь тебе в поиске новых фильмов. Пиши /start чтобы начать... """

start_command = '/start'
movie_command = '/movie'
commands = [start_command, movie_command]
user = User()


@lru_cache(maxsize=None)
def get_genres():
    return KinopoiskSearch().collect_genres()


def process_user_rating():
    ...


def process_genre(message):
    if message.text in get_genres():
        user.preferred_genres = message.text
        bot.register_next_step_handler(message, process_user_rating)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, укажи жанр из доступных...")
        bot.register_next_step_handler(message, process_genre)


@bot.message_handler(content_types='text')
def handle_text(message):
    if message.text not in commands:
        reply_message = 'Привет! Для того чтобы начать начать получать рекомендации от меня, введи /start'
        bot.send_message(message.chat.id, reply_message)
    elif message.text == start_command:
        handle_start(message)


def save_chat_id(chat_id):
    return False, {}


# добавить случай когда введен просто текст

@bot.message_handler(commands=['start'])
def handle_start(message):  # переписать на апи
    user_id = message.from_user.id if message.from_user.id else uuid.uuid4()
    user.id = user_id
    user.name = message.from_user.username
    exist, params = save_chat_id(user)
    user_name = message.chat.username
    if exist:
        reply = (f'Привет, {user_name}. Рад, что ты снова тут.'
                 f' Сейчас я отправляю тебе фильмы cо следующими параметрами {params}')
    else:
        reply = 'Привет! Давай выберем жанры фильмов, которые тебе нравятся'
    markup = types.ReplyKeyboardMarkup()
    genres = get_genres()
    # запускать обработку пока текст не будет включать одну из команд или пока не будет включать жанр фильма
    for i in range(0, len(genres) - 1, 2):
        markup.add(types.KeyboardButton(genres[i].name), types.KeyboardButton(genres[i + 1].name))
    bot.send_message(message.chat.id, reply)
    # bot.register_next_step_handler(message, process_genre)


@bot.message_handler(func=lambda m: True, content_types=['new_chat_participant'])
def new_chat(message):
    bot.reply_to(message, welcome)


bot.infinity_polling()
