from ignis.widgets import Widget
from ignis.utils import Utils
from .qs_button import QSButton
from typing import List
from gi.repository import GLib
import logging
import asyncio

try:
    from ignis.services.bluetooth import BluetoothService, BluetoothDevice
    bluetooth = BluetoothService.get_default()
    BLUETOOTH_AVAILABLE = True
    logging.info("Bluetooth service initialized successfully")
except Exception as e:
    logging.warning(f"Bluetooth service is not available: {str(e)}")
    BLUETOOTH_AVAILABLE = False
    bluetooth = None

class BluetoothHeader(Widget.Box):
    def __init__(self, bluetooth_service):
        super().__init__(
            css_classes=["bluetooth-header-box"],
            child=[
                Widget.Label(
                    label="Bluetooth",
                    css_classes=["bluetooth-header-label"]
                ),
                Widget.Switch(
                    halign="end",
                    hexpand=True,
                    active=bluetooth_service.bind("powered"),
                    on_change=lambda x, state: setattr(
                        bluetooth_service, "powered", state
                    ),
                    css_classes=["control-center-switch"]
                ),
            ]
        )

class BluetoothDeviceItem(Widget.Button):
    def __init__(self, device: BluetoothDevice):
        self.device = device
        self.connect_attempts = 0
        self.max_connect_attempts = 3
        self.is_connecting = False

        # Создаем и сохраняем battery_icon как атрибут класса
        self.battery_icon = Widget.Icon(
            image=self._get_battery_icon(),
            visible=device.bind(
                "battery_percentage",
                transform=lambda value: value > 0
            )
        )

        battery_label = Widget.Label(
            label=device.bind(
                "battery_percentage",
                transform=lambda value: f"{int(value)}%" if value > 0 else ""
            ),
            visible=device.bind(
                "battery_percentage",
                transform=lambda value: value > 0
            )
        )

        super().__init__(
            css_classes=["bluetooth-device-item"],
            on_click=lambda x: self.handle_connection(),
            child=Widget.Box(
                spacing=5,
                child=[
                    Widget.Icon(
                        image=self._get_device_icon(),
                    ),
                    Widget.Label(
                        label=device.alias,
                        halign="start",
                        css_classes=["bluetooth-device-label"],
                    ),
                    Widget.Box(
                        halign="end",
                        hexpand=True,
                        spacing=5,
                        child=[
                            self.battery_icon,  # Используем сохраненный battery_icon
                            battery_label,
                            Widget.Icon(
                                image="object-select-symbolic",
                                visible=device.bind("connected"),
                            ),
                        ]
                    )
                ]
            ),
        )

        self.menu = self._build_menu()
        self.child.append(self.menu)

        device.connect("notify::connected", self.on_connection_changed)
        device.connect("notify::battery-percentage", self._update_battery)


    def _get_battery_icon(self):
        percentage = self.device.battery_percentage
        if percentage <= 0:
            return None
        elif percentage <= 20:
            return "battery-level-20-symbolic"
        elif percentage <= 40:
            return "battery-level-40-symbolic"
        elif percentage <= 60:
            return "battery-level-60-symbolic"
        elif percentage <= 80:
            return "battery-level-80-symbolic"
        else:
            return "battery-level-100-symbolic"

    def _get_device_icon(self):
        if self.device.device_type == "mouse":
            return "input-mouse-symbolic"
        elif self.device.device_type == "keyboard":
            return "input-keyboard-symbolic"
        elif self.device.device_type == "headset":
            return "audio-headset-symbolic"
        return self.device.icon_name or "bluetooth-symbolic"

    def handle_connection(self):
        if self.is_connecting:
            return
        if self.device.connected:
            self.disconnect_device()
        else:
            self.connect_device()

    def connect_device(self):
        self.connect_attempts = 0
        self.is_connecting = True
        self._update_connection_state()
        self.try_connect()

    def disconnect_device(self):
        try:
            asyncio.create_task(self.device.disconnect_from())
        except Exception as e:
            logging.error(f"Error disconnecting from {self.device.alias}: {str(e)}")
            self._show_error_notification(f"Failed to disconnect: {str(e)}")

    def try_connect(self):
        if self.connect_attempts >= self.max_connect_attempts:
            self.is_connecting = False
            self._update_connection_state()
            self._show_error_notification()
            return

        try:
            asyncio.create_task(self.device.connect_to())
            self.connect_attempts += 1
            GLib.timeout_add(2000, self.check_connection)
        except Exception as e:
            logging.error(f"Error connecting to {self.device.alias}: {str(e)}")
            self.is_connecting = False
            self._update_connection_state()
            self._show_error_notification(str(e))

    def check_connection(self):
        if not self.device.connected and self.connect_attempts < self.max_connect_attempts:
            logging.info(f"Retrying connection to {self.device.alias} (attempt {self.connect_attempts + 1})")
            self.try_connect()
        return False

    def _update_connection_state(self):
        if self.is_connecting:
            self.add_css_class("connecting")
        else:
            self.remove_css_class("connecting")

    def _show_error_notification(self, error_msg=None):
        msg = f"Failed to connect to {self.device.alias}"
        if error_msg:
            msg += f": {error_msg}"
        logging.error(msg)
        # TODO: Implement system notification if needed

    def on_connection_changed(self, device, param):
        if device.connected:
            logging.info(f"Successfully connected to {device.alias}")
            self.connect_attempts = 0
            self.is_connecting = False
            self._update_connection_state()
        else:
            logging.info(f"Disconnected from {device.alias}")
            self.is_connecting = False
            self._update_connection_state()

    def _update_battery(self, device, param):
        # Update battery icon when battery level changes
        icon = self._get_battery_icon()
        if icon:
            self.battery_icon.image = icon

    def _build_menu(self) -> Widget.PopoverMenu:
        menu_items = [
            Widget.MenuItem(
                label="Connect" if not self.device.connected else "Disconnect",
                on_activate=lambda x: self.handle_connection()
            )
        ]

        if self.device.paired:
            menu_items.append(
                Widget.MenuItem(
                    label="Unpair",
                    on_activate=lambda x: self._unpair_device()
                )
            )

            menu_items.append(
                Widget.MenuItem(
                    label="Trust" if not self.device.trusted else "Untrust",
                    on_activate=lambda x: self._toggle_trust()
                )
            )

        return Widget.PopoverMenu(items=menu_items)

    def _unpair_device(self):
        logging.info(f"Unpairing device {self.device.alias}")
        # TODO: Implement unpairing functionality when available in BluetoothService

    def _toggle_trust(self):
        logging.info(f"Toggling trust for device {self.device.alias}")
        # TODO: Implement trust toggling functionality when available in BluetoothService

def bluetooth_qsbutton() -> QSButton:
    devices_list = Widget.Revealer(
        transition_duration=300,
        transition_type="slide_down",
        child=Widget.Box(
            vertical=True,
            css_classes=["bluetooth-device-list"],
            child=[
                BluetoothHeader(bluetooth),
                Widget.Box(
                    vertical=True,
                    child=bluetooth.bind(
                        "devices",
                        transform=lambda value: [BluetoothDeviceItem(i) for i in value],
                    ),
                ),
                Widget.Button(
                    css_classes=["bluetooth-device-item"],
                    style="margin-bottom: 0;",
                    on_click=lambda x: asyncio.create_task(Utils.exec_sh_async("blueman-manager")),
                    child=Widget.Box(
                        child=[
                            Widget.Icon(image="preferences-system-symbolic"),
                            Widget.Label(
                                label="Bluetooth Settings",
                                halign="start",
                                css_classes=["bluetooth-device-label"],
                            ),
                        ]
                    ),
                ),
            ],
        ),
    )

    def truncate_name(name: str) -> str:
        if len(name) > 10:
            return f"{name[:10]}..."
        return name

    def get_label(devices: List) -> str:
        if not bluetooth.powered:
            return "Bluetooth"

        connected_devices = [dev for dev in devices if dev.connected]
        if len(connected_devices) == 0:
            return "Not Connected"
        elif len(connected_devices) == 1:
            return truncate_name(connected_devices[0].alias)
        else:
            return f"{len(connected_devices)} Connected"

    def get_icon(powered: bool) -> str:
        return "bluetooth-active-symbolic" if powered else "bluetooth-disabled-symbolic"

    def toggle_list(x) -> None:
        devices_list.toggle()
        GLib.timeout_add(devices_list.transition_duration, lambda: set_discovery_mode(devices_list.reveal_child))

    def set_discovery_mode(active: bool) -> bool:
        if bluetooth.powered:
            bluetooth.setup_mode = active
        return False

    # Создаем кнопку
    button = QSButton(
        label=bluetooth.bind("devices", get_label),
        icon_name=bluetooth.bind("powered", get_icon),
        on_activate=toggle_list,
        on_deactivate=toggle_list,
        active=bluetooth.bind("powered"),
        content=devices_list,
    )

    def update_button_state(*args):
        GLib.idle_add(lambda: button.set_property("label", get_label(bluetooth.devices)))

    def setup_device_monitoring(device):
        device.connect("notify::connected", update_button_state)

    def on_device_added(service, device):
        setup_device_monitoring(device)
        update_button_state()

    def on_device_removed(*args):
        update_button_state()

    bluetooth.connect("device-added", on_device_added)
    bluetooth.connect("notify::devices", on_device_removed)

    for device in bluetooth.devices:
        setup_device_monitoring(device)

    bluetooth.connect("notify::powered", update_button_state)

    devices_list.connect("notify::reveal-child",
        lambda x, y: set_discovery_mode(x.reveal_child))

    return button


def bluetooth_control() -> List[QSButton]:
    if not BLUETOOTH_AVAILABLE:
        logging.warning("Bluetooth is not available, returning empty list")
        return []

    return [bluetooth_qsbutton()]
