import pyrogram
import telethon
from hikkatl.types import Message
from .. import loader, utils
import asyncio
from asyncio import subprocess  # Важно!
import shutil  # Для проверки наличия команды

@loader.tds
class TracePathModule(loader.Module):
    """
    Модуль для выполнения tracepath и mtr.
    """
    strings = {
        "name": "TracePath",
        "no_args": "<b>Укажи хост или IP адрес!</b>\n<code>.tracepath <хост></code> или <code>.mtr <хост></code>",
        "executing": "<b>Выполняю {} для</b> <code>{}</code>...",
        "error": "<b>Ошибка при выполнении {}:</b>\n<code>{}</code>",
        "timeout": "<b>{} превысила таймаут ({} сек).</b>",
        "output_too_long": "<b>Вывод {} слишком длинный, отправляю файлом...</b>",
        "file_caption": "<code>{} {}</code> вывод"
    }

    @loader.command()
    async def tracepathcmd(self, message: Message):
        """Выполняет tracepath до хоста"""
        await self.run_tool(message, tool="tracepath")

    @loader.command()
    async def mtrcmd(self, message: Message):
        """Выполняет mtr -rw до хоста"""
        await self.run_tool(message, tool="mtr")

    async def run_tool(self, message: Message, tool: str):
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_args"))
            return

        host = args.strip()
        initial = await utils.answer(message, self.strings("executing").format(tool, host))

        timeout_seconds = 120

        if shutil.which(tool) is None:
            await utils.answer(initial, self.strings("error").format(tool, f"Команда '{tool}' не найдена в системе!"))
            return

        try:
            # Для mtr нужны опции
            cmd = [tool, host] if tool == "tracepath" else [tool, "-rw", host]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                await utils.answer(initial, self.strings("timeout").format(tool, timeout_seconds))
                return

            if process.returncode != 0:
                err = stderr.decode(errors="ignore").strip()
                await utils.answer(initial, self.strings("error").format(tool, err or f"Код выхода: {process.returncode}"))
                return

            output = stdout.decode(errors="ignore").strip()

            if len(output) > 4000:
                await utils.answer(initial, self.strings("output_too_long").format(tool))
                await self._client.send_file(
                    message.peer_id,
                    file=(f"{tool}_{host}.txt", output.encode()),
                    caption=self.strings("file_caption").format(tool, host)
                )
            else:
                await utils.answer(initial, f"<b>{tool.upper()} вывод для</b> <code>{host}</code>:\n<pre>{output}</pre>")

        except Exception as e:
            await utils.answer(initial, self.strings("error").format(tool, str(e)))