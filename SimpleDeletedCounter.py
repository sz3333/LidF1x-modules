# meta developer: LidF1x

from telethon.tl.types import User
from telethon.errors import ChatAdminRequiredError
from .. import loader, utils

@loader.tds
class DeletedCounterMod(loader.Module):
    """Считает кол-во удалённых аккаунтов в ЛС и чатах"""
    strings = {"name": "DeletedCounter"}

    async def delpmcmd(self, message):
        """Посчитать удалённых аккаунтов в личках"""
        await utils.answer(message, "💫 Считаю удалённые аккаунты в ЛС…")

        dialogs = await message.client.get_dialogs()
        deleted_count = 0

        for d in dialogs:
            ent = d.entity
            if isinstance(ent, User) and ent.deleted:
                deleted_count += 1

        await utils.answer(
            message,
            f"<emoji document_id=5449449325434266744>❄️</emoji> **В твоих ЛС найдено {deleted_count} удалённых аккаунтов.**\n\n"
            "_epstein_",
            parse_mode="md"
        )

    async def delchatcmd(self, message):
        """Посчитать удалённых юзеров в текущем чате"""
        chat = await message.get_chat()

        try:
            members = await message.client.get_participants(chat)
        except ChatAdminRequiredError:
            return await utils.answer(
                message,
                "⚠️ Мне нужны права, чтобы посмотреть участников чата "
            )

        deleted_count = sum(1 for m in members if isinstance(m, User) and m.deleted)

        await utils.answer(
            message,
            f"<emoji document_id=5449449325434266744>❄️</emoji> **В этом чате обнаружено {deleted_count} удалённых участников.**\n\n"
            "_epstein_",
            parse_mode="md"
        )

    async def delinfocmd(self, message):
        """Инфа и лайтовые подсказки по удалённым"""
        txt = (
            "🐾 **Как определяется удалённый аккаунт:**\n"
            "- `user.deleted == True`\n"
            "- Нет имени\n"
            "- Нет username\n\n"
            "✨ Ты можешь:\n"
            "• Чистить удалённые аккаунты из ЛС\n"
            "• Мониторить активность в чатах\n"
            "• Строить статистику (по желанию)\n\n"
            "_epstein_"
        )
        await utils.answer(message, txt, parse_mode="md")