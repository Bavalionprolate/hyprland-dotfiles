from gi.repository import Gtk
from ignis.widgets import Widget
from .utils import focus_window, close_window
from ignis.utils import Utils
import logging

def trash_button(dock_manager: "DockManager") -> Widget.Box:
    button = Widget.Button(
        on_click=lambda x: Utils.exec_sh_async("nautilus trash://"),
        child=Widget.Icon(image="user-trash", pixel_size=45),
        css_classes=["trash-button-dock"],
    )
    return button

def launcher_button(dock_manager: "DockManager") -> Widget.Box:
    menu_items = [
        Widget.MenuItem(
            label="Toggle Auto-hide",
            on_activate=lambda x: dock_manager.toggle_auto_hide(),
        )
    ]

    menu = Widget.PopoverMenu(items=menu_items)

    button_box = Widget.Box(
        vertical=True,
        child=[
            Widget.Icon(image="slingscold", pixel_size=45),
            menu
        ],
    )

    button = Widget.Button(
        on_click=lambda x: Utils.exec_sh_async("ignis toggle ignis_LAUNCHPAD"),
        on_right_click=lambda x: menu.popup(),
        child=button_box,
        css_classes=["launcher-button-dock"],
    )

    button.menu = menu
    dock_manager.launcher_button = button

    menu.connect("notify::visible", lambda x, y: dock_manager.check_window_overlap())

    return button
