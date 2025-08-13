# -*- coding: utf-8 -*-

from telethon import types
from .. import loader, utils

@loader.tds
class МассоваяРассылкаПоЧатамМод(loader.Module):
    strings = {
        "name": "Массовая рассылка по чатам",
        "message_sent": "<b>Сообщение отправлено в {} чатов.</b>",
        "no_text": "<b>Пожалуйста, введите текст сообщения.</b>",
        "author": "Модуль разработан: @Fanzlk"
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
        sent_to = 0
        for dialog in dialogs:
            entity = dialog.entity
            if isinstance(entity, (types.Chat, types.ChatForbidden)) or (isinstance(entity, types.Channel) and entity.megagroup):
                try:
                    await self.client.send_message(entity, text)
                    sent_to += 1
                except Exception as e:
                    print(f"Ошибка при отправке в чат {entity.id}: {e}")

        await utils.answer(message, self.strings["message_sent"].format(sent_to))