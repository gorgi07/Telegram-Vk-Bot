import os
import random
import time
from pathlib import Path, PosixPath

import requests
import vk
from telebot import TeleBot
from telebot.types import (InputMediaAudio, InputMediaDocument,
                           InputMediaPhoto, InputMediaVideo)


BASE_DIR_PATH = Path(__file__).resolve().parent    # Текущий путь до папки с проектом
LAST_POST_ID_FILENAME = "last_post_id.txt"    # Название файла куда сохраняется последний отправленный id поста

# vk admin токен
TOKEN = "VK_ADMIN_TOKEN"

OWNER_ID = -187692562   # id сообщества вконтакте откуда берутся посты
CHAT_ID = -1001834534408    # id телеграмм канала куда отправляются посты
# id обязательно со знаком "-"

def save_last_post_id(post_id: int) -> None:
    """
    Сохраняет в файл id последней отправленной записи сообщества
    """
    file_path = BASE_DIR_PATH.joinpath(LAST_POST_ID_FILENAME)   # Путь до файла
    with open(file_path, "w", encoding="UTF-8") as file:    # "w" - запись
        file.write(f"{post_id}")    # Сохраняем переданный id записи в файл


def get_last_post_id() -> int | None:
    """
    Получаем из файла id последней отправленной записи сообщества
    """
    last_post_id = None
    file_path = BASE_DIR_PATH.joinpath(LAST_POST_ID_FILENAME)   # Путь до файла
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="UTF-8") as file:    # "r" - чтение
            last_post_id = int(file.read())     # читаем id последнего поста
    return last_post_id


def get_new_post(vk_api: vk.API, last_post_id: int | None) -> dict:
    """
    Получаем новые посты
    """
    new_post = None
    posts = vk_api.wall.get(owner_id=OWNER_ID, v=5.131)         # Получаем 100 последних постов сообщества
    for post in posts["items"]:
        if post["id"] == last_post_id:      # Если посты еще не присылались в тг, то берем последний пост из сообщества
            break
        new_post = post
    return new_post


def get_video_link(files: dict[str, str]) -> int | None:
    """
    Получаем ссылку на видео
    """
    link = None
    resolution = 0
    for file in files:
        try:
            if int(file.split("_")[-1]) > resolution:
                resolution = int(file.split("_")[-1])
                link = files[file]
        except Exception as e:
            print(e)
    return link


def save_video(link: str) -> PosixPath:
    """
    Сохраняет видео из поста в директорию с ботом
    """
    r = requests.get(link)
    file_name = "".join([random.choice(list("123456qwertyui"))      # даем имя файлу с видео
                        for i in range(12)])
    file_path = BASE_DIR_PATH.joinpath(file_name)   # путь до файла
    with open(file_path, "wb") as file:     # запись видео
        file.write(r.content)
    return file_path


def send_post(bot: TeleBot, vk_api: TeleBot, new_post: dict) -> None:
    """
    Отправляет пост из вк сообщества в канал тг
    """
    text = new_post["text"]

    if not text and "copy_history" in new_post:
        text = new_post["copy_history"][0]["text"]
    if len(text) > 1024 or "attachments" not in new_post or not new_post["attachments"]:
        bot.send_message(chat_id=CHAT_ID, text=text)  # Если текст поста больше 1024 символов, отправляется только текст
    else:
        attachments = []

        for ind, attachment in enumerate(new_post["attachments"]):
            if attachment["type"] == "photo":    # если фото, то отправляем его
                media = InputMediaPhoto(
                    attachment["photo"]["sizes"][-1]["url"])

            elif attachment["type"] == "video":     # если видео, то
                videos = (f"{attachment['video']['owner_id']}_"
                          f"{attachment['video']['id']}_"
                          f"{attachment['video']['access_key']},")
                files = vk_api.video.get(videos=videos,
                                         v=5.131)["items"][0]["files"]

                video_link = get_video_link(files)
                video_path = save_video(video_link)
                video_stat = os.stat(video_path)        # Ищем видео с самым лучшим разрешением

                if video_stat.st_size / 1024 ** 2 >= 50:    # проверяем вес видео
                    print("Видео файл слишком большой")
                    media = None
                else:
                    video_file = open(video_path, "rb")
                    media = InputMediaVideo(video_file.read())      # отправляем видео
                    video_file.close()
                    os.remove(video_path)                 # Удаляем файл видео с диска
            elif attachment["type"] == "doc":
                media = InputMediaDocument(attachment["doc"]["url"],
                                           attachment["doc"]["title"])
            elif attachment["type"] == "audio":
                media = InputMediaAudio(attachment["audio"]["url"],
                                        attachment["audio"]["artist"] + ".mp3")
            else:
                media = None

            if ind == 0 and media is not None:
                media.caption = text
            attachments.append(media)

        attachments = [media for media in attachments if media is not None]
        if attachments:
            bot.send_media_group(chat_id=CHAT_ID, media=attachments)


def auto_posting(bot: TeleBot):
    """
    Автопостинг
    """
    vk_api = vk.API(access_token=TOKEN)    # Получаем id последнего отправленного поста
    last_post_id = get_last_post_id()
    print(last_post_id)
    new_post = get_new_post(vk_api, last_post_id)    # Получаем новый пост из вк сообщества, если он есть, если нет то None
    if new_post is not None:
        send_post(bot, vk_api, new_post)        # Отправляем пост из сообщества вк в тг канал
        save_last_post_id(new_post["id"])        # Сохраняем id поста из сообщества вк, который отправили в тг
    else:
        print("Автопостинг: новых записей нет!")


def auto_posting_process(bot: TeleBot):
    """
    Запуск автопостинга
    """
    while True:
        auto_posting(bot)
        print("Автопостинг: засыпаю на 2 минуты")
        time.sleep(120)


if __name__ == "__main__":
    auto_posting()
