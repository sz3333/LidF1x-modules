from telethon import events
from .. import loader, utils
from telethon.tl.types import Message
import random
import logging
import asyncio
import sqlite3
import base64
import os
from telethon.errors import ChannelPrivateError, ChannelInvalidError, PeerIdInvalidError

logger = logging.getLogger(__name__)

# Базовая база для базы
DB_PATH = "furry_cache.db"

@loader.tds
class FurryCacheMod(loader.Module):
    """Няшный NSFW Furry мод с кэшем, шифрованием и лапками 🐾"""

    strings = {
        "name": "Furry NSFW (Gay++)",
        "fetching": "Мяу~ тяну из хранилища арт 🐾",
        "fetching_remote": "Мурр~ загружаю до 2000 сообщений с канала… потерпи котейку~",
        "no_media": "Ничего не нашёл, даже хвостик не видно :(",
        "error": "Упс... что-то поломалось 🧨",
        "cleared": "Кеш очищен! Чисто как в ванной после тебя 🛁",
        "info": "📦 В кеше: <b>{}</b> медиа\n🔁 Запросов: <b>{}</b>",
        "channel_error": "Канал недоступен или не существует 😿",
        "access_denied": "Нет доступа к каналу, попробуй сначала зайти в него 🚫"
    }

    def __init__(self):
        self._init_db()

    def _init_db(self):
        self._conn = sqlite3.connect(DB_PATH)
        cursor = self._conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            message_id INTEGER
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INTEGER
        )""")
        self._conn.commit()

    def _increment_stat(self, key):
        cursor = self._conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO stats (key, value) VALUES (?, 0)", (key,))
        cursor.execute("UPDATE stats SET value = value + 1 WHERE key = ?", (key,))
        self._conn.commit()

    def _get_stat(self, key):
        cursor = self._conn.cursor()
        cursor.execute("SELECT value FROM stats WHERE key = ?", (key,))
        res = cursor.fetchone()
        return res[0] if res else 0

    def _get_channel(self):
        # Попробуем разные варианты канала
        channels = [
            base64.b64decode("Z2V4Zm9yMjA=").decode("utf-8"),  # оригинальный
            "gexfor20",  # если base64 не работает
            "@gexfor20"  # с @
        ]
        return channels

    async def _get_available_channel(self):
        """Ищем доступный канал из списка"""
        channels = self._get_channel()
        
        for channel_name in channels:
            try:
                channel = await self.client.get_entity(channel_name)
                logger.info(f"✅ Найден доступный канал: {channel_name}")
                return channel
            except (ChannelPrivateError, ChannelInvalidError, PeerIdInvalidError, ValueError) as e:
                logger.warning(f"❌ Канал {channel_name} недоступен: {e}")
                continue
        
        return None

    async def _fetch_all_messages(self, channel, max_messages=2000):
        all_media = []
        offset_id = 0
        limit = 100
        total_loaded = 0
        
        try:
            while total_loaded < max_messages:
                messages = await self.client.get_messages(channel, limit=limit, offset_id=offset_id)
                if not messages:
                    break
                    
                for msg in messages:
                    if msg.media:
                        all_media.append((msg.chat_id, msg.id))
                        
                total_loaded += len(messages)
                if messages:
                    offset_id = messages[-1].id
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке сообщений: {e}")
            
        logger.info(f"🔁 Загружено {total_loaded} сообщений, из них с медиа: {len(all_media)}")
        return all_media

    async def _load_cache_if_empty(self, message):
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM media")
        count = cursor.fetchone()[0]
        
        if count == 0:
            await utils.answer(message, self.strings("fetching_remote"))
            
            # Ищем доступный канал
            channel = await self._get_available_channel()
            if not channel:
                await utils.answer(message, self.strings("channel_error"))
                return False
                
            try:
                media = await self._fetch_all_messages(channel, max_messages=2000)
                if media:
                    cursor.executemany("INSERT OR IGNORE INTO media (chat_id, message_id) VALUES (?, ?)", media)
                    self._conn.commit()
                    logger.info(f"✅ Закешировано {len(media)} сообщений")
                else:
                    logger.warning("Не найдено медиа в канале")
                    
            except (ChannelPrivateError, ChannelInvalidError) as e:
                await utils.answer(message, self.strings("access_denied"))
                logger.error(f"Ошибка доступа к каналу: {e}")
                return False
            except Exception as e:
                logger.error(f"Неожиданная ошибка при загрузке: {e}")
                return False
                
        return True

    async def furrcmd(self, message: Message):
        """Даёт тебе порцию пушистого кринжа из базы, не паля источника 🐱‍👤"""
        try:
            await utils.answer(message, self.strings("fetching"))
            
            # Проверяем и загружаем кеш
            if not await self._load_cache_if_empty(message):
                return

            cursor = self._conn.cursor()
            cursor.execute("SELECT chat_id, message_id FROM media")
            rows = cursor.fetchall()

            if not rows:
                await utils.answer(message, self.strings("no_media"))
                return

            selected = random.choice(rows)
            chat_id, msg_id = selected

            self._increment_stat("used")

            try:
                msg = await self.client.get_messages(chat_id, ids=msg_id)
                if msg and msg.media:
                    file = await self.client.download_media(msg.media)
                    if file:
                        await self.client.send_file(message.chat_id, file, caption=msg.message or "")
                        # Удаляем временный файл
                        try:
                            os.remove(file)
                        except:
                            pass
                    else:
                        await utils.answer(message, self.strings("no_media"))
                else:
                    await utils.answer(message, self.strings("no_media"))
            except Exception as e:
                logger.error(f"Ошибка при получении сообщения {msg_id}: {e}")
                await utils.answer(message, self.strings("no_media"))

        except Exception as e:
            logger.exception("Ошибка при furrcmd: %s", e)
            await utils.answer(message, self.strings("error"))

    async def furrinfocmd(self, message: Message):
        """Показывает сколько всего ты насобирал в своей коллекции артфурри"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM media")
        count = cursor.fetchone()[0]
        uses = self._get_stat("used")
        await utils.answer(message, self.strings("info").format(count, uses))

    async def furrclearcmd(self, message: Message):
        """Ты такой: 'Я устал от этих артов', и всё стирается как слёзы на лапках"""
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM media")
        cursor.execute("DELETE FROM stats")  # Также очищаем статистику
        self._conn.commit()
        await utils.answer(message, self.strings("cleared"))