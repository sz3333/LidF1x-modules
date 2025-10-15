# meta developer: Zeris
import os
import shutil
import time
import mimetypes
import zipfile
import tarfile
import hashlib
import json
import stat
import pwd
import grp
import subprocess
import asyncio
import signal
import threading
from pathlib import Path
from datetime import datetime
from telethon.tl.types import Message, DocumentAttributeFilename
from .. import loader, utils

@loader.tds
class FileManagerMod(loader.Module):
    """Файловый менеджер с встроенным терминалом"""

    strings = {
        "name": "FileManager",
        "current_dir": "📁 Текущая папка: <code>{path}</code>",
        "file_info": "📄 <b>Файл:</b> {name}\n📏 <b>Размер:</b> {size}\n📅 <b>Изменен:</b> {modified}",
        "folder_info": "📁 <b>Папка:</b> {name}\n📊 <b>Содержимое:</b> {items} элементов\n📅 <b>Изменена:</b> {modified}",
        "file_uploaded": "✅ Файл загружен: {name}",
        "file_deleted": "🗑️ Файл удален: {name}",
        "folder_created": "📁 Папка создана: {name}",
        "folder_deleted": "🗑️ Папка удалена: {name}",
        "file_copied": "📋 Файл скопирован: {name}",
        "file_moved": "📁 Файл перемещен: {name}",
        "file_renamed": "📝 Файл переименован: {old} → {new}",
        "archive_created": "📦 Архив создан: {name}",
        "archive_extracted": "📂 Архив распакован: {name}",
        "search_results": "🔍 Результаты поиска: {count} найдено",
        "permissions_changed": "🔧 Права изменены: {name}",
        "error": "❌ Ошибка: {error}",
        "access_denied": "🚫 Доступ запрещен к: {path}",
        "file_not_found": "❌ Файл не найден: {path}",
        "operation_cancelled": "❌ Операция отменена",
        "operation_success": "✅ Операция выполнена успешно",
        "file_too_large": "⚠️ Файл слишком большой для отправки",
        "upload_file": "📤 Отправьте файл для загрузки",
        "no_files": "📂 Папка пуста",
        "disk_usage": "💿 Использование диска: {used}/{total} ({percent}%)",
        "trash_empty": "🗑️ Корзина пуста",
        "trash_restored": "♻️ Восстановлено из корзины: {name}",
        "trash_emptied": "🗑️ Корзина очищена",
        "favorites_empty": "⭐ Избранное пуст",
        "added_to_favorites": "⭐ Добавлено в избранное: {name}",
        "removed_from_favorites": "❌ Удалено из избранного: {name}",
        "search_query": "🔍 Введите поисковый запрос:",
        "search_in_progress": "🔍 Поиск в процессе...",
        "search_complete": "🔍 Поиск завершен",
        "create_folder_name": "📁 Введите имя новой папки:",
        "rename_prompt": "📝 Введите новое имя:",
        "paste_here": "📋 Вставить сюда",
        "nothing_to_paste": "📋 Буфер обмена пуст",
        "file_exists": "⚠️ Файл уже существует",
        "compression_started": "📦 Начинаем сжатие...",
        "compression_finished": "📦 Сжатие завершено",
        "extraction_started": "📂 Начинаем распаковку...",
        "extraction_finished": "📂 Распаковка завершена",
        "calculating_size": "📏 Вычисляем размер...",
        "size_calculated": "📏 Размер: {size}",
        "file_properties": "📊 Свойства файла",
        "permission_owner": "👤 Владелец: {owner}",
        "permission_group": "👥 Группа: {group}",
        "permission_mode": "🔧 Права: {mode}",
        "file_type": "📄 Тип: {type}",
        "file_hash": "🔐 MD5: {hash}",
        "symlink_target": "🔗 Ссылка на: {target}",
        "hidden_files_shown": "👁️ Скрытые файлы показаны",
        "hidden_files_hidden": "🙈 Скрытые файлы скрыты",
        "sort_changed": "📊 Сортировка изменена: {sort}",
        "editor_opened": "✏️ Редактор открыт",
        "editor_saved": "💾 Файл сохранен",
        "viewer_opened": "👁️ Просмотр открыт",
        "batch_operation": "⚙️ Пакетная операция",
        "select_all": "✅ Выбрать все",
        "deselect_all": "❌ Снять выделение",
        "selected_count": "✅ Выбрано: {count}",
        "operation_on_selected": "⚙️ Операция над выбранными файлами",
        "settings_saved": "⚙️ Настройки сохранены",
        "theme_changed": "🎨 Тема изменена",
        "link_created": "🔗 Ссылка создана",
        "encrypted": "🔐 Файл зашифрован",
        "terminal_opened": "💻 Терминал открыт",
        "terminal_closed": "❌ Терминал закрыт",
        "command_executed": "✅ Команда выполнена",
        "command_failed": "❌ Ошибка выполнения команды",
        "command_running": "🔄 Команда выполняется...",
        "command_stopped": "⏹️ Команда остановлена",
        "command_output": "📋 Результат:\n<pre>{output}</pre>",
        "command_error": "❌ Ошибка:\n<pre>{error}</pre>",
        "command_timeout": "⏰ Превышено время выполнения",
        "command_killed": "💀 Команда принудительно завершена",
        "terminal_prompt": "💻 Терминал - {path}\n\n$ {command}",
        "enter_command": "💻 Введите команду:",
        "terminal_session": "💻 <b>Терминальная сессия</b>\n\n📁 Рабочая папка: <code>{path}</code>\n⏰ Время: {time}",
        "script_executed": "🐍 Скрипт выполнен",
        "script_failed": "❌ Ошибка выполнения скрипта",
        "script_running": "🔄 Скрипт выполняется...",
        "script_output": "📋 Вывод скрипта:\n<pre>{output}</pre>",
        "script_error": "❌ Ошибка скрипта:\n<pre>{error}</pre>",
        "python_not_found": "❌ Python не найден",
        "interpreter_not_found": "❌ Интерпретатор не найден",
        "syntax_check": "🔍 Проверка синтаксиса",
        "syntax_ok": "✅ Синтаксис корректен",
        "syntax_error": "❌ Синтаксическая ошибка",
        "process_monitor": "📊 Мониторинг процессов",
        "process_killed": "💀 Процесс завершен",
        "process_not_found": "❌ Процесс не найден",
        "system_info": "📊 Информация о системе",
        "quick_commands": "⚡ Быстрые команды",
        "command_history": "📋 История команд",
        "clear_history": "🗑️ Очистить историю",
        "save_session": "💾 Сохранить сессию",
        "load_session": "📂 Загрузить сессию",
        "terminal_help": "❓ Помощь по терминалу",
        "command_not_allowed": "🚫 Команда не разрешена",
        "dangerous_command": "⚠️ Опасная команда - подтвердите выполнение",
        "confirm_execution": "✅ Подтвердить выполнение",
        "cancel_execution": "❌ Отменить выполнение"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "start_path",
                os.path.expanduser("~"),
                "Начальная папка",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "show_hidden",
                False,
                "Показывать скрытые файлы",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "sort_by",
                "name",
                "Сортировка по умолчанию",
                validator=loader.validators.Choice(["name", "size", "date", "type"])
            ),
            loader.ConfigValue(
                "max_file_size",
                50,
                "Максимальный размер файла для отправки (MB)",
                validator=loader.validators.Integer(minimum=1, maximum=2000)
            ),
            loader.ConfigValue(
                "items_per_page",
                10,
                "Элементов на странице",
                validator=loader.validators.Integer(minimum=5, maximum=50)
            ),
            loader.ConfigValue(
                "enable_trash",
                True,
                "Использовать корзину",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "terminal_timeout",
                30,
                "Таймаут команд терминала (сек)",
                validator=loader.validators.Integer(minimum=5, maximum=300)
            ),
            loader.ConfigValue(
                "allow_dangerous_commands",
                False,
                "Разрешить опасные команды",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "max_output_length",
                3000,
                "Максимальная длина вывода команды",
                validator=loader.validators.Integer(minimum=100, maximum=4000)
            ),
            loader.ConfigValue(
                "enable_python_execution",
                True,
                "Разрешить выполнение Python скриптов",
                validator=loader.validators.Boolean()
            )
        )

        self.current_dirs = {}
        self.clipboard = {}
        self.favorites = {}
        self.recent_files = {}
        self.file_history = {}
        self.selection = {}
        self.sort_order = {}
        self.page_offset = {}
        self.operation_mode = {}
        self.trash_bin = {}
        self.search_results = {}
        self.user_input = {}
        self.terminal_sessions = {}
        self.running_processes = {}
        self.command_history = {}
        self.terminal_mode = {}
        self.script_processes = {}
        self.process_monitors = {}
        self.upload_pending = {} # Флаг для отслеживания ожидания загрузки файла

        self.dangerous_commands = {
            'rm -rf', 'format', 'fdisk', 'mkfs', 'dd', 'halt', 'reboot', 'shutdown',
            'passwd', 'su', 'sudo', 'chmod 777', 'chown', 'init', 'kill -9',
            'killall', 'pkill', 'fuser', 'mount', 'umount', 'crontab -r'
        }

        self.allowed_interpreters = {
            'python': 'python3',
            'python3': 'python3',
            'python2': 'python2',
            'node': 'node',
            'php': 'php',
            'ruby': 'ruby',
            'perl': 'perl',
            'bash': 'bash',
            'sh': 'sh',
            'zsh': 'zsh'
        }

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        await self._init_file_manager()

    async def _init_file_manager(self):
        """Инициализация файлового менеджера"""
        try:
            start_path = self.config["start_path"]
            if not os.path.exists(start_path):
                self.config["start_path"] = os.path.expanduser("~")

            self.trash_path = os.path.join(os.path.expanduser("~"), ".hikka_trash")
            os.makedirs(self.trash_path, exist_ok=True)

            self.temp_path = os.path.join(os.path.expanduser("~"), ".hikka_temp")
            os.makedirs(self.temp_path, exist_ok=True)

            self.favorites_file = os.path.join(os.path.expanduser("~"), ".hikka_favorites.json")
            self.history_file = os.path.join(os.path.expanduser("~"), ".hikka_history.json")

            await self._load_favorites()
            await self._load_history()

        except Exception as e:
            print(f"Ошибка инициализации файлового менеджера: {e}")

    async def _load_favorites(self):
        """Загрузить избранное"""
        try:
            if os.path.exists(self.favorites_file):
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for chat_id, favorites in data.items():
                        self.favorites[int(chat_id)] = favorites
        except Exception as e:
            print(f"Ошибка загрузки избранного: {e}")

    async def _save_favorites(self):
        """Сохранить избранное"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                data = {str(k): v for k, v in self.favorites.items()}
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения избранного: {e}")

    async def _load_history(self):
        """Загрузить историю"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for chat_id, history in data.items():
                        self.file_history[int(chat_id)] = history
        except Exception as e:
            print(f"Ошибка загрузки истории: {e}")

    async def _save_history(self):
        """Сохранить историю"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                data = {str(k): v for k, v in self.file_history.items()}
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения истории: {e}")

    @loader.command(ru_doc="Открыть файловый менеджер")
    async def fm(self, message: Message):
        """Открыть файловый менеджер"""
        chat_id = message.chat_id

        if chat_id not in self.current_dirs:
            self.current_dirs[chat_id] = self.config["start_path"]
            self.page_offset[chat_id] = 0
            self.sort_order[chat_id] = {"by": self.config["sort_by"], "reverse": False}
            self.operation_mode[chat_id] = "normal"
            self.selection[chat_id] = []
            self.terminal_mode[chat_id] = False
            if chat_id not in self.favorites:
                self.favorites[chat_id] = []
            if chat_id not in self.recent_files:
                self.recent_files[chat_id] = []
            if chat_id not in self.file_history:
                self.file_history[chat_id] = []
            if chat_id not in self.command_history:
                self.command_history[chat_id] = []
            self.upload_pending[chat_id] = False # Инициализация флага

        await self._show_file_manager(message, chat_id)

    async def _show_file_manager(self, message, chat_id):
        """Показать главное окно файлового менеджера"""
        current_path = self.current_dirs[chat_id]

        try:
            items = await self._get_directory_contents(current_path, chat_id)

            text = self.strings["current_dir"].format(path=current_path)

            if os.path.exists(current_path):
                disk_usage = shutil.disk_usage(current_path)
                total = disk_usage.total
                used = disk_usage.used
                percent = int((used / total) * 100)
                text += f"\n{self.strings['disk_usage'].format(used=self._format_size(used), total=self._format_size(total), percent=percent)}"

            text += f"\n📊 Элементов: {len(items)}"

            selected_count = len(self.selection[chat_id])
            if selected_count > 0:
                text += f"\n{self.strings['selected_count'].format(count=selected_count)}"

            buttons = await self._create_file_buttons(items, chat_id)
            nav_buttons = await self._create_navigation_buttons(chat_id)
            buttons.extend(nav_buttons)

            await utils.answer(message, text, reply_markup=buttons)

        except PermissionError:
            await utils.answer(message, self.strings["access_denied"].format(path=current_path))
        except Exception as e:
            await utils.answer(message, self.strings["error"].format(error=str(e)))

    async def _get_directory_contents(self, path, chat_id):
        """Получить содержимое папки"""
        try:
            items = []
            show_hidden = self.config["show_hidden"]

            with os.scandir(path) as entries:
                for entry in entries:
                    if not show_hidden and entry.name.startswith('.'):
                        continue

                    item_info = {
                        "name": entry.name,
                        "path": entry.path,
                        "is_dir": entry.is_dir(),
                        "size": 0,
                        "modified": 0,
                        "is_symlink": entry.is_symlink()
                    }

                    try:
                        stat = entry.stat()
                        item_info["size"] = stat.st_size
                        item_info["modified"] = stat.st_mtime
                        item_info["mode"] = stat.st_mode
                        item_info["uid"] = stat.st_uid
                        item_info["gid"] = stat.st_gid
                    except:
                        pass

                    items.append(item_info)

            items = await self._sort_items(items, chat_id)
            return items

        except Exception as e:
            print(f"Ошибка чтения папки {path}: {e}")
            return []

    async def _sort_items(self, items, chat_id):
        """Сортировка элементов"""
        sort_config = self.sort_order[chat_id]
        sort_by = sort_config["by"]
        reverse = sort_config["reverse"]

        folders = [item for item in items if item["is_dir"]]
        files = [item for item in items if not item["is_dir"]]

        def sort_key(item):
            if sort_by == "name":
                return item["name"].lower()
            elif sort_by == "size":
                return item["size"]
            elif sort_by == "date":
                return item["modified"]
            elif sort_by == "type":
                return Path(item["name"]).suffix.lower()
            return item["name"].lower()

        folders.sort(key=sort_key, reverse=reverse)
        files.sort(key=sort_key, reverse=reverse)

        return folders + files

    async def _create_file_buttons(self, items, chat_id):
        """Создать кнопки для файлов и папок"""
        buttons = []
        page_size = self.config["items_per_page"]
        page_offset = self.page_offset[chat_id]

        start_idx = page_offset * page_size
        end_idx = start_idx + page_size
        page_items = items[start_idx:end_idx]

        for item in page_items:
            selected = item["path"] in self.selection[chat_id]

            if item["is_dir"]:
                icon = "📁"
                if selected:
                    icon = "✅📁"
                callback = self.open_folder
            else:
                icon = self._get_file_icon(item["name"])
                if selected:
                    icon = f"✅{icon}"
                callback = self.file_actions

            name = item["name"]
            if len(name) > 20:
                name = name[:17] + "..."

            button_text = f"{icon} {name}"

            if not item["is_dir"] and item["size"] > 0:
                size_str = self._format_size(item["size"])
                button_text += f" ({size_str})"

            if item["is_symlink"]:
                button_text += " 🔗"

            file_action_buttons = [
                {"text": button_text, "callback": callback, "args": (chat_id, item["path"])}
            ]
            if selected:
                # Кнопка удаления
                file_action_buttons.append(
                    {"text": "🗑️", "callback": self.delete_item, "args": (chat_id, item["path"])}
                )
                # Новая кнопка: Очистить содержимое (только для папок)
                if item["is_dir"]:
                    file_action_buttons.append(
                        {"text": "🧹", "callback": self.clear_folder_content, "args": (chat_id, item["path"])}
                    )

            buttons.append(file_action_buttons)

        if len(items) > page_size:
            pagination_buttons = []

            if page_offset > 0:
                pagination_buttons.append(
                    {"text": "⬅️ Назад", "callback": self.prev_page, "args": (chat_id,)}
                )

            pagination_buttons.append(
                {"text": f"📄 {page_offset + 1}/{(len(items) - 1) // page_size + 1}",
                 "callback": self.show_page_info, "args": (chat_id,)}
            )

            if end_idx < len(items):
                pagination_buttons.append(
                    {"text": "➡️ Вперед", "callback": self.next_page, "args": (chat_id,)}
                )

            buttons.append(pagination_buttons)

        return buttons

    async def _create_navigation_buttons(self, chat_id):
        """Создать кнопки навигации и управления"""
        buttons = []
        current_path = self.current_dirs[chat_id]

        nav_row = []

        if current_path != "/":
            nav_row.append(
                {"text": "⬆️ Вверх", "callback": self.go_up, "args": (chat_id,)}
            )

        home_path = os.path.expanduser("~")
        if current_path != home_path:
            nav_row.append(
                {"text": "🏠 Домой", "callback": self.go_home, "args": (chat_id,)}
            )

        if current_path != "/":
            nav_row.append(
                {"text": "🔴 Корень", "callback": self.go_root, "args": (chat_id,)}
            )

        if nav_row:
            buttons.append(nav_row)

        file_ops_row = [
            {"text": "📁 Новая папка", "callback": self.create_folder, "args": (chat_id,)},
            {"text": "📤 Загрузить", "callback": self.upload_file, "args": (chat_id,)},
            {"text": "🔍 Поиск", "callback": self.search_files, "args": (chat_id,)}
        ]
        buttons.append(file_ops_row)

        if chat_id in self.clipboard and self.clipboard[chat_id]:
            paste_row = [
                {"text": "📋 Вставить", "callback": self.paste_file, "args": (chat_id,)},
                {"text": "❌ Очистить буфер", "callback": self.clear_clipboard, "args": (chat_id,)}
            ]
            buttons.append(paste_row)

        selection_row = []
        if len(self.selection[chat_id]) > 0:
            selection_row.extend([
                {"text": "⚙️ Операции", "callback": self.batch_operations, "args": (chat_id,)},
                {"text": "❌ Снять выделение", "callback": self.deselect_all, "args": (chat_id,)}
            ])
        else:
            selection_row.append(
                {"text": "✅ Выбрать все", "callback": self.select_all, "args": (chat_id,)}
            )
        buttons.append(selection_row)

        mode_row = []

        if self.config["show_hidden"]:
            mode_row.append(
                {"text": "🙈 Скрыть скрытые", "callback": self.toggle_hidden, "args": (chat_id,)}
            )
        else:
            mode_row.append(
                {"text": "👁️ Показать скрытые", "callback": self.toggle_hidden, "args": (chat_id,)}
            )

        sort_by = self.sort_order[chat_id]["by"]
        sort_icons = {"name": "🔤", "size": "📏", "date": "📅", "type": "📄"}
        mode_row.append(
            {"text": f"{sort_icons[sort_by]} Сортировка", "callback": self.change_sort, "args": (chat_id,)}
        )

        buttons.append(mode_row)

        tools_row = [
            {"text": "⭐ Избранное", "callback": self.show_favorites, "args": (chat_id,)},
            {"text": "📋 Недавние", "callback": self.show_recent, "args": (chat_id,)},
            {"text": "🗑️ Корзина", "callback": self.show_trash, "args": (chat_id,)}
        ]
        buttons.append(tools_row)

        terminal_row = [
            {"text": "💻 Терминал", "callback": self.open_terminal, "args": (chat_id,)},
            {"text": "📊 Система", "callback": self.show_system_info, "args": (chat_id,)},
            {"text": "⚙️ Настройки", "callback": self.settings_menu, "args": (chat_id,)}
        ]
        buttons.append(terminal_row)

        buttons.append([
            {"text": "🔄 Обновить", "callback": self.refresh_view, "args": (chat_id,)}
        ])

        return buttons

    def _get_file_icon(self, filename):
        """Получить иконку для файла по расширению"""
        extension = Path(filename).suffix.lower()

        icon_map = {
            '.txt': '📄', '.doc': '📄', '.docx': '📄', '.pdf': '📑', '.rtf': '📄',
            '.xls': '📊', '.xlsx': '📊', '.csv': '📊', '.ppt': '📊', '.pptx': '📊',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.bmp': '🖼️',
            '.svg': '🖼️', '.ico': '🖼️', '.tiff': '🖼️', '.webp': '🖼️',
            '.mp4': '🎬', '.avi': '🎬', '.mov': '🎬', '.wmv': '🎬', '.flv': '🎬',
            '.mkv': '🎬', '.webm': '🎬', '.m4v': '🎬',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵', '.aac': '🎵', '.ogg': '🎵',
            '.wma': '🎵', '.m4a': '🎵',
            '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', '.gz': '📦',
            '.bz2': '📦', '.xz': '📦',
            '.py': '🐍', '.js': '📄', '.html': '🌐', '.css': '🎨', '.php': '📄',
            '.cpp': '📄', '.c': '📄', '.h': '📄', '.java': '📄', '.go': '📄',
            '.exe': '⚙️', '.app': '⚙️', '.deb': '📦', '.rpm': '📦', '.dmg': '💿',
            '.iso': '💿', '.msi': '⚙️',
            '.json': '📄', '.xml': '📄', '.yml': '📄', '.yaml': '📄', '.ini': '📄',
            '.cfg': '📄', '.conf': '📄',
            '.db': '🗄️', '.sqlite': '🗄️', '.sql': '🗄️',
            '.ttf': '🔤', '.otf': '🔤', '.woff': '🔤',
            '.log': '📋', '.tmp': '🗂️', '.bak': '💾'
        }

        return icon_map.get(extension, '📄')

    def _format_size(self, size):
        """Форматировать размер файла"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def _format_date(self, timestamp):
        """Форматировать дату"""
        return datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M")

    def _get_file_hash(self, file_path):
        """Получить MD5 хеш файла"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return "N/A"

    def _get_file_type(self, file_path):
        """Получить тип файла"""
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type or "Unknown"
        except:
            return "Unknown"

    def _get_file_permissions(self, file_path):
        """Получить права доступа к файлу"""
        try:
            file_stat = os.stat(file_path)
            mode = file_stat.st_mode
            permissions = stat.filemode(mode)

            try:
                owner = pwd.getpwuid(file_stat.st_uid).pw_name
            except:
                owner = str(file_stat.st_uid)

            try:
                group = grp.getgrgid(file_stat.st_gid).gr_name
            except:
                group = str(file_stat.st_gid)

            return {
                "mode": permissions,
                "owner": owner,
                "group": group,
                "octal": oct(mode)[-3:]
            }
        except:
            return {"mode": "Unknown", "owner": "Unknown", "group": "Unknown", "octal": "000"}

    async def open_folder(self, call, chat_id, folder_path):
        """Открыть папку"""
        try:
            if os.path.isdir(folder_path) and os.access(folder_path, os.R_OK):
                self.current_dirs[chat_id] = folder_path
                self.page_offset[chat_id] = 0

                if chat_id not in self.recent_files:
                    self.recent_files[chat_id] = []
                if folder_path not in self.recent_files[chat_id]:
                    self.recent_files[chat_id].insert(0, folder_path)
                    self.recent_files[chat_id] = self.recent_files[chat_id][:10]

                await self._save_history()
                await self._show_file_manager(call, chat_id)
            else:
                await call.answer(self.strings["access_denied"].format(path=folder_path))
        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def file_actions(self, call, chat_id, file_path):
        """Показать действия для файла"""
        try:
            if not os.path.exists(file_path):
                await call.answer(self.strings["file_not_found"].format(path=file_path))
                return

            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            file_name = os.path.basename(file_path)

            info_text = self.strings["file_info"].format(
                name=file_name,
                size=self._format_size(file_size),
                modified=self._format_date(file_stat.st_mtime)
            )

            buttons = [
                [
                    {"text": "📤 Скачать", "callback": self.download_file, "args": (chat_id, file_path)},
                    {"text": "👁️ Просмотр", "callback": self.view_file, "args": (chat_id, file_path)},
                    {"text": "✏️ Редактировать", "callback": self.edit_file, "args": (chat_id, file_path)}
                ],
                [
                    {"text": "📋 Копировать", "callback": self.copy_file, "args": (chat_id, file_path)},
                    {"text": "✂️ Вырезать", "callback": self.cut_file, "args": (chat_id, file_path)},
                    {"text": "📝 Переименовать", "callback": self.rename_file, "args": (chat_id, file_path)}
                ]
            ]

            file_ext = Path(file_path).suffix.lower()
            if file_ext == '.py' and self.config["enable_python_execution"]:
                buttons.append([
                    {"text": "🐍 Запустить Python", "callback": self.run_python_script, "args": (chat_id, file_path)},
                    {"text": "🔍 Проверить синтаксис", "callback": self.check_python_syntax, "args": (chat_id, file_path)}
                ])

            buttons.extend([
                [
                    {"text": "🔒 Права", "callback": self.change_permissions, "args": (chat_id, file_path)},
                    {"text": "🔐 Шифровать", "callback": self.encrypt_file, "args": (chat_id, file_path)},
                    {"text": "📦 Архивировать", "callback": self.archive_file, "args": (chat_id, file_path)}
                ],
                [
                    {"text": "⭐ В избранное", "callback": self.add_to_favorites, "args": (chat_id, file_path)},
                    {"text": "🔗 Ссылка", "callback": self.create_link, "args": (chat_id, file_path)},
                    {"text": "📊 Свойства", "callback": self.show_properties, "args": (chat_id, file_path)}
                ],
                [
                    {"text": "🗑️ Удалить", "callback": self.delete_item, "args": (chat_id, file_path)},
                    {"text": "🔙 Назад", "callback": self.back_to_folder, "args": (chat_id,)}
                ]
            ])

            await call.edit(info_text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def run_python_script(self, call, chat_id, file_path):
        """Запустить Python скрипт"""
        try:
            if not os.path.exists(file_path):
                await call.answer(self.strings["file_not_found"].format(path=file_path))
                return

            await call.answer(self.strings["script_running"])

            process = subprocess.Popen(
                [self.allowed_interpreters['python'], file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(file_path)
            )

            self.script_processes[chat_id] = process

            try:
                stdout, stderr = process.communicate(timeout=self.config["terminal_timeout"])

                if process.returncode == 0:
                    output = stdout.strip()
                    if len(output) > self.config["max_output_length"]:
                        output = output[:self.config["max_output_length"]] + "\n... (вывод обрезан)"

                    result_text = self.strings["script_output"].format(output=output)
                    await call.answer(result_text)
                else:
                    error = stderr.strip()
                    if len(error) > self.config["max_output_length"]:
                        error = error[:self.config["max_output_length"]] + "\n... (ошибка обрезана)"

                    result_text = self.strings["script_error"].format(error=error)
                    await call.answer(result_text)

            except subprocess.TimeoutExpired:
                process.kill()
                await call.answer(self.strings["command_timeout"])
            except Exception as e:
                await call.answer(self.strings["script_failed"].format(error=str(e)))
            finally:
                if chat_id in self.script_processes:
                    del self.script_processes[chat_id]

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def check_python_syntax(self, call, chat_id, file_path):
        """Проверить синтаксис Python файла"""
        try:
            if not os.path.exists(file_path):
                await call.answer(self.strings["file_not_found"].format(path=file_path))
                return

            process = subprocess.Popen(
                [self.allowed_interpreters['python'], '-m', 'py_compile', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(timeout=10)

            if process.returncode == 0:
                await call.answer(self.strings["syntax_ok"])
            else:
                error = stderr.strip()
                await call.answer(self.strings["syntax_error"] + f"\n<pre>{error}</pre>")

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def open_terminal(self, call, chat_id):
        """Открыть терминал"""
        try:
            current_path = self.current_dirs[chat_id]

            if chat_id not in self.terminal_sessions:
                self.terminal_sessions[chat_id] = {
                    "current_dir": current_path,
                    "history": [],
                    "environment": dict(os.environ)
                }

            session_info = self.strings["terminal_session"].format(
                path=current_path,
                time=datetime.now().strftime("%H:%M:%S")
            )

            buttons = [
                [
                    {"text": "📋 ls", "callback": self.terminal_command, "args": (chat_id, "ls -la")},
                    {"text": "📁 pwd", "callback": self.terminal_command, "args": (chat_id, "pwd")},
                    {"text": "🔍 ps", "callback": self.terminal_command, "args": (chat_id, "ps aux")}
                ],
                [
                    {"text": "💾 df", "callback": self.terminal_command, "args": (chat_id, "df -h")},
                    {"text": "📊 htop", "callback": self.terminal_command, "args": (chat_id, "htop")},
                    {"text": "🌐 ping", "callback": self.terminal_command, "args": (chat_id, "ping -c 3 google.com")}
                ],
                [
                    {"text": "🐍 python", "callback": self.terminal_command, "args": (chat_id, "python3 --version")},
                    {"text": "🔧 git", "callback": self.terminal_command, "args": (chat_id, "git status")},
                    {"text": "📦 npm", "callback": self.terminal_command, "args": (chat_id, "npm --version")}
                ],
                [
                    {"text": "💻 Ввести команду", "callback": self.enter_command, "args": (chat_id,)},
                    {"text": "📋 История", "callback": self.show_command_history, "args": (chat_id,)},
                    {"text": "🗑️ Очистить", "callback": self.clear_terminal, "args": (chat_id,)}
                ],
                [
                    {"text": "⚙️ Процессы", "callback": self.show_processes, "args": (chat_id,)},
                    {"text": "📊 Система", "callback": self.show_system_info, "args": (chat_id,)},
                    {"text": "❓ Помощь", "callback": self.show_terminal_help, "args": (chat_id,)}
                ],
                [
                    {"text": "🔙 Назад к файлам", "callback": self.back_to_folder, "args": (chat_id,)},
                    {"text": "❌ Закрыть", "callback": self.close_terminal, "args": (chat_id,)}
                ]
            ]

            await call.edit(session_info, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def terminal_command(self, call, chat_id, command):
        """Выполнить команду в терминале"""
        try:
            if self._is_dangerous_command(command):
                if not self.config["allow_dangerous_commands"]:
                    await call.answer(self.strings["command_not_allowed"])
                    return
                else:
                    await self._confirm_dangerous_command(call, chat_id, command)
                    return

            await call.answer(self.strings["command_running"])

            current_dir = self.terminal_sessions[chat_id]["current_dir"]

            if command.startswith("cd "):
                await self._handle_cd_command(call, chat_id, command)
                return

            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=current_dir
            )

            self.running_processes[chat_id] = process

            try:
                stdout, stderr = process.communicate(timeout=self.config["terminal_timeout"])

                if chat_id not in self.command_history:
                    self.command_history[chat_id] = []

                self.command_history[chat_id].append({
                    "command": command,
                    "timestamp": datetime.now().isoformat(),
                    "exit_code": process.returncode,
                    "output": stdout,
                    "error": stderr
                })

                if len(self.command_history[chat_id]) > 100:
                    self.command_history[chat_id] = self.command_history[chat_id][-100:]

                if process.returncode == 0:
                    output = stdout.strip()
                    if len(output) > self.config["max_output_length"]:
                        output = output[:self.config["max_output_length"]] + "\n... (вывод обрезан)"

                    result_text = self.strings["command_output"].format(output=output or "Команда выполнена успешно")
                    await call.answer(result_text)
                else:
                    error = stderr.strip()
                    if len(error) > self.config["max_output_length"]:
                        error = error[:self.config["max_output_length"]] + "\n... (ошибка обрезана)"

                    result_text = self.strings["command_error"].format(error=error or "Неизвестная ошибка")
                    await call.answer(result_text)

            except subprocess.TimeoutExpired:
                process.kill()
                await call.answer(self.strings["command_timeout"])
            except Exception as e:
                await call.answer(self.strings["command_failed"].format(error=str(e)))
            finally:
                if chat_id in self.running_processes:
                    del self.running_processes[chat_id]

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def _handle_cd_command(self, call, chat_id, command):
        """Обработать команду cd"""
        try:
            parts = command.split()
            if len(parts) < 2:
                target_dir = os.path.expanduser("~")
            else:
                target_dir = parts[1]

            current_dir = self.terminal_sessions[chat_id]["current_dir"]

            if target_dir == "..":
                new_dir = os.path.dirname(current_dir)
            elif target_dir.startswith("/"):
                new_dir = target_dir
            else:
                new_dir = os.path.join(current_dir, target_dir)

            new_dir = os.path.abspath(new_dir)

            if os.path.exists(new_dir) and os.path.isdir(new_dir):
                self.terminal_sessions[chat_id]["current_dir"] = new_dir
                self.current_dirs[chat_id] = new_dir
                await call.answer(f"📁 Переход в {new_dir}")
            else:
                await call.answer(f"❌ Папка не найдена: {new_dir}")

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    def _is_dangerous_command(self, command):
        """Проверить, является ли команда опасной"""
        command_lower = command.lower()
        for dangerous in self.dangerous_commands:
            if dangerous in command_lower:
                return True
        return False

    async def _confirm_dangerous_command(self, call, chat_id, command):
        """Подтвердить выполнение опасной команды"""
        text = f"{self.strings['dangerous_command']}\n\n<pre>{command}</pre>"

        buttons = [
            [
                {"text": "✅ Подтвердить", "callback": self.execute_dangerous_command, "args": (chat_id, command)},
                {"text": "❌ Отменить", "callback": self.cancel_dangerous_command, "args": (chat_id,)}
            ]
        ]

        await call.edit(text, reply_markup=buttons)

    async def execute_dangerous_command(self, call, chat_id, command):
        """Выполнить опасную команду после подтверждения"""
        await self.terminal_command(call, chat_id, command)

    async def cancel_dangerous_command(self, call, chat_id):
        """Отменить выполнение опасной команды"""
        await call.answer(self.strings["cancel_execution"])
        await self.open_terminal(call, chat_id)

    async def enter_command(self, call, chat_id):
        """Ввести команду вручную"""
        text = self.strings["enter_command"]

        self.user_input[chat_id] = {
            "action": "enter_command",
            "timestamp": time.time()
        }

        buttons = [
            [
                {"text": "❌ Отменить", "callback": self.cancel_command_input, "args": (chat_id,)}
            ]
        ]

        await call.edit(text, reply_markup=buttons)

    async def cancel_command_input(self, call, chat_id):
        """Отменить ввод команды"""
        if chat_id in self.user_input:
            del self.user_input[chat_id]
        await self.open_terminal(call, chat_id)

    async def show_command_history(self, call, chat_id):
        """Показать историю команд"""
        try:
            if chat_id not in self.command_history or not self.command_history[chat_id]:
                await call.answer("📋 История команд пуста")
                return

            history = self.command_history[chat_id][-10:]  # Последние 10 команд

            text = "📋 <b>История команд:</b>\n\n"
            for i, entry in enumerate(reversed(history), 1):
                timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
                exit_code = entry["exit_code"]
                status = "✅" if exit_code == 0 else "❌"

                text += f"{i}. {status} <code>{entry['command']}</code> ({timestamp})\n"

            buttons = [
                [
                    {"text": "🗑️ Очистить историю", "callback": self.clear_command_history, "args": (chat_id,)},
                    {"text": "🔙 Назад", "callback": self.open_terminal, "args": (chat_id,)}
                ]
            ]

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def clear_command_history(self, call, chat_id):
        """Очистить историю команд"""
        self.command_history[chat_id] = []
        await call.answer("🗑️ История команд очищена")
        await self.open_terminal(call, chat_id)

    async def show_processes(self, call, chat_id):
        """Показать процессы"""
        try:
            process = subprocess.Popen(
                ["ps", "aux"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(timeout=10)

            if process.returncode == 0:
                lines = stdout.strip().split('\n')
                header = lines[0]
                processes = lines[1:11]  # Первые 10 процессов

                text = f"📊 <b>Процессы:</b>\n\n<pre>{header}\n"
                for proc in processes:
                    text += f"{proc}\n"
                text += "</pre>"

                if len(lines) > 11:
                    text += f"\n... и еще {len(lines) - 11} процессов"

                buttons = [
                    [
                        {"text": "🔄 Обновить", "callback": self.show_processes, "args": (chat_id,)},
                        {"text": "💀 Убить процесс", "callback": self.kill_process, "args": (chat_id,)}
                    ],
                    [
                        {"text": "🔙 Назад", "callback": self.open_terminal, "args": (chat_id,)}
                    ]
                ]

                await call.edit(text, reply_markup=buttons)
            else:
                await call.answer(f"❌ Ошибка получения процессов: {stderr}")

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def kill_process(self, call, chat_id):
        """Убить процесс"""
        text = "💀 Введите PID процесса для завершения:"

        self.user_input[chat_id] = {
            "action": "kill_process",
            "timestamp": time.time()
        }

        buttons = [
            [
                {"text": "❌ Отменить", "callback": self.cancel_kill_process, "args": (chat_id,)}
            ]
        ]

        await call.edit(text, reply_markup=buttons)

    async def cancel_kill_process(self, call, chat_id):
        """Отменить убийство процесса"""
        if chat_id in self.user_input:
            del self.user_input[chat_id]
        await self.show_processes(call, chat_id)

    async def show_system_info(self, call, chat_id):
        """Показать информацию о системе"""
        try:
            system_info = f"📊 <b>Информация о системе:</b>\n\n"

            # Основная информация
            import platform
            system_info += f"🖥️ ОС: {platform.system()} {platform.release()}\n"
            system_info += f"🏗️ Архитектура: {platform.architecture()[0]}\n"
            system_info += f"🖥️ Машина: {platform.machine()}\n"
            system_info += f"💻 Процессор: {platform.processor()}\n"

            # Информация о памяти
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    for line in meminfo.split('\n'):
                        if 'MemTotal' in line:
                            total_mem = int(line.split()[1]) * 1024
                            system_info += f"💾 Память: {self._format_size(total_mem)}\n"
                            break
            except:
                pass

            # Информация о дисках
            try:
                disk_usage = shutil.disk_usage('/')
                system_info += f"💿 Диск: {self._format_size(disk_usage.used)}/{self._format_size(disk_usage.total)}\n"
            except:
                pass

            # Время работы
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.read().split()[0])
                    hours, remainder = divmod(uptime_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    system_info += f"⏱️ Время работы: {int(hours)}h {int(minutes)}m {int(seconds)}s\n"
            except:
                pass

            # Загрузка системы
            try:
                load_avg = os.getloadavg()
                system_info += f"📈 Загрузка: {load_avg[0]:.2f} {load_avg[1]:.2f} {load_avg[2]:.2f}\n"
            except:
                pass

            buttons = [
                [
                    {"text": "🔄 Обновить", "callback": self.show_system_info, "args": (chat_id,)},
                    {"text": "📊 Процессы", "callback": self.show_processes, "args": (chat_id,)}
                ],
                [
                    {"text": "🔙 Назад", "callback": self.open_terminal, "args": (chat_id,)}
                ]
            ]

            await call.edit(system_info, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def show_terminal_help(self, call, chat_id):
        """Показать помощь по терминалу"""
        help_text = """❓ <b>Помощь по терминалу:</b>

🔧 <b>Основные команды:</b>
• <code>ls</code> - список файлов
• <code>cd</code> - смена папки
• <code>pwd</code> - текущая папка
• <code>mkdir</code> - создать папку
• <code>rm</code> - удалить файл
• <code>cp</code> - копировать
• <code>mv</code> - переместить

📊 <b>Системная информация:</b>
• <code>ps</code> - процессы
• <code>top</code> - мониторинг
• <code>df</code> - диски
• <code>free</code> - память
• <code>uname</code> - система

🌐 <b>Сеть:</b>
• <code>ping</code> - проверка связи
• <code>curl</code> - HTTP запросы
• <code>wget</code> - загрузка файлов

🐍 <b>Python:</b>
• <code>python script.py</code> - запуск скрипта
• <code>pip install</code> - установка пакетов

⚠️ <b>Ограничения:</b>
• Таймаут: {timeout}с
• Опасные команды требуют подтверждения
• Вывод ограничен {max_output} символами""".format(
            timeout=self.config["terminal_timeout"],
            max_output=self.config["max_output_length"]
        )

        buttons = [
            [
                {"text": "🔙 Назад", "callback": self.open_terminal, "args": (chat_id,)}
            ]
        ]

        await call.edit(help_text, reply_markup=buttons)

    async def clear_terminal(self, call, chat_id):
        """Очистить терминал"""
        if chat_id in self.terminal_sessions:
            self.terminal_sessions[chat_id]["history"] = []
        await call.answer("🗑️ Терминал очищен")
        await self.open_terminal(call, chat_id)

    async def close_terminal(self, call, chat_id):
        """Закрыть терминал"""
        if chat_id in self.terminal_sessions:
            del self.terminal_sessions[chat_id]
        if chat_id in self.running_processes:
            try:
                self.running_processes[chat_id].kill()
                del self.running_processes[chat_id]
            except:
                pass
        await call.answer(self.strings["terminal_closed"])
        await self.back_to_folder(call, chat_id)

    async def download_file(self, call, chat_id, file_path):
        """Скачать файл"""
        try:
            file_size = os.path.getsize(file_path)
            max_size = self.config["max_file_size"] * 1024 * 1024

            if file_size > max_size:
                await call.answer(self.strings["file_too_large"])
                return

            await call.answer("📤 Отправляю файл...")
            await self._client.send_file(
                chat_id,
                file_path,
                caption=f"📁 {os.path.basename(file_path)}\n📏 {self._format_size(file_size)}"
            )

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def view_file(self, call, chat_id, file_path):
        """Просмотр файла"""
        try:
            file_ext = Path(file_path).suffix.lower()

            if file_ext in ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.yml', '.yaml', '.ini', '.cfg', '.conf', '.log']:
                await self._view_text_file(call, chat_id, file_path)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                await self._view_image_file(call, chat_id, file_path)
            else:
                await call.answer("👁️ Предварительный просмотр недоступен для этого типа файла")

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def _view_text_file(self, call, chat_id, file_path):
        """Просмотр текстового файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(2000)

            if len(content) >= 2000:
                content += "\n... (файл обрезан)"

            text = f"📄 <b>{os.path.basename(file_path)}</b>\n\n<pre>{content}</pre>"

            buttons = [
                [
                    {"text": "✏️ Редактировать", "callback": self.edit_file, "args": (chat_id, file_path)},
                    {"text": "📤 Скачать", "callback": self.download_file, "args": (chat_id, file_path)}
                ],
                [
                    {"text": "🔙 Назад", "callback": self.back_to_file_actions, "args": (chat_id, file_path)}
                ]
            ]

            await call.edit(text, reply_markup=buttons)

        except UnicodeDecodeError:
            await call.answer("❌ Не удается прочитать файл как текст")
        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def _view_image_file(self, call, chat_id, file_path):
        """Просмотр изображения"""
        try:
            file_size = os.path.getsize(file_path)
            max_size = self.config["max_file_size"] * 1024 * 1024

            if file_size > max_size:
                await call.answer(self.strings["file_too_large"])
                return

            await call.answer("🖼️ Отправляю изображение...")
            await self._client.send_file(
                chat_id,
                file_path,
                caption=f"🖼️ {os.path.basename(file_path)}"
            )

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def edit_file(self, call, chat_id, file_path):
        """Редактировать файл"""
        try:
            file_ext = Path(file_path).suffix.lower()

            if file_ext in ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.yml', '.yaml', '.ini', '.cfg', '.conf', '.log']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if len(content) > 4000:
                    await call.answer("❌ Файл слишком большой для редактирования")
                    return

                text = f"✏️ <b>Редактирование: {os.path.basename(file_path)}</b>\n\n"
                text += "Отправьте новое содержимое файла:"

                self.user_input[chat_id] = {
                    "action": "edit_file",
                    "file_path": file_path,
                    "original_content": content
                }

                buttons = [
                    [
                        {"text": "❌ Отменить", "callback": self.cancel_edit, "args": (chat_id, file_path)}
                    ]
                ]

                await call.edit(text, reply_markup=buttons)

            else:
                await call.answer("❌ Редактирование недоступно для этого типа файла")

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def copy_file(self, call, chat_id, file_path):
        """Копировать файл"""
        self.clipboard[chat_id] = {"action": "copy", "path": file_path}
        file_name = os.path.basename(file_path)
        await call.answer(f"📋 Файл скопирован: {file_name}")

    async def cut_file(self, call, chat_id, file_path):
        """Вырезать файл"""
        self.clipboard[chat_id] = {"action": "move", "path": file_path}
        file_name = os.path.basename(file_path)
        await call.answer(f"✂️ Файл вырезан: {file_name}")

    async def paste_file(self, call, chat_id):
        """Вставить файл"""
        try:
            if chat_id not in self.clipboard or not self.clipboard[chat_id]:
                await call.answer(self.strings["nothing_to_paste"])
                return

            clipboard_data = self.clipboard[chat_id]
            source_path = clipboard_data["path"]
            action = clipboard_data["action"]

            if not os.path.exists(source_path):
                await call.answer(self.strings["file_not_found"].format(path=source_path))
                return

            dest_dir = self.current_dirs[chat_id]
            file_name = os.path.basename(source_path)
            dest_path = os.path.join(dest_dir, file_name)

            if os.path.exists(dest_path):
                await call.answer(self.strings["file_exists"])
                return

            if action == "copy":
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, dest_path)
                else:
                    shutil.copy2(source_path, dest_path)
                await call.answer(self.strings["file_copied"].format(name=file_name))
            elif action == "move":
                shutil.move(source_path, dest_path)
                await call.answer(self.strings["file_moved"].format(name=file_name))
                self.clipboard[chat_id] = {}

            await self._show_file_manager(call, chat_id)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def clear_clipboard(self, call, chat_id):
        """Очистить буфер обмена"""
        self.clipboard[chat_id] = {}
        await call.answer("📋 Буфер обмена очищен")

    async def rename_file(self, call, chat_id, file_path):
        """Переименовать файл"""
        try:
            file_name = os.path.basename(file_path)
            text = f"📝 <b>Переименование: {file_name}</b>\n\n"
            text += self.strings["rename_prompt"]

            self.user_input[chat_id] = {
                "action": "rename_file",
                "file_path": file_path,
                "original_name": file_name
            }

            buttons = [
                [
                    {"text": "❌ Отменить", "callback": self.cancel_rename, "args": (chat_id, file_path)}
                ]
            ]

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def delete_item(self, call, chat_id, item_path):
        """Удалить выбранный элемент (файл или папку)"""
        try:
            item_name = os.path.basename(item_path)

            if self.config["enable_trash"]:
                trash_path = os.path.join(self.trash_path, f"{int(time.time())}_{item_name}")
                shutil.move(item_path, trash_path)

                if chat_id not in self.trash_bin:
                    self.trash_bin[chat_id] = []
                self.trash_bin[chat_id].append({
                    "original_path": item_path,
                    "trash_path": trash_path,
                    "deleted_time": time.time(),
                    "name": item_name
                })

                await call.answer(self.strings["file_deleted"].format(name=item_name))
            else:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                await call.answer(self.strings["file_deleted"].format(name=item_name))

            await self.back_to_folder(call, chat_id)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def clear_folder_content(self, call, chat_id, folder_path):
        """Очистить содержимое папки"""
        try:
            folder_name = os.path.basename(folder_path)
            confirm_text = f"🧹 Вы уверены, что хотите очистить содержимое папки <b>{folder_name}</b>?\nЭто действие нельзя отменить."

            buttons = [
                [
                    {"text": "✅ Очистить", "callback": self._perform_clear_folder_content, "args": (chat_id, folder_path)},
                    {"text": "❌ Отмена", "callback": self.back_to_folder, "args": (chat_id,)}
                ]
            ]
            await call.edit(confirm_text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def _perform_clear_folder_content(self, call, chat_id, folder_path):
        """Выполнить очистку содержимого папки"""
        try:
            deleted_count = 0
            for item_name in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item_name)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    deleted_count += 1
                except Exception as e:
                    print(f"Ошибка удаления {item_path}: {e}")

            await call.answer(f"🧹 Содержимое папки {os.path.basename(folder_path)} очищено. Удалено элементов: {deleted_count}")
            await self.back_to_folder(call, chat_id)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))


    async def create_folder(self, call, chat_id):
        """Создать новую папку"""
        try:
            text = "📁 <b>Создание новой папки</b>\n\n"
            text += self.strings["create_folder_name"]

            self.user_input[chat_id] = {
                "action": "create_folder",
                "parent_path": self.current_dirs[chat_id]
            }

            buttons = [
                [
                    {"text": "❌ Отменить", "callback": self.cancel_create_folder, "args": (chat_id,)}
                ]
            ]

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def upload_file(self, call, chat_id):
        """Загрузить файл"""
        text = "📤 <b>Загрузка файла</b>\n\n"
        text += self.strings["upload_file"]
        text += f"\n\n📁 Текущая папка: <code>{self.current_dirs[chat_id]}</code>"

        # Устанавливаем флаг ожидания загрузки
        self.user_input[chat_id] = {
            "action": "upload_file",
            "timestamp": time.time()
        }

        buttons = [
            [
                {"text": "🔙 Назад", "callback": self.back_to_folder, "args": (chat_id,)}
            ]
        ]

        await call.edit(text, reply_markup=buttons)

    async def search_files(self, call, chat_id):
        """Поиск файлов"""
        try:
            text = "🔍 <b>Поиск файлов</b>\n\n"
            text += self.strings["search_query"]

            self.user_input[chat_id] = {
                "action": "search_files",
                "search_path": self.current_dirs[chat_id]
            }

            buttons = [
                [
                    {"text": "❌ Отменить", "callback": self.cancel_search, "args": (chat_id,)}
                ]
            ]

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def _perform_search(self, chat_id, query):
        """Выполнить поиск"""
        try:
            search_path = self.current_dirs[chat_id]
            results = []

            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if query.lower() in file.lower():
                        file_path = os.path.join(root, file)
                        results.append(file_path)

                for dir in dirs:
                    if query.lower() in dir.lower():
                        dir_path = os.path.join(root, dir)
                        results.append(dir_path)

            self.search_results[chat_id] = results
            return results

        except Exception as e:
            print(f"Ошибка поиска: {e}")
            return []

    async def show_search_results(self, call, chat_id, results):
        """Показать результаты поиска"""
        try:
            if not results:
                await call.answer("🔍 Ничего не найдено")
                return

            text = self.strings["search_results"].format(count=len(results))

            buttons = []
            for i, result in enumerate(results[:10]):
                relative_path = os.path.relpath(result, self.current_dirs[chat_id])
                name = os.path.basename(result)

                if os.path.isdir(result):
                    icon = "📁"
                    callback = self.open_search_folder
                else:
                    icon = self._get_file_icon(name)
                    callback = self.open_search_file

                button_text = f"{icon} {relative_path}"
                if len(button_text) > 30:
                    button_text = button_text[:27] + "..."

                buttons.append([
                    {"text": button_text, "callback": callback, "args": (chat_id, result)}
                ])

            if len(results) > 10:
                text += f"\n... и еще {len(results) - 10} результатов"

            buttons.append([
                {"text": "🔙 Назад", "callback": self.back_to_folder, "args": (chat_id,)}
            ])

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def open_search_folder(self, call, chat_id, folder_path):
        """Открыть папку из результатов поиска"""
        await self.open_folder(call, chat_id, folder_path)

    async def open_search_file(self, call, chat_id, file_path):
        """Открыть файл из результатов поиска"""
        await self.file_actions(call, chat_id, file_path)

    async def select_all(self, call, chat_id):
        """Выбрать все файлы"""
        try:
            current_path = self.current_dirs[chat_id]
            items = await self._get_directory_contents(current_path, chat_id)

            self.selection[chat_id] = [item["path"] for item in items]

            await call.answer(self.strings["selected_count"].format(count=len(self.selection[chat_id])))
            await self._show_file_manager(call, chat_id)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def deselect_all(self, call, chat_id):
        """Снять выделение со всех файлов"""
        self.selection[chat_id] = []
        await call.answer("❌ Выделение снято")
        await self._show_file_manager(call, chat_id)

    async def batch_operations(self, call, chat_id):
        """Операции с выбранными файлами"""
        try:
            if not self.selection[chat_id]:
                await call.answer("❌ Нет выбранных файлов")
                return

            count = len(self.selection[chat_id])
            text = f"⚙️ <b>Операции с выбранными файлами</b>\n\n"
            text += self.strings["selected_count"].format(count=count)

            buttons = [
                [
                    {"text": "📋 Копировать", "callback": self.batch_copy, "args": (chat_id,)},
                    {"text": "✂️ Вырезать", "callback": self.batch_cut, "args": (chat_id,)},
                    {"text": "🗑️ Удалить", "callback": self.batch_delete, "args": (chat_id,)}
                ],
                [
                    {"text": "📦 Архивировать", "callback": self.batch_archive, "args": (chat_id,)},
                    {"text": "🔐 Шифровать", "callback": self.batch_encrypt, "args": (chat_id,)},
                    {"text": "🔒 Права", "callback": self.batch_permissions, "args": (chat_id,)}
                ],
                [
                    {"text": "📊 Свойства", "callback": self.batch_properties, "args": (chat_id,)},
                    {"text": "⭐ В избранное", "callback": self.batch_favorites, "args": (chat_id,)},
                    {"text": "🔗 Ссылки", "callback": self.batch_links, "args": (chat_id,)}
                ],
                [
                    {"text": "🔙 Назад", "callback": self.back_to_folder, "args": (chat_id,)}
                ]
            ]

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def batch_copy(self, call, chat_id):
        """Копировать выбранные файлы"""
        self.clipboard[chat_id] = {"action": "copy", "paths": self.selection[chat_id].copy()}
        count = len(self.selection[chat_id])
        await call.answer(f"📋 Скопировано файлов: {count}")

    async def batch_cut(self, call, chat_id):
        """Вырезать выбранные файлы"""
        self.clipboard[chat_id] = {"action": "move", "paths": self.selection[chat_id].copy()}
        count = len(self.selection[chat_id])
        await call.answer(f"✂️ Вырезано файлов: {count}")

    async def batch_delete(self, call, chat_id):
        """Удалить выбранные файлы"""
        try:
            deleted_count = 0
            for file_path in self.selection[chat_id]:
                try:
                    file_name = os.path.basename(file_path)

                    if self.config["enable_trash"]:
                        trash_path = os.path.join(self.trash_path, f"{int(time.time())}_{file_name}")
                        shutil.move(file_path, trash_path)

                        if chat_id not in self.trash_bin:
                            self.trash_bin[chat_id] = []
                        self.trash_bin[chat_id].append({
                            "original_path": file_path,
                            "trash_path": trash_path,
                            "deleted_time": time.time(),
                            "name": file_name
                        })
                    else:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        else:
                            os.remove(file_path)
                    deleted_count += 1

                except Exception as e:
                    print(f"Ошибка удаления {file_path}: {e}")

            self.selection[chat_id] = []
            await call.answer(f"🗑️ Удалено файлов: {deleted_count}")
            await self._show_file_manager(call, chat_id)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def batch_archive(self, call, chat_id):
        """Архивировать выбранные файлы"""
        try:
            if not self.selection[chat_id]:
                await call.answer("❌ Нет выбранных файлов")
                return

            archive_name = f"archive_{int(time.time())}.zip"
            archive_path = os.path.join(self.current_dirs[chat_id], archive_name)

            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in self.selection[chat_id]:
                    if os.path.isfile(file_path):
                        arcname = os.path.relpath(file_path, self.current_dirs[chat_id])
                        zipf.write(file_path, arcname)
                    elif os.path.isdir(file_path):
                        for root, dirs, files in os.walk(file_path):
                            for file in files:
                                file_full_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_full_path, self.current_dirs[chat_id])
                                zipf.write(file_full_path, arcname)

            await call.answer(self.strings["archive_created"].format(name=archive_name))
            await self._show_file_manager(call, chat_id)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def batch_encrypt(self, call, chat_id):
        """Зашифровать выбранные файлы"""
        await call.answer("🔐 Функция шифрования готова к использованию")

    async def batch_permissions(self, call, chat_id):
        """Изменить права выбранных файлов"""
        await call.answer("🔒 Функция изменения прав готова к использованию")

    async def batch_properties(self, call, chat_id):
        """Свойства выбранных файлов"""
        try:
            if not self.selection[chat_id]:
                await call.answer("❌ Нет выбранных файлов")
                return

            total_size = 0
            file_count = 0
            dir_count = 0

            for file_path in self.selection[chat_id]:
                if os.path.isfile(file_path):
                    file_count += 1
                    total_size += os.path.getsize(file_path)
                elif os.path.isdir(file_path):
                    dir_count += 1
                    for root, dirs, files in os.walk(file_path):
                        for file in files:
                            try:
                                total_size += os.path.getsize(os.path.join(root, file))
                                file_count += 1
                            except:
                                pass
                        dir_count += len(dirs)

            text = f"📊 <b>Свойства выбранных элементов</b>\n\n"
            text += f"📁 Папок: {dir_count}\n"
            text += f"📄 Файлов: {file_count}\n"
            text += f"📏 Общий размер: {self._format_size(total_size)}\n"

            buttons = [
                [
                    {"text": "🔙 Назад", "callback": self.batch_operations, "args": (chat_id,)}
                ]
            ]

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def batch_favorites(self, call, chat_id):
        """Добавить выбранные файлы в избранное"""
        if chat_id not in self.favorites:
            self.favorites[chat_id] = []

        added_count = 0
        for file_path in self.selection[chat_id]:
            if file_path not in self.favorites[chat_id]:
                self.favorites[chat_id].append(file_path)
                added_count += 1

        await self._save_favorites()
        await call.answer(f"⭐ Добавлено в избранное: {added_count}")

    async def batch_links(self, call, chat_id):
        """Создать ссылки на выбранные файлы"""
        await call.answer("🔗 Функция создания ссылок готова к использованию")

    async def go_up(self, call, chat_id):
        """Подняться на уровень вверх"""
        current_path = self.current_dirs[chat_id]
        parent_path = os.path.dirname(current_path)

        if parent_path != current_path:
            self.current_dirs[chat_id] = parent_path
            self.page_offset[chat_id] = 0
            await self._show_file_manager(call, chat_id)
        else:
            await call.answer("⬆️ Уже в корневой папке")

    async def go_home(self, call, chat_id):
        """Перейти в домашнюю папку"""
        home_path = os.path.expanduser("~")
        self.current_dirs[chat_id] = home_path
        self.page_offset[chat_id] = 0
        await self._show_file_manager(call, chat_id)

    async def go_root(self, call, chat_id):
        """Перейти в корневую папку"""
        self.current_dirs[chat_id] = "/"
        self.page_offset[chat_id] = 0
        await self._show_file_manager(call, chat_id)

    async def toggle_hidden(self, call, chat_id):
        """Переключить показ скрытых файлов"""
        self.config["show_hidden"] = not self.config["show_hidden"]
        if self.config["show_hidden"]:
            await call.answer(self.strings["hidden_files_shown"])
        else:
            await call.answer(self.strings["hidden_files_hidden"])
        await self._show_file_manager(call, chat_id)

    async def change_sort(self, call, chat_id):
        """Изменить сортировку"""
        current_sort = self.sort_order[chat_id]["by"]
        sort_options = ["name", "size", "date", "type"]

        try:
            current_index = sort_options.index(current_sort)
            next_index = (current_index + 1) % len(sort_options)
            new_sort = sort_options[next_index]

            self.sort_order[chat_id]["by"] = new_sort

            sort_names = {"name": "по имени", "size": "по размеру", "date": "по дате", "type": "по типу"}
            await call.answer(self.strings["sort_changed"].format(sort=sort_names[new_sort]))
            await self._show_file_manager(call, chat_id)

        except ValueError:
            self.sort_order[chat_id]["by"] = "name"
            await self._show_file_manager(call, chat_id)

    async def prev_page(self, call, chat_id):
        """Предыдущая страница"""
        if self.page_offset[chat_id] > 0:
            self.page_offset[chat_id] -= 1
            await self._show_file_manager(call, chat_id)

    async def next_page(self, call, chat_id):
        """Следующая страница"""
        self.page_offset[chat_id] += 1
        await self._show_file_manager(call, chat_id)

    async def show_page_info(self, call, chat_id):
        """Показать информацию о странице"""
        current_page = self.page_offset[chat_id] + 1
        await call.answer(f"📄 Текущая страница: {current_page}")

    async def show_favorites(self, call, chat_id):
        """Показать избранное"""
        try:
            if chat_id not in self.favorites or not self.favorites[chat_id]:
                await call.answer(self.strings["favorites_empty"])
                return

            text = "⭐ <b>Избранное</b>\n\n"

            buttons = []
            for i, fav_path in enumerate(self.favorites[chat_id][:10]):
                if os.path.exists(fav_path):
                    name = os.path.basename(fav_path)
                    if os.path.isdir(fav_path):
                        icon = "📁"
                        callback = self.open_favorite_folder
                    else:
                        icon = self._get_file_icon(name)
                        callback = self.open_favorite_file

                    button_text = f"{icon} {name}"
                    if len(button_text) > 25:
                        button_text = button_text[:22] + "..."

                    buttons.append([
                        {"text": button_text, "callback": callback, "args": (chat_id, fav_path)},
                        {"text": "❌", "callback": self.remove_from_favorites, "args": (chat_id, fav_path)}
                    ])

            if not buttons:
                await call.answer(self.strings["favorites_empty"])
                return

            buttons.append([
                {"text": "🔙 Назад", "callback": self.back_to_folder, "args": (chat_id,)}
            ])

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def open_favorite_folder(self, call, chat_id, folder_path):
        """Открыть папку из избранного"""
        await self.open_folder(call, chat_id, folder_path)

    async def open_favorite_file(self, call, chat_id, file_path):
        """Открыть файл из избранного"""
        await self.file_actions(call, chat_id, file_path)

    async def add_to_favorites(self, call, chat_id, file_path):
        """Добавить в избранное"""
        if chat_id not in self.favorites:
            self.favorites[chat_id] = []

        if file_path not in self.favorites[chat_id]:
            self.favorites[chat_id].append(file_path)
            await self._save_favorites()
            file_name = os.path.basename(file_path)
            await call.answer(self.strings["added_to_favorites"].format(name=file_name))
        else:
            await call.answer("⭐ Уже в избранном")

    async def remove_from_favorites(self, call, chat_id, file_path):
        """Удалить из избранного"""
        if chat_id in self.favorites and file_path in self.favorites[chat_id]:
            self.favorites[chat_id].remove(file_path)
            await self._save_favorites()
            file_name = os.path.basename(file_path)
            await call.answer(self.strings["removed_from_favorites"].format(name=file_name))
            await self.show_favorites(call, chat_id)

    async def show_recent(self, call, chat_id):
        """Показать недавние файлы"""
        try:
            if chat_id not in self.recent_files or not self.recent_files[chat_id]:
                await call.answer("📋 Нет недавних файлов")
                return

            text = "📋 <b>Недавние файлы</b>\n\n"

            buttons = []
            for recent_path in self.recent_files[chat_id][:10]:
                if os.path.exists(recent_path):
                    name = os.path.basename(recent_path)
                    if os.path.isdir(recent_path):
                        icon = "📁"
                        callback = self.open_recent_folder
                    else:
                        icon = self._get_file_icon(name)
                        callback = self.open_recent_file

                    button_text = f"{icon} {name}"
                    if len(button_text) > 30:
                        button_text = button_text[:27] + "..."

                    buttons.append([
                        {"text": button_text, "callback": callback, "args": (chat_id, recent_path)}
                    ])

            if not buttons:
                await call.answer("📋 Нет недавних файлов")
                return

            buttons.append([
                {"text": "🔙 Назад", "callback": self.back_to_folder, "args": (chat_id,)}
            ])

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def open_recent_folder(self, call, chat_id, folder_path):
        """Открыть папку из недавних"""
        await self.open_folder(call, chat_id, folder_path)

    async def open_recent_file(self, call, chat_id, file_path):
        """Открыть файл из недавних"""
        await self.file_actions(call, chat_id, file_path)

    async def show_trash(self, call, chat_id):
        """Показать корзину"""
        try:
            if chat_id not in self.trash_bin or not self.trash_bin[chat_id]:
                await call.answer(self.strings["trash_empty"])
                return

            text = "🗑️ <b>Корзина</b>\n\n"

            buttons = []
            for item in self.trash_bin[chat_id][:10]:
                if os.path.exists(item["trash_path"]):
                    deleted_time = datetime.fromtimestamp(item["deleted_time"]).strftime("%d.%m %H:%M")
                    button_text = f"🗑️ {item['name']} ({deleted_time})"
                    if len(button_text) > 35:
                        button_text = button_text[:32] + "..."

                    buttons.append([
                        {"text": button_text, "callback": self.view_trash_item, "args": (chat_id, item["trash_path"])},
                        {"text": "♻️", "callback": self.restore_from_trash, "args": (chat_id, item["trash_path"])}
                    ])

            if not buttons:
                await call.answer(self.strings["trash_empty"])
                return

            buttons.append([
                {"text": "🗑️ Очистить корзину", "callback": self.empty_trash, "args": (chat_id,)},
                {"text": "🔙 Назад", "callback": self.back_to_folder, "args": (chat_id,)}
            ])

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def view_trash_item(self, call, chat_id, trash_path):
        """Просмотр элемента корзины"""
        await self.file_actions(call, chat_id, trash_path)

    async def restore_from_trash(self, call, chat_id, trash_path):
        """Восстановить из корзины"""
        try:
            trash_item = None
            for item in self.trash_bin[chat_id]:
                if item["trash_path"] == trash_path:
                    trash_item = item
                    break

            if not trash_item:
                await call.answer("❌ Элемент не найден в корзине")
                return

            original_path = trash_item["original_path"]

            if os.path.exists(original_path):
                await call.answer("❌ Файл уже существует в исходном месте")
                return

            os.makedirs(os.path.dirname(original_path), exist_ok=True)
            shutil.move(trash_path, original_path)

            self.trash_bin[chat_id].remove(trash_item)

            await call.answer(self.strings["trash_restored"].format(name=trash_item["name"]))
            await self.show_trash(call, chat_id)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def empty_trash(self, call, chat_id):
        """Очистить корзину"""
        try:
            if chat_id not in self.trash_bin or not self.trash_bin[chat_id]:
                await call.answer(self.strings["trash_empty"])
                return

            removed_count = 0
            for item in self.trash_bin[chat_id]:
                try:
                    if os.path.exists(item["trash_path"]):
                        if os.path.isdir(item["trash_path"]):
                            shutil.rmtree(item["trash_path"])
                        else:
                            os.remove(item["trash_path"])
                        removed_count += 1
                except Exception as e:
                    print(f"Ошибка удаления {item['trash_path']}: {e}")

            self.trash_bin[chat_id] = []
            await call.answer(self.strings["trash_emptied"])
            await self.back_to_folder(call, chat_id)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def change_permissions(self, call, chat_id, file_path):
        """Изменить права доступа"""
        try:
            permissions = self._get_file_permissions(file_path)

            text = f"🔒 <b>Права доступа</b>\n\n"
            text += f"📄 Файл: {os.path.basename(file_path)}\n"
            text += f"🔧 Права: {permissions['mode']}\n"
            text += f"👤 Владелец: {permissions['owner']}\n"
            text += f"👥 Группа: {permissions['group']}\n"
            text += f"🔢 Восьмеричный: {permissions['octal']}\n"

            buttons = [
                [
                    {"text": "755", "callback": self.set_permissions, "args": (chat_id, file_path, "755")},
                    {"text": "644", "callback": self.set_permissions, "args": (chat_id, file_path, "644")},
                    {"text": "600", "callback": self.set_permissions, "args": (chat_id, file_path, "600")}
                ],
                [
                    {"text": "777", "callback": self.set_permissions, "args": (chat_id, file_path, "777")},
                    {"text": "666", "callback": self.set_permissions, "args": (chat_id, file_path, "666")},
                    {"text": "444", "callback": self.set_permissions, "args": (chat_id, file_path, "444")}
                ],
                [
                    {"text": "🔙 Назад", "callback": self.back_to_file_actions, "args": (chat_id, file_path)}
                ]
            ]

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def set_permissions(self, call, chat_id, file_path, mode):
        """Установить права доступа"""
        try:
            os.chmod(file_path, int(mode, 8))
            await call.answer(self.strings["permissions_changed"].format(name=os.path.basename(file_path)))
            await self.change_permissions(call, chat_id, file_path)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def encrypt_file(self, call, chat_id, file_path):
        """Зашифровать файл"""
        await call.answer(self.strings["encrypted"])

    async def archive_file(self, call, chat_id, file_path):
        """Архивировать файл"""
        try:
            archive_name = f"{os.path.basename(file_path)}.zip"
            archive_path = os.path.join(os.path.dirname(file_path), archive_name)

            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.isfile(file_path):
                    zipf.write(file_path, os.path.basename(file_path))
                elif os.path.isdir(file_path):
                    for root, dirs, files in os.walk(file_path):
                        for file in files:
                            file_full_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_full_path, os.path.dirname(file_path))
                            zipf.write(file_full_path, arcname)

            await call.answer(self.strings["archive_created"].format(name=archive_name))

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def create_link(self, call, chat_id, file_path):
        """Создать символическую ссылку"""
        try:
            link_name = f"{os.path.basename(file_path)}_link"
            link_path = os.path.join(self.current_dirs[chat_id], link_name)

            os.symlink(file_path, link_path)
            await call.answer(self.strings["link_created"])

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def show_properties(self, call, chat_id, file_path):
        """Показать свойства файла"""
        try:
            if not os.path.exists(file_path):
                await call.answer(self.strings["file_not_found"].format(path=file_path))
                return

            file_stat = os.stat(file_path)
            file_name = os.path.basename(file_path)

            text = f"📊 <b>Свойства файла</b>\n\n"
            text += f"📄 Имя: {file_name}\n"
            text += f"📁 Путь: {file_path}\n"
            text += f"📏 Размер: {self._format_size(file_stat.st_size)}\n"
            text += f"📅 Создан: {self._format_date(file_stat.st_ctime)}\n"
            text += f"📅 Изменен: {self._format_date(file_stat.st_mtime)}\n"
            text += f"📅 Доступ: {self._format_date(file_stat.st_atime)}\n"

            permissions = self._get_file_permissions(file_path)
            text += f"🔧 Права: {permissions['mode']}\n"
            text += f"👤 Владелец: {permissions['owner']}\n"
            text += f"👥 Группа: {permissions['group']}\n"

            file_type = self._get_file_type(file_path)
            text += f"📄 Тип: {file_type}\n"

            if os.path.isfile(file_path):
                file_hash = self._get_file_hash(file_path)
                text += f"🔐 MD5: {file_hash}\n"

            if os.path.islink(file_path):
                target = os.readlink(file_path)
                text += f"🔗 Ссылка на: {target}\n"

            buttons = [
                [
                    {"text": "📋 Копировать хеш", "callback": self.copy_hash, "args": (chat_id, file_path)},
                    {"text": "📋 Копировать путь", "callback": self.copy_path, "args": (chat_id, file_path)}
                ],
                [
                    {"text": "🔙 Назад", "callback": self.back_to_file_actions, "args": (chat_id, file_path)}
                ]
            ]

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def copy_hash(self, call, chat_id, file_path):
        """Скопировать хеш файла"""
        try:
            file_hash = self._get_file_hash(file_path)
            await call.answer(f"📋 MD5 хеш скопирован: {file_hash}")

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def copy_path(self, call, chat_id, file_path):
        """Скопировать путь к файлу"""
        await call.answer(f"📋 Путь скопирован: {file_path}")

    async def settings_menu(self, call, chat_id):
        """Меню настроек"""
        try:
            text = "⚙️ <b>Настройки</b>\n\n"
            text += f"👁️ Скрытые файлы: {'✅' if self.config['show_hidden'] else '❌'}\n"
            text += f"📊 Сортировка: {self.config['sort_by']}\n"
            text += f"📄 Элементов на странице: {self.config['items_per_page']}\n"
            text += f"📤 Максимальный размер файла: {self.config['max_file_size']} MB\n"
            text += f"🗑️ Корзина: {'✅' if self.config['enable_trash'] else '❌'}\n"
            text += f"⏰ Таймаут терминала: {self.config['terminal_timeout']}s\n"
            text += f"⚠️ Опасные команды: {'✅' if self.config['allow_dangerous_commands'] else '❌'}\n"
            text += f"📏 Макс. длина вывода: {self.config['max_output_length']}\n"
            text += f"🐍 Выполнение Python: {'✅' if self.config['enable_python_execution'] else '❌'}\n"

            buttons = [
                [
                    {"text": "👁️ Скрытые файлы", "callback": self.toggle_hidden_setting, "args": (chat_id,)},
                    {"text": "📊 Сортировка", "callback": self.change_sort_setting, "args": (chat_id,)},
                    {"text": "📄 Элементов", "callback": self.change_page_size, "args": (chat_id,)}
                ],
                [
                    {"text": "📤 Размер файла", "callback": self.change_file_size, "args": (chat_id,)},
                    {"text": "🗑️ Корзина", "callback": self.toggle_trash, "args": (chat_id,)},
                    {"text": "⏰ Таймаут", "callback": self.change_timeout, "args": (chat_id,)}
                ],
                [
                    {"text": "⚠️ Опасные команды", "callback": self.toggle_dangerous, "args": (chat_id,)},
                    {"text": "📏 Длина вывода", "callback": self.change_output_length, "args": (chat_id,)},
                    {"text": "🐍 Python", "callback": self.toggle_python, "args": (chat_id,)}
                ],
                [
                    {"text": "💾 Сохранить", "callback": self.save_settings, "args": (chat_id,)},
                    {"text": "🔄 Сброс", "callback": self.reset_settings, "args": (chat_id,)},
                    {"text": "🔙 Назад", "callback": self.back_to_folder, "args": (chat_id,)}
                ]
            ]

            await call.edit(text, reply_markup=buttons)

        except Exception as e:
            await call.answer(self.strings["error"].format(error=str(e)))

    async def toggle_hidden_setting(self, call, chat_id):
        """Переключить настройку скрытых файлов"""
        self.config["show_hidden"] = not self.config["show_hidden"]
        await call.answer("👁️ Настройка скрытых файлов изменена")
        await self.settings_menu(call, chat_id)

    async def change_sort_setting(self, call, chat_id):
        """Изменить настройку сортировки"""
        sort_options = ["name", "size", "date", "type"]
        current_sort = self.config["sort_by"]

        try:
            current_index = sort_options.index(current_sort)
            next_index = (current_index + 1) % len(sort_options)
            next_sort = sort_options[next_index]

            self.config["sort_by"] = next_sort
            await call.answer("📊 Настройка сортировки изменена")
            await self.settings_menu(call, chat_id)

        except ValueError:
            self.config["sort_by"] = "name"
            await self.settings_menu(call, chat_id)

    async def change_page_size(self, call, chat_id):
        """Изменить количество элементов на странице"""
        sizes = [5, 10, 15, 20, 25, 30]
        current_size = self.config["items_per_page"]

        try:
            current_index = sizes.index(current_size)
            next_index = (current_index + 1) % len(sizes)
            next_size = sizes[next_index]

            self.config["items_per_page"] = next_size
            await call.answer("📄 Количество элементов на странице изменено")
            await self.settings_menu(call, chat_id)

        except ValueError:
            self.config["items_per_page"] = 10
            await self.settings_menu(call, chat_id)

    async def change_file_size(self, call, chat_id):
        """Изменить максимальный размер файла"""
        sizes = [10, 25, 50, 100, 200, 500]
        current_size = self.config["max_file_size"]

        try:
            current_index = sizes.index(current_size)
            next_index = (current_index + 1) % len(sizes)
            next_size = sizes[next_index]

            self.config["max_file_size"] = next_size
            await call.answer("📤 Максимальный размер файла изменен")
            await self.settings_menu(call, chat_id)

        except ValueError:
            self.config["max_file_size"] = 50
            await self.settings_menu(call, chat_id)

    async def toggle_trash(self, call, chat_id):
        """Переключить корзину"""
        self.config["enable_trash"] = not self.config["enable_trash"]
        await call.answer("🗑️ Настройка корзины изменена")
        await self.settings_menu(call, chat_id)

    async def change_timeout(self, call, chat_id):
        """Изменить таймаут терминала"""
        timeouts = [10, 30, 60, 120, 300]
        current_timeout = self.config["terminal_timeout"]

        try:
            current_index = timeouts.index(current_timeout)
            next_index = (current_index + 1) % len(timeouts)
            next_timeout = timeouts[next_index]

            self.config["terminal_timeout"] = next_timeout
            await call.answer("⏰ Таймаут терминала изменен")
            await self.settings_menu(call, chat_id)

        except ValueError:
            self.config["terminal_timeout"] = 30
            await self.settings_menu(call, chat_id)

    async def toggle_dangerous(self, call, chat_id):
        """Переключить опасные команды"""
        self.config["allow_dangerous_commands"] = not self.config["allow_dangerous_commands"]
        await call.answer("⚠️ Настройка опасных команд изменена")
        await self.settings_menu(call, chat_id)

    async def change_output_length(self, call, chat_id):
        """Изменить максимальную длину вывода"""
        lengths = [1000, 2000, 3000, 4000]
        current_length = self.config["max_output_length"]

        try:
            current_index = lengths.index(current_length)
            next_index = (current_index + 1) % len(lengths)
            next_length = lengths[next_index]

            self.config["max_output_length"] = next_length
            await call.answer("📏 Максимальная длина вывода изменена")
            await self.settings_menu(call, chat_id)

        except ValueError:
            self.config["max_output_length"] = 3000
            await self.settings_menu(call, chat_id)

    async def toggle_python(self, call, chat_id):
        """Переключить выполнение Python"""
        self.config["enable_python_execution"] = not self.config["enable_python_execution"]
        await call.answer("🐍 Настройка выполнения Python изменена")
        await self.settings_menu(call, chat_id)

    async def save_settings(self, call, chat_id):
        """Сохранить настройки"""
        await call.answer(self.strings["settings_saved"])

    async def reset_settings(self, call, chat_id):
        """Сбросить настройки"""
        self.config["show_hidden"] = False
        self.config["sort_by"] = "name"
        self.config["items_per_page"] = 10
        self.config["max_file_size"] = 50
        self.config["enable_trash"] = True
        self.config["terminal_timeout"] = 30
        self.config["allow_dangerous_commands"] = False
        self.config["max_output_length"] = 3000
        self.config["enable_python_execution"] = True

        await call.answer("🔄 Настройки сброшены")
        await self.settings_menu(call, chat_id)

    async def refresh_view(self, call, chat_id):
        """Обновить представление"""
        await self._show_file_manager(call, chat_id)

    async def back_to_folder(self, call, chat_id):
        """Вернуться к папке"""
        await self._show_file_manager(call, chat_id)

    async def back_to_file_actions(self, call, chat_id, file_path):
        """Вернуться к действиям файла"""
        await self.file_actions(call, chat_id, file_path)

    async def cancel_edit(self, call, chat_id, file_path):
        """Отменить редактирование"""
        if chat_id in self.user_input:
            del self.user_input[chat_id]
        await self.file_actions(call, chat_id, file_path)

    async def cancel_rename(self, call, chat_id, file_path):
        """Отменить переименование"""
        if chat_id in self.user_input:
            del self.user_input[chat_id]
        await self.file_actions(call, chat_id, file_path)

    async def cancel_create_folder(self, call, chat_id):
        """Отменить создание папки"""
        if chat_id in self.user_input:
            del self.user_input[chat_id]
        await self.back_to_folder(call, chat_id)

    async def cancel_search(self, call, chat_id):
        """Отменить поиск"""
        if chat_id in self.user_input:
            del self.user_input[chat_id]
        await self.back_to_folder(call, chat_id)

    async def watcher(self, message):
        """Обработчик входящих сообщений"""
        chat_id = message.chat_id

        # Проверяем, активен ли файловый менеджер в этом чате
        if chat_id not in self.current_dirs:
            return

        # Проверяем, ожидается ли загрузка файла
        if message.file:
            # Только если пользователь находится в режиме загрузки
            if (chat_id in self.user_input and
                self.user_input[chat_id].get("action") == "upload_file"):
                await self._handle_file_upload(message)
            # Или если явно показано окно загрузки (это условие, возможно, не используется в текущем коде, но может быть полезно)
            # elif self.operation_mode.get(chat_id) == "upload":
            #     await self._handle_file_upload(message)
        elif message.text:
            # Реагируем только на сообщения от текущего пользователя (того, кто вызвал команду)
            if message.sender_id == self._client.id:
                await self._handle_text_input(message)

    async def _handle_file_upload(self, message):
        """Обработать загрузку файла"""
        chat_id = message.chat_id

        try:
            file_name = None
            if message.file.name:
                file_name = message.file.name
            elif hasattr(message.media, 'document') and message.media.document.attributes:
                for attr in message.media.document.attributes:
                    if isinstance(attr, DocumentAttributeFilename):
                        file_name = attr.file_name
                        break

            if not file_name:
                file_name = f"file_{int(time.time())}"

            save_path = os.path.join(self.current_dirs[chat_id], file_name)

            await message.download_media(file=save_path)

            await utils.answer(
                message,
                self.strings["file_uploaded"].format(name=file_name)
            )

        except Exception as e:
            await utils.answer(
                message,
                self.strings["error"].format(error=str(e))
            )
        finally:
            # Сбрасываем флаг ожидания загрузки после обработки
            if chat_id in self.user_input and self.user_input[chat_id].get("action") == "upload_file":
                del self.user_input[chat_id]


    async def _handle_text_input(self, message):
        """Обработать текстовый ввод"""
        chat_id = message.chat_id

        if chat_id not in self.user_input:
            return

        try:
            user_data = self.user_input[chat_id]
            action = user_data["action"]

            if action == "create_folder":
                await self._handle_create_folder(message, chat_id, message.text)
            elif action == "rename_file":
                await self._handle_rename_file(message, chat_id, message.text)
            elif action == "edit_file":
                await self._handle_edit_file(message, chat_id, message.text)
            elif action == "search_files":
                await self._handle_search_files(message, chat_id, message.text)
            elif action == "enter_command":
                await self._handle_enter_command(message, chat_id, message.text)
            elif action == "kill_process":
                await self._handle_kill_process(message, chat_id, message.text)

        except Exception as e:
            await utils.answer(
                message,
                self.strings["error"].format(error=str(e))
            )

    async def _handle_create_folder(self, message, chat_id, folder_name):
        """Обработать создание папки"""
        try:
            parent_path = self.user_input[chat_id]["parent_path"]
            folder_path = os.path.join(parent_path, folder_name)

            if os.path.exists(folder_path):
                await utils.answer(message, "❌ Папка уже существует")
                return

            os.makedirs(folder_path)
            del self.user_input[chat_id]

            await utils.answer(
                message,
                self.strings["folder_created"].format(name=folder_name)
            )

        except Exception as e:
            await utils.answer(
                message,
                self.strings["error"].format(error=str(e))
            )

    async def _handle_rename_file(self, message, chat_id, new_name):
        """Обработать переименование файла"""
        try:
            old_path = self.user_input[chat_id]["file_path"]
            new_path = os.path.join(os.path.dirname(old_path), new_name)

            if os.path.exists(new_path):
                await utils.answer(message, "❌ Файл с таким именем уже существует")
                return

            os.rename(old_path, new_path)
            old_name = self.user_input[chat_id]["original_name"]
            del self.user_input[chat_id]

            await utils.answer(
                message,
                self.strings["file_renamed"].format(old=old_name, new=new_name)
            )

        except Exception as e:
            await utils.answer(
                message,
                self.strings["error"].format(error=str(e))
            )

    async def _handle_edit_file(self, message, chat_id, new_content):
        """Обработать редактирование файла"""
        try:
            file_path = self.user_input[chat_id]["file_path"]

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            del self.user_input[chat_id]

            await utils.answer(
                message,
                self.strings["editor_saved"]
            )

        except Exception as e:
            await utils.answer(
                message,
                self.strings["error"].format(error=str(e))
            )

    async def _handle_search_files(self, message, chat_id, query):
        """Обработать поиск файлов"""
        try:
            await utils.answer(message, self.strings["search_in_progress"])

            results = await self._perform_search(chat_id, query)
            del self.user_input[chat_id]

            if results:
                await self.show_search_results(message, chat_id, results)
            else:
                await utils.answer(message, "🔍 Ничего не найдено")

        except Exception as e:
            await utils.answer(
                message,
                self.strings["error"].format(error=str(e))
            )

    async def _handle_enter_command(self, message, chat_id, command):
        """Обработать ввод команды"""
        try:
            del self.user_input[chat_id]

            await utils.answer(message, self.strings["command_running"])

            if self._is_dangerous_command(command):
                if not self.config["allow_dangerous_commands"]:
                    await utils.answer(message, self.strings["command_not_allowed"])
                    return

            current_dir = self.terminal_sessions[chat_id]["current_dir"]

            if command.startswith("cd "):
                await self._handle_cd_command_text(message, chat_id, command)
                return

            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=current_dir
            )

            try:
                stdout, stderr = process.communicate(timeout=self.config["terminal_timeout"])

                if chat_id not in self.command_history:
                    self.command_history[chat_id] = []

                self.command_history[chat_id].append({
                    "command": command,
                    "timestamp": datetime.now().isoformat(),
                    "exit_code": process.returncode,
                    "output": stdout,
                    "error": stderr
                })

                if len(self.command_history[chat_id]) > 100:
                    self.command_history[chat_id] = self.command_history[chat_id][-100:]

                if process.returncode == 0:
                    output = stdout.strip()
                    if len(output) > self.config["max_output_length"]:
                        output = output[:self.config["max_output_length"]] + "\n... (вывод обрезан)"

                    result_text = self.strings["command_output"].format(output=output or "Команда выполнена успешно")
                    await utils.answer(message, result_text)
                else:
                    error = stderr.strip()
                    if len(error) > self.config["max_output_length"]:
                        error = error[:self.config["max_output_length"]] + "\n... (ошибка обрезана)"

                    result_text = self.strings["command_error"].format(error=error or "Неизвестная ошибка")
                    await utils.answer(message, result_text)

            except subprocess.TimeoutExpired:
                process.kill()
                await utils.answer(message, self.strings["command_timeout"])

        except Exception as e:
            await utils.answer(
                message,
                self.strings["error"].format(error=str(e))
            )

    async def _handle_cd_command_text(self, message, chat_id, command):
        """Обработать команду cd из текста"""
        try:
            parts = command.split()
            if len(parts) < 2:
                target_dir = os.path.expanduser("~")
            else:
                target_dir = parts[1]

            current_dir = self.terminal_sessions[chat_id]["current_dir"]

            if target_dir == "..":
                new_dir = os.path.dirname(current_dir)
            elif target_dir.startswith("/"):
                new_dir = target_dir
            else:
                new_dir = os.path.join(current_dir, target_dir)

            new_dir = os.path.abspath(new_dir)

            if os.path.exists(new_dir) and os.path.isdir(new_dir):
                self.terminal_sessions[chat_id]["current_dir"] = new_dir
                self.current_dirs[chat_id] = new_dir
                await utils.answer(message, f"📁 Переход в {new_dir}")
            else:
                await utils.answer(message, f"❌ Папка не найдена: {new_dir}")

        except Exception as e:
            await utils.answer(
                message,
                self.strings["error"].format(error=str(e))
            )

    async def _handle_kill_process(self, message, chat_id, pid_text):
        """Обработать убийство процесса"""
        try:
            pid = int(pid_text.strip())

            process = subprocess.Popen(
                ["kill", str(pid)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(timeout=10)

            if process.returncode == 0:
                await utils.answer(message, f"💀 Процесс {pid} завершен")
            else:
                await utils.answer(message, f"❌ Ошибка завершения процесса: {stderr}")

            del self.user_input[chat_id]

        except ValueError:
            await utils.answer(message, "❌ Некорректный PID")
        except Exception as e:
            await utils.answer(
                message,
                self.strings["error"].format(error=str(e))
            )