__version__ = (1, 1, 0)
# meta developer: @ExclusiveFurry
from telethon.tl.types import Message
from telethon import events
from .. import loader, utils
import asyncio
import logging
import random

logger = logging.getLogger(__name__)

@loader.tds
class KisikAutoMod(loader.Module):
    """Автоматически ухаживает за котиком в @Kisik_Kotik_Bot"""

    strings = {
        "name": "KisikAuto",
        "started": "🐱 <b>Автоуход за котиком запущен!</b>\nБот: @Kisik_Kotik_Bot\nИнтервал: ~5 минут",
        "stopped": "🛑 <b>Автоуход за котиком остановлен</b>",
        "not_started": "❌ <b>Автоуход не запущен</b>",
        "bot_not_found": "❌ <b>Бот @Kisik_Kotik_Bot не найден в диалогах</b>",
        "error": "❌ <b>Ошибка:</b> {error}",
        "status_running": "🟢 <b>Автоуход активен</b>\nСледующий цикл через: < 5 минут",
        "status_stopped": "🔴 <b>Автоуход остановлен</b>"
    }

    def __init__(self):
        self.running = False
        self.task = None
        self.bot_username = "Kisik_Kotik_Bot"

    async def client_ready(self, client, db):
        self.client = client

    async def find_bot(self):
        try:
            async for dialog in self.client.iter_dialogs():
                if getattr(dialog.entity, "username", None) == self.bot_username:
                    return dialog.entity
            return None
        except Exception:
            logger.exception("Error finding bot")
            return None

    async def click_button_and_handle_response(self, bot_entity, button_text):
        try:
            # отправляем текст (как ты и хотел)
            await self.client.send_message(bot_entity, button_text)
            await asyncio.sleep(random.uniform(1.5, 3.5))

            messages = await self.client.get_messages(bot_entity, limit=10)

            for msg in messages:
                if msg.reply_markup and hasattr(msg.reply_markup, 'rows'):
                    buttons = []
                    for row in msg.reply_markup.rows:
                        for button in row.buttons:
                            if hasattr(button, 'data'):
                                buttons.append(button)

                    if buttons:
                        # небольшая пауза перед кликом, будто человек читает кнопки
                        await asyncio.sleep(random.uniform(0.4, 1.8))
                        random_button = random.choice(buttons)
                        await msg.click(data=random_button.data)
                        logger.info(f"Clicked inline button after {button_text}")
                        return True

            return False

        except Exception:
            logger.exception(f"Error in click_button_and_handle_response for {button_text}")
            return False

    async def care_cycle(self, bot_entity):
        actions = [
            "Clothes 🧢",
            "Check the kitty",
            "Go for a walk 🧭",
            "Feed",
            "Care",
            "Play"
        ]

        random.shuffle(actions)

        for action in actions:
            # иногда пропускаем действие, чтобы не было идеально регулярного паттерна
            if random.random() < 0.08:
                logger.info(f"Randomly skipped action: {action}")
                continue

            await self.click_button_and_handle_response(bot_entity, action)

            # неравномерная, более "человечная" пауза между действиями
            base_delay = random.uniform(1.2, 4.5)
            if random.random() < 0.15:
                # изредка более длинная пауза, будто отвлеклись
                base_delay += random.uniform(3, 10)
            await asyncio.sleep(base_delay)

        logger.info("Care cycle completed")

    async def auto_care_loop(self, bot_entity):
        while self.running:
            try:
                await self.care_cycle(bot_entity)

                # рандомизированный интервал между циклами (~5 мин ± разброс)
                base_interval = random.uniform(240, 420)
                if random.random() < 0.1:
                    # редкая длинная пауза, имитирующая "отошли от телефона"
                    base_interval += random.uniform(120, 600)
                await asyncio.sleep(base_interval)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in auto care loop")
                await asyncio.sleep(60)

    @loader.command(ru_doc="Запустить автоуход за котиком")
    async def kisikstart(self, message: Message):
        if self.running:
            await utils.answer(message, self.strings("started"))
            return

        bot_entity = await self.find_bot()
        if not bot_entity:
            await utils.answer(message, self.strings("bot_not_found"))
            return

        try:
            self.running = True
            self.task = asyncio.create_task(self.auto_care_loop(bot_entity))
            await utils.answer(message, self.strings("started"))

        except Exception as e:
            self.running = False
            await utils.answer(message, self.strings("error").format(error=str(e)))

    @loader.command(ru_doc="Остановить автоуход за котиком")
    async def kisikstop(self, message: Message):
        if not self.running:
            await utils.answer(message, self.strings("not_started"))
            return

        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        await utils.answer(message, self.strings("stopped"))

    @loader.command(ru_doc="Проверить статус автоухода")
    async def kisikstatus(self, message: Message):
        if self.running:
            await utils.answer(message, self.strings("status_running"))
        else:
            await utils.answer(message, self.strings("status_stopped"))