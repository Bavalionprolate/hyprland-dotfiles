from ignis.utils import Utils
from ignis.app import IgnisApp

app = IgnisApp.get_default()
app.apply_css(f"{Utils.get_current_dir()}/style.scss")

from modules.launchpad import launchpad
from modules.bar import bar
from modules.dock import dock
from modules.control_center import control_center
from modules.notification_popup import notification_popup
from modules.power import power
from modules.wallpaper_panel import wallpaper_panel

for monitor in range(Utils.get_n_monitors()):
    notification_popup(monitor)
    bar(monitor)
    dock(monitor)
    control_center(monitor)

launchpad()
power()
wallpaper_panel()
