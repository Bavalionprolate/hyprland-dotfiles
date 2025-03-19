import datetime, os, json
from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.app import IgnisApp
from ignis.services.audio import AudioService, Stream
from ignis.services.system_tray import SystemTrayService, SystemTrayItem
from ignis.services.hyprland import HyprlandService
from ignis.services.notifications import NotificationService
from ignis.services.mpris import MprisService, MprisPlayer
from ignis.exceptions import HyprlandIPCNotFoundError
from ignis.services.applications import Application
from gi.repository import Gio
from typing import Any


from modules.bar.vpn_control import toggle_vpn, check_vpn_status

audio = AudioService.get_default()
system_tray = SystemTrayService.get_default()
hyprland = HyprlandService.get_default()
notifications = NotificationService.get_default()
mpris = MprisService.get_default()

from .toggle_control import toggle_control_center, read_state
from modules.osd import OSD
osd = OSD()

from functools import lru_cache
from gi.repository import Gio

def workspace_button(workspace: dict) -> Widget.Button:
    widget = Widget.Button(
        css_classes=["workspace"],
        on_click=lambda x, id=workspace["id"]: hyprland.switch_to_workspace(id),
        child=Widget.Label(label=str(workspace["id"])),
    )
    if workspace["id"] == hyprland.active_workspace["id"]:
        widget.add_css_class("active")

    return widget


def scroll_workspaces(direction: str, monitor_id: int) -> None:
    current = hyprland.active_workspace["id"]
    target = current + (-1 if direction == "up" else 1)

    workspaces = [ws for ws in hyprland.workspaces if ws["monitorID"] == monitor_id]
    workspace_ids = sorted([ws["id"] for ws in workspaces])

    if target in workspace_ids:
        hyprland.switch_to_workspace(target)


def workspaces(monitor_id: int) -> Widget.EventBox:
    return Widget.EventBox(
        on_scroll_up=lambda x: scroll_workspaces("up", monitor_id),
        on_scroll_down=lambda x: scroll_workspaces("down", monitor_id),
        css_classes=["workspaces"],
        spacing=5,
        child=hyprland.bind(
            "workspaces",
            transform=lambda value: [
                workspace_button(i)
                for i in value
                if i["monitorID"] == monitor_id
            ],
        ),
    )

def workspace_add_button() -> Widget.Button:
    return Widget.Button(
        on_click=lambda x: Utils.exec_sh_async("hyprctl dispatch workspace emptynm"),
        child=Widget.Label(label="+"),
    )

def clock() -> Widget.Button:
    return Widget.Button(
        css_classes=["clock"],
        on_click=lambda x: toggle_calendar(),
        child=Widget.Label(
            label=Utils.Poll(
                1, lambda self: datetime.datetime.now().strftime("%h %d %H:%M")
            ).bind("output"),
        ),
    )

def toggle_calendar():
    app = IgnisApp.get_default()
    calendar_visible = app.get_window("ignis_CALENDAR").visible
    if calendar_visible:
        Utils.exec_sh_async("ignis close ignis_CALENDAR")
    else:
        Utils.exec_sh_async("ignis open ignis_CALENDAR")

def kb_layout():
    hyprland = HyprlandService.get_default()
    return Widget.Button(
        css_classes=["kb-layout"],
        on_click=lambda x: hyprland.switch_kb_layout(),
        child=Widget.Label(
            label=hyprland.bind(
                "kb_layout", transform=lambda value: value[:2].lower()
            )
        ),
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

def vpn_button() -> Widget.Button:
    button = Widget.Button(
        css_classes=["vpn-button"],
        on_click=lambda x: toggle_vpn() and update_button(button),
        child=Widget.Label(label="VPN")
    )

    def update_button(widget):
        if check_vpn_status():
            widget.add_css_class("vpn-active")
        else:
            widget.remove_css_class("vpn-active")

    Utils.Poll(5, lambda _: update_button(button))

    return button

def control_center_button() -> Widget.Button:
    button = Widget.Button(
        css_classes=["control-center-button"],
        on_click=lambda x: toggle_control_center(button),
        child=Widget.Label(label="")
    )

    def update_button_status():
        if read_state():
            button.child.label = ""
        else:
            button.child.label = ""

    Utils.Poll(5, lambda x: update_button_status())

    return button

def left(monitor_id: int = 0) -> Widget.Box:
    return Widget.Box(
        child=[
            workspaces(monitor_id),
            workspace_add_button(),
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
            vpn_button(),
            kb_layout(),
            control_center_button(),
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
