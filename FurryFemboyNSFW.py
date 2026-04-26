__version__ = (0, 0, 3)

# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/

# meta developer: ExclusiveFurry.t.me
# scope: inline
# scope: hikka_only
# scope: hikka_min 1.3.0

from .. import loader, utils
from telethon.tl.types import Message
import random, asyncio, aiohttp

@loader.tds
class YiffScrollerMod(loader.Module):
    """Няшный Furry мод с кэшем 🐾 + галерея + арты e621"""

    strings = {
        "name": "YiffScroller",
        "fetching": "Мяу~ тяну из хранилища арт 🐾",
        "fetching_remote": "Мурр~ загружаю сообщения с канала… потерпи котейку~",
        "no_media": "Ничего не нашёл, даже хвостик не видно :(",
        "no_cache": "Кеш пуст! Сначала загрузи медиа командой .furrload",
        "error": "Упс... что-то поломалось 🧨",
        "cleared": "Кеш очищен! Чисто как в ванной после тебя 🛁",
        "info": "📦 В кеше: <b>{}</b> медиа\n🔁 Запросов: <b>{}</b>",
        "channel_error": "Все каналы недоступны 😿 Попробуй добавить свой канал командой .furrset <канал>",
        "channel_set": "✅ Канал установлен: <b>{}</b>",
    }

    def __init__(self):
        self.running = False
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "channels",
                ["@FurryFemboysPlace,@gexfor20, @FemboysSpanish, @BadFurryFemboy, @paws_qq,@furry_yaoi_arts"],
                "Список каналов для загрузки",
                validator=loader.validators.Series()
            ),
            loader.ConfigValue(
                "max_messages",
                2000,
                "Максимум сообщений для загрузки",
                validator=loader.validators.Integer()
            )
        )

    async def send_furry(self):
        """Фурри? фурри"""
        channel = random.choice(self.config['channels'])
        msgs = (await self.client.get_messages(channel, limit=0)).total
        return f"https://t.me/{channel[1:]}/{random.randint(1, msgs)}"

    @loader.command(ru_doc="Открыть скроллер пикч🐾")
    async def furrcmd(self, message: Message):
        """Open furry scroller"""
        await message.delete()
        await self.inline.gallery(
            message=message,
            next_handler=self.send_furry,
            caption=f"<i>🐾 YiffScroller {utils.ascii_face()}</i>",
        )

    async def furrsetcmd(self, message: Message):
        """Добавляет новый канал в список: .furrset @channel"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "Использование: .furrset @channel_name")
            return
        ch = args.strip()
        try:
            await message.client.get_entity(ch)
            channels = self.config["channels"]
            if isinstance(channels, str):
                channels = [c.strip() for c in channels.split(",")]
            if ch not in channels:
                channels.append(ch)
                self.config["channels"] = channels
            await utils.answer(message, self.strings("channel_set").format(ch))
        except Exception:
            await utils.answer(message, f"❌ Канал {ch} недоступен")

    async def e6cmd(self, message):
        """.e6 тег;тег;тег количество"""
        args = utils.get_args_raw(message).split()
        if len(args) < 2:
            await utils.answer(message, "❌ Используй: `.e6 femboy;catboy 5`")
            return
        tags = args[0].split(";")
        try:
            count = int(args[1])
        except ValueError:
            await utils.answer(message, "❌ Количество должно быть числом")
            return
        self.running = True
        await utils.answer(message, f"🧦 Отправляю {count} артов с тегами: {', '.join(tags)}")
        asyncio.create_task(self._send_e6(message, tags, count))

    async def _send_e6(self, message, tags, count):
        headers = {"User-Agent": "HikkaBot/1.0 by Lidik"}
        sent = 0
        tag_query = "+".join(tags)
        async with aiohttp.ClientSession() as session:
            while self.running and sent < count:
                url = f"https://e621.net/posts.json?tags={tag_query}+order:random&limit=1"
                try:
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            await asyncio.sleep(10)
                            continue
                        data = await resp.json()
                        posts = data.get("posts", [])
                        for post in posts:
                            file_url = post.get("file", {}).get("url")
                            if not file_url:
                                continue
                            try:
                                await message.client.send_file(
                                    message.chat_id,
                                    file_url,
                                    caption=f"🎨 Теги: {', '.join(tags)}"
                                )
                                sent += 1
                            except Exception:
                                continue
                            await asyncio.sleep(random.randint(5, 10))
                except Exception:
                    await asyncio.sleep(5)
        await message.respond("✅ Отправка завершена.")

    async def stop_e6cmd(self, message):
        """Остановить e621"""
        self.running = False
        await utils.answer(message, "🛑 e621 остановлен.")