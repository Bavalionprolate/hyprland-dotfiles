import datetime
from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.services.audio import AudioService, Stream
from ignis.services.system_tray import SystemTrayService, SystemTrayItem
from ignis.services.hyprland import HyprlandService
from ignis.services.notifications import NotificationService
from ignis.services.mpris import MprisService

import asyncio

audio = AudioService.get_default()
system_tray = SystemTrayService.get_default()
hyprland = HyprlandService.get_default()
notifications = NotificationService.get_default()
mpris = MprisService.get_default()

from modules.osd import OSD
osd = OSD()

from functools import lru_cache
from gi.repository import Gio, GLib

def workspace_button(workspace) -> Widget.Button:
    widget = Widget.Button(
        css_classes=["workspace"],
        on_click=lambda x: workspace.switch_to(),
        child=Widget.Label(label=str(workspace.id)),
    )
    if workspace.id == hyprland.active_workspace.id:
        widget.add_css_class("active")

    return widget

def scroll_workspaces(direction: str, monitor_name: str = "") -> None:
    current = hyprland.active_workspace.id
    if direction == "up":
        target = current - 1
        hyprland.switch_to_workspace(target)
    else:
        target = current + 1
        if target == 11:
            return
        hyprland.switch_to_workspace(target)

def workspaces(monitor_name: str) -> Widget.EventBox:
    return Widget.EventBox(
        on_scroll_up=lambda x: scroll_workspaces("up"),
        on_scroll_down=lambda x: scroll_workspaces("down"),
        css_classes=["workspaces"],
        spacing=5,
        child=hyprland.bind_many(
            ["workspaces", "active_workspace"],
            transform=lambda workspaces, active_workspace: [
                workspace_button(i) for i in workspaces
            ],
        ),
    )

def workspace_add_button() -> Widget.Button:
    return Widget.Button(
        on_click=lambda x: asyncio.create_task(Utils.exec_sh_async("hyprctl dispatch workspace emptynm")),
        child=Widget.Label(label="+"),
    )

def clock() -> Widget.Button:
    return Widget.Button(
        css_classes=["clock"],
        child=Widget.Label(
            label=Utils.Poll(
                1, lambda self: datetime.datetime.now().strftime("%h %d %H:%M")
            ).bind("output"),
        ),
    )

def kb_layout():
    return Widget.EventBox(
        on_click=lambda self: hyprland.main_keyboard.switch_layout("next"),
        child=[Widget.Label(label=hyprland.main_keyboard.bind("active_keymap"))],
    )

def speaker_volume(stream: Stream) -> Widget.Button:
    return Widget.Button(
        child=Widget.Box(
            child=[
                Widget.Icon(
                    image=stream.bind("icon_name"), style="margin-right: 5px;",
                    pixel_size=18,
                ),
                Widget.Label(
                    label=stream.bind("volume", transform=lambda value: str(value))
                )
        ]),
        on_click=lambda x: stream.set_is_muted(not stream.is_muted),
    )

def tray_item(item: SystemTrayItem) -> Widget.Button:
    if item.menu:
        menu = item.menu.copy()
    else:
        menu = None

    return Widget.Button(
        child=Widget.Box(
            child=[
                Widget.Icon(image=item.bind("icon"), pixel_size=16),
                menu,
            ]
        ),
        setup=lambda self: item.connect("removed", lambda x: self.unparent()),
        tooltip_text=item.bind("tooltip"),
        on_click=lambda x: menu.popup() if menu else None,
        on_right_click=lambda x: menu.popup() if menu else None,
        css_classes=["tray-item"],
    )

def tray():
    return Widget.Box(
        setup=lambda self: system_tray.connect(
            "added", lambda x, item: self.append(tray_item(item))
        ),
        spacing=10,
    )

def speaker_slider() -> Widget.Scale:
    return Widget.Scale(
        min=0,
        max=100,
        step=1,
        value=audio.speaker.bind("volume"),
        on_change=lambda x: [
            audio.speaker.set_volume(x.value),
            osd.set_property("visible", True)
        ],
        css_classes=["volume-slider"],
    )

def control_center_button(monitor_id) -> Widget.Switch:
    return Widget.Switch(
        on_change=lambda switch, active: asyncio.create_task(Utils.exec_sh_async(f"ignis toggle ignis_CONTROL_CENTER_{monitor_id}")),
        css_classes=["control-center-switch"]
    )

def left(monitor_id: int = 0) -> Widget.Box:
    return Widget.Box(
        child=[
            workspace_add_button(),
            workspaces(monitor_id)
        ],
        spacing=10,
    )

def center(monitor_id: int = 0) -> Widget.Box:
    return Widget.Box(
        child=[
        ],
        spacing=10,
    )

def right(monitor_id: int = 0) -> Widget.Box:
    return Widget.Box(
        child=[
            tray(),
            kb_layout(),
            control_center_button(monitor_id),
            speaker_volume(audio.speaker),
            speaker_slider(),
            clock()
        ],
        spacing=10
    )

def bar(monitor_id: int = 0) -> Widget.Window:
    return Widget.Window(
        namespace=f"ignis_bar_{monitor_id}",
        monitor=monitor_id,
        anchor=["left", "top", "right"],
        exclusivity="exclusive",
        child=Widget.CenterBox(
            css_classes=["bar"],
            start_widget=left(monitor_id),
            center_widget=center(monitor_id),
            end_widget=right(monitor_id),
        ),
    )
