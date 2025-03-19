import os
import json
import logging
import socket
from gi.repository import GLib, Gio, Gtk, GObject, Gdk
from threading import Thread
from ignis.widgets import Widget
from ignis.services.applications import ApplicationsService
from ignis.services.options import OptionsService
from ignis.services.hyprland import HyprlandService
from ignis.exceptions import HyprlandIPCNotFoundError
from ignis.utils import Utils

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
hyprland = HyprlandService.get_default()
applications_service = ApplicationsService.get_default()
pixel_size_app = 45

class DockManager:
    def __init__(self, monitor_id: int = 0):
        self.monitor_id = monitor_id
        self.apps_list = Widget.Box(spacing=10)
        self.is_listening = False
        self.app_buttons = []
        applications_service.connect("notify::pinned", lambda x, y: self.refresh_apps_list())

    def get_pinned_apps_with_order(self) -> list["Application"]:
        options_service = OptionsService.get_default()
        apps_group = options_service.get_group("applications")
        pinned_apps_ids = apps_group.data.get("pinned_apps", [])
        app_dict = {app.id.lower(): app for app in applications_service.apps}
        pinned_apps = []
        for app_id in pinned_apps_ids:
            if app_id.lower() in app_dict:
                pinned_apps.append(app_dict[app_id.lower()])
        return pinned_apps

    def refresh_apps_list(self):
        logging.info(f"Обновление списка приложений для монитора {self.monitor_id}...")
        running_clients = self.get_all_clients(self.monitor_id)
        running_apps = {}
        for client in running_clients:
            app_class = client.get("class", "").lower()
            if app_class not in running_apps:
                running_apps[app_class] = []
            running_apps[app_class].append(client)
        pinned_apps = self.get_pinned_apps_with_order()
        self.app_buttons = []

        for app in pinned_apps:
            app_id = app.id.lower()
            instances = running_apps.get(app_id, [])
            self.app_buttons.append(
                AppItem(app, instances, is_pinned=True, dock_manager=self)
            )

        for app_class, instances in running_apps.items():
            if app_class not in {app.id.lower() for app in pinned_apps}:
                app = self.find_application_by_class(app_class)
                if app:
                    self.app_buttons.append(
                        AppItem(app, instances, is_pinned=False, dock_manager=self)
                    )
        GLib.idle_add(self._update_gui)

    def swap_apps(self, from_index, to_index):
        pinned_count = sum(1 for btn in self.app_buttons if btn.is_pinned)
        # Блокируем перемещение через разделитель
        if (from_index < pinned_count and to_index >= pinned_count) or \
           (from_index >= pinned_count and to_index < pinned_count):
            logging.warning("Нельзя перемещать элементы через разделитель!")
            return

        if from_index < 0 or to_index < 0 or \
           from_index >= len(self.app_buttons) or to_index >= len(self.app_buttons):
            return

        app_button = self.app_buttons.pop(from_index)
        self.app_buttons.insert(to_index, app_button)
        # Обновляем порядок закрепленных приложений
        if app_button.is_pinned:
            new_order = [btn.app.id for btn in self.app_buttons if btn.is_pinned]
            self.update_pinned_order(new_order)
        self._update_gui()

    def update_pinned_order(self, new_order):
        options_service = OptionsService.get_default()
        apps_group = options_service.get_group("applications")
        try:
            option = apps_group.create_option("pinned_apps", default=new_order, exists_ok=True)
            option.value = new_order
        except OptionExistsError:
            option = apps_group.get_option("pinned_apps")
            option.value = new_order
        logging.info(f"Обновлен порядок закрепленных приложений: {new_order}")

    def _update_gui(self):
        for child in self.apps_list.get_child():
            if hasattr(child, "unparent"):
                child.unparent()

        pinned_count = sum(1 for btn in self.app_buttons if btn.is_pinned)
        active_count = len(self.app_buttons) - pinned_count

        for button in self.app_buttons[:pinned_count]:
            self.apps_list.append(button)

        if pinned_count > 0 and active_count > 0:
            separator = Widget.Separator()
            separator.set_orientation(Gtk.Orientation.VERTICAL)
            separator.add_css_class("dock-separator")
            self.apps_list.append(separator)

        for button in self.app_buttons[pinned_count:]:
            self.apps_list.append(button)

        for button in self.app_buttons:
            button.remove_css_class("drop-target")
            button.remove_css_class("drop-prohibited")
        logging.info(f"Обновлен список приложений: {len(self.app_buttons)} элементов")

    def get_all_clients(self, monitor_id: int) -> list[dict]:
        if not hyprland.is_available:
            logging.error("Hyprland недоступен")
            return []
        try:
            clients = json.loads(hyprland.send_command("j/clients"))
        except Exception as e:
            logging.error(f"Ошибка при получении клиентов Hyprland: {e}")
            return []
        filtered_clients = [
            client
            for client in clients
            if (
                client["title"]
                and client["workspace"]
                and not client["class"].startswith("conkyc")
                and client["monitor"] == monitor_id
            )
        ]
        return filtered_clients

    def listen_for_events(self):
        if self.is_listening:
            logging.warning("Слушатель событий уже запущен.")
            return
        self.is_listening = True
        def event_listener():
            socket_path = self.find_hyprland_socket()
            if not socket_path:
                logging.error("Не удалось найти сокет Hyprland.")
                return
            buffer = ""
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                try:
                    sock.connect(socket_path)
                    logging.info(f"Успешно подключились к сокету: {socket_path}")
                    while True:
                        data = sock.recv(4096).decode("utf-8").strip()
                        if not data:
                            continue
                        buffer += data
                        while ">>" in buffer:
                            idx = buffer.find(">>")
                            event_type = buffer[:idx]
                            remaining = buffer[idx + 2:]
                            newline_idx = remaining.find("\n")
                            if newline_idx != -1:
                                event_payload = remaining[:newline_idx]
                                buffer = remaining[newline_idx + 1:]
                            else:
                                event_payload = remaining
                                buffer = ""
                            self.handle_event(f"{event_type}>>{event_payload}")
                except ConnectionRefusedError:
                    logging.error(f"Не удалось подключиться к сокету {socket_path}.")
        thread = Thread(target=event_listener, daemon=True)
        thread.start()

    def handle_event(self, event_data):
        parts = event_data.split(">>", 1)
        if len(parts) < 2:
            return
        event_type, event_payload = parts[0], parts[1]
        interesting_events = ["openwindow", "closewindow", "activewindow"]
        if event_type in interesting_events:
            logging.info(f"Получено событие: {event_type} с данными: {event_payload}")
            GLib.idle_add(self.refresh_apps_list)

    def find_hyprland_socket(self):
        xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
        if not xdg_runtime_dir or not os.path.exists(xdg_runtime_dir):
            logging.error(f"Переменная среды XDG_RUNTIME_DIR не установлена или недоступна: {xdg_runtime_dir}")
            return None
        hyprland_dir = os.path.join(xdg_runtime_dir, "hypr")
        if not os.path.exists(hyprland_dir):
            logging.error(f"Директория {hyprland_dir} не существует.")
            return None
        instances = [f for f in os.listdir(hyprland_dir) if os.path.isdir(os.path.join(hyprland_dir, f))]
        if not instances:
            logging.error(f"Не найдено ни одного экземпляра Hyprland в {hyprland_dir}.")
            return None
        instance_signature = instances[0]
        socket_path = os.path.join(hyprland_dir, instance_signature, ".socket2.sock")
        if not os.path.exists(socket_path):
            logging.error(f"Сокет {socket_path} не существует.")
            return None
        logging.info(f"Найден сокет Hyprland: {socket_path}")
        return socket_path

    def find_application_by_class(self, app_class: str) -> "Application | None":
        for app in applications_service.apps:
            if app.id.lower().startswith(app_class):
                return app
        return None

class AppItem(Widget.Button):
    def __init__(
        self,
        app: "Application",
        instances: list[dict],
        is_pinned: bool,
        dock_manager: DockManager
    ):
        self.app = app
        self.instances = instances
        self.dock_manager = dock_manager
        self.is_pinned = is_pinned
        icon = app.icon
        indicator = (
            Widget.Label(label=".", css_classes=["app-item-indicator-start"])
            if instances
            else Widget.Label(label="", css_classes=["app-item-indicator-start"])
        )
        self.menu = self._build_menu()
        self.app.connect("pinned", lambda _: self._sync_menu())
        self.app.connect("unpinned", lambda _: self._sync_menu())
        super().__init__(
            child=Widget.Box(
                child=[
                    Widget.Icon(
                        image=icon,
                        pixel_size=pixel_size_app,
                        css_classes=["app-item-dock-button"],
                    ),
                    indicator,
                    self.menu,
                ],
                vertical=True,
            ),
            on_click=lambda x: self.handle_click(),
            on_right_click=lambda x: self.menu.popup(),
            css_classes=["app-item-dock"],
        )
        self.drag_source = Gtk.DragSource.new()
        self.drag_source.set_actions(Gdk.DragAction.MOVE)
        self.drag_source.connect("prepare", self.on_drag_prepare)
        self.drag_source.connect("begin", self.on_drag_begin)
        self.drag_source.connect("end", self.on_drag_end)
        self.drag_source.connect("cancel", self.on_drag_cancel)
        self.add_controller(self.drag_source)

        self.drop_target = Gtk.DropTarget.new(GObject.TYPE_PYOBJECT, Gdk.DragAction.MOVE)
        self.drop_target.connect("enter", self.on_drop_target_enter)
        self.drop_target.connect("leave", self.on_drop_target_leave)
        self.drop_target.connect("drop", self.on_drop)
        self.add_controller(self.drop_target)

    def handle_click(self):
        if self.instances:
            address = self.instances[0]["address"]
            logging.info(f"Фокусировка на окне приложения {self.app.id} с адресом {address}.")
            focus_window(address)
        else:
            logging.info(f"Запуск приложения {self.app.id}.")
            self.app.launch()

    def on_drop_target_enter(self, drop_target, x, y):
        self.add_css_class("drop-target")
        current_index = self.dock_manager.app_buttons.index(self)

        value = drop_target.get_value()
        dragged_index = value.get("index", -1) if value else -1
        pinned_count = sum(1 for btn in self.dock_manager.app_buttons if btn.is_pinned)
        if (dragged_index < pinned_count and current_index >= pinned_count) or \
           (dragged_index >= pinned_count and current_index < pinned_count):
            self.add_css_class("drop-prohibited")
        else:
            self.add_css_class("drop-target")

    def on_drop_target_leave(self, drop_target):
        self.remove_css_class("drop-target")
        self.remove_css_class("drop-prohibited")


    def on_drag_prepare(self, drag_source, x, y):
        return Gdk.ContentProvider.new_for_value({
            "index": self.dock_manager.app_buttons.index(self),
            "app_id": self.app.id,
        })

    def on_drag_begin(self, drag_source, gesture):
        self.show()

    def on_drag_end(self, drag_source, drag):
        self.show()

    def on_drag_cancel(self, drag_source, _):
        self.show()

    def on_drop(self, drop_target, value, x, y):
        dragged_index = value["index"]
        target_index = self.dock_manager.app_buttons.index(self)
        if 0 <= dragged_index < len(self.dock_manager.app_buttons) and \
           0 <= target_index < len(self.dock_manager.app_buttons):
            self.dock_manager.swap_apps(dragged_index, target_index)
        return True

    def _build_menu(self) -> Widget.PopoverMenu:
        menu_items = [
            Widget.MenuItem(
                label="Launch",
                on_activate=lambda x: self.app.launch(),
            )
        ]
        for action in self.app.actions:
            menu_items.append(
                Widget.MenuItem(
                    label=action.name,
                    on_activate=lambda x, act=action: act.launch(),
                )
            )
        if self.instances:
            menu_items.append(Widget.Separator())
        for instance in self.instances:
            menu_items.append(
                Widget.MenuItem(
                    label=instance.get("title", "Unknown"),
                    on_activate=lambda x, addr=instance["address"]: focus_window(addr),
                )
            )
        menu_items.append(Widget.Separator())
        if self.app.is_pinned:
            menu_items.append(
                Widget.MenuItem(
                    label="󰤰 Unpin",
                    on_activate=lambda x: self.unpin_app(),
                )
            )
        else:
            menu_items.append(
                Widget.MenuItem(
                    label="󰤱 Pin",
                    on_activate=lambda x: self.pin_app(),
                )
            )
        for instance in self.instances:
            menu_items.append(
                Widget.MenuItem(
                    label=f"Close {instance.get('title', 'Unknown')}",
                    on_activate=lambda x, addr=instance["address"]: close_window(addr),
                )
            )
        if len(self.instances) > 1:
            menu_items.append(
                Widget.MenuItem(
                    label="Close All",
                    on_activate=lambda x: close_all_windows(self.app.id, self.dock_manager.monitor_id),
                )
            )
        return Widget.PopoverMenu(items=menu_items)

    def pin_app(self):
        self.app.pin()
        self.is_pinned = True
        self._sync_menu()

    def unpin_app(self):
        self.app.unpin()
        self.is_pinned = False
        self._sync_menu()

    def _sync_menu(self):
        if self.menu and self.menu.get_parent():
            self.menu.get_parent().remove(self.menu)
        self.menu = self._build_menu()
        if not self.menu.get_parent():
            self.child.append(self.menu)

def focus_window(address: str):
    Utils.exec_sh_async(f"hyprctl dispatch focuswindow address:{address}")

def close_window(address: str):
    Utils.exec_sh_async(f"hyprctl dispatch closewindow address:{address}")

def close_all_windows(app_id: str, monitor_id: int = 0):
    running_clients = dock_manager.get_all_clients(monitor_id)
    instances = [
        client
        for client in running_clients
        if client.get("class", "").lower() == app_id.lower()
    ]
    for instance in instances:
        address = instance["address"]
        logging.info(f"Закрытие окна приложения {app_id} с адресом {address}.")
        close_window(address)

def launcher_button() -> Widget.Box:
    return Widget.Button(
        css_classes=["launcher-button-dock"],
        on_click=lambda x: Utils.exec_sh_async("ignis toggle ignis_LAUNCHPAD"),
        child=Widget.Icon(image="slingscold", pixel_size=pixel_size_app),
    )

def dock(monitor_id: int = 0) -> Widget.Window:
    global dock_manager
    dock_manager = DockManager(monitor_id)
    dock_manager.listen_for_events()
    dock_manager.refresh_apps_list()
    return Widget.Window(
        namespace=f"ignis_dock_{monitor_id}",
        monitor=monitor_id,
        anchor=["bottom"],
        exclusivity="normal",
        child=Widget.CenterBox(
            css_classes=["dock"],
            start_widget=launcher_button(),
            center_widget=dock_manager.apps_list,
            end_widget=None,
        ),
    )
