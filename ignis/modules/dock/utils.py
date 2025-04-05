from ignis.utils import Utils

def focus_window(address: str):
    Utils.exec_sh_async(f"hyprctl dispatch focuswindow address:{address}")
    Utils.exec_sh_async(f"hyprctl dispatch alterzorder top,address:{address}")

def close_window(address: str):
    Utils.exec_sh_async(f"hyprctl dispatch closewindow address:{address}")
