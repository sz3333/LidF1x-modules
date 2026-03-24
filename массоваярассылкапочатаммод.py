# -*- coding: utf-8 -*-
# meta developer: @ExclusiveFurry

import asyncio
import random
from telethon import types
from .. import loader, utils

@loader.tds
class МассоваяРассылкаПоЧатамМод(loader.Module):
    strings = {
        "name": "Массовая рассылка по чатам",
        "no_text": "<b>Пожалуйста, введите текст сообщения.</b>",
        "author": "Модуль разработан: @ExclusiveFurry",
        "progress": (
            "📢 <b>Рассылка начата</b>\n\n"
            "📊 <b>Прогресс:</b> {current}/{total} чатов\n"
            "✅ <b>Успешно:</b> {success}\n"
            "❌ <b>Ошибка:</b> {errors}"
        ),
        "done": (
            "✅ <b>Рассылка завершена</b>\n\n"
            "📊 <b>Статистика:</b>\n"
            "• Всего чатов: {total}\n"
            "• Успешно: {success}\n"
            "• Ошибок: {errors}"
        ),
    }

    async def client_ready(self, client, db):
        self.client = client
        print(self.strings["author"])

    async def mymsgcmd(self, message):
        text = utils.get_args_raw(message)
        if not text:
            await utils.answer(message, self.strings["no_text"])
            return

        dialogs = await self.client.get_dialogs()

        chats = [
            dialog.entity
            for dialog in dialogs
            if isinstance(dialog.entity, (types.Chat, types.ChatForbidden))
            or (isinstance(dialog.entity, types.Channel) and dialog.entity.megagroup)
        ]

        # Перемешиваем чаты в случайном порядке
        random.shuffle(chats)

        total = len(chats)
        success = 0
        errors = 0

        status_msg = await utils.answer(
            message,
            self.strings["progress"].format(
                current=0, total=total, success=success, errors=errors
            ),
        )

        for i, entity in enumerate(chats, start=1):
            try:
                await self.client.send_message(entity, text)
                success += 1
            except Exception as e:
                errors += 1
                print(f"Ошибка при отправке в чат {entity.id}: {e}")

            await utils.answer(
                status_msg,
                self.strings["progress"].format(
                    current=i, total=total, success=success, errors=errors
                ),
            )

            if i < total:
                # Случайная задержка от 4 до 8 секунд
                await asyncio.sleep(random.uniform(4, 8))

        await utils.answer(
            status_msg,
            self.strings["done"].format(total=total, success=success, errors=errors),
        )
