# coding: utf-8
# Module by ChatGPT
from .. import loader, utils

class MessageDeleterMod(loader.Module):
    """Модуль для удаления сообщений"""
    strings = {
        "name": "MessageDeleter",
        "deleted": "❌ Удалено {} сообщений.",
        "invalid_arg": "🚫 Укажите количество сообщений для удаления.",
    }

    async def delmsgcmd(self, message):
        """
        Использование: .delmsg <кол-во сообщений>
        Удаляет указанное количество ваших сообщений.
        """
        args = utils.get_args_raw(message)
        if not args or not args.isdigit():
            await utils.answer(message, self.strings("invalid_arg"))
            return

        count = int(args)
        if count < 1:
            await utils.answer(message, self.strings("invalid_arg"))
            return

        deleted = 0
        async for msg in message.client.iter_messages(
            message.chat_id, from_user="me", limit=count
        ):
            await msg.delete()
            deleted += 1

        await utils.answer(message, self.strings("deleted").format(deleted))