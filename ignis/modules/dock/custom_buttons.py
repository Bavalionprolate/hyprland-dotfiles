from gi.repository import Gtk
from ignis.widgets import Widget
from .utils import focus_window, close_window
from ignis.utils import Utils
import logging, asyncio
from options import settings

class CustomButton:
    def __init__(self, button: Widget.Button, icon: Widget.Icon):
        self.button = button
        self.icon = icon
        # Подписываемся на изменения размера иконок
        settings.dock.connect_option("icon_size", self._on_icon_size_changed)

    def _on_icon_size_changed(self):
        self.icon.pixel_size = settings.dock.icon_size

def trash_button(dock_manager: "DockManager") -> Widget.Box:
    icon = Widget.Icon(image="user-trash", pixel_size=settings.dock.icon_size)
    button = Widget.Button(
        on_click=lambda x: asyncio.create_task(Utils.exec_sh_async("nautilus trash://")),
        child=icon,
        css_classes=["trash-button-dock"],
    )
    # Создаем экземпляр CustomButton для отслеживания изменений
    CustomButton(button, icon)
    return button

def launcher_button(dock_manager: "DockManager") -> Widget.Box:
    menu_items = [
        Widget.MenuItem(
            label="Toggle Auto-hide",
            on_activate=lambda x: dock_manager.toggle_auto_hide(),
        )
    ]

    menu = Widget.PopoverMenu(items=menu_items)

    icon = Widget.Icon(image="slingscold", pixel_size=settings.dock.icon_size)
    button_box = Widget.Box(
        vertical=True,
        child=[
            icon,
            menu
        ],
    )

    button = Widget.Button(
        on_click=lambda x: asyncio.create_task(Utils.exec_sh_async("ignis toggle ignis_LAUNCHPAD")),
        on_right_click=lambda x: menu.popup(),
        child=button_box,
        css_classes=["launcher-button-dock"],
    )

    # Создаем экземпляр CustomButton для отслеживания изменений
    CustomButton(button, icon)

    button.menu = menu
    dock_manager.launcher_button = button

    menu.connect("notify::visible", lambda x, y: dock_manager.check_window_overlap())

    return button
