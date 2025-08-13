from .. import loader, utils
import random


class FemboyPickerMod(loader.Module):
    """Это просто фембой порно, какого вообще хуя ."""
    strings = {"name": " FemboyPorn"}

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

        # Список ссылок на каналы (каналы можно добавить)
        self.channels = [
            "https://t.me/+s5sOl_ZyC2YwYzIy",
            "https://t.me/+cfc6yMw10n03Y2Ji",
            "https://t.me/+VCeDbzVfq6s4Mzli",
            "https://t.me/+S-ho28mkiGliMmY6",
            "https://t.me/+OuiVJIXxWxBjZTcy"
        ]

    async def fpcmd(self, message):
        """ фембой порно(wtf)
        Использование: .fp [photo|video] (можно не указывать для рандома)
        """
        args = utils.get_args_raw(message)
        media_types = ["photo", "video"]
        media_filter = args.lower() if args.lower() in media_types else None

        selected_channel = random.choice(self.channels)

        try:
            # Получаем последние 100 сообщений из канала (можно изменить)
            messages = []
            async for msg in self.client.iter_messages(selected_channel, limit=300):
                if media_filter == "photo" and msg.photo:
                    messages.append(msg)
                elif media_filter == "video" and msg.video:
                    messages.append(msg)
                elif not media_filter and (msg.photo or msg.video):
                    messages.append(msg)

            if not messages:
                await message.edit(f"❌ В канале {selected_channel} нет подходящих медиа.")
                return

            random_msg = random.choice(messages)

            await self.client.send_file(
                message.chat_id,
                file=random_msg.media,
                reply_to=message.reply_to_msg_id if message.is_reply else None,
            )
            await message.delete()

        except Exception as e:
            await message.edit(f"❌ Ошибка при получении данных из канала {selected_channel}: {e}")