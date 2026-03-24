# meta developer: @ExclusiveFurry
# requires: playwright

import os
import tempfile
from .. import loader, utils


class WebShotMod(loader.Module):
    """Делает скриншот сайта и отправляет в чат"""

    @loader.command()
    async def webshotcmd(self, message):
        """Использование: .webshot [секунды] <URL>"""
        args = utils.get_args_raw(message)

        if not args:
            return await utils.answer(
                message,
                "❌ <b>Укажи URL!</b>\n\n"
                "📌 Использование: <code>.webshot [секунды] URL</code>\n"
                "📌 Пример: <code>.webshot 12 https://example.com</code>\n"
                "📌 Без времени: <code>.webshot https://example.com</code>",
            )

        parts = args.split(maxsplit=1)
        wait_seconds = 10
        url = args

        if len(parts) == 2:
            try:
                wait_seconds = int(parts[0])
                url = parts[1]
            except ValueError:
                url = args

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        tmp_path = None

        try:
            from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
        except ImportError:
            return await utils.answer(
                message,
                "❌ <b>Playwright не установлен!</b>\n\n"
                "Установи:\n"
                "<code>pip install playwright</code>\n"
                "<code>playwright install chromium</code>",
            )

        try:
            await utils.answer(message, f"🌐 <b>Открываю сайт...</b>\n🔗 <code>{url}</code>")

            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)

                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 2000},
                    locale="ru-RU",
                )

                page = await context.new_page()

                try:
                    await page.goto(url, wait_until="networkidle", timeout=30_000)
                except PlaywrightTimeout:
                    # Если networkidle не дождались — продолжаем
                    pass

                await utils.answer(
                    message,
                    f"⏳ <b>Жду загрузку...</b> ({wait_seconds} сек)\n🔗 <code>{url}</code>",
                )

                await page.wait_for_timeout(wait_seconds * 1000)

                # Скролл для lazy-контента
                await page.evaluate(
                    """
                    async () => {
                        await new Promise(resolve => {
                            let totalHeight = 0;
                            const distance = 300;
                            const timer = setInterval(() => {
                                window.scrollBy(0, distance);
                                totalHeight += distance;
                                if (totalHeight >= 1500) {
                                    clearInterval(timer);
                                    window.scrollTo(0, 0);
                                    resolve();
                                }
                            }, 80);
                        });
                    }
                """
                )

                await page.wait_for_timeout(500)

                await utils.answer(
                    message,
                    f"📸 <b>Делаю скрин...</b>\n🔗 <code>{url}</code>",
                )

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False, prefix="webshot_") as f:
                    tmp_path = f.name

                await page.screenshot(path=tmp_path, full_page=True)

                await browser.close()

            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                return await utils.answer(message, "❌ <b>Скриншот не создался.</b> Попробуй ещё раз.")

            # Отправка файла
            try:
                await message.client.send_file(
                    entity=message.to_id,  # <--- вот что работает в новых версиях
                    file=tmp_path,
                    caption=f"🌐 <b>{url}</b>\n⏱ Ожидание: {wait_seconds} сек",
                    parse_mode="html",
                    reply_to=getattr(message, "reply_to_msg_id", None),
                )
            except Exception as e:
                return await utils.answer(
                    message,
                    f"❌ <b>Не удалось отправить файл:</b> <code>{type(e).__name__}: {e}</code>"
                )
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

            # Удаляем команду после успешной отправки
            try:
                await message.delete()
            except Exception:
                pass

        except PlaywrightTimeout:
            await utils.answer(
                message,
                f"⏰ <b>Таймаут!</b> Сайт слишком долго не отвечал.\n🔗 <code>{url}</code>",
            )
        except Exception as e:
            await utils.answer(
                message,
                f"❌ <b>Ошибка:</b> <code>{type(e).__name__}: {e}</code>",
            )