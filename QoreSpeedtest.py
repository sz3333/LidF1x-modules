# Бля братан, спасибо огромное выручил
# meta developer: @mwmodules & forked by ExclusiveFurry.t.me
# meta desc: 🚀 Extended Upload Speed Test — long duration test with large data volumes for accurate measurement
# by @mwmodules + edited by DepsoitUser.t.me
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import aiohttp
import time
from datetime import datetime
from .. import loader, utils

@loader.tds
class ExtendedSpeedTestMod(loader.Module):
    """🚀 Extended Upload Speed Test with large data volumes for accurate measurement
    🚀 Расширенный тест скорости отдачи с большими объемами данных для точного измерения
    🚀 Розширений тест швидкості віддачі з великими обсягами даних для точного вимірювання"""

    strings = {
        "name": "ExtendedSpeedTest",

        "testing_en": "🔄 <b>Running extended upload test...</b>\n<i>📊 Transferring large data volumes for accurate measurement...</i>",
        "testing_ru": "🔄 <b>Запуск расширенного теста отдачи...</b>\n<i>📊 Передача больших объемов данных для точного измерения...</i>",
        "testing_uk": "🔄 <b>Запуск розширеного тесту віддачі...</b>\n<i>📊 Передача великих обсягів даних для точного вимірювання...</i>",

        "progress_en": "🔄 <b>Extended upload test in progress...</b>\n<i>📊 Chunk {}/{} • {} transferred • {:.1f}s elapsed</i>",
        "progress_ru": "🔄 <b>Расширенный тест отдачи в процессе...</b>\n<i>📊 Блок {}/{} • {} передано • {:.1f}с прошло</i>",
        "progress_uk": "🔄 <b>Розширений тест віддачі в процесі...</b>\n<i>📊 Блок {}/{} • {} передано • {:.1f}с минуло</i>",

        "error_en": "❌ <b>Test error:</b>\n<code>{}</code>",
        "error_ru": "❌ <b>Ошибка при тестировании:</b>\n<code>{}</code>",
        "error_uk": "❌ <b>Помилка тестування:</b>\n<code>{}</code>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "language", "en", "Module language (en, ru, uk)",
            "chunk_size_mb", 25, "Size of each upload chunk in MB (default: 25)",
            "total_chunks", 8, "Number of chunks to upload (default: 8 = 200MB total)",
            "warmup_chunks", 2, "Number of warmup chunks (excluded from measurement)"
        )

    def format_speed(self, bytes_per_sec):
        if bytes_per_sec <= 0:
            return "0 Mbps"
        mbits = (bytes_per_sec * 8) / (1024 * 1024)
        return f"{mbits:.1f} Mbps" if mbits >= 1 else f"{mbits * 1000:.1f} Kbps"

    def format_size(self, bytes_size):
        if bytes_size >= 1024 * 1024 * 1024:
            return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"
        elif bytes_size >= 1024 * 1024:
            return f"{bytes_size / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_size / 1024:.1f} KB"

    async def upload_chunk(self, session, chunk_data, url="https://speed.cloudflare.com/__up"):
        try:
            start = time.time()
            async with session.post(url, data=chunk_data) as response:
                await response.read()
            duration = time.time() - start
            return len(chunk_data) / duration if duration > 0 else 0, duration
        except Exception:
            return 0, 0

    async def measure_ping(self, session):
        try:
            pings = []
            for _ in range(3):
                start = time.time()
                async with session.get("https://www.google.com") as response:
                    await response.read()
                pings.append(int((time.time() - start) * 1000))
                await asyncio.sleep(0.5)
            return sum(pings) // len(pings)
        except:
            return 0

    async def get_network_info(self, session):
        try:
            async with session.get("https://ipinfo.io/json") as response:
                data = await response.json()
                return {
                    "location": f"{data.get('city', 'N/A')}, {data.get('country', 'N/A')}",
                    "org": data.get('org', 'N/A').replace('AS', '')
                }
        except:
            return {"location": "N/A", "org": "N/A"}

    @loader.command(
        ru_doc="Запустить расширенный тест скорости отдачи с большими объемами данных",
        uk_doc="Запустити розширений тест швидкості віддачі з великими обсягами даних",
        en_doc="Start extended upload speed test with large data volumes"
    )
    async def extspeedtest(self, message):
        """🚀 Start extended upload speed test with large data volumes"""
        lang = self.config["language"]
        chunk_size = self.config["chunk_size_mb"] * 1024 * 1024
        total_chunks = self.config["total_chunks"]
        warmup_chunks = self.config["warmup_chunks"]

        # Бля братан, спасибо огромное выручил
        await utils.answer(message, self.strings.get(f"testing_{lang}", "🔄 <b>Testing...</b>"))

        # Бля братан, спасибо огромное выручил
        client = getattr(self, "allclients", [self.client])[0]

        start_time = time.time()
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                network_info = await self.get_network_info(session)
                ping = await self.measure_ping(session)

                chunk_data = b"0" * chunk_size
                speeds = []
                total_bytes = 0
                measurement_start = None

                for chunk_num in range(1, total_chunks + 1):
                    elapsed = time.time() - start_time
                    progress_msg = self.strings.get(f"progress_{lang}", "🔄 Testing...").format(
                        chunk_num, total_chunks, 
                        self.format_size(total_bytes),
                        elapsed
                    )
                    await utils.answer(message, progress_msg)

                    speed, duration = await self.upload_chunk(session, chunk_data)

                    if chunk_num == warmup_chunks + 1:
                        measurement_start = time.time()
                        speeds = []
                        total_bytes = 0

                    if chunk_num > warmup_chunks and speed > 0:
                        speeds.append(speed)
                        total_bytes += len(chunk_data)

                    await asyncio.sleep(0.2)

                measurement_duration = time.time() - measurement_start if measurement_start else 0
                avg_speed = sum(speeds) / len(speeds) if speeds else 0
                total_duration = time.time() - start_time
                actual_speed = total_bytes / measurement_duration if measurement_duration > 0 else 0
                final_speed = min(avg_speed, actual_speed) if avg_speed and actual_speed else max(avg_speed, actual_speed)

                result_template = {
                    "en": """<b>🚀 Extended Upload Speed Test Results:</b>

<b>📤 Upload Speed:</b> <code>{}</code>
<b>🕒 Ping:</b> <code>{}ms</code>

<b>📊 Test Details:</b>
• <code>{}</code> total transferred
• <code>{}</code> measurement chunks
• <code>{:.1f}s</code> measurement time
• <code>{:.1f}s</code> total test time

<b>🌐 Server:</b> <code>{}</code>
<b>📡 Provider:</b> <code>{}</code>
<b>📅 Time:</b> <code>{}</code>""",

                    "ru": """<b>🚀 Результаты расширенного теста отдачи:</b>

<b>📤 Скорость отдачи:</b> <code>{}</code>
<b>🕒 Пинг:</b> <code>{}мс</code>

<b>📊 Детали теста:</b>
• <code>{}</code> всего передано
• <code>{}</code> блоков измерения
• <code>{:.1f}с</code> время измерения
• <code>{:.1f}с</code> общее время теста

<b>🌐 Сервер:</b> <code>{}</code>
<b>📡 Провайдер:</b> <code>{}</code>
<b>📅 Время:</b> <code>{}</code>""",

                    "uk": """<b>🚀 Результати розширеного тесту віддачі:</b>

<b>📤 Швидкість віддачі:</b> <code>{}</code>
<b>🕒 Пінг:</b> <code>{}мс</code>

<b>📊 Деталі тесту:</b>
• <code>{}</code> всього передано
• <code>{}</code> блоків вимірювання
• <code>{:.1f}с</code> час вимірювання
• <code>{:.1f}с</code> загальний час тесту

<b>🌐 Сервер:</b> <code>{}</code>
<b>📡 Провайдер:</b> <code>{}</code>
<b>📅 Час:</b> <code>{}</code>"""
                }

                result = result_template.get(lang, result_template["en"]).format(
                    self.format_speed(final_speed),
                    ping,
                    self.format_size(total_bytes),
                    total_chunks - warmup_chunks,
                    measurement_duration,
                    total_duration,
                    network_info["location"],
                    network_info["org"],
                    datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                )

                await utils.answer(message, result)

            except Exception as e:
                await utils.answer(
                    message,
                    self.strings.get(f"error_{lang}", "❌ <b>Error:</b>\n<code>{}</code>").format(str(e))
                )