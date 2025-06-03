import os
from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.app import IgnisApp
from ignis.services.fetch import FetchService

fetch = FetchService.get_default()
app = IgnisApp.get_default()

def format_uptime(value):
    days, hours, minutes, seconds = value
    if days:
        return f"up {days:02} days {hours:02} hours, {minutes:02} minutes"
    else:
        return f"up {hours:02} hours, {minutes:02} minutes"

def username() -> Widget.Box:
    return Widget.Box(
        child=[
            Widget.Label(
                label=os.getenv("USER"),
                css_classes=["user-name"],
                halign="start"
            ),
            Widget.Label(
                label=Utils.Poll(
                    timeout=60 * 1000,
                    callback=lambda x: fetch.uptime
                ).bind("output", lambda value: format_uptime(value)),
                halign="start",
                css_classes=["user-name-secondary"],
            ),
        ],
        vertical=True,
        css_classes=["user-name-box"],
    )

def settings_button() -> Widget.Button:
    return Widget.Button(
        child=Widget.Icon(image="emblem-system-symbolic", pixel_size=23),
        halign="end",
        hexpand=True,
        css_classes=["user-settings"],
    )

def power_button() -> Widget.Button:
    return Widget.Button(
        child=Widget.Icon(image="system-shutdown-symbolic", pixel_size=23),
        halign="end",
        css_classes=["user-power"],
        on_click=lambda x: app.toggle_window("ignis_POWER"),
    )

def user() -> Widget.Box:
    return Widget.Box(
        child=[username(), settings_button(), power_button()],
        css_classes=["user"],
    )
