# meta developer: @xdesai && LidF1x
# Команда steal вынесена из ChatModule в отдельный модуль

__version__ = (0, 0, 2)

import asyncio

from telethon import functions
from telethon.tl.types import Channel
from telethon.errors import (
    FloodWaitError,
    PeerFloodError,
    UsersTooMuchError,
    ChatAdminRequiredError,
    UserPrivacyRestrictedError,
    UserNotMutualContactError,
    UserChannelsTooMuchError,
)

from .. import loader, utils


@loader.tds
class MembersStealer(loader.Module):
    """Переносит участников из одного чата в другой.
    Команду пишешь в чате, КУДА добавлять, а ID указываешь того чата, ОТКУДА брать."""

    strings = {
        "name": "MembersStealer",
        "invalid_args": "❌ <b>Неверные аргументы.</b>\nПример: <code>.steal -1001234567890</code> или <code>.steal -1001234567890 nobot</code>",
        "not_a_chat": "❌ <b>Команду нужно писать в группе/канале, куда добавлять участников.</b>",
        "chat_unavailable": "❌ <b>Чат-источник недоступен или приватный.</b>",
        "no_rights": "❌ <b>Не хватает прав (нужно право добавлять участников).</b>",
        "start": "⏳ <b>Начинаю добавление.</b> К добавлению: <code>{count}</code>",
        "flood_wait": "⏳ <b>FloodWait.</b> Telegram просит подождать <code>{seconds}</code> сек. Жду и продолжаю добавление...\nДобавлено: <code>{added}</code> | Не удалось: <code>{failed}</code>",
        "nothing": "🤷 <b>Некого добавлять — все уже здесь.</b>",
        "users_too_much": "⚠️ <b>Достигнут лимит участников в чате.</b>",
        "peer_flood": "⚠️ <b>Telegram ограничил приглашения (PeerFlood). Остановлено.</b>",
        "done": "✅ <b>Готово.</b>\nДобавлено: <code>{added}</code>\nНе удалось: <code>{failed}</code>",
    }

    strings_ru = {
        "_cls_doc": "Переносит участников из одного чата в другой. Команду пишешь в чате, КУДА добавлять, а ID указываешь того чата, ОТКУДА брать.",
    }

    async def _invite(self, client, target, user, status=None, added=0, failed=0):
        """Приглашает одного пользователя в целевой чат. При FloodWait показывает
        сколько секунд просит подождать Telegram, ждёт и сам продолжает добавление."""
        while True:
            try:
                if isinstance(target, Channel):
                    await client(functions.channels.InviteToChannelRequest(
                        channel=target,
                        users=[user],
                    ))
                else:
                    await client(functions.messages.AddChatUserRequest(
                        chat_id=target.id,
                        user_id=user,
                        fwd_limit=0,
                    ))
                return
            except FloodWaitError as e:
                if status is not None:
                    await utils.answer(
                        status,
                        self.strings("flood_wait").format(
                            seconds=e.seconds, added=added, failed=failed
                        ),
                    )
                await asyncio.sleep(e.seconds + 1)

    @loader.owner
    async def stealcmd(self, message):
        """<id/юзернейм чата-источника> [nobot] — добавить участников из указанного чата в ЭТОТ чат"""
        if message.is_private:
            await utils.answer(message, self.strings("not_a_chat"))
            return

        args = utils.get_args_raw(message).split()
        if not args:
            await utils.answer(message, self.strings("invalid_args"))
            return

        raw = args[0]
        source_ref = int(raw) if raw.lstrip("-").isdigit() else raw
        nobot = len(args) > 1 and args[1].lower() == "nobot"

        client = message.client
        target = await message.get_chat()

        try:
            source = await client.get_entity(source_ref)
        except Exception:
            await utils.answer(message, self.strings("chat_unavailable"))
            return

        try:
            existing = {u.id async for u in client.iter_participants(target)}
            users = [
                u async for u in client.iter_participants(source)
                if not u.deleted
                and not u.is_self
                and u.id not in existing
                and not (nobot and u.bot)
            ]
        except ChatAdminRequiredError:
            await utils.answer(message, self.strings("no_rights"))
            return
        except Exception:
            await utils.answer(message, self.strings("chat_unavailable"))
            return

        if not users:
            await utils.answer(message, self.strings("nothing"))
            return

        status = await utils.answer(message, self.strings("start").format(count=len(users)))

        added = failed = 0
        for u in users:
            try:
                await self._invite(client, target, u, status=status, added=added, failed=failed)
                added += 1
            except UsersTooMuchError:
                await utils.answer(status, self.strings("users_too_much"))
                return
            except PeerFloodError:
                await utils.answer(status, self.strings("peer_flood"))
                return
            except ChatAdminRequiredError:
                await utils.answer(status, self.strings("no_rights"))
                return
            except (UserPrivacyRestrictedError, UserNotMutualContactError, UserChannelsTooMuchError):
                failed += 1
            except Exception as e:
                print(f"[MembersStealer] {e}")
                failed += 1
            await asyncio.sleep(2)

        await utils.answer(status, self.strings("done").format(added=added, failed=failed))