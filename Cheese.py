# meta developer: @ExclusiveFurry
# scope: hikka_only
# scope: hikka_min 1.6.2

from hikkatl.types import Message
from hikkatl.errors import BadRequestError
from .. import loader, utils
import asyncio

@loader.tds
class CheeseModule(loader.Module):
    """Модуль для отправки сыра 🧀"""

    strings = {
        "name": "CheeseSender",
        "already_cheesing": "Уже сыримся! 🧀",
        "start_cheesing": "Начинаю сырить каждые 10 секунд! 🧀",
        "not_cheesing": "Мы и так не сырим! 🧀",
        "stop_cheesing": "Стоп! Сырок закончился. 🧀❌",
    }

    strings_ru = {
        "already_cheesing": "Уже сыримся! 🧀",
        "start_cheesing": "Начинаю сырить каждые 10 секунд! 🧀",
        "not_cheesing": "Мы и так не сырим! 🧀",
        "stop_cheesing": "Стоп! Сырок закончился. 🧀❌",
    }

    def __init__(self):
        self.tasks = {}

    async def client_ready(self, client, db):
        self._client = client

    async def send_cheese(self, chat_id: int):
        try:
            while True:
                await self._client.send_message(chat_id, "🧀")
                await asyncio.sleep(10)
        except (asyncio.CancelledError, BadRequestError):
            pass

    @loader.command(ru_doc="Начать сырить каждые 10 секунд")
    async def сырcmd(self, message: Message):
        """Начать отправлять сыр"""
        chat_id = utils.get_chat_id(message)

        if chat_id in self.tasks:
            await utils.answer(message, self.strings("already_cheesing"))
            return

        self.tasks[chat_id] = asyncio.create_task(self.send_cheese(chat_id))
        await utils.answer(message, self.strings("start_cheesing"))

    @loader.command(ru_doc="Остановить сыр")
    async def стопсырcmd(self, message: Message):
        """Остановить отправку сыра"""
        chat_id = utils.get_chat_id(message)

        task = self.tasks.get(chat_id)
        if not task:
            await utils.answer(message, self.strings("not_cheesing"))
            return

        task.cancel()
        del self.tasks[chat_id]
        await utils.answer(message, self.strings("stop_cheesing"))

    async def on_unload(self):
        for task in self.tasks.values():
            task.cancel()
        self.tasks.clear()
