# meta developer: @ExclusiveFurry + Grok (починил Lid'у)
# requires: playwright

import os
import tempfile
from .. import loader, utils
from telethon.tl.types import DocumentAttributeFilename  # <-- добавил для 100% файла


class WebShotMod(loader.Module):
    """Делает полный скриншот сайта и отправляет БЕЗ СЖАТИЯ"""

    @loader.command()
    async def webshotcmd(self, message):
        """Использование: .webshot [секунды] <URL>"""
        args = utils.get_args_raw(message).strip()

        if not args:
            return await utils.answer(
                message,
                "❌ <b>Укажи URL!</b>\n\n"
                "📌 <code>.webshot https://example.com</code>\n"
                "📌 <code>.webshot 15 https://example.com</code>"
            )

        parts = args.split(maxsplit=1)
        wait_seconds = 10
        url = args

        if len(parts) == 2 and parts[0].isdigit():
            wait_seconds = int(parts[0])
            url = parts[1]

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        tmp_path = None

        try:
            from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
        except ImportError:
            return await utils.answer(
                message,
                "❌ <b>Playwright не установлен!</b>\n\n"
                "<code>pip install playwright</code>\n"
                "<code>playwright install chromium</code>"
            )

        await utils.answer(message, f"🌐 <b>Открываю сайт...</b>\n🔗 <code>{url}</code>")

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                    viewport={"width": 1366, "height": 2000},
                    locale="ru-RU",
                    device_scale_factor=1,          # <-- 1:1 пиксели
                )

                page = await context.new_page()

                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                await utils.answer(message, f"⏳ <b>Жду {wait_seconds} сек...</b>")
                await page.wait_for_timeout(wait_seconds * 1000)

                # лёгкий скролл для lazy-load
                await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight / 3)")
                await page.wait_for_timeout(400)
                await page.evaluate("() => window.scrollTo(0, 0)")
                await page.wait_for_timeout(600)

                await utils.answer(message, "📸 <b>Делаю скриншот...</b>")

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False, prefix="webshot_") as f:
                    tmp_path = f.name

                await page.screenshot(
                    path=tmp_path,
                    full_page=True,
                    scale="css",           # <-- ИСПРАВИЛ ЗДЕСЬ!
                    omit_background=False
                )

                await browser.close()

            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                return await utils.answer(message, "❌ Скриншот пустой.")

            # === ОТПРАВКА КАК НАСТОЯЩИЙ ФАЙЛ (без сжатия) ===
            await message.client.send_file(
                entity=message.to_id,
                file=tmp_path,
                caption=f"🌐 <b>WebShot</b>\n🔗 <code>{url}</code>\n⏱ {wait_seconds} сек",
                parse_mode="html",
                reply_to=getattr(message, "reply_to_msg_id", None),
                force_document=True,
                attributes=[DocumentAttributeFilename(file_name=f"webshot_{wait_seconds}s.png")],
            )

            # чистка
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass

            try:
                await message.delete()
            except:
                pass

        except Exception as e:
            await utils.answer(
                message,
                f"❌ <b>Ошибка:</b> <code>{type(e).__name__}: {str(e)[:400]}</code>"
        )
