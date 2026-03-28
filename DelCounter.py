# meta developer: LidF1x
# meta version: 2.0.0

import asyncio
import random

from telethon.tl.types import User, Chat, Channel
from telethon.errors import ChatAdminRequiredError, UserAdminInvalidError, FloodWaitError
from .. import loader, utils


@loader.tds
class DeletedCounterMod(loader.Module):
    """Счётчик и менеджер удалённых аккаунтов Telegram"""

    strings = {"name": "DeletedCounter"}

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _is_deleted(user) -> bool:
        return isinstance(user, User) and user.deleted

    @staticmethod
    def _chat_title(entity) -> str:
        if hasattr(entity, "title") and entity.title:
            return entity.title
        return "Без названия"

    @staticmethod
    def _progress_bar(done: int, total: int, width: int = 12) -> str:
        if total == 0:
            return "░" * width
        filled = int(width * done / total)
        return "█" * filled + "░" * (width - filled)

    # ──────────────────────────────────────────────
    # .delpm — удалённые в ЛС
    # ──────────────────────────────────────────────

    async def delpmcmd(self, message):
        """Посчитать удалённые аккаунты в личках"""
        status = await utils.answer(message, "💫 <b>Сканирую ЛС…</b>")

        dialogs = await message.client.get_dialogs()
        pm_dialogs = [d for d in dialogs if isinstance(d.entity, User)]
        deleted = [d for d in pm_dialogs if d.entity.deleted]
        total = len(pm_dialogs)
        total_no_bots = sum(1 for d in pm_dialogs if not d.entity.bot)

        lines = []
        for d in deleted:
            u = d.entity
            uid = u.id
            lines.append(f"  • <a href='tg://user?id={uid}'>Deleted Account</a> (<code>{uid}</code>)")

        preview = "\n".join(lines[:10])
        more = f"\n  <i>…и ещё {len(deleted) - 10}</i>" if len(deleted) > 10 else ""

        text = (
            f"<emoji document_id=5449449325434266744>❄️</emoji> <b>Удалённые аккаунты в ЛС</b>\n\n"
            f"👤 Всего диалогов: <b>{total}</b>\n"
            f"👤 Без ботов: <b>{total_no_bots}</b>\n"
            f"🗑 Удалённых: <b>{len(deleted)}</b>\n"
            f"📊 Доля: <b>{len(deleted) / total * 100:.1f}%</b>\n"
            f"📊 Доля без ботов: <b>{len(deleted) / total_no_bots * 100:.1f}%</b>\n\n"
            + (f"<blockquote>{preview}{more}</blockquote>" if deleted else "✅ Удалённых аккаунтов не найдено.")
        )
        await utils.answer(status, text)

    # ──────────────────────────────────────────────
    # .delchat — удалённые в текущем чате
    # ──────────────────────────────────────────────

    async def delchatcmd(self, message):
        """Посчитать удалённых участников в текущем чате"""
        chat = await message.get_chat()
        status = await utils.answer(message, "💫 <b>Сканирую участников чата…</b>")

        try:
            members = await message.client.get_participants(chat)
        except ChatAdminRequiredError:
            return await utils.answer(status, "⚠️ <b>Нужны права администратора для просмотра участников.</b>")

        deleted = [m for m in members if self._is_deleted(m)]
        total = len(members)

        lines = [f"  • <code>{u.id}</code>" for u in deleted[:15]]
        more = f"\n  <i>…и ещё {len(deleted) - 15}</i>" if len(deleted) > 15 else ""

        text = (
            f"<emoji document_id=5449449325434266744>❄️</emoji> <b>Удалённые в «{self._chat_title(chat)}»</b>\n\n"
            f"👥 Всего участников: <b>{total}</b>\n"
            f"🗑 Удалённых: <b>{len(deleted)}</b>\n"
            f"📊 Доля: <b>{len(deleted) / total * 100:.1f}%</b>\n\n"
            + (f"<blockquote>{''.join(lines)}{more}</blockquote>" if deleted else "✅ Удалённых аккаунтов не найдено.")
        )
        await utils.answer(status, text)

    # ──────────────────────────────────────────────
    # .delkick — кикнуть удалённых из текущего чата
    # ──────────────────────────────────────────────

    async def delkickcmd(self, message):
        """Кикнуть всех удалённых участников из текущего чата"""
        chat = await message.get_chat()
        status = await utils.answer(message, "💫 <b>Получаю список участников…</b>")

        try:
            members = await message.client.get_participants(chat)
        except ChatAdminRequiredError:
            return await utils.answer(status, "⚠️ <b>Нужны права администратора.</b>")

        deleted = [m for m in members if self._is_deleted(m)]

        if not deleted:
            return await utils.answer(status, "✅ <b>Удалённых аккаунтов нет — чат чист.</b>")

        kicked = 0
        failed = 0

        for i, user in enumerate(deleted, 1):
            bar = self._progress_bar(i, len(deleted))
            await utils.answer(
                status,
                f"🔄 <b>Кикаю удалённых…</b>\n"
                f"<code>[{bar}]</code> {i}/{len(deleted)}"
            )
            try:
                await message.client.kick_participant(chat, user)
                kicked += 1
            except (ChatAdminRequiredError, UserAdminInvalidError):
                failed += 1
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 2)
                try:
                    await message.client.kick_participant(chat, user)
                    kicked += 1
                except Exception:
                    failed += 1
            except Exception:
                failed += 1

            await asyncio.sleep(random.uniform(0.4, 0.9))

        await utils.answer(
            status,
            f"<emoji document_id=5449449325434266744>❄️</emoji> <b>Кик завершён</b>\n\n"
            f"✅ Кикнуто: <b>{kicked}</b>\n"
            f"❌ Не удалось: <b>{failed}</b>"
        )

    # ──────────────────────────────────────────────
    # .delall — полное сканирование всех чатов
    # ──────────────────────────────────────────────

    async def delallcmd(self, message):
        """Полное сканирование всех групп и каналов на удалённые аккаунты"""
        status = await utils.answer(message, "💫 <b>Загружаю список диалогов…</b>")

        dialogs = await message.client.get_dialogs()
        groups = [d for d in dialogs if isinstance(d.entity, (Chat, Channel)) and not getattr(d.entity, "broadcast", False)]

        total_deleted = 0
        scanned = 0
        top_chats = []  # (count, title)
        errors = 0

        for i, d in enumerate(groups, 1):
            bar = self._progress_bar(i, len(groups))
            await utils.answer(
                status,
                f"🔍 <b>Сканирую чаты…</b>\n"
                f"<code>[{bar}]</code> {i}/{len(groups)}\n"
                f"💬 <i>{self._chat_title(d.entity)}</i>"
            )

            try:
                members = await message.client.get_participants(d.entity)
                count = sum(1 for m in members if self._is_deleted(m))
                scanned += 1
                total_deleted += count
                if count > 0:
                    top_chats.append((count, self._chat_title(d.entity)))
            except (ChatAdminRequiredError, Exception):
                errors += 1

            await asyncio.sleep(random.uniform(0.3, 0.7))

        top_chats.sort(reverse=True)
        top_lines = "\n".join(
            f"  {j}. <b>{title}</b> — {cnt} уд."
            for j, (cnt, title) in enumerate(top_chats[:10], 1)
        )

        text = (
            f"<emoji document_id=5449449325434266744>❄️</emoji> <b>Итог полного сканирования</b>\n\n"
            f"💬 Просканировано чатов: <b>{scanned}</b>\n"
            f"⚠️ Пропущено (нет доступа): <b>{errors}</b>\n"
            f"🗑 Итого удалённых: <b>{total_deleted}</b>\n\n"
            + (f"🏆 <b>Топ чатов с удалёнными:</b>\n{top_lines}" if top_chats else "✅ Удалённых аккаунтов нигде не найдено.")
        )
        await utils.answer(status, text)

    # ──────────────────────────────────────────────
    # .delinfo — справка
    # ──────────────────────────────────────────────

    async def delinfocmd(self, message):
        """Справка по модулю"""
        text = (
            "🐾 <b>DeletedCounter v2.0 — справка</b>\n\n"
            "<b>Команды:</b>\n"
            "• <code>.delpm</code> — удалённые аккаунты в ЛС\n"
            "• <code>.delchat</code> — удалённые в текущем чате\n"
            "• <code>.delkick</code> — кикнуть удалённых из текущего чата\n"
            "• <code>.delall</code> — полное сканирование всех групп\n"
            "• <code>.delinfo</code> — эта справка\n\n"
            "<b>Как определяется удалённый аккаунт:</b>\n"
            "→ <code>user.deleted == True</code>\n"
            "→ нет имени, нет username\n\n"
            "<b>Примечания:</b>\n"
            "• Кик требует прав администратора\n"
            "• <code>.delall</code> может работать долго в зависимости от количества чатов\n"
            "• FloodWait обрабатывается автоматически"
        )
        await utils.answer(message, text)


# // meta developer: LidF1x
