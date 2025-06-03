from ignis.widgets import Widget
from ignis.app import IgnisApp
from .dock_manager import DockManager
from .custom_buttons import launcher_button, trash_button
from options import settings

app = IgnisApp.get_default()

#Макет дока с кнопками и списком приложений
def create_dock_layout(dock_manager: DockManager) -> Widget.CenterBox:
    return Widget.CenterBox(
        css_classes=["dock"],
        start_widget=launcher_button(dock_manager),
        center_widget=dock_manager.apps_list,
        end_widget=trash_button(dock_manager),
    )

#Виджет для анимации скытия и отображения
def create_revealer(dock_layout: Widget.CenterBox) -> Widget.Revealer:
    return Widget.Revealer(
        transition_type="slide_up",
        child=dock_layout,
        transition_duration=settings.dock.animation_speed,
        reveal_child=True,
    )

def create_dock_window(revealer: Widget.Revealer, monitor_id: int) -> Widget.RevealerWindow:
    return Widget.RevealerWindow(
        namespace=f"ignis_dock_{monitor_id}",
        monitor=monitor_id,
        anchor=["bottom"],
        exclusivity="normal",
        child=Widget.Box(child=[revealer]),
        revealer=revealer,
    )


def dock(monitor_id: int = 0) -> Widget.RevealerWindow:
    # Создаем менеджер дока для этого монитора
    dock_manager = DockManager(monitor_id)
    dock_manager.listen_for_events()
    dock_manager.refresh_apps_list()

    # Создаем компоненты дока
    dock_layout = create_dock_layout(dock_manager)
    revealer = create_revealer(dock_layout)
    dock_window = create_dock_window(revealer, monitor_id)

    # Устанавливаем окно в менеджер для управления
    dock_manager.set_dock_window(dock_window)

    return dock_window
