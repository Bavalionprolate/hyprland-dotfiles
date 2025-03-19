from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.app import IgnisApp
from ignis.services.hyprland import HyprlandService
from ignis.services.wallpaper import WallpaperService
import os

app = IgnisApp.get_default()

app.apply_css(f"{Utils.get_current_dir()}/style.scss")

from modules.launchpad import launchpad
from modules.bar import bar
from modules.dock import dock
from modules.control_center import control_center
from modules.notification_popup import notification_popup
from modules.power import power
from modules.bar.calendar import calendar_window

for monitor in range(Utils.get_n_monitors()):
    notification_popup(monitor)
    bar(monitor)
    dock(monitor)

launchpad()
control_center()
power()
calendar_window()
