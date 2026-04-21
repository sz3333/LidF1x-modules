
__version__ = (1, 0, 0)

# meta developer: @ExclusiveFurry

import re
import os
import io
import json
import time
import uuid
import random
import socket
import base64
import asyncio
import logging
import tempfile
import aiohttp
from markdown_it import MarkdownIt
import pytz

from PIL import Image
from datetime import datetime
from telethon import types as tg_types
from telethon.tl.types import Message, DocumentAttributeFilename, DocumentAttributeSticker
from telethon.utils import get_display_name, get_peer_id
from telethon.errors.rpcerrorlist import (
    MessageTooLongError,
    ChatAdminRequiredError,
    UserNotParticipantError,
    ChannelPrivateError
)

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

DB_HISTORY_KEY = "grok_conversations_v1"
DB_GAUTO_HISTORY_KEY = "grok_gauto_conversations_v1"
DB_IMPERSONATION_KEY = "grok_impersonation_chats"
DB_PRESETS_KEY = "grok_prompt_presets"
GROK_TIMEOUT = 120
MAX_FFMPEG_SIZE = 90 * 1024 * 1024
GROK_API_BASE = "https://api.x.ai/v1"

# requires: aiohttp pytz markdown_it_py Pillow


class Grok(loader.Module):
    """Модуль для работы с Grok AI (xAI). Поддержка фото/файлов/аудио/видео."""

    strings = {
        "name": "Grok",
        "cfg_api_key_doc": "API ключ(и) xAI Grok, через запятую. Будут скрыты.",
        "cfg_model_name_doc": "Модель Grok (например: grok-3, grok-3-mini, grok-2-vision-1212).",
        "cfg_buttons_doc": "Включить интерактивные кнопки (очистить / перегенерировать).",
        "cfg_system_instruction_doc": "Системная инструкция (промпт) для Grok.",
        "cfg_max_history_length_doc": "Макс. кол-во пар 'вопрос-ответ' в памяти (0 - без лимита).",
        "cfg_timezone_doc": "Ваш часовой пояс. Список: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
        "cfg_proxy_doc": "Прокси. Формат: http://user:pass@host:port",
        "cfg_impersonation_prompt_doc": "Промпт для режима авто-ответа. {my_name} и {chat_history} будут заменены.",
        "cfg_impersonation_history_limit_doc": "Сколько последних сообщений из чата отправлять как контекст для авто-ответа.",
        "cfg_impersonation_reply_chance_doc": "Вероятность ответа в режиме gauto (от 0.0 до 1.0).",
        "cfg_temperature_doc": "Температура генерации (креативность). От 0.0 до 2.0.",
        "cfg_inline_pagination_doc": "Использовать инлайн-кнопки для длинных ответов.",
        "no_api_key": (
            '❗️ <b>API ключ(и) не настроен(ы).</b>\n'
            'Получить ключ можно на <a href="https://console.x.ai/">console.x.ai</a>.\n'
            '<b>Добавьте ключ в конфиге:</b> <code>.cfg Grok api_key</code>'
        ),
        "invalid_api_key": '❗️ <b>API ключ недействителен.</b>\nПроверьте ключ на <a href="https://console.x.ai/">console.x.ai</a>.',
        "all_keys_exhausted": "❗️ <b>Все API ключи ({}) исчерпали квоту.</b>\nПопробуйте позже или добавьте новые: <code>.cfg Grok api_key</code>",
        "no_prompt_or_media": "⚠️ <i>Нужен текст или ответ на медиа/файл.</i>",
        "processing": "<emoji document_id=5386367538735104399>⌛️</emoji> <b>Обработка...</b>",
        "api_error": "❗️ <b>Ошибка Grok API:</b>\n<code>{}</code>",
        "api_timeout": f"❗️ <b>Таймаут ответа от Grok API ({GROK_TIMEOUT} сек).</b>",
        "blocked_error": "🚫 <b>Запрос/ответ заблокирован.</b>\n<code>{}</code>",
        "generic_error": "❗️ <b>Ошибка:</b>\n<code>{}</code>",
        "question_prefix": "💬 <b>Запрос:</b>",
        "response_prefix": "<emoji document_id=5325547803936572038>✨</emoji> <b>Grok:</b>",
        "unsupported_media_type": "⚠️ <b>Формат медиа ({}) не поддерживается.</b>",
        "memory_status": "🧠 [{}/{}]",
        "memory_status_unlimited": "🧠 [{}/∞]",
        "memory_cleared": "🧹 <b>Память диалога очищена.</b>",
        "memory_cleared_gauto": "🧹 <b>Память gauto в этом чате очищена.</b>",
        "no_memory_to_clear": "ℹ️ <b>В этом чате нет истории.</b>",
        "no_gauto_memory_to_clear": "ℹ️ <b>В этом чате нет истории gauto.</b>",
        "memory_chats_title": "🧠 <b>Чаты с историей ({}):</b>",
        "memory_chat_line": "  • {} (<code>{}</code>)",
        "no_memory_found": "ℹ️ Память Grok пуста.",
        "media_reply_placeholder": "[ответ на медиа]",
        "btn_clear": "🧹 Очистить",
        "btn_regenerate": "🔄 Другой ответ",
        "no_last_request": "Последний запрос не найден для повторной генерации.",
        "memory_fully_cleared": "🧹 <b>Вся память Grok очищена (затронуто {} чатов).</b>",
        "gauto_memory_fully_cleared": "🧹 <b>Вся память gauto очищена (затронуто {} чатов).</b>",
        "no_memory_to_fully_clear": "ℹ️ <b>Память Grok и так пуста.</b>",
        "no_gauto_memory_to_fully_clear": "ℹ️ <b>Память gauto и так пуста.</b>",
        "response_too_long": "Ответ Grok был слишком длинным и отправлен файлом.",
        "auto_mode_on": "🎭 <b>Режим авто-ответа включен в этом чате.</b>\nВероятность ответа: {}%.",
        "auto_mode_off": "🎭 <b>Режим авто-ответа выключен в этом чате.</b>",
        "auto_mode_chats_title": "🎭 <b>Чаты с активным авто-ответом ({}):</b>",
        "no_auto_mode_chats": "ℹ️ Нет чатов с включённым режимом авто-ответа.",
        "auto_mode_usage": "ℹ️ <b>Использование:</b> <code>.gauto on/off</code> или <code>.gauto [id/username] [on/off]</code>",
        "gauto_chat_not_found": "🚫 <b>Не удалось найти чат:</b> <code>{}</code>",
        "gauto_state_updated": "🎭 <b>Режим авто-ответа для чата {} {}</b>",
        "gauto_enabled": "включен",
        "gauto_disabled": "выключен",
        "gch_usage": "ℹ️ <b>Использование:</b>\n<code>.gch <кол-во> <вопрос></code>\n<code>.gch <id чата> <кол-во> <вопрос></code>",
        "gch_processing": "<emoji document_id=5386367538735104399>⌛️</emoji> <b>Анализирую {} сообщений...</b>",
        "gch_result_caption": "Анализ последних {} сообщений",
        "gch_result_caption_from_chat": "Анализ последних {} сообщений из чата <b>{}</b>",
        "gch_chat_error": "❗️ <b>Ошибка доступа к чату</b> <code>{}</code>: <i>{}</i>",
        "gmodel_usage": "ℹ️ <b>Использование:</b> <code>.gkmodel [модель] [-s]</code>",
        "gmodel_list_title": "📋 <b>Доступные модели Grok:</b>",
        "gme_sent_to_saved": "💾 История экспортирована в избранное.",
        "gprompt_usage": "ℹ️ <b>Использование:</b>\n<code>.gkprompt <текст></code> — установить.\n<code>.gkprompt -c</code> — очистить.",
        "gprompt_updated": "✅ <b>Системный промпт обновлён!</b>\nДлина: {} символов.",
        "gprompt_cleared": "🗑 <b>Системный промпт очищен.</b>",
        "gprompt_current": "📝 <b>Текущий системный промпт:</b>",
        "gprompt_file_error": "❗️ <b>Ошибка чтения файла:</b> {}",
        "gprompt_file_too_big": "❗️ <b>Файл слишком большой</b> (лимит 1 МБ).",
        "gprompt_not_text": "❗️ Это не текстовый файл (только .txt).",
        "gmodel_no_models": "⚠️ Не удалось получить список моделей.",
        "gmodel_list_error": "❗️ Ошибка получения списка: {}",
        "gpreset_loaded": "✅ <b>Установлен пресет:</b> [<code>{}</code>]\nДлина: {} симв.",
        "gpreset_saved": "💾 <b>Пресет сохранён!</b>\n🏷 <b>Имя:</b> {}\n№ <b>Индекс:</b> {}",
        "gpreset_deleted": "🗑 <b>Пресет удалён:</b> {}",
        "gpreset_not_found": "🚫 Пресет не найден.",
        "gpreset_list_head": "📋 <b>Ваши пресеты:</b>\n",
        "gpreset_empty": "📂 Список пресетов пуст.",
        "gpresets_usage": (
            "ℹ️ <b>Управление пресетами:</b>\n"
            "• <code>.gkpresets save [Имя] текст</code> — сохранить.\n"
            "• <code>.gkpresets load 1</code> или <code>имя</code> — загрузить.\n"
            "• <code>.gkpresets del 1</code> или <code>имя</code> — удалить.\n"
            "• <code>.gkpresets list</code> — список."
        ),
    }

    TEXT_MIME_TYPES = {
        "text/plain", "text/markdown", "text/html", "text/css", "text/csv",
        "application/json", "application/xml", "application/x-python", "text/x-python",
        "application/javascript", "application/x-sh",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("api_key", "", self.strings["cfg_api_key_doc"], validator=loader.validators.Hidden()),
            loader.ConfigValue("model_name", "grok-3", self.strings["cfg_model_name_doc"]),
            loader.ConfigValue("interactive_buttons", True, self.strings["cfg_buttons_doc"], validator=loader.validators.Boolean()),
            loader.ConfigValue("system_instruction", "", self.strings["cfg_system_instruction_doc"], validator=loader.validators.String()),
            loader.ConfigValue("max_history_length", 50, self.strings["cfg_max_history_length_doc"], validator=loader.validators.Integer(minimum=0)),
            loader.ConfigValue("timezone", "Europe/Moscow", self.strings["cfg_timezone_doc"]),
            loader.ConfigValue("proxy", "", self.strings["cfg_proxy_doc"]),
            loader.ConfigValue(
                "impersonation_prompt",
                (
                    "Ты — это я, пользователь Telegram по имени {my_name}. Отвечай от моего имени, "
                    "на основе последних сообщений в чате. Веди себя как обычный человек, не как ИИ. "
                    "Не признавайся что ты — ИИ. Используй неформальный язык, отвечай кратко.\n\n"
                    "ИСТОРИЯ ЧАТА:\n{chat_history}\n\n{my_name}:"
                ),
                self.strings["cfg_impersonation_prompt_doc"],
                validator=loader.validators.String()
            ),
            loader.ConfigValue("impersonation_history_limit", 20, self.strings["cfg_impersonation_history_limit_doc"], validator=loader.validators.Integer(minimum=5, maximum=100)),
            loader.ConfigValue("impersonation_reply_chance", 0.25, self.strings["cfg_impersonation_reply_chance_doc"], validator=loader.validators.Float(minimum=0.0, maximum=1.0)),
            loader.ConfigValue("gauto_in_pm", False, "Разрешить авто-ответы в личных сообщениях.", validator=loader.validators.Boolean()),
            loader.ConfigValue("temperature", 1.0, self.strings["cfg_temperature_doc"], validator=loader.validators.Float(minimum=0.0, maximum=2.0)),
            loader.ConfigValue("inline_pagination", False, self.strings["cfg_inline_pagination_doc"], validator=loader.validators.Boolean()),
        )
        self.conversations = {}
        self.gauto_conversations = {}
        self.last_requests = {}
        self.impersonation_chats = set()
        self._lock = asyncio.Lock()
        self.memory_disabled_chats = set()
        self.pager_cache = {}
        self.api_keys = []
        self.prompt_presets = []

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.me = await client.get_me()
        api_key_str = self.config["api_key"]
        self.api_keys = [k.strip() for k in api_key_str.split(",") if k.strip()] if api_key_str else []
        self.conversations = self._load_history_from_db(DB_HISTORY_KEY)
        self.gauto_conversations = self._load_history_from_db(DB_GAUTO_HISTORY_KEY)
        self.impersonation_chats = set(self.db.get(self.strings["name"], DB_IMPERSONATION_KEY, []))
        self.prompt_presets = self.db.get(self.strings["name"], DB_PRESETS_KEY, [])
        if isinstance(self.prompt_presets, dict):
            self.prompt_presets = [{"name": k, "content": v} for k, v in self.prompt_presets.items()]
        if not self.api_keys:
            logger.warning("Grok: API ключи не настроены.")

    # ───────────────────────── Helpers ──────────────────────────

    def _get_proxy(self):
        p = self.config["proxy"]
        return p if p else None

    def _load_history_from_db(self, key):
        d = self.db.get(self.strings["name"], key, {})
        return d if isinstance(d, dict) else {}

    def _save_history_sync(self, gauto: bool = False):
        if getattr(self, "_db_broken", False):
            return
        data, key = (self.gauto_conversations, DB_GAUTO_HISTORY_KEY) if gauto else (self.conversations, DB_HISTORY_KEY)
        try:
            self.db.set(self.strings["name"], key, data)
        except Exception:
            self._db_broken = True

    def _get_structured_history(self, cid, gauto=False):
        d = self.gauto_conversations if gauto else self.conversations
        if str(cid) not in d:
            d[str(cid)] = []
        return d[str(cid)]

    def _clear_history(self, cid, gauto=False):
        d = self.gauto_conversations if gauto else self.conversations
        if str(cid) in d:
            del d[str(cid)]
            self._save_history_sync(gauto)

    def _update_history(self, chat_id, user_text: str, model_response: str, regeneration: bool = False, message: Message = None, gauto: bool = False):
        if not self._is_memory_enabled(str(chat_id)):
            return
        history = self._get_structured_history(chat_id, gauto)
        now = int(time.time())
        message_id = getattr(message, "id", None)
        if regeneration and history:
            for i in range(len(history) - 1, -1, -1):
                if history[i].get("role") == "assistant":
                    history[i].update({"content": model_response, "date": now})
                    break
        else:
            history.append({"role": "user", "content": user_text, "date": now, "message_id": message_id})
            history.append({"role": "assistant", "content": model_response, "date": now})
        limit = self.config["max_history_length"]
        if limit > 0 and len(history) > limit * 2:
            history = history[-(limit * 2):]
        target = self.gauto_conversations if gauto else self.conversations
        target[str(chat_id)] = history
        self._save_history_sync(gauto)

    def _is_memory_enabled(self, chat_id: str) -> bool:
        return chat_id not in self.memory_disabled_chats

    def _build_openai_messages(self, chat_id, sys_prompt: str, gauto=False) -> list:
        messages = []
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        history = self._get_structured_history(chat_id, gauto)
        try:
            user_tz = pytz.timezone(self.config["timezone"])
        except Exception:
            user_tz = pytz.utc
        for item in history:
            role = item.get("role", "user")
            content = item.get("content", "")
            if "date" in item and item["date"]:
                dt = datetime.fromtimestamp(item["date"], user_tz)
                content = f"[{dt.strftime('%d.%m.%Y %H:%M')}] {content}"
            messages.append({"role": role, "content": content})
        return messages

    async def _call_grok_api(self, messages: list, model: str = None, temperature: float = None) -> str:
        """Вызов Grok API (OpenAI-совместимый формат). Перебирает ключи при ошибках квоты."""
        api_key_str = self.config["api_key"]
        self.api_keys = [k.strip() for k in api_key_str.split(",") if k.strip()] if api_key_str else []
        if not self.api_keys:
            raise ValueError("no_api_key")
        model = model or self.config["model_name"]
        temperature = temperature if temperature is not None else self.config["temperature"]
        proxy = self._get_proxy()
        last_error = None
        for i, api_key in enumerate(self.api_keys):
            if i > 0:
                await asyncio.sleep(1)
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": min(float(temperature), 2.0),
            }
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{GROK_API_BASE}/chat/completions",
                        headers=headers,
                        json=payload,
                        proxy=proxy,
                        timeout=aiohttp.ClientTimeout(total=GROK_TIMEOUT),
                    ) as resp:
                        text = await resp.text()
                        if resp.status == 200:
                            data = json.loads(text)
                            return data["choices"][0]["message"]["content"]
                        elif resp.status in (429, 503):
                            last_error = f"HTTP {resp.status}"
                            continue
                        elif resp.status == 401:
                            raise ValueError("invalid_api_key")
                        else:
                            try:
                                err_data = json.loads(text)
                                msg = err_data.get("error", {}).get("message", text)
                            except Exception:
                                msg = text
                            raise ConnectionError(f"Grok API Error {resp.status}: {msg}")
            except (ValueError, ConnectionError):
                raise
            except Exception as e:
                last_error = str(e)
                continue
        raise RuntimeError(f"all_keys_exhausted|{len(self.api_keys)}")

    async def _prepare_content(self, message: Message, custom_text: str = None):
        """Возвращает (user_text, image_b64, mime_type, warnings)."""
        user_args = custom_text if custom_text is not None else utils.get_args_raw(message)
        reply = await message.get_reply_message()
        prompt_chunks = []
        warnings = []
        image_data = None
        image_mime = None

        if reply and getattr(reply, "text", None):
            try:
                reply_sender = await reply.get_sender()
                reply_author = get_display_name(reply_sender) if reply_sender else "Unknown"
                prompt_chunks.append(f"{reply_author}: {reply.text}")
            except Exception:
                prompt_chunks.append(f"Ответ на: {reply.text}")

        try:
            current_sender = await message.get_sender()
            current_name = get_display_name(current_sender) if current_sender else "User"
            prompt_chunks.append(f"{current_name}: {user_args or ''}")
        except Exception:
            prompt_chunks.append(f"Запрос: {user_args or ''}")

        media_source = message if (message.media or message.sticker) else reply
        has_media = bool(media_source and (media_source.media or media_source.sticker))

        if has_media:
            if media_source.sticker and hasattr(media_source.sticker, "mime_type") and media_source.sticker.mime_type == "application/x-tgsticker":
                alt = next((a.alt for a in media_source.sticker.attributes if isinstance(a, DocumentAttributeSticker)), "?")
                prompt_chunks.append(f"[Анимированный стикер: {alt}]")
            else:
                mime_type = "application/octet-stream"
                filename = "file"
                if media_source.photo:
                    mime_type = "image/jpeg"
                elif hasattr(media_source, "document") and media_source.document:
                    mime_type = getattr(media_source.document, "mime_type", mime_type)
                    doc_attr = next((a for a in media_source.document.attributes if isinstance(a, DocumentAttributeFilename)), None)
                    if doc_attr:
                        filename = doc_attr.file_name

                async def get_bytes(m):
                    bio = io.BytesIO()
                    await self.client.download_media(m, bio)
                    return bio.getvalue()

                if mime_type.startswith("image/"):
                    try:
                        data = await get_bytes(media_source.media or media_source)
                        image_data = base64.b64encode(data).decode("utf-8")
                        image_mime = mime_type
                    except Exception as e:
                        warnings.append(f"⚠️ Ошибка обработки изображения: {e}")

                elif mime_type in self.TEXT_MIME_TYPES or filename.split(".")[-1] in ("txt", "py", "js", "json", "md", "html", "css", "sh"):
                    try:
                        data = await get_bytes(media_source.media or media_source)
                        file_content = data.decode("utf-8")
                        prompt_chunks.insert(0, f"[Содержимое файла '{filename}']:\n```\n{file_content}\n```")
                    except Exception as e:
                        warnings.append(f"⚠️ Ошибка чтения файла '{filename}': {e}")

                elif mime_type.startswith("audio/"):
                    input_path, output_path = None, None
                    try:
                        with tempfile.NamedTemporaryFile(suffix=f".{filename.split('.')[-1]}", delete=False) as tf:
                            input_path = tf.name
                        await self.client.download_media(media_source.media or media_source, input_path)
                        if os.path.getsize(input_path) > MAX_FFMPEG_SIZE:
                            warnings.append(f"⚠️ Аудио '{filename}' слишком большое.")
                        else:
                            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
                                output_path = tf.name
                            proc = await asyncio.create_subprocess_exec(
                                "ffmpeg", "-y", "-i", input_path, "-c:a", "libmp3lame", "-q:a", "2", output_path,
                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                            )
                            await proc.communicate()
                            with open(output_path, "rb") as f:
                                audio_b64 = base64.b64encode(f.read()).decode("utf-8")
                            prompt_chunks.append(f"[Аудиофайл '{filename}' прикреплён. Расшифруй/опиши содержимое, если возможно.]")
                            # Grok не поддерживает аудио inline, сообщаем пользователю
                            warnings.append("ℹ️ Grok не поддерживает прямую обработку аудио. Отправлен текстовый контекст.")
                    except Exception as e:
                        warnings.append(f"⚠️ Ошибка обработки аудио: {e}")
                    finally:
                        for p in [input_path, output_path]:
                            if p and os.path.exists(p):
                                os.remove(p)

                elif mime_type.startswith("video/"):
                    warnings.append("ℹ️ Grok не поддерживает прямую обработку видео. Используйте текстовый запрос.")
                    prompt_chunks.append(f"[Видеофайл '{filename}' был прикреплён, но Grok не может его обработать.]")

        if not user_args and has_media and not image_data:
            prompt_chunks.append(self.strings["media_reply_placeholder"])

        full_text = "\n".join(c for c in prompt_chunks if c and c.strip()).strip()
        return full_text, image_data, image_mime, warnings

    async def _send_to_grok(self, message: Message, user_text: str, image_data=None, image_mime=None,
                             regeneration: bool = False, call: InlineCall = None, status_msg=None,
                             chat_id_override: int = None, impersonation_mode: bool = False,
                             display_prompt: str = None):
        if regeneration:
            chat_id = chat_id_override
            base_message_id = message
            try:
                msg_obj = await self.client.get_messages(chat_id, ids=base_message_id)
            except Exception:
                msg_obj = None
        else:
            chat_id = utils.get_chat_id(message)
            base_message_id = message.id
            msg_obj = message

        if not self.api_keys:
            if not impersonation_mode and status_msg:
                await utils.answer(status_msg, self.strings["no_api_key"])
            return None

        if regeneration:
            cached = self.last_requests.get(f"{chat_id}:{base_message_id}")
            if cached:
                user_text, display_prompt = cached
        else:
            req_display = display_prompt or user_text or self.strings["media_reply_placeholder"]
            self.last_requests[f"{chat_id}:{base_message_id}"] = (user_text, req_display)
            display_prompt = req_display

        try:
            user_tz = pytz.timezone(self.config["timezone"])
        except Exception:
            user_tz = pytz.utc
        now = datetime.now(user_tz)
        time_note = f"[System Info: Current local time is {now.strftime('%Y-%m-%d %H:%M:%S %Z')}]"

        if impersonation_mode:
            my_name = get_display_name(self.me)
            chat_history_text = await self._get_recent_chat_text(chat_id)
            sys_instruct = self.config["impersonation_prompt"].format(my_name=my_name, chat_history=chat_history_text)
        else:
            sys_val = self.config["system_instruction"]
            sys_instruct = (sys_val.strip() if isinstance(sys_val, str) else "") or None

        messages = self._build_openai_messages(chat_id, sys_instruct, gauto=impersonation_mode)

        if regeneration and len(messages) >= 2:
            # Remove last assistant turn for regen
            while messages and messages[-1].get("role") == "assistant":
                messages.pop()
            if messages and messages[-1].get("role") == "user":
                messages.pop()

        # Build user message content
        if image_data and image_mime:
            user_content = [
                {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{image_data}"}},
                {"type": "text", "text": f"{time_note}\n\n{user_text}" if not impersonation_mode else user_text},
            ]
        else:
            user_content = f"{time_note}\n\n{user_text}" if not impersonation_mode else user_text

        messages.append({"role": "user", "content": user_content})

        result_text = ""
        try:
            result_text = await self._call_grok_api(messages)
            result_text = result_text.strip()
            result_text = re.sub(r"^\[System Info:.*?\]\s*", "", result_text, flags=re.IGNORECASE)
            result_text = re.sub(r"^\[\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}\]\s*(?:Grok:|Model:|Ассистент:|AI:)?\s*", "", result_text, flags=re.IGNORECASE)

            if self._is_memory_enabled(str(chat_id)):
                self._update_history(chat_id, user_text, result_text, regeneration, msg_obj, gauto=impersonation_mode)

            if impersonation_mode:
                return result_text

            hist_len = len(self._get_structured_history(chat_id)) // 2
            if self.config["max_history_length"] <= 0:
                mem_ind = self.strings["memory_status_unlimited"].format(hist_len)
            else:
                mem_ind = self.strings["memory_status"].format(hist_len, self.config["max_history_length"])

            response_html = self._markdown_to_html(result_text)
            formatted_body = self._format_response_with_smart_separation(response_html)
            question_html = f"<blockquote>{utils.escape_html((display_prompt or '')[:200])}</blockquote>"
            text_to_send = f"{mem_ind}\n\n{self.strings['question_prefix']}\n{question_html}\n\n{self.strings['response_prefix']}\n{formatted_body}"
            buttons = self._get_inline_buttons(chat_id, base_message_id) if self.config["interactive_buttons"] else None

            is_long = len(result_text) > 3500
            if is_long and self.config["inline_pagination"]:
                chunks = self._paginate_text(result_text, 3000)
                uid = uuid.uuid4().hex[:6]
                header = (
                    f"{mem_ind}\n\n{self.strings['question_prefix']} "
                    f"<blockquote>{utils.escape_html((display_prompt or '')[:100])}...</blockquote>\n\n"
                    f"{self.strings['response_prefix']}\n"
                )
                self.pager_cache[uid] = {"chunks": chunks, "total": len(chunks), "header": header, "chat_id": chat_id, "msg_id": base_message_id}
                await self._render_page(uid, 0, call or status_msg)
            elif len(text_to_send) > 4096:
                file_content = f"Вопрос: {display_prompt}\n\n════════════════════\n\nОтвет Grok:\n{result_text}"
                file = io.BytesIO(file_content.encode("utf-8"))
                file.name = "Grok_response.txt"
                if call:
                    await call.answer("Ответ длинный, отправляю файлом...", show_alert=False)
                    await self.client.send_file(call.chat_id, file, caption=self.strings["response_too_long"], reply_to=call.message_id)
                elif status_msg:
                    await status_msg.delete()
                    await self.client.send_file(chat_id, file, caption=self.strings["response_too_long"], reply_to=base_message_id)
            else:
                if call:
                    await call.edit(text_to_send, reply_markup=buttons)
                elif status_msg:
                    await utils.answer(status_msg, text_to_send, reply_markup=buttons)

        except Exception as e:
            error_text = self._handle_error(e)
            if impersonation_mode:
                logger.error(f"Gauto Grok error: {error_text}")
            elif call:
                await call.edit(error_text, reply_markup=None)
            elif status_msg:
                await utils.answer(status_msg, error_text)

        return None if impersonation_mode else ""

    # ───────────────────────── Commands ─────────────────────────

    @loader.command()
    async def gk(self, message: Message):
        """[текст или reply] — спросить у Grok."""
        clean_args = utils.get_args_raw(message)
        status_msg = await utils.answer(message, self.strings["processing"])
        status_msg = await self.client.get_messages(status_msg.chat_id, ids=status_msg.id)
        user_text, img_data, img_mime, warnings = await self._prepare_content(message, custom_text=clean_args)
        if warnings:
            try:
                await status_msg.edit(f"{status_msg.text}\n\n" + "\n".join(warnings))
            except Exception:
                pass
        if not user_text and not img_data:
            return await utils.answer(status_msg, self.strings["no_prompt_or_media"])
        await self._send_to_grok(
            message=message,
            user_text=user_text,
            image_data=img_data,
            image_mime=img_mime,
            status_msg=status_msg,
            display_prompt=clean_args or None,
        )

    @loader.command()
    async def gkclear(self, message: Message):
        """[auto] — Очистить память текущего чата. auto — память gauto."""
        gauto = "auto" in utils.get_args_raw(message)
        cid = utils.get_chat_id(message)
        hist = self._get_structured_history(cid, gauto=gauto)
        if not hist:
            key = "no_gauto_memory_to_clear" if gauto else "no_memory_to_clear"
            return await utils.answer(message, self.strings[key])
        self._clear_history(cid, gauto=gauto)
        key = "memory_cleared_gauto" if gauto else "memory_cleared"
        await utils.answer(message, self.strings[key])

    @loader.command()
    async def gkres(self, message: Message):
        """[auto] — Очистить ВСЮ память. auto — только gauto."""
        if "auto" in utils.get_args_raw(message):
            if not self.gauto_conversations:
                return await utils.answer(message, self.strings["no_gauto_memory_to_fully_clear"])
            n = len(self.gauto_conversations)
            self.gauto_conversations.clear()
            self._save_history_sync(True)
            await utils.answer(message, self.strings["gauto_memory_fully_cleared"].format(n))
        else:
            if not self.conversations:
                return await utils.answer(message, self.strings["no_memory_to_fully_clear"])
            n = len(self.conversations)
            self.conversations.clear()
            self._save_history_sync(False)
            await utils.answer(message, self.strings["memory_fully_cleared"].format(n))

    @loader.command()
    async def gkmodel(self, message: Message):
        """[модель] [-s] — Узнать/сменить модель. -s — список доступных."""
        args_raw = utils.get_args_raw(message).strip()
        args_list = args_raw.split()
        is_list = "-s" in [a.lower() for a in args_list]

        if is_list:
            status_msg = await utils.answer(message, self.strings["processing"])
            try:
                api_key_str = self.config["api_key"]
                keys = [k.strip() for k in api_key_str.split(",") if k.strip()] if api_key_str else []
                if not keys:
                    return await utils.answer(status_msg, self.strings["no_api_key"])
                proxy = self._get_proxy()
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{GROK_API_BASE}/models",
                        headers={"Authorization": f"Bearer {keys[0]}"},
                        proxy=proxy,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        if resp.status != 200:
                            raise ValueError(f"HTTP {resp.status}")
                        data = await resp.json()
                models = data.get("data", [])
                txt = "\n".join(f"• <code>{m['id']}</code>" for m in models)
                f = io.BytesIO((self.strings["gmodel_list_title"] + "\n" + txt).encode("utf-8"))
                f.name = "grok_models.txt"
                await self.client.send_file(message.chat_id, file=f, caption="📋 Доступные модели Grok", reply_to=message.id)
                await status_msg.delete()
            except Exception as e:
                await utils.answer(status_msg, self.strings["gmodel_list_error"].format(utils.escape_html(str(e))))
            return

        if not args_raw or args_raw == "-s":
            return await utils.answer(message, f"🤖 <b>Текущая модель:</b> <code>{self.config['model_name']}</code>")
        model_name = args_raw.replace("-s", "").strip()
        if model_name:
            self.config["model_name"] = model_name
            await utils.answer(message, f"✅ Модель установлена: <code>{model_name}</code>")

    @loader.command()
    async def gkprompt(self, message: Message):
        """<текст/-c/reply на .txt> — Установить системный промпт."""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        if args == "-c":
            self.config["system_instruction"] = ""
            return await utils.answer(message, self.strings["gprompt_cleared"])
        new_prompt = None
        preset = self._find_preset(args)
        if preset:
            new_prompt = preset["content"]
        elif reply and reply.file:
            if reply.file.size > 1024 * 1024:
                return await utils.answer(message, self.strings["gprompt_file_too_big"])
            try:
                file_data = await self.client.download_file(reply.media, bytes)
                try:
                    new_prompt = file_data.decode("utf-8")
                except UnicodeDecodeError:
                    return await utils.answer(message, self.strings["gprompt_not_text"])
            except Exception as e:
                return await utils.answer(message, self.strings["gprompt_file_error"].format(e))
        elif args:
            new_prompt = args
        if new_prompt is None:
            current = self.config["system_instruction"]
            if current:
                return await utils.answer(message, f"{self.strings['gprompt_current']}\n<code>{utils.escape_html(current[:1000])}</code>")
            return await utils.answer(message, self.strings["gprompt_usage"])
        self.config["system_instruction"] = new_prompt
        await utils.answer(message, self.strings["gprompt_updated"].format(len(new_prompt)))

    @loader.command()
    async def gkpresets(self, message: Message):
        """save/load/del/list — Управление пресетами промптов."""
        args = utils.get_args_raw(message).strip()
        if not args:
            return await utils.answer(message, self.strings["gpresets_usage"])
        parts = args.split(None, 1)
        action = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

        if action == "list":
            if not self.prompt_presets:
                return await utils.answer(message, self.strings["gpreset_empty"])
            lines = [self.strings["gpreset_list_head"]]
            for i, p in enumerate(self.prompt_presets, 1):
                lines.append(f"{i}. <b>{utils.escape_html(p['name'])}</b> ({len(p['content'])} симв.)")
            return await utils.answer(message, "\n".join(lines))

        if action == "save":
            name_match = re.match(r"^\[(.+?)\]\s*(.*)", rest, re.DOTALL)
            if name_match:
                name, content = name_match.group(1).strip(), name_match.group(2).strip()
            else:
                p2 = rest.split(None, 1)
                name = p2[0] if p2 else "Без имени"
                content = p2[1] if len(p2) > 1 else ""
            if not content:
                return await utils.answer(message, "❗️ Укажите текст пресета.")
            existing = self._find_preset(name)
            if existing:
                existing["content"] = content
            else:
                self.prompt_presets.append({"name": name, "content": content})
            self.db.set(self.strings["name"], DB_PRESETS_KEY, self.prompt_presets)
            await utils.answer(message, self.strings["gpreset_saved"].format(name, len(self.prompt_presets)))

        elif action == "load":
            target = self._find_preset(rest.strip())
            if not target:
                return await utils.answer(message, self.strings["gpreset_not_found"])
            self.config["system_instruction"] = target["content"]
            await utils.answer(message, self.strings["gpreset_loaded"].format(target["name"], len(target["content"])))

        elif action == "del":
            target = self._find_preset(rest.strip())
            if not target:
                return await utils.answer(message, self.strings["gpreset_not_found"])
            self.prompt_presets.remove(target)
            self.db.set(self.strings["name"], DB_PRESETS_KEY, self.prompt_presets)
            await utils.answer(message, self.strings["gpreset_deleted"].format(target["name"]))
        else:
            await utils.answer(message, self.strings["gpresets_usage"])

    @loader.command()
    async def gkauto(self, message: Message):
        """on/off [id/username] — Включить/выключить режим авто-ответа."""
        args = utils.get_args_raw(message).split()
        if not args:
            chats = list(self.impersonation_chats)
            if not chats:
                return await utils.answer(message, self.strings["no_auto_mode_chats"])
            lines = [self.strings["auto_mode_chats_title"].format(len(chats))]
            for cid in chats:
                try:
                    e = await self.client.get_entity(int(cid))
                    name = get_display_name(e)
                except Exception:
                    name = f"Unknown ({cid})"
                lines.append(f"  • {name} (<code>{cid}</code>)")
            return await utils.answer(message, "\n".join(lines))

        if len(args) == 1:
            action = args[0].lower()
            target_id = str(utils.get_chat_id(message))
        elif len(args) == 2:
            try:
                entity = await self.client.get_entity(int(args[0]) if args[0].lstrip("-").isdigit() else args[0])
                target_id = str(entity.id)
            except Exception:
                return await utils.answer(message, self.strings["gauto_chat_not_found"].format(args[0]))
            action = args[1].lower()
        else:
            return await utils.answer(message, self.strings["auto_mode_usage"])

        if action == "on":
            self.impersonation_chats.add(target_id)
            self.db.set(self.strings["name"], DB_IMPERSONATION_KEY, list(self.impersonation_chats))
            chance = int(self.config["impersonation_reply_chance"] * 100)
            await utils.answer(message, self.strings["auto_mode_on"].format(chance))
        elif action == "off":
            self.impersonation_chats.discard(target_id)
            self.db.set(self.strings["name"], DB_IMPERSONATION_KEY, list(self.impersonation_chats))
            await utils.answer(message, self.strings["auto_mode_off"])
        else:
            await utils.answer(message, self.strings["auto_mode_usage"])

    @loader.command()
    async def gkch(self, message: Message):
        """<[id чата]> <кол-во> <вопрос> — Проанализировать историю чата."""
        args_str = utils.get_args_raw(message)
        if not args_str:
            return await utils.answer(message, self.strings["gch_usage"])
        parts = args_str.split()
        target_chat_id = utils.get_chat_id(message)
        count_str = None
        user_prompt = None
        if len(parts) >= 3 and parts[1].isdigit():
            try:
                entity = await self.client.get_entity(int(parts[0]) if parts[0].lstrip("-").isdigit() else parts[0])
                target_chat_id = entity.id
                count_str = parts[1]
                user_prompt = " ".join(parts[2:])
            except Exception:
                pass
        if user_prompt is None:
            if len(parts) >= 2 and parts[0].isdigit():
                count_str = parts[0]
                user_prompt = " ".join(parts[1:])
            else:
                return await utils.answer(message, self.strings["gch_usage"])
        try:
            count = int(count_str)
        except Exception:
            return await utils.answer(message, "❗️ Кол-во должно быть числом.")
        status_msg = await utils.answer(message, self.strings["gch_processing"].format(count))
        try:
            entity = await self.client.get_entity(target_chat_id)
            chat_name = utils.escape_html(get_display_name(entity))
            chat_log = await self._get_recent_chat_text(target_chat_id, count=count, skip_last=False)
        except (ValueError, TypeError, ChatAdminRequiredError, UserNotParticipantError, ChannelPrivateError) as e:
            return await utils.answer(status_msg, self.strings["gch_chat_error"].format(target_chat_id, e.__class__.__name__))
        except Exception as e:
            return await utils.answer(status_msg, self.strings["gch_chat_error"].format(target_chat_id, e))

        full_prompt = (
            f"Проанализируй историю чата и ответь на вопрос пользователя. "
            f"Отвечай только на основе предоставленной истории.\n\n"
            f"ВОПРОС: \"{user_prompt}\"\n\nИСТОРИЯ ЧАТА:\n---\n{chat_log}\n---"
        )
        try:
            messages = [{"role": "user", "content": full_prompt}]
            response_text = await self._call_grok_api(messages)
            header = self.strings["gch_result_caption_from_chat"].format(count, chat_name)
            resp_html = self._markdown_to_html(response_text)
            text = (
                f"<b>{header}</b>\n\n"
                f"{self.strings['question_prefix']}\n<blockquote expandable>{utils.escape_html(user_prompt)}</blockquote>\n\n"
                f"{self.strings['response_prefix']}\n{self._format_response_with_smart_separation(resp_html)}"
            )
            if len(text) > 4096:
                f = io.BytesIO(response_text.encode("utf-8"))
                f.name = "analysis.txt"
                await status_msg.delete()
                await message.reply(file=f, caption=f"📝 {header}")
            else:
                await utils.answer(status_msg, text)
        except Exception as e:
            await utils.answer(status_msg, self._handle_error(e))

    @loader.command()
    async def gkmemshow(self, message: Message):
        """[auto] — Показать память чата. auto — gauto."""
        gauto = "auto" in utils.get_args_raw(message)
        cid = utils.get_chat_id(message)
        hist = self._get_structured_history(cid, gauto=gauto)
        if not hist:
            return await utils.answer(message, "Память пуста.")
        out = []
        for e in hist[-40:]:
            role = e.get("role")
            content = utils.escape_html(str(e.get("content", ""))[:300])
            if role == "user":
                out.append(content)
            elif role == "assistant":
                out.append(f"<b>Grok:</b> {content}")
        await utils.answer(message, "<blockquote expandable='true'>" + "\n".join(out) + "</blockquote>")

    @loader.command()
    async def gkmemchats(self, message: Message):
        """— Показать чаты с активной памятью."""
        if not self.conversations:
            return await utils.answer(message, self.strings["no_memory_found"])
        out = [self.strings["memory_chats_title"].format(len(self.conversations))]
        for cid in list(self.conversations.keys()):
            if not str(cid).lstrip("-").isdigit():
                continue
            try:
                e = await self.client.get_entity(int(cid))
                name = get_display_name(e)
            except Exception:
                name = f"Unknown ({cid})"
            out.append(self.strings["memory_chat_line"].format(name, cid))
        if len(out) == 1:
            return await utils.answer(message, self.strings["no_memory_found"])
        await utils.answer(message, "\n".join(out))

    @loader.command()
    async def gkmemoff(self, message: Message):
        """— Отключить память в этом чате."""
        self.memory_disabled_chats.add(str(utils.get_chat_id(message)))
        await utils.answer(message, "Память в этом чате отключена.")

    @loader.command()
    async def gkmemon(self, message: Message):
        """— Включить память в этом чате."""
        self.memory_disabled_chats.discard(str(utils.get_chat_id(message)))
        await utils.answer(message, "Память в этом чате включена.")

    @loader.command()
    async def gkmemdel(self, message: Message):
        """[N] — Удалить последние N пар сообщений из памяти."""
        try:
            n = int(utils.get_args_raw(message) or 1)
        except Exception:
            n = 1
        cid = utils.get_chat_id(message)
        hist = self._get_structured_history(cid)
        if n > 0 and len(hist) >= n * 2:
            self.conversations[str(cid)] = hist[: -n * 2]
            self._save_history_sync()
            await utils.answer(message, f"🧹 Удалено последних <b>{n}</b> пар сообщений.")
        else:
            await utils.answer(message, "Недостаточно истории для удаления.")

    @loader.command()
    async def gkmemfind(self, message: Message):
        """[слово] — Поиск в памяти текущего чата."""
        q = utils.get_args_raw(message).lower()
        if not q:
            return await utils.answer(message, "Укажите слово для поиска.")
        cid = utils.get_chat_id(message)
        hist = self._get_structured_history(cid)
        found = [f"{e['role']}: {e.get('content', '')[:200]}" for e in hist if q in str(e.get("content", "")).lower()]
        if not found:
            await utils.answer(message, "Ничего не найдено.")
        else:
            await utils.answer(message, "\n\n".join(found[:10]))

    @loader.command()
    async def gkmemexport(self, message: Message):
        """[auto] [-s] — Экспорт памяти. -s — в избранное."""
        args = utils.get_args_raw(message).split()
        save_to_self = "-s" in args
        if save_to_self:
            args.remove("-s")
        gauto = "auto" in args
        if gauto:
            args.remove("auto")
        cid = utils.get_chat_id(message)
        hist = self._get_structured_history(cid, gauto=gauto)
        if not hist:
            return await utils.answer(message, "История для экспорта пуста.")
        data = json.dumps(hist, ensure_ascii=False, indent=2)
        f = io.BytesIO(data.encode("utf-8"))
        f.name = f"grok_{'gauto_' if gauto else ''}{cid}.json"
        dest = "me" if save_to_self else message.chat_id
        cap = "Экспорт истории gauto Grok" if gauto else "Экспорт памяти Grok"
        await self.client.send_file(dest, f, caption=cap)
        if save_to_self:
            await utils.answer(message, self.strings["gme_sent_to_saved"])

    @loader.command()
    async def gkmemimport(self, message: Message):
        """[auto] — Импорт памяти из json-файла (ответом на файл)."""
        reply = await message.get_reply_message()
        if not reply or not reply.document:
            return await utils.answer(message, "Ответьте на json-файл с памятью.")
        gauto = "auto" in utils.get_args_raw(message)
        try:
            f = await self.client.download_media(reply, bytes)
            hist = json.loads(f)
            if not isinstance(hist, list):
                raise ValueError("Неверный формат.")
            cid = utils.get_chat_id(message)
            target = self.gauto_conversations if gauto else self.conversations
            target[str(cid)] = hist
            self._save_history_sync(gauto)
            await utils.answer(message, "Память успешно импортирована.")
        except Exception as e:
            await utils.answer(message, f"Ошибка импорта: {e}")

    # ─────────────────── watcher (gauto) ────────────────────────

    async def watcher(self, message: Message):
        if not isinstance(message, Message):
            return
        cid = utils.get_chat_id(message)
        if str(cid) not in self.impersonation_chats:
            return
        if message.sender_id == self.me.id:
            return
        is_pm = isinstance(message.peer_id, tg_types.PeerUser)
        if is_pm and not self.config["gauto_in_pm"]:
            return
        sender = await message.get_sender()
        if isinstance(sender, tg_types.User) and sender.bot:
            return
        if random.random() > self.config["impersonation_reply_chance"]:
            return
        user_text, img_data, img_mime, warnings = await self._prepare_content(message)
        if not user_text and not img_data:
            return
        resp = await self._send_to_grok(message=message, user_text=user_text, image_data=img_data, image_mime=img_mime, impersonation_mode=True)
        if resp and resp.strip():
            cln = resp.strip()
            await asyncio.sleep(random.uniform(2, 8))
            try:
                await self.client.send_read_acknowledge(cid, message=message)
            except Exception:
                pass
            async with message.client.action(cid, "typing"):
                await asyncio.sleep(min(25.0, max(1.5, len(cln) * random.uniform(0.1, 0.25))))
            await message.reply(cln)

    # ───────────────────── Inline/Callback ──────────────────────

    @loader.callback_handler()
    async def grok_callback_handler(self, call: InlineCall):
        if not call.data.startswith("grok:"):
            return
        parts = call.data.split(":")
        action = parts[1]
        if action == "noop":
            await call.answer()
            return
        if action == "pg":
            uid = parts[2]
            page = int(parts[3])
            await self._render_page(uid, page, call)

    async def _clear_callback(self, call: InlineCall, chat_id: int):
        self._clear_history(chat_id, gauto=False)
        await call.edit(self.strings["memory_cleared"], reply_markup=None)

    async def _regenerate_callback(self, call: InlineCall, mid, cid):
        key = f"{cid}:{mid}"
        if key not in self.last_requests:
            return await call.answer(self.strings["no_last_request"], show_alert=True)
        user_text, disp = self.last_requests[key]
        await self._send_to_grok(mid, user_text, regeneration=True, call=call, chat_id_override=cid, display_prompt=disp)

    async def _close_callback(self, call: InlineCall, uid: str):
        await call.answer()
        if uid in self.pager_cache:
            del self.pager_cache[uid]
        try:
            await self.client.delete_messages(call.chat_id, call.message_id)
        except Exception:
            try:
                await call.edit("✔️ Сессия закрыта.", reply_markup=None)
            except Exception:
                pass

    async def _render_page(self, uid, page_num, entity):
        data = self.pager_cache.get(uid)
        if not data:
            if isinstance(entity, InlineCall):
                await entity.edit("⚠️ <b>Сессия истекла.</b>", reply_markup=None)
            return
        chunks = data["chunks"]
        total = data["total"]
        header = data.get("header", "")
        raw_text_chunk = chunks[page_num]
        safe_text = self._markdown_to_html(raw_text_chunk)
        formatted_body = self._format_response_with_smart_separation(safe_text)
        text_to_show = f"{header}\n{formatted_body}"
        nav_row = []
        if page_num > 0:
            nav_row.append({"text": "◀️", "data": f"grok:pg:{uid}:{page_num - 1}"})
        nav_row.append({"text": f"{page_num + 1}/{total}", "data": "grok:noop"})
        if page_num < total - 1:
            nav_row.append({"text": "▶️", "data": f"grok:pg:{uid}:{page_num + 1}"})
        extra_row = [{"text": "❌ Закрыть", "callback": self._close_callback, "args": (uid,)}]
        if data.get("chat_id") and data.get("msg_id"):
            extra_row.append({"text": "🔄", "callback": self._regenerate_callback, "args": (data["msg_id"], data["chat_id"])})
        buttons = [nav_row, extra_row]
        if isinstance(entity, Message):
            await self.inline.form(text=text_to_show, message=entity, reply_markup=buttons)
        elif isinstance(entity, InlineCall):
            await entity.edit(text=text_to_show, reply_markup=buttons)
        elif hasattr(entity, "edit"):
            try:
                await entity.edit(text=text_to_show, reply_markup=buttons)
            except Exception:
                pass

    def _get_inline_buttons(self, chat_id, base_message_id):
        return [[
            {"text": self.strings["btn_clear"], "callback": self._clear_callback, "args": (chat_id,)},
            {"text": self.strings["btn_regenerate"], "callback": self._regenerate_callback, "args": (base_message_id, chat_id)},
        ]]

    # ───────────────────── Utilities ────────────────────────────

    def _find_preset(self, query):
        if not query:
            return None
        if str(query).isdigit():
            idx = int(query) - 1
            if 0 <= idx < len(self.prompt_presets):
                return self.prompt_presets[idx]
        for p in self.prompt_presets:
            if p["name"].lower() == str(query).lower():
                return p
        return None

    def _paginate_text(self, text: str, limit: int) -> list:
        pages = []
        current_lines = []
        current_len = 0
        in_code_block = False
        current_code_lang = ""
        for line in text.split("\n"):
            line_len = len(line) + 1
            stripped = line.strip()
            if stripped.startswith("```"):
                if in_code_block:
                    in_code_block = False
                    current_code_lang = ""
                else:
                    in_code_block = True
                    current_code_lang = stripped[3:].strip()
            if current_len + line_len > limit and current_lines:
                if in_code_block:
                    current_lines.append("```")
                pages.append("\n".join(current_lines))
                current_lines = []
                current_len = 0
                if in_code_block:
                    current_lines.append(f"```{current_code_lang}")
                    current_len = len(current_lines[0]) + 1
            current_lines.append(line)
            current_len += line_len
        if current_lines:
            pages.append("\n".join(current_lines))
        return pages if pages else [text]

    async def _get_recent_chat_text(self, cid, count=None, skip_last=False) -> str:
        lim = (count or self.config["impersonation_history_limit"]) + (1 if skip_last else 0)
        lines = []
        try:
            msgs = await self.client.get_messages(cid, limit=lim)
            if skip_last and msgs:
                msgs = msgs[1:]
            for m in msgs:
                if not m:
                    continue
                if not (m.text or m.sticker or m.photo or m.file or m.media):
                    continue
                name = get_display_name(await m.get_sender()) or "Unknown"
                txt = m.text or ""
                if m.sticker:
                    alt = next((a.alt for a in m.sticker.attributes if isinstance(a, DocumentAttributeSticker)), "?")
                    txt += f" [Стикер: {alt}]"
                elif m.photo:
                    txt += " [Фото]"
                elif m.file:
                    txt += " [Файл]"
                elif m.media and not txt:
                    txt += " [Медиа]"
                if txt.strip():
                    lines.append(f"{name}: {txt.strip()}")
        except Exception:
            pass
        return "\n".join(reversed(lines))

    def _handle_error(self, e: Exception) -> str:
        logger.exception("Grok execution error")
        if isinstance(e, asyncio.TimeoutError):
            return self.strings["api_timeout"]
        msg = str(e)
        if "no_api_key" in msg:
            return self.strings["no_api_key"]
        if "invalid_api_key" in msg:
            return self.strings["invalid_api_key"]
        if "all_keys_exhausted" in msg:
            count = msg.split("|")[-1] if "|" in msg else "?"
            return self.strings["all_keys_exhausted"].format(count)
        if isinstance(e, (OSError, socket.timeout)):
            return "❗️ <b>Сетевая ошибка:</b>\n<code>{}</code>".format(utils.escape_html(msg))
        if "quota" in msg.lower() or "429" in msg:
            return self.strings["all_keys_exhausted"].format(len(self.api_keys))
        return self.strings["generic_error"].format(utils.escape_html(msg))

    def _markdown_to_html(self, text: str) -> str:
        def heading_replacer(match):
            level = len(match.group(1))
            title = match.group(2).strip()
            indent = "   " * (level - 1)
            return f"{indent}<b>{title}</b>"
        text = re.sub(r"^(#+)\s+(.*)", heading_replacer, text, flags=re.MULTILINE)
        text = re.sub(r"^([ \t]*)[-*+]\s+", lambda m: f"{m.group(1)}• ", text, flags=re.MULTILINE)
        md = MarkdownIt("commonmark", {"html": True, "linkify": True})
        md.enable("strikethrough")
        md.disable("hr")
        md.disable("heading")
        md.disable("list")
        html_text = md.render(text)
        def format_code(match):
            lang = utils.escape_html(match.group(1).strip())
            code = utils.escape_html(match.group(2).strip())
            return f'<pre><code class="language-{lang}">{code}</code></pre>' if lang else f"<pre><code>{code}</code></pre>"
        html_text = re.sub(r"```(.*?)\n([\s\S]+?)\n```", format_code, html_text)
        html_text = re.sub(r"<p>(<pre>[\s\S]*?</pre>)</p>", r"\1", html_text, flags=re.DOTALL)
        html_text = html_text.replace("<p>", "").replace("</p>", "\n").strip()
        return html_text

    def _format_response_with_smart_separation(self, text: str) -> str:
        pattern = r"(<pre.*?>[\s\S]*?</pre>)"
        parts = re.split(pattern, text, flags=re.DOTALL)
        result_parts = []
        for i, part in enumerate(parts):
            if not part or part.isspace():
                continue
            if i % 2 == 1:
                result_parts.append(part.strip())
            else:
                stripped = part.strip()
                if stripped:
                    result_parts.append(f'<blockquote expandable="true">{stripped}</blockquote>')
        return "\n".join(result_parts)
