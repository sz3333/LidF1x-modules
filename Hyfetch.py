# meta developer: Femboy4k.t.me
import subprocess
import traceback
from .. import loader, utils

@loader.tds
class HyfetchMod(loader.Module):
    """Показывает системную инфу через HyFetch (аниме-style UwU)"""
    strings = {"name": "Hyfetch"}

    async def hyfetchcmd(self, message):  
        try:  
            # Проверка наличия hyfetch  
            subprocess.run(["which", "hyfetch"], check=True, capture_output=True)  
        except subprocess.CalledProcessError:  
            await message.edit("<b>❌ Hyfetch не установлен!</b>\n<code>pip install hyfetch</code> или <code>yay -S hyfetch</code>")  
            return  

        try:  
            # Проверка наличия sed  
            subprocess.run(["which", "sed"], check=True, capture_output=True)  
        except subprocess.CalledProcessError:  
            await message.edit("<b>❌ sed не найден! Установи его:</b>\n<code>pacman -S sed</code>")  
            return  

        try:  
            # Запуск hyfetch  
            process = subprocess.run(["hyfetch"], capture_output=True, text=True)  
            if process.returncode != 0:  
                await message.edit(f"<b>⚠️ Hyfetch ошибка:</b>\n<pre>{utils.escape_html(process.stderr)}</pre>")  
                return  

            # Удаление ANSI-кодов  
            clean_output = subprocess.run(  
                ["sed", r"s/\x1B\[[0-9;]*[mK]//g"],  
                input=process.stdout,  
                text=True,  
                capture_output=True  
            )  

            if clean_output.returncode != 0:  
                await message.edit(f"<b>⚠️ Ошибка при очистке ANSI-кодов:</b>\n<pre>{utils.escape_html(clean_output.stderr)}</pre>")  
                return  

            await message.edit(f"<pre>{utils.escape_html(clean_output.stdout)}</pre>")  

        except Exception as e:  
            error_trace = traceback.format_exc()  
            await message.edit(f"<b>💥 Непредвиденная ошибка:</b>\n<pre>{utils.escape_html(error_trace)}</pre>")  

#meowfinish 🐾