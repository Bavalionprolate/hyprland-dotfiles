from gi.repository import Gtk
from ignis.widgets import Widget
from .dock_manager import DockManager
from .custom_buttons import launcher_button, trash_button

def dock(monitor_id: int = 0) -> Widget.RevealerWindow:
    global dock_manager
    dock_manager = DockManager(monitor_id)
    dock_manager.listen_for_events()
    dock_manager.refresh_apps_list()

    revealer = Widget.Revealer(
        transition_type="slide_up",
        child=Widget.CenterBox(
            css_classes=["dock"],
            start_widget=launcher_button(dock_manager),
            center_widget=dock_manager.apps_list,
            end_widget=trash_button(dock_manager),
        ),
        transition_duration=500,
        reveal_child=True,
    )

    dock_window = Widget.RevealerWindow(
        namespace=f"ignis_dock_{monitor_id}",
        monitor=monitor_id,
        anchor=["bottom"],
        exclusivity="normal",
        child=Widget.Box(child=[revealer]),
        revealer=revealer,
    )

    dock_manager.set_dock_window(dock_window)

    return dock_window
