__version__ = (1, 0, 0)

# ███╗░░░███╗███████╗░█████╗░██████╗░░█████╗░░██╗░░░░░░░██╗░██████╗░██████╗
# ████╗░████║██╔════╝██╔══██╗██╔══██╗██╔══██╗░██║░░██╗░░██║██╔════╝██╔════╝
# ██╔████╔██║█████╗░░███████║██║░░██║██║░░██║░╚██╗████╗██╔╝╚█████╗░╚█████╗░
# ██║╚██╔╝██║██╔══╝░░██╔══██║██║░░██║██║░░██║░░████╔═████║░░╚═══██╗░╚═══██╗
# ██║░╚═╝░██║███████╗██║░░██║██████╔╝╚█████╔╝░░╚██╔╝░╚██╔╝░██████╔╝██████╔╝
# ╚═╝░░░░░╚═╝╚══════╝╚═╝░░╚═╝╚═════╝░░╚════╝░░░░╚═╝░░░╚═╝░░╚═════╝░╚═════╝░
#                © Copyright 2025
#            ✈ https://t.me/mead0wssMods

# scope: hikka_only
# scope: hikka_min 1.3.3
# meta developer: @mead0wssMods
# meta banner: https://x0.at/yCcx.jpg

from telethon import events
from .. import loader, utils


@loader.tds
class AutoFormatting(loader.Module):
    """Модуль для автоматического форматирования текста в <pre><code> теги."""
    
    strings = {"name": "AutoFormatting"}

    def __init__(self):
        self.enabled = False
        self.quotes_enabled = False  # автоматические кавычки
        self.language = "python"  # язык по умолчанию
        self.available_languages = [
            "python", "javascript", "html", "css", "bash", "json", 
            "xml", "sql", "php", "java", "cpp", "c", "go", "rust", 
            "ruby", "swift", "kotlin", "typescript", "yaml", "markdown"
        ]

    async def format_message(self, message):
        content = message.text
        if not content:
            return

        # Добавляем кавычки если включено
        if self.quotes_enabled:
            content = f'"{content}"'

        # Оборачиваем текст в pre code теги
        formatted_content = f'<pre><code class="language-{self.language}">{content}</code></pre>'
        await message.edit(formatted_content, parse_mode="HTML")

    @loader.command()
    async def autoformat(self, message):
        """Включает или отключает автоформатирование в <pre><code>."""
        self.enabled = not self.enabled
        status = "включено" if self.enabled else "выключено"
        await utils.answer(
            message,
            f"🪐 <b>Автоформатирование</b> {status} ʕ·ᴥ·ʔ\n"
            f"Текущий язык: <code>{self.language}</code>\n"
            f"Кавычки: {'включены' if self.quotes_enabled else 'выключены'}",
            parse_mode="HTML",
        )

    @loader.command()
    async def aflang(self, message):
        """Устанавливает язык для подсветки синтаксиса. Использование: .aflang python"""
        args = utils.get_args_raw(message)
        if not args:
            available = ", ".join(self.available_languages)
            await utils.answer(
                message,
                f"🪐 <b>Доступные языки:</b>\n<code>{available}</code>\n\n"
                f"<b>Текущий язык:</b> <code>{self.language}</code>\n\n"
                f"<b>Использование:</b> <code>.aflang python</code>",
                parse_mode="HTML",
            )

    @loader.command()
    async def afquotes(self, message):
        """Включает/выключает автоматические кавычки (работает только с автоформатером)."""
        if not self.enabled:
            await utils.answer(
                message,
                "🪐 <b>Ошибка!</b> Сначала включите автоформатирование командой <code>.autoformat</code> ʕ·ᴥ·ʔ",
                parse_mode="HTML",
            )
            return
        
        self.quotes_enabled = not self.quotes_enabled
        status = "включены" if self.quotes_enabled else "выключены"
        quote_text = 'оборачиваться в "кавычки"' if self.quotes_enabled else 'без кавычек'
        await utils.answer(
            message,
            f"🪐 <b>Автоматические кавычки</b> {status} ʕ·ᴥ·ʔ\n"
            f"Теперь текст будет {quote_text}",
            parse_mode="HTML",
        )
            return

        language = args.lower()
        if language in self.available_languages:
            self.language = language
            await utils.answer(
                message,
                f"🪐 <b>Язык изменен на:</b> <code>{self.language}</code> ʕ·ᴥ·ʔ",
                parse_mode="HTML",
            )
        else:
            await utils.answer(
                message,
                f"🪐 <b>Неизвестный язык:</b> <code>{language}</code>\n"
                f"Используйте <code>.aflang</code> без параметров для списка языков",
                parse_mode="HTML",
            )

    @loader.command()
    async def formatnow(self, message):
        """Форматирует текущее сообщение в <pre><code> теги."""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(
                message,
                "🪐 <b>Использование:</b> <code>.formatnow ваш код здесь</code>",
                parse_mode="HTML",
            )
            return
        
        # Добавляем кавычки если включено и автоформатер включен
        content = args
        if self.enabled and self.quotes_enabled:
            content = f'"{content}"'
            
        formatted_content = f'<pre><code class="language-{self.language}">{content}</code></pre>'
        await utils.answer(message, formatted_content, parse_mode="HTML")

    @loader.command()
    async def formatlang(self, message):
        """Форматирует текст с указанием языка. Использование: .formatlang python print("hello")"""
        args = utils.get_args_raw(message).split(" ", 1)
        if len(args) < 2:
            await utils.answer(
                message,
                "🪐 <b>Использование:</b> <code>.formatlang python ваш код</code>",
                parse_mode="HTML",
            )
            return
        
        language, code = args
        if language not in self.available_languages:
            await utils.answer(
                message,
                f"🪐 <b>Неизвестный язык:</b> <code>{language}</code>",
                parse_mode="HTML",
            )
            return
        
        # Добавляем кавычки если включено и автоформатер включен
        content = code
        if self.enabled and self.quotes_enabled:
            content = f'"{content}"'
            
        formatted_content = f'<pre><code class="language-{language}">{content}</code></pre>'
        await utils.answer(message, formatted_content, parse_mode="HTML")

    @loader.command()
    async def formatstatus(self, message):
        """Показывает статус автоформатирования."""
        status = "включено" if self.enabled else "выключено"
        quotes_status = "включены" if self.quotes_enabled else "выключены"
        await utils.answer(
            message,
            f"🪐 <b>Автоформатирование:</b> {status}\n"
            f"<b>Кавычки:</b> {quotes_status}\n"
            f"<b>Язык:</b> <code>{self.language}</code>\n\n"
            f"<b>Команды:</b>\n"
            f"<code>.autoformat</code> - вкл/выкл автоформатирование\n"
            f"<code>.afquotes</code> - вкл/выкл кавычки\n"
            f"<code>.aflang язык</code> - установить язык\n"
            f"<code>.formatnow текст</code> - форматировать сейчас\n"
            f"<code>.formatlang язык текст</code> - форматировать с языком",
            parse_mode="HTML",
        )

    @loader.watcher(out=True)
    async def message_watcher(self, message):
        # Проверяем, что это не команда модуля
        if not message.text:
            return
            
        commands = [".autoformat", ".afquotes", ".aflang", ".formatnow", ".formatlang", ".formatstatus"]
        text_lower = message.text.lower()
        
        # Если сообщение начинается с команды - пропускаем
        for cmd in commands:
            if text_lower.startswith(cmd):
                return
        
        # Если автоформатирование включено - форматируем
        if self.enabled:
            await self.format_message(message)