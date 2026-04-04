# meta developer: LidF1x.

from .. import loader, utils
import asyncio
import re

try:
    import pymorphy3
    _morph = pymorphy3.MorphAnalyzer()
    _MORPH_OK = True
except ImportError:
    _MORPH_OK = False

# Токенизация: только слова (без знаков препинания)
_RE_WORD = re.compile(r"[а-яёa-z]+", re.IGNORECASE)

# Батч для delete_messages (Telegram лимит — 100 за раз)
_BATCH = 100
# Обновлять прогресс каждые N сообщений
_PROGRESS_STEP = 200


def _lemma(word: str) -> str:
    """Нормальная форма слова (если морфология доступна)."""
    if not _MORPH_OK:
        return word.lower()
    return _morph.parse(word)[0].normal_form


def _lemmas_of_query(query: str) -> set[str]:
    """Леммы всех слов запроса."""
    return {_lemma(w) for w in _RE_WORD.findall(query)}


def _msg_matches(text: str, query_lemmas: set[str], query_raw: str) -> bool:
    """
    Сообщение считается совпадением если:
    - простое вхождение подстроки (для фраз / латиницы), ИЛИ
    - пересечение лемм слов сообщения с леммами запроса (для морфологии).
    """
    low = text.lower()
    # быстрый путь: прямое вхождение
    if query_raw.lower() in low:
        return True
    if not _MORPH_OK:
        return False
    # морфологический путь
    msg_lemmas = {_lemma(w) for w in _RE_WORD.findall(low)}
    return bool(query_lemmas & msg_lemmas)


async def _delete_batched(client, chat, ids: list[int]) -> int:
    """Удаляет сообщения батчами по _BATCH, возвращает кол-во успешно удалённых."""
    deleted = 0
    for i in range(0, len(ids), _BATCH):
        chunk = ids[i : i + _BATCH]
        try:
            await client.delete_messages(chat, chunk)
            deleted += len(chunk)
        except Exception:
            pass  # часть могла уже быть удалена
        await asyncio.sleep(0.05)  # небольшая пауза, чтобы не флудить
    return deleted


@loader.tds
class WordScanner(loader.Module):
    """Сканирует и удаляет сообщения по слову (с морфологией)"""

    strings = {
        "name": "WordScanner",
        "no_word": "😿 Укажи слово для поиска!",
        "scanning": (
            "🔍 Сканирую... проверено <b>{checked}</b> сообщ."
            " | найдено <b>{found}</b>"
            "{morph_hint}"
        ),
        "found": (
            "✅ Готово! Найдено <b>{found}</b> из <b>{checked}</b> сообщений."
            "{morph_hint}"
        ),
        "deleting": "🔥 Удаляю <b>{}</b> сообщений...",
        "deleted": "🗑 Удалено <b>{deleted}</b> из <b>{total}</b> найденных.",
        "no_found": "🤷 Сообщений с <code>{}</code> не найдено.",
        "morph_on": "\n<i>🧠 Морфология вкл., формы: {}</i>",
        "morph_off": "\n<i>⚠️ pymorphy3 не установлен — только точное совпадение</i>",
    }

    async def _scan(
        self,
        message,
        word: str,
        limit: int | None,
        live: bool = True,
    ) -> list[int]:
        """
        Сканирует чат, возвращает список id сообщений.
        live=True — обновляет сообщение во время сканирования.
        """
        chat = message.chat_id
        query_lemmas = _lemmas_of_query(word)

        morph_hint = ""
        if _MORPH_OK:
            sample = ", ".join(sorted(query_lemmas)[:5])
            morph_hint = self.strings("morph_on").format(sample)
        else:
            morph_hint = self.strings("morph_off")

        ids: list[int] = []
        checked = 0

        async for msg in self.client.iter_messages(chat, limit=limit):
            text = getattr(msg, "text", None) or getattr(msg, "message", None)
            if isinstance(text, str) and _msg_matches(text, query_lemmas, word):
                ids.append(msg.id)
            checked += 1

            if live and checked % _PROGRESS_STEP == 0:
                await utils.answer(
                    message,
                    self.strings("scanning").format(
                        checked=checked,
                        found=len(ids),
                        morph_hint=morph_hint,
                    ),
                )

        return ids, checked, morph_hint

    async def findbwcmd(self, message):
        """.findbw <слово> [лимит] — ищет сообщения (морфология)"""
        args = utils.get_args_raw(message).split()
        if not args:
            await utils.answer(message, self.strings("no_word"))
            return

        word = args[0]
        limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

        await utils.answer(
            message,
            self.strings("scanning").format(checked=0, found=0, morph_hint=""),
        )

        ids, checked, morph_hint = await self._scan(message, word, limit, live=True)

        await utils.answer(
            message,
            self.strings("found").format(
                found=len(ids),
                checked=checked,
                morph_hint=morph_hint,
            ),
        )

    async def delbwcmd(self, message):
        """.delbw <слово> [лимит] — удаляет сообщения с этим словом (морфология)"""
        args = utils.get_args_raw(message).split()
        if not args:
            await utils.answer(message, self.strings("no_word"))
            return

        word = args[0]
        limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

        await utils.answer(
            message,
            self.strings("scanning").format(checked=0, found=0, morph_hint=""),
        )

        ids, checked, morph_hint = await self._scan(message, word, limit, live=True)

        if not ids:
            await utils.answer(message, self.strings("no_found").format(word))
            return

        await utils.answer(message, self.strings("deleting").format(len(ids)))

        deleted = await _delete_batched(self.client, message.chat_id, ids)

        await utils.answer(
            message,
            self.strings("deleted").format(deleted=deleted, total=len(ids)),
    )
                        
