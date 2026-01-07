from .. import loader, utils
import asyncio

@loader.tds
class WordScanner(loader.Module):
    """Сканирует и удаляет сообщения по слову"""

    strings = {
        "name": "WordScanner",
        "no_word": "😿 Укажи слово для поиска!",
        "scanning": "🐾 Сканирую чат...",
        "found": "✨ Найдено сообщений: <b>{}</b>",
        "deleting": "🔥 Удаляю сообщения...",
        "deleted": "🗑 Удалено сообщений: <b>{}</b>",
    }

    async def _scan_messages(self, chat, word):
        """Возвращает список id сообщений с нужным словом"""
        ids = []
        async for msg in self.client.iter_messages(chat):
            text = getattr(msg, "text", None)  # безопасно достаем текст
            if isinstance(text, str) and word.lower() in text.lower():
                ids.append(msg.id)
        return ids

    async def findbwcmd(self, message):
        """.findbw <слово> — ищет сообщения с этим словом"""
        word = utils.get_args_raw(message)
        if not word:
            await utils.answer(message, self.strings("no_word"))
            return

        chat = message.chat_id
        await utils.answer(message, self.strings("scanning"))
        ids = await self._scan_messages(chat, word)
        await utils.answer(message, self.strings("found").format(len(ids)))

    async def delbwcmd(self, message):
        """.delbw <слово> — удаляет сообщения с этим словом (только если ты админ)"""
        word = utils.get_args_raw(message)
        if not word:
            await utils.answer(message, self.strings("no_word"))
            return

        chat = message.chat_id
        await utils.answer(message, self.strings("deleting"))
        ids = await self._scan_messages(chat, word)

        if ids:
            try:
                await self.client.delete_messages(chat, ids)
            except Exception as e:
                await utils.answer(message, f"❗ Ошибка при удалении: {e}")
                return

        await utils.answer(message, self.strings("deleted").format(len(ids)))