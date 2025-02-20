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
from modules.bar.pinned_apps import pinned_apps
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

def launcher_button()-> Widget.Box:
    return Widget.Button(
        css_classes=["launcher_button"],
        on_click=lambda x: Utils.exec_sh_async("ignis toggle ignis_LAUNCHPAD"),
        child=Widget.Label(label=""),
    )

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

def get_all_clients(monitor_id: int) -> list[dict[str, Any]]:
    try:
        if not hyprland.is_available:
            return []
        clients = json.loads(hyprland.send_command("j/clients"))
        return [
            client 
            for client in clients 
            if (
                client["title"] and
                client["workspace"] and 
                not client["class"].startswith("conkyc") and 
                client["monitor"] == monitor_id
            )
        ]
    except Exception as e:
        print(f"Ошибка при получении списка клиентов: {e}")
        return []

def get_app_icon(app_class: str) -> str:
    try:
        app_id = map_class_to_app_id(app_class)
        if app_id:
            app_info = Gio.DesktopAppInfo.new(app_id)
            if app_info:
                return app_info.get_string("Icon") or "image-missing"
    except Exception:
        pass
    return "image-missing"

def map_class_to_app_id(app_class: str) -> str | None:
    class_to_app_map = {
        "code-url-handler": "visual-studio-code.desktop",
        "Navigator": "firefox.desktop",
        "org.gnome.Nautilus": "org.gnome.Nautilus.desktop",
        "org.libreofficeriter": "libreoffice-writer.desktop",
    }

    if app_class in class_to_app_map:
        return class_to_app_map[app_class]

    guessed_app_id = f"{app_class.lower()}.desktop"
    if os.path.exists(f"/usr/share/applications/{guessed_app_id}"):
        return guessed_app_id

    return None

def running_apps_list(monitor_id: int) -> Widget.Box:
    return Widget.Box(
        spacing=5,
        child=Utils.Poll(
            timeout=1200,
            callback=lambda _: [
                Widget.Button(
                    css_classes=["app-item"],
                    on_click=lambda x, client_id=client["address"], workspace_id=client["workspace"]["id"]: (
                        hyprland.switch_to_workspace(workspace_id),
                    ),
                    child=Widget.Box(
                        child=[
                            Widget.Label(
                                css_classes=["workspace-id-label"],
                                label=f"{client['workspace']['id']}",
                                style="font-size: 10px;",
                                justify='left'
                            ),
                            Widget.Icon(
                                image=get_app_icon(client.get("class", "")),
                                css_classes=["app-item-icon"],
                                pixel_size=20,
                            ),
                            Widget.Label(
                                css_classes=["app-item-label"],
                                label=client.get("title", ""),
                                ellipsize="end",
                                max_width_chars=20,
                            ),
                        ],
                    ),
                )
                for client in get_all_clients(monitor_id)
            ] or [Widget.Label(label="No applications running")],
        ).bind("output"),
    )

def clock() -> Widget.Label:
    return Widget.Label(
        css_classes=["clock"],
        label=Utils.Poll(
            1, lambda self: datetime.datetime.now().strftime("%h %d %H:%M")
        ).bind("output"),
    )

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

    Utils.Poll(5, lambda _: update_button_status(button))

    return button

def update_button_status(widget):
    if read_state():
        widget.child.label = ""
    else:
        widget.child.label = ""

def left(monitor_id: int = 0) -> Widget.Box:
    return Widget.Box(
        child=[
            launcher_button(),
            workspaces(monitor_id),
            workspace_add_button(),
            pinned_apps(),
            running_apps_list(monitor_id)
        ],
        spacing=10,
    )

def center() -> Widget.Box:
    return Widget.Box(
        child=[
           
        ],
        spacing=10,
    )

def right() -> Widget.Box:
    return Widget.Box(
        child=[tray(), vpn_button(), kb_layout(), control_center_button(), speaker_volume(audio.speaker), speaker_slider(), clock()], spacing=10
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
            center_widget=center(),
            end_widget=right(),
        ),
    )