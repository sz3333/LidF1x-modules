# meta developer: LidF1x.

from .. import loader, utils

class InstantDeleteMod(loader.Module):
    """Отправляет и мгновенно удаляет"""

    @loader.command()
    async def sd(self, message):
        """<текст> — отправить и удалить сразу"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ Нет текста")
            return

        msg = await utils.answer(message, args)

        # гойда
        await msg.delete()

# хуй
# ало
# ало да да 
# Епштейн да ало приезжай жду