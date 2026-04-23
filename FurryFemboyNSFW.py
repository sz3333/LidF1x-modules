# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.

# meta developer: ExclusiveFurry.t.me (optimized by neko 😼)
# scope: inline
# scope: hikka_only
# scope: hikka_min 1.3.0

from .. import loader, utils
from telethon.tl.types import Message
import random
import logging
import asyncio
import sqlite3
import aiohttp

logger = logging.getLogger(__name__)
DB_PATH = "furry_cache.db"


@loader.tds
class YiffScrollerMod(loader.Module):
    """Няшный Furry мод с кешем 🐾 + быстрая галерея"""

    strings = {
        "name": "YiffScroller",
        "no_cache": "Кеш пуст! Сначала .furrload",
        "cleared": "Кеш очищен 🧹",
        "info": "📦 В кеше: <b>{}</b>\n🔁 Использовано: <b>{}</b>",
    }

    def __init__(self):
        self._init_db()
        self.running = False

        # ⚡ RAM кеш
        self._ram_cache = []
        self._ram_limit = 30

        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "channels",
                [
                    "@FurryFemboysPlace",
                    "@fur_pub_sas",
                    "@gexfor20",
                    "@FemboysSpanish",
                    "@BadFurryFemboy",
                    "@paws_qq",
                    "@furry_yaoi_arts",
                ],
                "Каналы"
            ),
            loader.ConfigValue(
                "max_messages",
                2000,
                "Лимит загрузки"
            )
        )

    # ================= DB =================

    def _init_db(self):
        self._conn = sqlite3.connect(DB_PATH)
        cur = self._conn.cursor()

        cur.execute("""CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            message_id INTEGER,
            UNIQUE(chat_id, message_id)
        )""")

        cur.execute("""CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INTEGER
        )""")

        self._conn.commit()

    def _increment_stat(self, key):
        cur = self._conn.cursor()
        cur.execute("INSERT OR IGNORE INTO stats VALUES (?, 0)", (key,))
        cur.execute("UPDATE stats SET value = value + 1 WHERE key = ?", (key,))
        self._conn.commit()

    def _get_stat(self, key):
        cur = self._conn.cursor()
        cur.execute("SELECT value FROM stats WHERE key = ?", (key,))
        res = cur.fetchone()
        return res[0] if res else 0

    def _get_random_media(self):
        cur = self._conn.cursor()
        cur.execute("SELECT chat_id, message_id FROM media ORDER BY RANDOM() LIMIT 1")
        return cur.fetchone()

    # ================= ⚡ FAST GALLERY =================

    async def _next_cached(self):
        # 🐾 1. RAM кеш
        if self._ram_cache:
            return random.choice(self._ram_cache)

        batch = []

        # 🐾 2. грузим пачку
        for _ in range(10):
            row = self._get_random_media()
            if not row:
                continue

            chat_id, msg_id = row

            try:
                msg = await self.client.get_messages(chat_id, ids=msg_id)
                if not msg or not msg.media:
                    continue

                file = msg.file

                # ⚡ если есть URL
                if file and file.url:
                    batch.append(file.url)
                    continue

                # fallback → bytes
                data = await self.client.download_media(msg.media, bytes)
                if data:
                    batch.append(data)

            except Exception as e:
                logger.warning(f"RAM load error: {e}")

        if not batch:
            return "https://i.imgur.com/removed.png"

        # 🧠 кладём в RAM
        self._ram_cache.extend(batch)
        self._ram_cache = self._ram_cache[-self._ram_limit:]

        self._increment_stat("used")

        return random.choice(self._ram_cache)

    # ================= COMMANDS =================

    @loader.command()
    async def furrcmd(self, message: Message):
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM media")
        count = cur.fetchone()[0]

        if not count:
            await utils.answer(message, self.strings("no_cache"))
            return

        await self.inline.gallery(
            message=message,
            next_handler=self._next_cached,
            caption=lambda: "🐾 YiffScroller",
            preload=3,
        )

    async def furrloadcmd(self, message: Message):
        await utils.answer(message, "🔄 Загружаю...")

        total = 0

        for ch in self.config["channels"]:
            try:
                msgs = await message.client.get_messages(
                    ch,
                    limit=self.config["max_messages"]
                )

                cur = self._conn.cursor()

                for msg in msgs:
                    if msg.media:
                        cur.execute(
                            "INSERT OR IGNORE INTO media (chat_id, message_id) VALUES (?, ?)",
                            (msg.chat_id, msg.id)
                        )
                        total += 1

                self._conn.commit()

            except Exception:
                continue

            await asyncio.sleep(0.3)

        await utils.answer(message, f"✅ Загружено: {total}")

    async def furrinfocmd(self, message: Message):
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM media")
        count = cur.fetchone()[0]

        uses = self._get_stat("used")

        await utils.answer(message, self.strings("info").format(count, uses))

    async def furrclearcmd(self, message: Message):
        cur = self._conn.cursor()
        cur.execute("DELETE FROM media")
        cur.execute("DELETE FROM stats")
        self._conn.commit()

        self._ram_cache.clear()

        await utils.answer(message, self.strings("cleared"))

    # ================= e621 =================

    async def e6cmd(self, message):
        args = utils.get_args_raw(message).split()

        if len(args) < 2:
            return await utils.answer(message, "❌ .e6 tag1;tag2 5")

        tags = args[0].split(";")
        count = int(args[1])

        self.running = True

        await utils.answer(message, f"🎨 {count} артов...")

        asyncio.create_task(self._send_e6(message, tags, count))

    async def _send_e6(self, message, tags, count):
        headers = {"User-Agent": "HikkaBot/1.0"}
        sent = 0
        query = "+".join(tags)

        async with aiohttp.ClientSession() as session:
            while self.running and sent < count:
                try:
                    url = f"https://e621.net/posts.json?tags={query}+order:random&limit=1"

                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            await asyncio.sleep(5)
                            continue

                        data = await resp.json()

                        for post in data.get("posts", []):
                            file_url = post["file"]["url"]

                            await message.client.send_file(
                                message.chat_id,
                                file_url,
                                caption=f"🎨 {', '.join(tags)}"
                            )

                            sent += 1
                            await asyncio.sleep(random.randint(3, 7))

                except Exception:
                    await asyncio.sleep(5)

        await message.respond("✅ Готово")

    async def stop_e6cmd(self, message):
        self.running = False
        await utils.answer(message, "🛑 Стоп")