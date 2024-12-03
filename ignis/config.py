
from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.app import IgnisApp
from ignis.services.hyprland import HyprlandService

app = IgnisApp.get_default()
app.apply_css(f"{Utils.get_current_dir()}/style.scss")

from modules.bar import bar

for i in range(Utils.get_n_monitors()):
    bar(i)