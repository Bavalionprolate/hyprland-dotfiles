from ignis.utils import Utils
import asyncio

def focus_window(address: str):
    asyncio.create_task(Utils.exec_sh_async(f"hyprctl dispatch focuswindow address:{address}"))
    asyncio.create_task(Utils.exec_sh_async(f"hyprctl dispatch alterzorder top,address:{address}"))

def close_window(address: str):
    asyncio.create_task(Utils.exec_sh_async(f"hyprctl dispatch closewindow address:{address}"))
