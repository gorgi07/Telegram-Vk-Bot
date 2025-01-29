import telebot
import sqlite3
import os
from pathlib import Path
from threading import Thread
from autopost import auto_posting_process
from telebot import types

bot = telebot.TeleBot("TOKEN")     # токен телеграмм бота
BASE_DIR_PATH = Path(__file__).resolve().parent
INFOMATION_FALENAME = "information.txt"

@bot.message_handler(commands=['start'])    # отправляет сообщения при команде /start
def start(message: types.Message) -> None:
    bot.send_message(message.chat.id, "Привет👋")
    bot.send_message(message.chat.id, "Я бот помощник и я буду помогать тебе ориентироваться в нашей системе. "
                                      "Чтобы ознакомиться с полным списком моих умений, воспользуйтесь командой /help .")


@bot.message_handler(commands=['help'])     # отправляет сообщения при команде /help и вызывает reply клавиатуру
def help(message: types.Message) -> None:
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row("Организация 🏫", "Новости 🎆")
    keyboard.row("Расписание уроков 📋", "Звонки 🔔")
    keyboard.row("Поддержка 🛠")
    bot.send_message(message.chat.id, """Вот всё, что я умею:
/organization - подробнее узнать о нашей организации 🏫
/events - события и мероприятия 🎆
/timetable - здесь можно узнать актуальное расписание занятий 📋
/jingle - расписание звонков 🔔
/support - сюда вы можете сообщить о неисправности бота 🛠""", reply_markup=keyboard)


@bot.message_handler(commands=['organization'])     # отправляет текст и файлы при коман
def organization(message: types.Message) -> None:
    file_path = BASE_DIR_PATH.joinpath(INFOMATION_FALENAME)   # Путь до файла
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="UTF-8") as file:    # "r" - чтение
            information = str(file.read())
            bot.send_message(message.chat.id, information)
    bot.send_document(message.chat.id, open(
        "Организация.pdf", "rb"))
    bot.send_document(message.chat.id, open(
        "Банковские реквизиты.pdf", "rb"))
    bot.send_document(message.chat.id, open(
        "Режим образовательного процесса.pdf", "rb"))
    bot.send_document(message.chat.id, open(
        "Режим работы.pdf", "rb"))


@bot.message_handler(commands=['events'])
def events(message: types.Message) -> None:
    markup = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton("Telegram", url='https://t.me/gboy_biulu')
    button_2 = types.InlineKeyboardButton("VK", url='https://vk.com/gbou_biuli')
    button_3 = types.InlineKeyboardButton("Сайт", url='https://bel-licei-inter.ru')
    markup.add(button_1, button_2)
    markup.add(button_3)
    bot.send_message(message.chat.id, "Следите за новостями у нас в Телеграм канале, группе ВК или на сайте",
                     reply_markup=markup)

@bot.message_handler(commands=['timetable'])
def timetable(message: types.Message) -> None:
    bot.send_document(message.chat.id, open(
       "Расписание_общее.pdf", "rb"))

@bot.message_handler(commands=['jingle'])
def jingle(message: types.Message) -> None:
    conn = sqlite3.connect("Звонки.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM 'Звонки'")
    results = cur.fetchmany(10)
    results = """
    """.join(" ".join(tup) for tup in results)
    bot.send_message(message.chat.id, results)


@bot.message_handler(commands=['support'])
def support(message: types.Message) -> None:
    markup = types.InlineKeyboardMarkup()
    button_1 = types.InlineKeyboardButton("TG", url='https://t.me/nyrsy1tan')
    button_2 = types.InlineKeyboardButton("VK", url='https://vk.com/nyrsy1tan')
    button_3 = types.InlineKeyboardButton("MAIL", url='mailto:erokhin.egor07@gmail.com')
    markup.add(button_1, button_2)
    markup.add(button_3)
    bot.send_message(message.chat.id, """Сообщить об ошибке вы можете сюда:
    TG: @nyrsy1tan
    VK: @nyrsy1tan
    MAIL: erokhin.egor07@gmail.com
    """, reply_markup=markup)

@bot.message_handler(content_types=['text'])
def message_reply(message: types.Message) -> None:
    if message.text == "Организация 🏫":
        organization(message)
    elif message.text == "Новости 🎆":
        events(message)
    elif message.text == "Расписание уроков 📋":
        timetable(message)
    elif message.text == "Звонки 🔔":
        jingle(message)
    elif message.text == "Поддержка 🛠":
        support(message)
    else:
        bot.send_message(message.chat.id, "Я тебя не понимаю 😔")

def run_bot() -> None:
    bot.polling(none_stop=True, interval=0)


if __name__ == "__main__":
    bot_th = Thread(target=run_bot)
    autopost_th = Thread(target=auto_posting_process, args=(bot,))
    bot_th.start()
    autopost_th.start()
