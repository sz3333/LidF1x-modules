import asyncio
import contextlib
import os
import platform
import sys
import time
from datetime import timedelta
import psutil
from telethon.tl.types import Message
from .. import loader, utils

def bytes_to_megabytes(b: int) -> float:
    return round(b / 1024 / 1024, 1)

def bytes_to_gb(b: int) -> float:
    return round(b / 1024 / 1024 / 1024, 2)

def seconds_to_readable(seconds: int) -> str:
    return str(timedelta(seconds=seconds))

def get_usage_bar(percent: float, length: int = 10) -> str:
    """Create a visual usage bar"""
    filled = int((percent / 100) * length)
    empty = length - filled
    
    if percent >= 90:
        bar_color = "🔴"
    elif percent >= 70:
        bar_color = "🟡"
    else:
        bar_color = "🟢"
        
    return f"{'█' * filled}{'░' * empty} {bar_color}"

def get_temp_emoji(temp: float) -> str:
    """Get temperature emoji based on value"""
    if temp >= 80:
        return "🔥"
    elif temp >= 60:
        return "🌡️"
    else:
        return "❄️"

@loader.tds
class EnhancedServerInfoMod(loader.Module):
    """🚀 Show beautiful detailed server info with visual indicators"""

    strings = {
        "name": "EnhancedServerInfo",
        "loading": "⚡ <b>Scanning system resources...</b> <code>⠋</code>",
        "servinfo": (
            "╭─ <b>🖥️ System Overview</b> ─╮\n"
            "│\n"
            "├ 🧠 <b>CPU:</b> <code>{cpu_cores}</code> cores @ <code>{cpu_freq} GHz</code>\n"
            "│  ├─ Load: <code>{cpu_load}%</code> {cpu_bar}\n"
            "│\n"
            "├ 🎯 <b>Memory:</b> <code>{ram_used}</code>/<code>{ram_total} MB</code>\n"
            "│  ├─ Usage: <code>{ram_percent}%</code> {ram_bar}\n"
            "│\n"
            "├ 💾 <b>Storage:</b> <code>{disk_used}</code>/<code>{disk_total} GB</code>\n"
            "│  ├─ Usage: <code>{disk_percent}%</code> {disk_bar}\n"
            "│\n"
            "├ 🌡️ <b>Temperature:</b> {temperature}\n"
            "├ 💨 <b>Cooling:</b> {fan_speed}\n"
            "├ 📡 <b>Network:</b> <code>{ping} ms</code> {ping_status}\n"
            "│\n"
            "├─ <b>🔧 System Details</b> ─┤\n"
            "│\n"
            "├ 🐧 <b>OS:</b> <code>{os}</code>\n"
            "├ ⚙️ <b>Kernel:</b> <code>{kernel}</code> <code>({arch})</code>\n"
            "├ 🐍 <b>Python:</b> <code>{python}</code>\n"
            "├ ⏱️ <b>Uptime:</b> <code>{uptime}</code> {uptime_emoji}\n"
            "├ 👥 <b>Users:</b> <code>{users}</code>\n"
            "├ ⚡ <b>Processes:</b> <code>{processes}</code>\n"
            "│\n"
            "╰─ <i>Generated at {timestamp}</i> ─╯"
        ),
    }

    @loader.command()
    async def enhancedinfo(self, message: Message):
        """🚀 Show beautiful detailed server info"""
        loading_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        
        # Animated loading
        for i in range(3):
            for frame in loading_frames[:3]:
                await utils.answer(message, f"⚡ <b>Scanning system resources...</b> <code>{frame}</code>")
                await asyncio.sleep(0.1)

        info = {}

        # CPU Info
        with contextlib.suppress(Exception):
            info["cpu_cores"] = psutil.cpu_count(logical=True)

        with contextlib.suppress(Exception):
            cpu_freq = psutil.cpu_freq().current / 1000
            info["cpu_freq"] = round(cpu_freq, 2)

        with contextlib.suppress(Exception):
            cpu_load = psutil.cpu_percent()
            info["cpu_load"] = cpu_load
            info["cpu_bar"] = get_usage_bar(cpu_load)

        # RAM Info
        with contextlib.suppress(Exception):
            ram = psutil.virtual_memory()
            info["ram_used"] = bytes_to_megabytes(ram.used)
            info["ram_total"] = bytes_to_megabytes(ram.total)
            info["ram_percent"] = ram.percent
            info["ram_bar"] = get_usage_bar(ram.percent)

        # Disk Info
        with contextlib.suppress(Exception):
            disk = psutil.disk_usage("/")
            info["disk_used"] = bytes_to_gb(disk.used)
            info["disk_total"] = bytes_to_gb(disk.total)
            info["disk_percent"] = disk.percent
            info["disk_bar"] = get_usage_bar(disk.percent)

        # Kernel and OS Info
        with contextlib.suppress(Exception):
            info["kernel"] = platform.release()

        with contextlib.suppress(Exception):
            info["arch"] = platform.architecture()[0]

        with contextlib.suppress(Exception):
            system = os.popen("cat /etc/*release").read()
            b = system.find('PRETTY_NAME="') + 13
            os_name = system[b : system.find('"', b)]
            # Shorten long OS names
            if len(os_name) > 25:
                os_name = os_name[:22] + "..."
            info["os"] = os_name if os_name else "Unknown Linux"

        # Temperature and Fan Speed
        with contextlib.suppress(Exception):
            temps = psutil.sensors_temperatures()
            if "coretemp" in temps:
                temp_val = temps['coretemp'][0].current
                temp_emoji = get_temp_emoji(temp_val)
                info["temperature"] = f"<code>{temp_val}°C</code> {temp_emoji}"
            else:
                info["temperature"] = "<code>N/A</code> ❔"

        with contextlib.suppress(Exception):
            fans = psutil.sensors_fans()
            if fans:
                fan_speeds = [f.current for f in fans.get(next(iter(fans)), []) if f.current]
                if fan_speeds:
                    rpm = fan_speeds[0]
                    fan_emoji = "🌪️" if rpm > 3000 else "💨"
                    info["fan_speed"] = f"<code>{rpm} RPM</code> {fan_emoji}"
                else:
                    info["fan_speed"] = "<code>N/A</code> ❔"
            else:
                info["fan_speed"] = "<code>N/A</code> ❔"

        # Ping with visual indicator
        with contextlib.suppress(Exception):
            start = time.time()
            os.system("ping -c 1 8.8.8.8 > /dev/null 2>&1")
            ping_val = round((time.time() - start) * 1000, 2)
            info["ping"] = ping_val
            
            if ping_val < 50:
                info["ping_status"] = "🟢"
            elif ping_val < 150:
                info["ping_status"] = "🟡"
            else:
                info["ping_status"] = "🔴"

        # Uptime with emoji
        with contextlib.suppress(Exception):
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_str = seconds_to_readable(int(uptime_seconds))
            info["uptime"] = uptime_str
            
            days = int(uptime_seconds / 86400)
            if days > 30:
                info["uptime_emoji"] = "🏆"
            elif days > 7:
                info["uptime_emoji"] = "💪"
            elif days > 1:
                info["uptime_emoji"] = "✅"
            else:
                info["uptime_emoji"] = "🆕"

        # Python Version
        with contextlib.suppress(Exception):
            info["python"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # Processes
        with contextlib.suppress(Exception):
            info["processes"] = len(psutil.pids())

        # Users
        with contextlib.suppress(Exception):
            users = psutil.users()
            unique_users = {user.name for user in users}
            if len(unique_users) > 3:
                info["users"] = f"{len(unique_users)} users"
            else:
                info["users"] = ", ".join(unique_users) if unique_users else "None"

        # Timestamp
        info["timestamp"] = time.strftime("%H:%M:%S")

        # Fill missing values
        for key, value in info.items():
            if value is None or (isinstance(value, str) and not value):
                info[key] = "N/A"

        # Ensure all required keys exist
        required_keys = [
            "cpu_cores", "cpu_freq", "cpu_load", "cpu_bar",
            "ram_used", "ram_total", "ram_percent", "ram_bar",
            "disk_used", "disk_total", "disk_percent", "disk_bar",
            "temperature", "fan_speed", "ping", "ping_status",
            "os", "kernel", "arch", "python", "uptime", "uptime_emoji",
            "users", "processes", "timestamp"
        ]
        
        for key in required_keys:
            if key not in info:
                info[key] = "N/A"

        await utils.answer(message, self.strings("servinfo").format(**info))