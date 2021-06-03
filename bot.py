import asyncio
import logging
import os
from xml.etree import ElementTree

import requests
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

try:
    from config import TOKEN
except ImportError:
    TOKEN = os.environ["TOKEN"]
from messages import MESSAGES

logging.basicConfig(
    format="%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s [%(asctime)s] %(message)s",
    level=logging.DEBUG,
)

current_answers = []
correct = False
history = set()


class CurrentQuestion:
    def __init__(self, question_id):
        self.question = question_id


current_question = CurrentQuestion(None)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands=["start"])
async def process_start_command(message: types.Message):
    await message.reply(MESSAGES["start"])


@dp.message_handler(commands=["question"])
async def process_help_command(message: types.Message):
    r = requests.get(
        "https://db.chgk.info/xml/random/from_2010-01-01/types1/complexity2/limit1"
    )
    tree = ElementTree.fromstring(r.content)
    root = tree[0]
    question = root.find("Question").text
    question_id = root.find("QuestionId").text
    comment = root.find("Comments").text or ""
    answer = root.find("Answer").text.replace(".", "")
    current_answers.append(answer)
    await message.reply(question)
    current_question.question = question_id
    history.add(question_id)
    # await message.reply(answer)
    await asyncio.sleep(60)
    if question_id in history:
        await message.reply(f"Руша, осталось 10 секунд!")
    await asyncio.sleep(10)
    if question_id in history:
        await message.reply(
            f"<b>Правильный ответ</b>: {answer}\n \n <b>Комментарий</b>: {comment}",
            parse_mode="HTML",
        )
        # await message.reply(f"Комментарий: {comment}")
        history.remove(question_id)


@dp.message_handler(state="*")
async def process_pending(message: types.Message):
    if current_question.question in history:
        if message.text == current_answers[-1]:
            first_name = message.from_user.first_name
            last_name = message.from_user.last_name
            await message.reply(
                f"Верно, <b>{first_name} {last_name}</b>!",
                reply=False,
                parse_mode="HTML",
            )
            history.remove(current_question.question)
        else:
            await message.reply(
                "Увы, нет. Так Мыndex не выиграет чемпионат мира по ЧГК :(", reply=False
            )


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == "__main__":
    executor.start_polling(dp, on_shutdown=shutdown)
