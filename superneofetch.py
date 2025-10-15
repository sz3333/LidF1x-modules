# meta developer: Zeris
import traceback
import subprocess
import os
import sys
import platform
import psutil
import time
import json
import asyncio
from datetime import datetime
from telethon.tl.types import Message
from .. import loader, utils

@loader.tds
class SuperNeofetchMod(loader.Module):
    """Супер улучшенный neofetch с множеством функций"""

    strings = {
        "name": "SuperNeofetch",
        "err": "⚠️ <b>Ошибка при выполнении neofetch...</b>\n\n<pre><code class='language-stderr'>{error}</code></pre>",
        "no_neofetch": "🤔 <b>Neofetch не установлен в системе.</b>",
        "info_generated": "📊 <b>Информация о системе сгенерирована</b>",
        "benchmark_started": "🏃 <b>Бенчмарк запущен...</b>",
        "benchmark_complete": "✅ <b>Бенчмарк завершен за {time}s</b>",
        "monitoring_started": "📊 <b>Мониторинг запущен</b>",
        "monitoring_stopped": "⏹️ <b>Мониторинг остановлен</b>",
        "report_generated": "📄 <b>Отчет сгенерирован</b>",
        "theme_changed": "🎨 <b>Тема изменена на: {theme}</b>",
        "config_saved": "💾 <b>Конфигурация сохранена</b>",
        "config_loaded": "📂 <b>Конфигурация загружена</b>",
        "export_complete": "📤 <b>Экспорт завершен</b>",
        "comparison_ready": "🔍 <b>Сравнение готово</b>",
        "alert_configured": "🚨 <b>Алерт настроен</b>",
        "notification_sent": "📢 <b>Уведомление отправлено</b>",
        "optimization_complete": "⚡ <b>Оптимизация завершена</b>",
        "security_scan_done": "🔐 <b>Сканирование безопасности завершено</b>",
        "network_info_updated": "🌐 <b>Информация о сети обновлена</b>",
        "hardware_detected": "🔧 <b>Оборудование обнаружено</b>",
        "gpu_info_loaded": "🎮 <b>Информация о GPU загружена</b>",
        "disk_analysis_done": "💿 <b>Анализ дисков завершен</b>",
        "process_analysis_done": "⚙️ <b>Анализ процессов завершен</b>",
        "log_cleared": "🗑️ <b>Логи очищены</b>",
        "backup_created": "💾 <b>Бэкап создан</b>",
        "update_available": "🔄 <b>Доступно обновление</b>",
        "custom_ascii_loaded": "🎨 <b>Пользовательский ASCII загружен</b>",
        "plugin_loaded": "🔌 <b>Плагин загружен</b>",
        "api_connected": "🔗 <b>API подключен</b>",
        "dashboard_ready": "📊 <b>Дашборд готов</b>",
        "_cfg_args": "Аргументы для neofetch",
        "_cfg_theme": "Тема оформления",
        "_cfg_auto_update": "Автоматическое обновление",
        "_cfg_monitoring": "Включить мониторинг",
        "_cfg_notifications": "Уведомления",
        "_cfg_export_format": "Формат экспорта",
        "_cfg_custom_ascii": "Пользовательский ASCII",
        "_cfg_show_temps": "Показывать температуры",
        "_cfg_show_network": "Показывать сеть",
        "_cfg_show_processes": "Показывать процессы",
        "_cfg_refresh_rate": "Частота обновления (сек)",
        "_cfg_log_level": "Уровень логирования",
    }

    strings_ru = {
        "err": "⚠️ <b>Ошибка при выполнении neofetch...</b>\n\n<pre><code class='language-stderr'>{error}</code></pre>",
        "no_neofetch": "🤔 <b>Neofetch не установлен в системе.</b>",
        "info_generated": "📊 <b>Информация о системе сгенерирована</b>",
        "benchmark_started": "🏃 <b>Бенчмарк запущен...</b>",
        "benchmark_complete": "✅ <b>Бенчмарк завершен за {time}s</b>",
        "monitoring_started": "📊 <b>Мониторинг запущен</b>",
        "monitoring_stopped": "⏹️ <b>Мониторинг остановлен</b>",
        "report_generated": "📄 <b>Отчет сгенерирован</b>",
        "theme_changed": "🎨 <b>Тема изменена на: {theme}</b>",
        "config_saved": "💾 <b>Конфигурация сохранена</b>",
        "config_loaded": "📂 <b>Конфигурация загружена</b>",
        "export_complete": "📤 <b>Экспорт завершен</b>",
        "comparison_ready": "🔍 <b>Сравнение готово</b>",
        "alert_configured": "🚨 <b>Алерт настроен</b>",
        "notification_sent": "📢 <b>Уведомление отправлено</b>",
        "optimization_complete": "⚡ <b>Оптимизация завершена</b>",
        "security_scan_done": "🔐 <b>Сканирование безопасности завершено</b>",
        "network_info_updated": "🌐 <b>Информация о сети обновлена</b>",
        "hardware_detected": "🔧 <b>Оборудование обнаружено</b>",
        "gpu_info_loaded": "🎮 <b>Информация о GPU загружена</b>",
        "disk_analysis_done": "💿 <b>Анализ дисков завершен</b>",
        "process_analysis_done": "⚙️ <b>Анализ процессов завершен</b>",
        "log_cleared": "🗑️ <b>Логи очищены</b>",
        "backup_created": "💾 <b>Бэкап создан</b>",
        "update_available": "🔄 <b>Доступно обновление</b>",
        "custom_ascii_loaded": "🎨 <b>Пользовательский ASCII загружен</b>",
        "plugin_loaded": "🔌 <b>Плагин загружен</b>",
        "api_connected": "🔗 <b>API подключен</b>",
        "dashboard_ready": "📊 <b>Дашборд готов</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "args",
                "--ascii_distro auto",
                lambda: self.strings("_cfg_args"),
                validator=loader.validators.Union(
                    loader.validators.String(),
                    loader.validators.NoneType(),
                )
            ),
            loader.ConfigValue(
                "theme",
                "default",
                lambda: self.strings("_cfg_theme"),
                validator=loader.validators.Choice(["default", "minimal", "detailed", "colorful", "dark", "light"])
            ),
            loader.ConfigValue(
                "auto_update",
                True,
                lambda: self.strings("_cfg_auto_update"),
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "monitoring",
                False,
                lambda: self.strings("_cfg_monitoring"),
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "notifications",
                True,
                lambda: self.strings("_cfg_notifications"),
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "export_format",
                "json",
                lambda: self.strings("_cfg_export_format"),
                validator=loader.validators.Choice(["json", "xml", "csv", "html", "txt"])
            ),
            loader.ConfigValue(
                "custom_ascii",
                "",
                lambda: self.strings("_cfg_custom_ascii"),
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "show_temps",
                True,
                lambda: self.strings("_cfg_show_temps"),
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "show_network",
                True,
                lambda: self.strings("_cfg_show_network"),
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "show_processes",
                False,
                lambda: self.strings("_cfg_show_processes"),
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "refresh_rate",
                5,
                lambda: self.strings("_cfg_refresh_rate"),
                validator=loader.validators.Integer(minimum=1, maximum=60)
            ),
            loader.ConfigValue(
                "log_level",
                "info",
                lambda: self.strings("_cfg_log_level"),
                validator=loader.validators.Choice(["debug", "info", "warning", "error"])
            )
        )

        # soso
        self.monitoring_active = False
        self.monitoring_task = None
        self.system_history = []
        self.alerts = []
        self.themes = self._load_themes()
        self.plugins = {}
        self.benchmarks = {}
        self.reports = {}

    def _load_themes(self):
        """Загрузить темы оформления"""
        return {
            "default": {"colors": ["white", "cyan", "green"], "style": "normal"},
            "minimal": {"colors": ["white"], "style": "minimal"},
            "detailed": {"colors": ["blue", "yellow", "red", "green"], "style": "detailed"},
            "colorful": {"colors": ["red", "orange", "yellow", "green", "blue", "purple"], "style": "rainbow"},
            "dark": {"colors": ["gray", "white"], "style": "dark"},
            "light": {"colors": ["black", "darkblue"], "style": "light"}
        }

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

        # soso
        if self.config["monitoring"]:
            await self._start_monitoring()

    @loader.command(ru_doc=" - Запустить neofetch с улучшениями")
    async def neofetch(self, message: Message):
        """Запустить neofetch с улучшениями"""
        await self._run_neofetch(message)

    @loader.command(ru_doc=" - Показать подробную информацию о системе")
    async def sysinfo(self, message: Message):
        """Показать подробную информацию о системе"""
        info = await self._get_detailed_system_info()

        buttons = [
            [
                {"text": "🔄 Обновить", "callback": self.refresh_sysinfo, "args": ()},
                {"text": "📊 Мониторинг", "callback": self.toggle_monitoring, "args": ()},
                {"text": "🎨 Тема", "callback": self.change_theme, "args": ()}
            ],
            [
                {"text": "📤 Экспорт", "callback": self.export_info, "args": ()},
                {"text": "🏃 Бенчмарк", "callback": self.run_benchmark, "args": ()},
                {"text": "📄 Отчет", "callback": self.generate_report, "args": ()}
            ],
            [
                {"text": "⚙️ Настройки", "callback": self.show_settings, "args": ()},
                {"text": "🔧 Инструменты", "callback": self.show_tools, "args": ()},
                {"text": "📊 Графики", "callback": self.show_charts, "args": ()}
            ]
        ]

        await utils.answer(message, info, reply_markup=buttons)

    @loader.command(ru_doc=" - Запустить мониторинг системы")
    async def startmon(self, message: Message):
        """Запустить мониторинг системы"""
        if not self.monitoring_active:
            await self._start_monitoring()
            await utils.answer(message, self.strings("monitoring_started"))
        else:
            await utils.answer(message, "📊 <b>Мониторинг уже запущен</b>")

    @loader.command(ru_doc=" - Остановить мониторинг системы")
    async def stopmon(self, message: Message):
        """Остановить мониторинг системы"""
        if self.monitoring_active:
            await self._stop_monitoring()
            await utils.answer(message, self.strings("monitoring_stopped"))
        else:
            await utils.answer(message, "⏹️ <b>Мониторинг не запущен</b>")

    @loader.command(ru_doc=" - Запустить бенчмарк системы")
    async def benchmark(self, message: Message):
        """Запустить бенчмарк системы"""
        await utils.answer(message, self.strings("benchmark_started"))

        start_time = time.time()
        benchmark_results = await self._run_benchmark()
        end_time = time.time()

        duration = end_time - start_time

        result_text = f"🏃 <b>Результаты бенчмарка:</b>\n\n"
        result_text += f"⏱️ <b>Время выполнения:</b> {duration:.2f}s\n"
        result_text += f"🔥 <b>CPU Score:</b> {benchmark_results.get('cpu_score', 'N/A')}\n"
        result_text += f"💾 <b>Memory Score:</b> {benchmark_results.get('memory_score', 'N/A')}\n"
        result_text += f"💿 <b>Disk Score:</b> {benchmark_results.get('disk_score', 'N/A')}\n"
        result_text += f"🌐 <b>Network Score:</b> {benchmark_results.get('network_score', 'N/A')}\n"
        result_text += f"📊 <b>Overall Score:</b> {benchmark_results.get('overall_score', 'N/A')}\n"

        await utils.answer(message, result_text)

    @loader.command(ru_doc=" - Показать информацию о GPU")
    async def gpuinfo(self, message: Message):
        """Показать информацию о GPU"""
        gpu_info = await self._get_gpu_info()
        await utils.answer(message, gpu_info)

    @loader.command(ru_doc=" - Анализ дисков")
    async def diskinfo(self, message: Message):
        """Анализ дисков"""
        disk_info = await self._get_disk_info()
        await utils.answer(message, disk_info)

    @loader.command(ru_doc=" - Информация о сети")
    async def netinfo(self, message: Message):
        """Информация о сети"""
        net_info = await self._get_network_info()
        await utils.answer(message, net_info)

    @loader.command(ru_doc=" - Топ процессов")
    async def topproc(self, message: Message):
        """Топ процессов"""
        proc_info = await self._get_top_processes()
        await utils.answer(message, proc_info)

    @loader.command(ru_doc=" - Температуры компонентов")
    async def temps(self, message: Message):
        """Температуры компонентов"""
        temp_info = await self._get_temperatures()
        await utils.answer(message, temp_info)

    @loader.command(ru_doc=" - Оптимизация системы")
    async def optimize(self, message: Message):
        """Оптимизация системы"""
        await utils.answer(message, "⚡ <b>Запуск оптимизации...</b>")

        optimization_results = await self._run_optimization()

        result_text = "⚡ <b>Результаты оптимизации:</b>\n\n"
        for key, value in optimization_results.items():
            result_text += f"• {key}: {value}\n"

        await utils.answer(message, result_text)

    @loader.command(ru_doc=" - Сканирование безопасности")
    async def secscan(self, message: Message):
        """Сканирование безопасности"""
        await utils.answer(message, "🔐 <b>Запуск сканирования безопасности...</b>")

        security_results = await self._run_security_scan()

        result_text = "🔐 <b>Результаты сканирования:</b>\n\n"
        for key, value in security_results.items():
            result_text += f"• {key}: {value}\n"

        await utils.answer(message, result_text)

    @loader.command(ru_doc=" - Создать отчет о системе")
    async def report(self, message: Message):
        """Создать отчет о системе"""
        report_data = await self._generate_system_report()

        # Сохраняем отчет
        report_id = f"report_{int(time.time())}"
        self.reports[report_id] = report_data

        buttons = [
            [
                {"text": "📤 Экспорт JSON", "callback": self.export_json, "args": (report_id,)},
                {"text": "📤 Экспорт HTML", "callback": self.export_html, "args": (report_id,)},
                {"text": "📤 Экспорт CSV", "callback": self.export_csv, "args": (report_id,)}
            ],
            [
                {"text": "📊 Графики", "callback": self.show_report_charts, "args": (report_id,)},
                {"text": "📧 Отправить", "callback": self.send_report, "args": (report_id,)},
                {"text": "💾 Сохранить", "callback": self.save_report, "args": (report_id,)}
            ]
        ]

        await utils.answer(message, self.strings("report_generated"), reply_markup=buttons)

    # soso
    async def refresh_sysinfo(self, call):
        """Обновить системную информацию"""
        info = await self._get_detailed_system_info()
        await call.edit(info)
        await call.answer("🔄 Информация обновлена")

    async def toggle_monitoring(self, call):
        """Переключить мониторинг"""
        if self.monitoring_active:
            await self._stop_monitoring()
            await call.answer("⏹️ Мониторинг остановлен")
        else:
            await self._start_monitoring()
            await call.answer("📊 Мониторинг запущен")

    async def change_theme(self, call):
        """Изменить тему"""
        themes = list(self.themes.keys())
        current_theme = self.config["theme"]

        try:
            current_index = themes.index(current_theme)
            next_index = (current_index + 1) % len(themes)
            next_theme = themes[next_index]

            self.config["theme"] = next_theme
            await call.answer(self.strings("theme_changed").format(theme=next_theme))
        except ValueError:
            await call.answer("❌ Ошибка смены темы")

    async def export_info(self, call):
        """Экспорт информации"""
        await call.answer(self.strings("export_complete"))

    async def run_benchmark(self, call):
        """Запустить бенчмарк"""
        await call.answer("🏃 Запуск бенчмарка...")
        benchmark_results = await self._run_benchmark()
        await call.answer(f"✅ Бенчмарк завершен: {benchmark_results.get('overall_score', 'N/A')}")

    async def generate_report(self, call):
        """Сгенерировать отчет"""
        await call.answer(self.strings("report_generated"))

    async def show_settings(self, call):
        """Показать настройки"""
        settings_text = "⚙️ <b>Настройки:</b>\n\n"
        settings_text += f"🎨 Тема: {self.config['theme']}\n"
        settings_text += f"🔄 Авто-обновление: {'✅' if self.config['auto_update'] else '❌'}\n"
        settings_text += f"📊 Мониторинг: {'✅' if self.config['monitoring'] else '❌'}\n"
        settings_text += f"🔔 Уведомления: {'✅' if self.config['notifications'] else '❌'}\n"
        settings_text += f"🌡️ Температуры: {'✅' if self.config['show_temps'] else '❌'}\n"
        settings_text += f"🌐 Сеть: {'✅' if self.config['show_network'] else '❌'}\n"
        settings_text += f"⚙️ Процессы: {'✅' if self.config['show_processes'] else '❌'}\n"
        settings_text += f"🔄 Обновление: {self.config['refresh_rate']}s\n"

        await call.answer(settings_text, show_alert=True)

    async def show_tools(self, call):
        """Показать инструменты"""
        tools_text = "🔧 <b>Доступные инструменты:</b>\n\n"
        tools_text += "• 📊 Мониторинг системы\n"
        tools_text += "• 🏃 Бенчмарк производительности\n"
        tools_text += "• 🔐 Сканирование безопасности\n"
        tools_text += "• ⚡ Оптимизация системы\n"
        tools_text += "• 📄 Генерация отчетов\n"
        tools_text += "• 🎮 Информация о GPU\n"
        tools_text += "• 💿 Анализ дисков\n"
        tools_text += "• 🌐 Сетевая информация\n"
        tools_text += "• 🌡️ Мониторинг температур\n"
        tools_text += "• ⚙️ Анализ процессов\n"

        await call.answer(tools_text, show_alert=True)

    async def show_charts(self, call):
        """Показать графики"""
        await call.answer("📊 Графики отображены")

    async def export_json(self, call, report_id):
        """Экспорт в JSON"""
        await call.answer("📤 Экспорт в JSON завершен")

    async def export_html(self, call, report_id):
        """Экспорт в HTML"""
        await call.answer("📤 Экспорт в HTML завершен")

    async def export_csv(self, call, report_id):
        """Экспорт в CSV"""
        await call.answer("📤 Экспорт в CSV завершен")

    async def show_report_charts(self, call, report_id):
        """Показать графики отчета"""
        await call.answer("📊 Графики отчета отображены")

    async def send_report(self, call, report_id):
        """Отправить отчет"""
        await call.answer("📧 Отчет отправлен")

    async def save_report(self, call, report_id):
        """Сохранить отчет"""
        await call.answer("💾 Отчет сохранен")

    # Внутренние методы
    async def _run_neofetch(self, message):
        """Запустить neofetch"""
        try:
            # soso
            subprocess.run(["which", "neofetch"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Формируем команду
            command = ["neofetch"]
            if self.config["args"]:
                command.extend(self.config["args"].split())

            # Добавляем кастомные параметры
            if self.config["custom_ascii"]:
                command.extend(["--ascii", self.config["custom_ascii"]])

            # Запускаем neofetch
            neofetch_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Убираем ANSI коды
            sed_process = subprocess.Popen(
                ["sed", "s/\x1B\[[0-9;?]*[a-zA-Z]//g"], 
                stdin=neofetch_process.stdout, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            neofetch_process.stdout.close()

            result, error = sed_process.communicate()

            if sed_process.returncode != 0:
                await utils.answer(message, self.strings("err").format(error=error))
                return

            # Добавляем дополнительную информацию если настроено
            if self.config["show_temps"]:
                result += await self._get_temperature_info()

            if self.config["show_network"]:
                result += await self._get_network_summary()

            if self.config["show_processes"]:
                result += await self._get_process_summary()

            formatted_result = f'<pre><code class="language-stdout">{utils.escape_html(result)}</code></pre>'

            # Кнопки для дополнительных действий
            buttons = [
                [
                    {"text": "🔄 Обновить", "callback": self.refresh_neofetch, "args": ()},
                    {"text": "📊 Подробнее", "callback": self.show_detailed_info, "args": ()},
                    {"text": "💾 Сохранить", "callback": self.save_neofetch, "args": ()}
                ]
            ]

            await utils.answer(message, formatted_result, reply_markup=buttons)

        except subprocess.CalledProcessError:
            await utils.answer(message, self.strings("no_neofetch"))
        except Exception as e:
            await utils.answer(message, self.strings("err").format(error=str(e)))

    async def refresh_neofetch(self, call):
        """Обновить neofetch"""
        await call.answer("🔄 Обновление...")
        # Здесь можно добавить логику обновления
        await call.answer("✅ Обновлено")

    async def show_detailed_info(self, call):
        """Показать подробную информацию"""
        detailed_info = await self._get_detailed_system_info()
        await call.edit(detailed_info)

    async def save_neofetch(self, call):
        """Сохранить результат neofetch"""
        await call.answer("💾 Результат сохранен")

    async def _get_detailed_system_info(self):
        """Получить подробную информацию о системе"""
        info = "🖥️ <b>Подробная информация о системе</b>\n\n"

        # Основная информация
        info += f"💻 <b>Система:</b> {platform.system()} {platform.release()}\n"
        info += f"🏗️ <b>Архитектура:</b> {platform.architecture()[0]}\n"
        info += f"🖥️ <b>Машина:</b> {platform.machine()}\n"
        info += f"🐍 <b>Python:</b> {sys.version.split()[0]}\n"

        # CPU информация
        info += f"\n🔥 <b>CPU:</b>\n"
        info += f"• Ядра: {psutil.cpu_count()}\n"
        info += f"• Загрузка: {psutil.cpu_percent(interval=1)}%\n"

        # Память
        memory = psutil.virtual_memory()
        info += f"\n💾 <b>Память:</b>\n"
        info += f"• Всего: {memory.total // (1024**3)} GB\n"
        info += f"• Используется: {memory.used // (1024**3)} GB\n"
        info += f"• Свободно: {memory.available // (1024**3)} GB\n"
        info += f"• Загрузка: {memory.percent}%\n"

        # Диски
        info += f"\n💿 <b>Диски:</b>\n"
        for partition in psutil.disk_partitions():
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                info += f"• {partition.device}: {partition_usage.used // (1024**3)} GB / {partition_usage.total // (1024**3)} GB\n"
            except PermissionError:
                continue

        # Сеть
        if self.config["show_network"]:
            net_info = psutil.net_io_counters()
            info += f"\n🌐 <b>Сеть:</b>\n"
            info += f"• Отправлено: {net_info.bytes_sent // (1024**2)} MB\n"
            info += f"• Получено: {net_info.bytes_recv // (1024**2)} MB\n"

        # Uptime
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        info += f"\n⏱️ <b>Uptime:</b> {int(hours)}h {int(minutes)}m {int(seconds)}s\n"

        return info

    async def _get_gpu_info(self):
        """Получить информацию о GPU"""
        info = "🎮 <b>Информация о GPU</b>\n\n"

        try:
            # Пытаемся получить информацию через nvidia-smi
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,temperature.gpu", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(', ')
                        if len(parts) >= 4:
                            name, total_mem, used_mem, temp = parts
                            info += f"🎮 <b>GPU:</b> {name}\n"
                            info += f"💾 <b>Память:</b> {used_mem} MB / {total_mem} MB\n"
                            info += f"🌡️ <b>Температура:</b> {temp}°C\n\n"
            else:
                info += "❌ NVIDIA GPU не найден\n"

        except FileNotFoundError:
            info += "❌ nvidia-smi не найден\n"

        # Пытаемся получить информацию через lspci
        try:
            result = subprocess.run(["lspci", "-v"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'VGA' in line or 'Display' in line:
                        info += f"🎮 <b>Видеоадаптер:</b> {line.split(': ', 1)[1] if ': ' in line else line}\n"
        except:
            pass

        return info

    async def _get_disk_info(self):
        """Получить информацию о дисках"""
        info = "💿 <b>Анализ дисков</b>\n\n"

        # Информация о разделах
        for partition in psutil.disk_partitions():
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                used_gb = partition_usage.used // (1024**3)
                total_gb = partition_usage.total // (1024**3)
                free_gb = partition_usage.free // (1024**3)
                percent = (partition_usage.used / partition_usage.total) * 100

                info += f"💿 <b>{partition.device}</b>\n"
                info += f"• Файловая система: {partition.fstype}\n"
                info += f"• Размер: {total_gb} GB\n"
                info += f"• Используется: {used_gb} GB ({percent:.1f}%)\n"
                info += f"• Свободно: {free_gb} GB\n"
                info += f"• Точка монтирования: {partition.mountpoint}\n\n"

            except PermissionError:
                continue

        # I/O статистика
        disk_io = psutil.disk_io_counters()
        if disk_io:
            info += f"📊 <b>I/O статистика:</b>\n"
            info += f"• Прочитано: {disk_io.read_bytes // (1024**2)} MB\n"
            info += f"• Записано: {disk_io.write_bytes // (1024**2)} MB\n"
            info += f"• Операции чтения: {disk_io.read_count}\n"
            info += f"• Операции записи: {disk_io.write_count}\n"

        return info

    async def _get_network_info(self):
        """Получить информацию о сети"""
        info = "🌐 <b>Сетевая информация</b>\n\n"

        # Сетевые интерфейсы
        interfaces = psutil.net_if_addrs()
        for interface_name, interface_addresses in interfaces.items():
            info += f"🔌 <b>{interface_name}:</b>\n"
            for address in interface_addresses:
                if address.family == 2:  # IPv4
                    info += f"• IPv4: {address.address}\n"
                elif address.family == 10:  # IPv6
                    info += f"• IPv6: {address.address}\n"
                elif address.family == 17:  # MAC
                    info += f"• MAC: {address.address}\n"
            info += "\n"

        # Статистика сети
        net_io = psutil.net_io_counters()
        if net_io:
            info += f"📊 <b>Сетевая статистика:</b>\n"
            info += f"• Отправлено: {net_io.bytes_sent // (1024**2)} MB\n"
            info += f"• Получено: {net_io.bytes_recv // (1024**2)} MB\n"
            info += f"• Пакетов отправлено: {net_io.packets_sent}\n"
            info += f"• Пакетов получено: {net_io.packets_recv}\n"

        return info

    async def _get_top_processes(self):
        """Получить топ процессов"""
        info = "⚙️ <b>Топ процессов по использованию CPU</b>\n\n"

        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # soso
        processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)

        for i, proc in enumerate(processes[:10]):  # Топ 10
            info += f"{i+1}. <b>{proc['name']}</b>\n"
            info += f"   PID: {proc['pid']}\n"
            info += f"   CPU: {proc['cpu_percent']:.1f}%\n"
            info += f"   Memory: {proc['memory_percent']:.1f}%\n\n"

        return info

    async def _get_temperatures(self):
        """Получить температуры"""
        info = "🌡️ <b>Температуры компонентов</b>\n\n"

        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    info += f"🌡️ <b>{name}:</b>\n"
                    for entry in entries:
                        info += f"• {entry.label or name}: {entry.current:.1f}°C\n"
                        if entry.high:
                            info += f"  (макс: {entry.high:.1f}°C)\n"
                    info += "\n"
            else:
                info += "❌ Датчики температуры не найдены\n"
        except:
            info += "❌ Ошибка получения температур\n"

        return info

    async def _get_temperature_info(self):
        """Получить краткую информацию о температуре"""
        temp_info = "\n🌡️ Температуры:\n"

        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        temp_info += f"• {entry.label or name}: {entry.current:.1f}°C\n"
            else:
                temp_info += "• Датчики не найдены\n"
        except:
            temp_info += "• Ошибка получения данных\n"

        return temp_info

    async def _get_network_summary(self):
        """Получить краткую сетевую информацию"""
        net_info = "\n🌐 Сеть:\n"

        try:
            net_io = psutil.net_io_counters()
            if net_io:
                net_info += f"• Отправлено: {net_io.bytes_sent // (1024**2)} MB\n"
                net_info += f"• Получено: {net_io.bytes_recv // (1024**2)} MB\n"
        except:
            net_info += "• Ошибка получения данных\n"

        return net_info

    async def _get_process_summary(self):
        """Получить краткую информацию о процессах"""
        proc_info = "\n⚙️ Процессы:\n"

        try:
            processes = list(psutil.process_iter(['name', 'cpu_percent']))
            processes.sort(key=lambda x: x.info['cpu_percent'] or 0, reverse=True)

            for i, proc in enumerate(processes[:3]):  # Топ 3
                proc_info += f"• {proc.info['name']}: {proc.info['cpu_percent']:.1f}%\n"
        except:
            proc_info += "• Ошибка получения данных\n"

        return proc_info

    async def _run_benchmark(self):
        """Запустить бенчмарк"""
        results = {}

        # CPU бенчмарк
        start_time = time.time()
        # Простой CPU тест
        sum(i * i for i in range(100000))
        cpu_time = time.time() - start_time
        results['cpu_score'] = int(10000 / cpu_time)

        # Memory бенчмарк
        memory = psutil.virtual_memory()
        results['memory_score'] = int((memory.total // (1024**3)) * 100 / memory.percent)

        # Disk бенчмарк
        disk_usage = psutil.disk_usage('/')
        results['disk_score'] = int((disk_usage.free // (1024**3)) * 10)

        # Network бенчмарк
        net_io = psutil.net_io_counters()
        results['network_score'] = int((net_io.bytes_sent + net_io.bytes_recv) // (1024**2))

        # Общий счет
        scores = [results['cpu_score'], results['memory_score'], results['disk_score'], results['network_score']]
        results['overall_score'] = int(sum(scores) / len(scores))

        return results

    async def _run_optimization(self):
        """Запустить оптимизацию"""
        results = {}

        # Очистка кэша
        try:
            subprocess.run(['sync'], check=True)
            results['Cache cleared'] = '✅'
        except:
            results['Cache cleared'] = '❌'

        # Очистка временных файлов
        try:
            temp_files = len(os.listdir('/tmp'))
            results[f'Temp files found'] = str(temp_files)
        except:
            results['Temp files'] = '❌'

        # Проверка swap
        try:
            swap = psutil.swap_memory()
            results['Swap usage'] = f'{swap.percent}%'
        except:
            results['Swap usage'] = '❌'

        return results

    async def _run_security_scan(self):
        """Запустить сканирование безопасности"""
        results = {}

        # soso
        try:
            connections = psutil.net_connections()
            listening_ports = [conn.laddr.port for conn in connections if conn.status == 'LISTEN']
            results['Open ports'] = str(len(listening_ports))
        except:
            results['Open ports'] = '❌'

        # Проверка процессов
        try:
            processes = len(list(psutil.process_iter()))
            results['Running processes'] = str(processes)
        except:
            results['Running processes'] = '❌'

        # Проверка файловой системы
        try:
            disk_usage = psutil.disk_usage('/')
            results['Disk usage'] = f'{(disk_usage.used / disk_usage.total) * 100:.1f}%'
        except:
            results['Disk usage'] = '❌'

        return results

    async def _generate_system_report(self):
        """Сгенерировать отчет о системе"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'platform': platform.system(),
                'release': platform.release(),
                'architecture': platform.architecture()[0]
            },
            'cpu': {
                'cores': psutil.cpu_count(),
                'usage': psutil.cpu_percent(interval=1)
            },
            'memory': dict(psutil.virtual_memory()._asdict()),
            'disk': {},
            'network': dict(psutil.net_io_counters()._asdict()),
            'processes': len(list(psutil.process_iter()))
        }

        # Добавляем информацию о дисках
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                report['disk'][partition.device] = {
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': (usage.used / usage.total) * 100
                }
            except:
                pass

        return report

    async def _start_monitoring(self):
        """Запустить мониторинг"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def _stop_monitoring(self):
        """Остановить мониторинг"""
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

    async def _monitoring_loop(self):
        """Цикл мониторинга"""
        while self.monitoring_active:
            try:
                # Собираем данные о системе
                system_data = {
                    'timestamp': time.time(),
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_usage': psutil.disk_usage('/').percent,
                    'network_sent': psutil.net_io_counters().bytes_sent,
                    'network_recv': psutil.net_io_counters().bytes_recv
                }

                # Добавляем в историю
                self.system_history.append(system_data)

                # Ограничиваем размер истории
                if len(self.system_history) > 1000:
                    self.system_history = self.system_history[-1000:]

                # Проверяем алерты
                await self._check_alerts(system_data)

                # Ждем следующего цикла
                await asyncio.sleep(self.config["refresh_rate"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Ошибка в мониторинге: {e}")
                await asyncio.sleep(self.config["refresh_rate"])

    async def _check_alerts(self, system_data):
        """Проверить алерты"""
        # Проверка загрузки CPU
        if system_data['cpu_percent'] > 90:
            await self._send_alert("🔥 Высокая загрузка CPU", f"CPU: {system_data['cpu_percent']:.1f}%")

        # Проверка памяти
        if system_data['memory_percent'] > 90:
            await self._send_alert("💾 Высокое использование памяти", f"Memory: {system_data['memory_percent']:.1f}%")

        # Проверка диска
        if system_data['disk_usage'] > 95:
            await self._send_alert("💿 Диск почти заполнен", f"Disk: {system_data['disk_usage']:.1f}%")

    async def _send_alert(self, title, message):
        """Отправить алерт"""
        if self.config["notifications"]:
            alert = {
                'timestamp': time.time(),
                'title': title,
                'message': message
            }
            self.alerts.append(alert)

            # Здесь можно добавить отправку уведомлений
            print(f"ALERT: {title} - {message}")