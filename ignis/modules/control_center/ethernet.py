from typing import List
from ignis.widgets import Widget
from ignis.utils import Utils
from .qs_button import QSButton
from ignis.services.network import NetworkService, EthernetDevice

import asyncio

network = NetworkService.get_default()

class EthernetConnectionItem(Widget.Button):
    def __init__(self, device: EthernetDevice):
        super().__init__(
            css_classes=["ethernet-connection-item"],
            on_click=lambda x: asyncio.create_task(device.disconnect_from())
            if device.is_connected
            else asyncio.create_task(device.connect_to()),
            child=Widget.Box(
                child=[
                    Widget.Icon(image="network-wired-symbolic"),
                    Widget.Label(
                        label=device.name,
                        ellipsize="end",
                        max_width_chars=20,
                        halign="start",
                        css_classes=["ethernet-connection-label"],
                    ),
                    Widget.Button(
                        child=Widget.Label(
                            label=device.bind(
                                "is_connected",
                                lambda value: "Disconnect" if value else "Connect",
                            )
                        ),
                        css_classes=["ethernet-connection-item-connect-label"],
                        halign="end",
                        hexpand=True,
                    ),
                ]
            ),
        )


def ethernet_control() -> List[QSButton]:
    networks_list = Widget.Revealer(
        transition_duration=300,
        transition_type="slide_down",
        child=Widget.Box(
            vertical=True,
            css_classes=["ethernet-network-list"],
            child=[
                Widget.Box(
                    css_classes=["ethernet-header-box"],
                    child=[
                        Widget.Icon(icon_name="network-wired-symbolic", pixel_size=28),
                        Widget.Label(
                            label="Wired connections",
                            css_classes=["ethernet-header-label"],
                        ),
                    ],
                ),
                Widget.Box(
                    vertical=True,
                    child=network.ethernet.bind(
                        "devices",
                        lambda value: [EthernetConnectionItem(i) for i in value],
                    ),
                ),
                Widget.Button(
                    css_classes=["ethernet-connection-item"],
                    style="margin-bottom: 0;",
                    on_click=lambda x: asyncio.create_task(Utils.exec_sh_async("nm-connection-editor")),
                    child=Widget.Box(
                        child=[
                            Widget.Icon(image="preferences-system-symbolic"),
                            Widget.Label(
                                label="Network Settings",
                                halign="start",
                                css_classes=["ethernet-connection-label"],
                            ),
                        ]
                    ),
                ),
            ],
        ),
    )

    if len(network.ethernet.devices) > 0:
        return [
            QSButton(
                label="Wired",
                icon_name="network-wired-symbolic",
                on_activate=lambda x: networks_list.toggle(),
                on_deactivate=lambda x: networks_list.toggle(),
                content=networks_list,
                active=network.ethernet.bind("is_connected"),
            )
        ]
    else:
        return []
