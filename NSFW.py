# meta developer: ExclusiveFurry.t.me
from telethon import events
from .. import loader, utils
from telethon.tl.types import Message
import random
import logging
import asyncio
import sqlite3
import base64
import os
from telethon.errors import ChannelPrivateError, ChannelInvalidError, PeerIdInvalidError, RPCError

logger = logging.getLogger(__name__)

DB_PATH = "furry_cache.db"

@loader.tds
class FurryCacheMod(loader.Module):
    """Няшный NSFW Furry мод с кэшем, шифрованием и лапками 🐾"""

    strings = {
        "name": "Furry NSFW (Gay++)",
        "fetching": "Мяу~ тяну из хранилища арт 🐾",
        "fetching_remote": "Мурр~ загружаю сообщения с канала… потерпи котейку~",
        "no_media": "Ничего не нашёл, даже хвостик не видно :(",
        "error": "Упс... что-то поломалось 🧨",
        "cleared": "Кеш очищен! Чисто как в ванной после тебя 🛁",
        "info": "📦 В кеше: <b>{}</b> медиа\n🔁 Запросов: <b>{}</b>",
        "channel_error": "Все каналы недоступны 😿 Попробуй добавить свой канал командой .furrset <канал>",
        "channel_set": "✅ Канал установлен: <b>{}</b>",
        "no_cache": "Кеш пуст! Сначала загрузи медиа командой .furrload"
    }

    def __init__(self):
        self._init_db()
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "channels",
                ["@FurryFemboysPlace", "femboyfurr", "gexfor20"],
                "Список каналов для загрузки (через запятую или список)",
                validator=loader.validators.Union(
                    loader.validators.Series(loader.validators.String()),
                    loader.validators.String()
                )
            ),
            loader.ConfigValue(
                "max_messages",
                2000,
                "Максимум сообщений для загрузки",
                validator=loader.validators.Integer(minimum=100, maximum=10000)
            )
        )

    def _init_db(self):
        self._conn = sqlite3.connect(DB_PATH)
        cursor = self._conn.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            message_id INTEGER,
            UNIQUE(chat_id, message_id)
        )""")

        try:
            cursor.execute("SELECT channel_name FROM media LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE media ADD COLUMN channel_name TEXT DEFAULT 'unknown'")
            logger.info("Добавлена колонка channel_name в таблицу media")

        cursor.execute("""CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INTEGER
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            chat_id INTEGER,
            accessible INTEGER DEFAULT 1
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

    def _get_channels(self):
        channels = self.config["channels"]
        if isinstance(channels, str):
            channels = [c.strip() for c in channels.split(",")]

        fallback_channels = [
            "furry_femboy_world",
            "@FopskyFemboyHootersTMUwU", 
            "furr_hub",
            "@furry_yaoi_arts",
            "YeaFuta",
            "@BasementFemboys"
        ]
        all_channels = list(dict.fromkeys(channels + fallback_channels))
        return all_channels

    async def _test_channel_access(self, channel_name):
        try:
            channel = await self.client.get_entity(channel_name)
            messages = await self.client.get_messages(channel, limit=1)
            return channel, True
        except Exception as e:
            logger.warning(f"Канал {channel_name} недоступен: {e}")
            return None, False

    async def _find_accessible_channels(self):
        channels = self._get_channels()
        accessible = []

        for channel_name in channels:
            channel, is_accessible = await self._test_channel_access(channel_name)
            if is_accessible:
                accessible.append((channel_name, channel))
                logger.info(f"✅ Канал доступен: {channel_name}")
            await asyncio.sleep(0.5)
        return accessible

    async def _load_from_channel(self, channel_name, channel, max_messages):
        media_loaded = 0
        offset_id = 0
        limit = 100

        try:
            while media_loaded < max_messages:
                messages = await self.client.get_messages(
                    channel, 
                    limit=min(limit, max_messages - media_loaded),
                    offset_id=offset_id
                )

                if not messages:
                    break

                cursor = self._conn.cursor()
                for msg in messages:
                    if msg.media:
                        try:
                            cursor.execute(
                                "INSERT OR IGNORE INTO media (chat_id, message_id, channel_name) VALUES (?, ?, ?)",
                                (msg.chat_id, msg.id, channel_name)
                            )
                            media_loaded += 1
                        except Exception as e:
                            logger.error(f"Ошибка при сохранении медиа: {e}")

                self._conn.commit()
                if messages:
                    offset_id = messages[-1].id

                await asyncio.sleep(0.2)
        except Exception as e:
            logger.error(f"Ошибка при загрузке из {channel_name}: {e}")

        return media_loaded

    async def furrloadcmd(self, message: Message):
        """Загружает медиа из доступных каналов в кеш"""
        await utils.answer(message, "🔍 Ищу доступные каналы...")

        accessible_channels = await self._find_accessible_channels()

        if not accessible_channels:
            await utils.answer(message, self.strings("channel_error"))
            return

        await utils.answer(message, f"📥 Загружаю из {len(accessible_channels)} каналов...")

        total_loaded = 0
        max_per_channel = self.config["max_messages"] // len(accessible_channels)

        for channel_name, channel in accessible_channels:
            loaded = await self._load_from_channel(channel_name, channel, max_per_channel)
            total_loaded += loaded
            logger.info(f"Загружено из {channel_name}: {loaded} медиа")

        await utils.answer(message, f"✅ Загружено {total_loaded} медиа файлов!")

    async def furrcmd(self, message: Message):
        """Даёт тебе порцию пушистого кринжа из базы 🐱‍👤"""
        try:
            await utils.answer(message, self.strings("fetching"))

            cursor = self._conn.cursor()
            try:
                cursor.execute("SELECT chat_id, message_id, channel_name FROM media ORDER BY RANDOM() LIMIT 1")
                row = cursor.fetchone()
                if row:
                    chat_id, msg_id, channel_name = row
                else:
                    chat_id, msg_id, channel_name = None, None, None
            except sqlite3.OperationalError:
                cursor.execute("SELECT chat_id, message_id FROM media ORDER BY RANDOM() LIMIT 1")
                row = cursor.fetchone()
                if row:
                    chat_id, msg_id = row
                    channel_name = "неизвестный"
                else:
                    chat_id, msg_id, channel_name = None, None, None

            if not chat_id:
                await utils.answer(message, self.strings("no_cache"))
                return

            self._increment_stat("used")

            try:
                msg = await self.client.get_messages(chat_id, ids=msg_id)
                if msg and msg.media:
                    file = await self.client.download_media(msg.media)
                    if file:
                        # ⚡ теперь без текста и подписи, чистое медиа
                        await self.client.send_file(
                            message.chat_id,
                            file,
                            caption=None,
                            force_document=False
                        )
                        try:
                            os.remove(file)
                        except:
                            pass
                    else:
                        raise Exception("Не удалось скачать файл")
                else:
                    raise Exception("Сообщение не найдено")

            except Exception as e:
                logger.error(f"Не удалось получить сообщение {msg_id}: {e}")
                cursor.execute("DELETE FROM media WHERE chat_id = ? AND message_id = ?", (chat_id, msg_id))
                self._conn.commit()
                await self.furrcmd(message)
                return

        except Exception as e:
            logger.exception("Ошибка при furrcmd: %s", e)
            await utils.answer(message, self.strings("error"))

    async def furrsetcmd(self, message: Message):
        """Добавляет новый канал в список: .furrset @channel"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "Использование: .furrset @channel_name")
            return

        channel_name = args.strip()
        channel, is_accessible = await self._test_channel_access(channel_name)

        if is_accessible:
            current_channels = self.config["channels"]
            if isinstance(current_channels, str):
                current_channels = [c.strip() for c in current_channels.split(",")]

            if channel_name not in current_channels:
                current_channels.append(channel_name)
                self.config["channels"] = current_channels

            await utils.answer(message, self.strings("channel_set").format(channel_name))
        else:
            await utils.answer(message, f"❌ Канал {channel_name} недоступен")

    async def furrinfocmd(self, message: Message):
        """Показывает статистику кеша"""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM media")
        count = cursor.fetchone()[0]

        try:
            cursor.execute("SELECT channel_name, COUNT(*) FROM media WHERE channel_name IS NOT NULL GROUP BY channel_name")
            by_channel = cursor.fetchall()
        except sqlite3.OperationalError:
            by_channel = []

        uses = self._get_stat("used")

        info = self.strings("info").format(count, uses)
        if by_channel:
            info += "\n\n📊 По каналам:"
            for channel, cnt in by_channel:
                info += f"\n• {channel or 'неизвестный'}: {cnt}"

        await utils.answer(message, info)

    async def furrclearcmd(self, message: Message):
        """Очищает весь кеш"""
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM media")
        cursor.execute("DELETE FROM stats")
        self._conn.commit()
        await utils.answer(message, self.strings("cleared"))
