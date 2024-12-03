import datetime
from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.services.audio import AudioService
from ignis.services.system_tray import SystemTrayService, SystemTrayItem
from ignis.services.hyprland import HyprlandService


audio = AudioService.get_default()
system_tray = SystemTrayService.get_default()
hyprland = HyprlandService.get_default()


def workspace_button(workspace: dict) -> Widget.Button:
    widget = Widget.Button(
        css_classes=["workspace"],
        on_click=lambda x, id=workspace["id"]: hyprland.switch_to_workspace(id),
        child=Widget.Label(label=str(workspace["id"])),
    )
    if workspace["id"] == hyprland.active_workspace["id"]:
        widget.add_css_class("active")

    return widget

def scroll_workspaces(direction: str) -> None:
    current = hyprland.active_workspace["id"]
    if direction == "up":
        target = current - 1
        hyprland.switch_to_workspace(target)
    else:
        target = current + 1
        if target == 11:
            return
        hyprland.switch_to_workspace(target)

def workspaces() -> Widget.EventBox:
    return Widget.EventBox(
        on_scroll_up=lambda x: scroll_workspaces("up"),
        on_scroll_down=lambda x: scroll_workspaces("down"),
        css_classes=["workspaces"],
        spacing=5,
        child=hyprland.bind(
            "workspaces",
            transform=lambda value: [workspace_button(i) for i in value],
        ),
    )

def client_title() -> Widget.Label:
    return Widget.Label(
        ellipsize="end",
        max_width_chars=40,
        label=hyprland.bind(
            "active_window",
            transform=lambda value: value.get(
                "title",
                ""
            ),
        ),
    )

def clock() -> Widget.Label:
    return Widget.Label(
        css_classes=["clock"],
        label=Utils.Poll(
            1, lambda self: datetime.datetime.now().strftime("%h %d %H:%M")
        ).bind("output"),
    )

def speaker_volume() -> Widget.Box:
    return Widget.Box(
        child=[
            Widget.Icon(
                image=audio.speaker.bind("icon_name"), style="margin-right: 5px;"
            ),
            Widget.Label(
                label=audio.speaker.bind("volume", transform=lambda value: str(value))
            ),
        ]
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
            audio.speaker.set_volume(x.value)
        ],
        css_classes=["volume-slider"],
    )

def left() -> Widget.Box:
    return Widget.Box(child=[workspaces(), client_title()], spacing=10)

def center() -> Widget.Box:
    return Widget.Box(
        child=[
           
        ],
        spacing=10,
    )

def right() -> Widget.Box:
    return Widget.Box(
        child=[tray(), speaker_volume(), speaker_slider(), clock()], spacing=10
    )

def bar(monitor_id: int = 0) -> Widget.Window:
    return Widget.Window(
        namespace=f"ignis_bar_{monitor_id}",
        monitor=monitor_id,
        anchor=["left", "top", "right"],
        exclusivity="exclusive",
        child=Widget.CenterBox(
            css_classes=["bar"],
            start_widget=left(),
            center_widget=center(),
            end_widget=right(),
        ),
    )