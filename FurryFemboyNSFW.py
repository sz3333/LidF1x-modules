# meta developer: ExclusiveFurry.t.me (clean rewrite 😼)
# scope: inline
# scope: hikka_only
# scope: hikka_min 1.3.0

from .. import loader, utils
from telethon.tl.types import Message
import random
import logging
import asyncio
import sqlite3

logger = logging.getLogger(__name__)
DB_PATH = "furry_cache.db"


@loader.tds
class YiffScrollerMod(loader.Module):
    """🐾 Furry gallery with RAM cache (fast & clean)"""

    strings = {
        "name": "YiffScroller",
        "no_cache": "Кеш пуст, сначала .furrload",
        "cleared": "Кеш очищен 🧹",
        "info": "📦 Кеш: <b>{}</b>\n🔁 Использований: <b>{}</b>",
    }

    def __init__(self):
        self._init_db()

        # ⚡ RAM cache (bytes only)
        self._ram_cache = []
        self._ram_limit = 40

        self.running = False

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
                "Channels list"
            ),
            loader.ConfigValue(
                "max_messages",
                1500,
                "Load limit per channel"
            ),
        )

    # ================= DB =================

    def _init_db(self):
        self._conn = sqlite3.connect(DB_PATH)
        cur = self._conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            message_id INTEGER,
            UNIQUE(chat_id, message_id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INTEGER
        )
        """)

        self._conn.commit()

    def _get_random_media(self):
        cur = self._conn.cursor()
        cur.execute("SELECT chat_id, message_id FROM media ORDER BY RANDOM() LIMIT 1")
        return cur.fetchone()

    def _inc(self, key):
        cur = self._conn.cursor()
        cur.execute("INSERT OR IGNORE INTO stats VALUES (?, 0)", (key,))
        cur.execute("UPDATE stats SET value = value + 1 WHERE key = ?", (key,))
        self._conn.commit()

    def _stat(self, key):
        cur = self._conn.cursor()
        cur.execute("SELECT value FROM stats WHERE key=?", (key,))
        r = cur.fetchone()
        return r[0] if r else 0

    # ================= FAST GALLERY =================

    async def _next_cached(self):
        # ⚡ 1. RAM first
        if self._ram_cache:
            return random.choice(self._ram_cache)

        batch = []

        # ⚡ 2. preload batch from DB
        for _ in range(12):
            row = self._get_random_media()
            if not row:
                continue

            chat_id, msg_id = row

            try:
                msg = await self.client.get_messages(chat_id, ids=msg_id)

                if not msg or not msg.media:
                    continue

                # 💥 Telethon way: ONLY bytes
                data = await self.client.download_media(msg.media, bytes)

                if data:
                    batch.append(data)

            except Exception as e:
                logger.warning(f"cache load error: {e}")

        if not batch:
            return "https://i.imgur.com/removed.png"

        # 🧠 store in RAM
        self._ram_cache.extend(batch)
        self._ram_cache = self._ram_cache[-self._ram_limit:]

        self._inc("used")

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
            preload=3,
            caption=lambda: "🐾 YiffScroller"
        )

    async def furrloadcmd(self, message: Message):
        await utils.answer(message, "🔄 Loading cache...")

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

            await asyncio.sleep(0.2)

        await utils.answer(message, f"✅ Loaded: {total}")

    async def furrinfocmd(self, message: Message):
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM media")
        count = cur.fetchone()[0]

        uses = self._stat("used")

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

        try:
            count = int(args[1])
        except:
            return await utils.answer(message, "❌ number invalid")

        self.running = True

        await utils.answer(message, f"🎨 Sending {count} posts...")

        asyncio.create_task(self._e6_worker(message, tags, count))

    async def _e6_worker(self, message, tags, count):
        import aiohttp

        headers = {"User-Agent": "HikkaBot"}
        sent = 0
        query = "+".join(tags)

        async with aiohttp.ClientSession() as session:
            while self.running and sent < count:
                try:
                    url = f"https://e621.net/posts.json?tags={query}+order:random&limit=1"

                    async with session.get(url, headers=headers) as r:
                        if r.status != 200:
                            await asyncio.sleep(5)
                            continue

                        data = await r.json()

                        for post in data.get("posts", []):
                            file_url = post["file"]["url"]

                            await message.client.send_file(
                                message.chat_id,
                                file_url,
                                caption=f"🎨 {', '.join(tags)}"
                            )

                            sent += 1
                            await asyncio.sleep(4)

                except Exception:
                    await asyncio.sleep(3)

        await message.respond("✅ Done")

    async def stop_e6cmd(self, message):
        self.running = False
        await utils.answer(message, "🛑 stopped")