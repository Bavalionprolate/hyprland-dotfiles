import os
import json
import logging
import socket
from threading import Thread
from gi.repository import GLib, Gio, Gtk, GObject, Gdk
from ignis.widgets import Widget
from ignis.services.applications import ApplicationsService
from ignis.services.options import OptionsService
from ignis.services.hyprland import HyprlandService
from ignis.exceptions import HyprlandIPCNotFoundError
from ignis.utils import Utils
from .app_item import AppItem
from .utils import focus_window, close_window

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
hyprland = HyprlandService.get_default()
applications_service = ApplicationsService.get_default()

class DockManager:
    def __init__(self, monitor_id: int = 0):
        self.monitor_id = monitor_id
        self.apps_list = Widget.Box(spacing=10)
        self.is_listening = False
        self.app_buttons = []
        self.is_hidden = False
        self.dock_window = None
        self.is_auto_hide_enabled = True
        self.mouse_in_activation_zone = False
        self.cursor_check_timer = None
        self.launcher_menu = None
        applications_service.connect("notify::pinned", lambda x, y: self.refresh_apps_list())

        self.start_cursor_check_timer()

    def start_cursor_check_timer(self):
        if self.cursor_check_timer:
            return

        def check_cursor_position():
            if not self.is_auto_hide_enabled or not self.dock_window:
                return True

            dock_geo = self.get_dock_geometry()
            if not dock_geo:
                return True

            cursor_pos = self.get_cursor_position()
            if not cursor_pos:
                return True

            # Определяем зону активации (над доком)
            activation_zone = {
                "x": dock_geo["x"],
                "y": dock_geo["y"] - 20,  # 20px выше дока
                "w": dock_geo["w"],
                "h": 20
            }

            # Проверяем положение курсора
            is_cursor_in_activation_zone = (
                activation_zone["x"] <= cursor_pos["x"] <= activation_zone["x"] + activation_zone["w"] and
                activation_zone["y"] <= cursor_pos["y"] <= activation_zone["y"] + activation_zone["h"]
            )

            is_cursor_in_dock = (
                dock_geo["x"] <= cursor_pos["x"] <= dock_geo["x"] + dock_geo["w"] and
                dock_geo["y"] <= cursor_pos["y"] <= dock_geo["y"] + dock_geo["h"]
            )

            old_state = self.mouse_in_activation_zone
            self.mouse_in_activation_zone = is_cursor_in_activation_zone or is_cursor_in_dock

            if old_state != self.mouse_in_activation_zone:
                if self.mouse_in_activation_zone and self.is_hidden:
                    self.show_dock()
                elif not self.mouse_in_activation_zone and not self.is_hidden:
                    self.check_window_overlap()

            return True

        self.cursor_check_timer = GLib.timeout_add(100, check_cursor_position)

    def set_dock_window(self, window):
        self.dock_window = window

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
        except Exception:
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
            button.remove_css_class("dragging")
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

    def get_dock_geometry(self):
        try:
            layers = json.loads(hyprland.send_command("j/layers"))
            monitor_name = self.get_monitor_name(self.monitor_id)
            if not monitor_name or monitor_name not in layers:
                logging.error(f"Монитор {monitor_name} не найден в списке слоев")
                return None

            for level in layers[monitor_name]["levels"].values():
                for layer in level:
                    if layer.get("namespace") == f"ignis_dock_{self.monitor_id}":
                        return {
                            "x": layer["x"],
                            "y": layer["y"],
                            "w": layer["w"],
                            "h": layer["h"]
                        }
            return None
        except Exception as e:
            logging.error(f"Ошибка при получении геометрии дока: {e}")
            return None

    def get_monitor_name(self, monitor_id):
        try:
            monitors = json.loads(hyprland.send_command("j/monitors"))
            for monitor in monitors:
                if monitor.get("id") == monitor_id:
                    return monitor.get("name")
            return None
        except Exception as e:
            logging.error(f"Ошибка при получении имени монитора: {e}")
            return None

    def is_menu_open(self):
        for button in self.app_buttons:
            if button.menu and button.menu.get_visible():
                return True
        if self.launcher_button and self.launcher_button.menu.get_visible():
            return True
        return False

    def check_window_overlap(self):
        if not self.is_auto_hide_enabled or not self.dock_window:
            return

        if self.mouse_in_activation_zone or self.is_menu_open():
            if self.is_hidden:
                self.show_dock()
            return

        dock_geo = self.get_dock_geometry()
        if not dock_geo:
            return

        current_workspace = hyprland.active_workspace["id"] if hasattr(hyprland, "active_workspace") else None
        clients = self.get_all_clients(self.monitor_id)

        # Проверяем перекрытие дока окнами, учитывая рабочий стол
        windows_overlap = False
        for client in clients:
            if not client.get("mapped") or client.get("hidden"):
                continue

            if current_workspace is not None and client.get("workspace", {}).get("id") != current_workspace:
                continue

            # Проверяем перекрытие
            if self.rectangles_overlap(
                dock_geo["x"], dock_geo["y"], dock_geo["w"], dock_geo["h"],
                client["at"][0], client["at"][1], client["size"][0], client["size"][1]
            ):
                windows_overlap = True
                break

        if windows_overlap and not self.is_hidden:
            self.hide_dock()

        elif not windows_overlap and self.is_hidden:
            self.show_dock()

    def get_cursor_position(self):
        try:
            cursor_pos = json.loads(hyprland.send_command("j/cursorpos"))
            return cursor_pos
        except Exception as e:
            logging.error(f"Ошибка при получении позиции курсора: {e}")
            return None

    def rectangles_overlap(self, x1, y1, w1, h1, x2, y2, w2, h2):
        return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)

    def hide_dock(self):
        self.is_hidden = True
        self.dock_window.revealer.reveal_child = False
        logging.info("Док скрыт")

    def show_dock(self):
        self.is_hidden = False
        self.dock_window.revealer.reveal_child = True
        logging.info("Док показан")

    def toggle_auto_hide(self):
        self.is_auto_hide_enabled = not self.is_auto_hide_enabled

        if self.is_auto_hide_enabled:
            self.start_cursor_check_timer()
            self.check_window_overlap()
        else:
            if self.is_hidden:
                self.show_dock()

        logging.info(f"Автоскрытие дока {'включено' if self.is_auto_hide_enabled else 'выключено'}")

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

        if event_type in ["openwindow", "closewindow", "movewindow"]:
            logging.info(f"Получено событие: {event_type} с данными: {event_payload}")
            GLib.idle_add(self.refresh_apps_list)

        elif event_type in ["movewindow", "changefloatingmode", "fullscreen", "workspace", "activewindow"]:
            logging.info(f"Получено событие изменения окна/рабочего стола: {event_type}")
            GLib.idle_add(self.check_window_overlap)

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
