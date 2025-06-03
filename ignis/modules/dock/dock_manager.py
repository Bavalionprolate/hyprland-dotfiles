from threading import Thread
from gi.repository import GLib, Gtk
from ignis.widgets import Widget
from ignis.services.applications import ApplicationsService, Application
from ignis.services.hyprland import HyprlandService
from .app_item import AppItem
from options import settings
from typing import List, Dict, Optional

import os
import json
import logging
import socket

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DockManager:
    def __init__(self, monitor_id: int = 0):
        self.monitor_id = monitor_id
        self.apps_list = Widget.Box(spacing=10)
        self.app_buttons: List[AppItem] = []

        self.is_listening = False
        self.is_hidden = False
        self.dock_window = None
        self.overlap_window = None
        self.launcher_button = None

        self.is_auto_hide_enabled = settings.dock.auto_hide
        self.mouse_in_activation_zone = False
        self.cursor_check_timer = None

        self.hyprland = HyprlandService.get_default()
        self.applications = ApplicationsService.get_default()

        self._pinned_apps_cache = {}
        self._load_pinned_apps()

        self._setup_settings_handlers()
        self.start_cursor_check_timer()
        GLib.timeout_add(100, self._update_overlap_window_size)

    #Настройка обработчиков изменения настроек
    def _setup_settings_handlers(self):
        settings.dock.connect_option("auto_hide", self._on_auto_hide_changed)
        settings.dock.connect_option("icon_size", lambda: self.refresh_apps_list())
        settings.dock.connect_option("icon_padding", lambda: self.refresh_apps_list())
        settings.dock.connect_option("icon_border_radius", lambda: self.refresh_apps_list())

        self.applications.connect("notify::pinned", lambda x, y: self.refresh_apps_list())
        settings.apps.connect_option("pinned_apps", lambda: self.refresh_apps_list())

    #Загрузка кэша закрепленных приложений
    def _load_pinned_apps(self):
        self._pinned_apps_cache = {app_id.lower(): app_id for app_id in settings.apps.pinned_apps}

    #Установка основного окна дока и создание окна перекрытия
    def set_dock_window(self, window: Widget.Window):
        self.dock_window = window
        self.overlap_window = Widget.Window(
            namespace=f"ignis_dock_overlap_{self.monitor_id}",
            monitor=self.monitor_id,
            anchor=["bottom"],
            layer="background",
            exclusivity="normal",
            visible=True,
            style="border-bottom: 1px solid transparent;",
            default_width = 200,
            child=Widget.Box(css_classes=["dock-overlap-detector"]),
        )

    def get_monitor_name(self, monitor_id: int) -> Optional[str]:
        try:
            monitors = json.loads(self.hyprland.send_command("j/monitors"))
            for monitor in monitors:
                if monitor.get("id") == monitor_id:
                    return monitor.get("name")
            return None
        except Exception as e:
            logging.error(f"Ошибка при получении имени монитора: {e}")
            return None

    def pin_app(self, app_id: str) -> None:
        try:
            if settings.apps.pin_app(app_id):
                self._pinned_apps_cache[app_id.lower()] = app_id
                logging.info(f"Приложение закреплено: {app_id}")
                self.refresh_apps_list()
        except Exception as e:
            logging.error(f"Ошибка при закреплении приложения {app_id}: {e}")

    def unpin_app(self, app_id: str) -> None:
        try:
            if settings.apps.unpin_app(app_id):
                self._pinned_apps_cache.pop(app_id.lower(), None)
                logging.info(f"Приложение откреплено: {app_id}")
                self.refresh_apps_list()
        except Exception as e:
            logging.error(f"Ошибка при откреплении приложения {app_id}: {e}")

    def is_app_pinned(self, app_id: str) -> bool:
        return app_id.lower() in self._pinned_apps_cache

    #Получение списка закрепленных приложений с сохранением порядка
    def get_pinned_apps_with_order(self) -> List[Application]:
        pinned_apps_ids = settings.apps.pinned_apps
        app_dict = {app.id.lower(): app for app in self.applications.apps}
        return [app_dict[app_id.lower()]
                for app_id in pinned_apps_ids
                if app_id.lower() in app_dict]

    #Обновление списка приложений в доке
    def refresh_apps_list(self):
        self.app_buttons.clear()
        running_clients = self.get_all_clients(self.monitor_id)
        running_apps = {}
        seen_apps = set()

        for client in running_clients:
            app_class = client.get("class", "").lower()
            if app_class:
                if app_class not in running_apps:
                    running_apps[app_class] = []
                running_apps[app_class].append(client)

        for app in self.get_pinned_apps_with_order():
            app_id = app.id.lower()
            instances = running_apps.get(app_id, [])
            self.app_buttons.append(AppItem(app, instances, True, self))
            seen_apps.add(app_id)

        for app_class, instances in running_apps.items():
            if app_class not in seen_apps:
                app = self.find_application_by_class(app_class)
                if app:
                    self.app_buttons.append(AppItem(app, instances, False, self))
                    seen_apps.add(app_class)

        GLib.idle_add(self._update_gui)
        GLib.timeout_add(100, self._update_overlap_window_size)

    #Обновление размеров окна перекрытия
    def _update_overlap_window_size(self):
        if not self.dock_window or not self.overlap_window:
            return False

        try:
            layers = json.loads(self.hyprland.send_command("j/layers"))
            monitor_name = self.get_monitor_name(self.monitor_id)

            if monitor_name and monitor_name in layers:
                for level in layers[monitor_name]["levels"].values():
                    for layer in level:
                        if layer.get("namespace") == f"ignis_dock_{self.monitor_id}":
                            self.overlap_window.default_width = layer["w"]
                            self.overlap_window.default_height = layer["h"]
                            return False
        except Exception as e:
            logging.error(f"Ошибка при обновлении размеров окна перекрытия: {e}")

        return False

    def _update_gui(self):
        """Обновление GUI дока"""
        while child := self.apps_list.get_first_child():
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

        return False

    #Проверка перекрытия дока окнами и управление видимостью
    def check_window_overlap(self):
        """"""
        if not self.is_auto_hide_enabled or not self.dock_window or not self.overlap_window:
            return

        if self.mouse_in_activation_zone or self.is_menu_open():
            if self.is_hidden:
                self.show_dock()
            return

        overlap_geo = self.get_overlap_geometry()
        if not overlap_geo:
            return

        windows_overlap = self._check_windows_overlap(overlap_geo)

        if windows_overlap and not self.is_hidden:
            self.hide_dock()
        elif not windows_overlap and self.is_hidden:
            self.show_dock()

    #Проверка перекрытия окнами области дока
    def _check_windows_overlap(self, overlap_geo: Dict) -> bool:
        current_workspace = self.hyprland.active_workspace.id
        clients = self.get_all_clients(self.monitor_id)

        for client in clients:
            if not self._is_window_relevant(client, current_workspace):
                continue

            if self.rectangles_overlap(
                overlap_geo["x"], overlap_geo["y"],
                overlap_geo["w"], overlap_geo["h"],
                client["at"][0], client["at"][1],
                client["size"][0], client["size"][1]
            ):
                return True
        return False

    #Проверка актуальности окна для перекрытия
    def _is_window_relevant(self, client: Dict, current_workspace: int) -> bool:
        return not any([
            not client.get("mapped"),
            client.get("hidden"),
            client.get("monitor") != self.monitor_id,
            current_workspace is not None and
            client.get("workspace", {}).get("id") != current_workspace,
            client.get("floating") == 0
        ])

    def hide_dock(self):
        self.is_hidden = True
        self.dock_window.revealer.reveal_child = False

    def show_dock(self):
        self.is_hidden = False
        self.dock_window.revealer.reveal_child = True

    def toggle_auto_hide(self):
        settings.dock.auto_hide = not settings.dock.auto_hide
        self.is_auto_hide_enabled = settings.dock.auto_hide

        if self.is_auto_hide_enabled:
            self.start_cursor_check_timer()
            self.check_window_overlap()
        elif self.is_hidden:
            self.show_dock()

    #Изменения настройки автоскрытия
    def _on_auto_hide_changed(self):
        self.is_auto_hide_enabled = settings.dock.auto_hide
        if not self.is_auto_hide_enabled and self.is_hidden:
            self.show_dock()
        elif self.is_auto_hide_enabled:
            self.check_window_overlap()

    #Запуск таймера проверки положения курсора
    def start_cursor_check_timer(self):
        if not self.cursor_check_timer:
            self.cursor_check_timer = GLib.timeout_add(100, self._check_cursor_position)

    #Проверка положения курсора относительно дока
    def _check_cursor_position(self) -> bool:
        if not self.is_auto_hide_enabled or not self.dock_window:
            return True

        overlap_geo = self.get_overlap_geometry()
        cursor_pos = self.get_cursor_position()
        if not overlap_geo or not cursor_pos:
            return True

        dock_geo = self._get_dock_geometry()
        if not dock_geo:
            return True

        activation_zone = {
            "x": dock_geo["x"],
            "y": dock_geo["y"] - 5,
            "w": dock_geo["w"],
            "h": 5
        }

        is_cursor_in_activation_zone = self._is_point_in_rect(
            cursor_pos["x"], cursor_pos["y"],
            activation_zone
        )
        is_cursor_in_dock = self._is_point_in_rect(
            cursor_pos["x"], cursor_pos["y"],
            dock_geo
        )

        old_state = self.mouse_in_activation_zone
        self.mouse_in_activation_zone = is_cursor_in_activation_zone or is_cursor_in_dock

        if old_state != self.mouse_in_activation_zone:
            if self.mouse_in_activation_zone and self.is_hidden:
                self.show_dock()
            elif not self.mouse_in_activation_zone and not self.is_hidden:
                self.check_window_overlap()

        return True

    def rectangles_overlap(self, x1: int, y1: int, w1: int, h1: int,
                         x2: int, y2: int, w2: int, h2: int) -> bool:
        """Проверка перекрытия двух прямоугольников"""
        return not (x1 + w1 <= x2 or
                   x2 + w2 <= x1 or
                   y1 + h1 <= y2 or
                   y2 + h2 <= y1)

    def _is_point_in_rect(self, x: int, y: int, rect: Dict) -> bool:
        """Проверка попадания точки в прямоугольник"""
        return (rect["x"] <= x <= rect["x"] + rect["w"] and
                rect["y"] <= y <= rect["y"] + rect["h"])

    #Получение геометрии области перекрытия
    def get_overlap_geometry(self) -> Optional[Dict]:
        try:
            layers = json.loads(self.hyprland.send_command("j/layers"))
            monitor_name = self.get_monitor_name(self.monitor_id)
            if not monitor_name or monitor_name not in layers:
                return None

            for level in layers[monitor_name]["levels"].values():
                for layer in level:
                    if layer.get("namespace") == f"ignis_dock_overlap_{self.monitor_id}":
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

    def _get_dock_geometry(self) -> Optional[Dict]:
        try:
            layers = json.loads(self.hyprland.send_command("j/layers"))
            monitor_name = self.get_monitor_name(self.monitor_id)
            if monitor_name and monitor_name in layers:
                for level in layers[monitor_name]["levels"].values():
                    for layer in level:
                        if layer.get("namespace") == f"ignis_dock_{self.monitor_id}":
                            return {
                                "x": layer["x"],
                                "y": layer["y"],
                                "w": layer["w"],
                                "h": layer["h"]
                            }
        except Exception as e:
            logging.error(f"Ошибка при получении геометрии дока: {e}")
        return None

    def get_cursor_position(self) -> Optional[Dict]:
        try:
            return json.loads(self.hyprland.send_command("j/cursorpos"))
        except Exception as e:
            logging.error(f"Ошибка при получении позиции курсора: {e}")
            return None

    def get_all_clients(self, monitor_id: int) -> List[Dict]:
        if not self.hyprland.is_available:
            logging.error("Hyprland недоступен")
            return []

        try:
            clients = json.loads(self.hyprland.send_command("j/clients"))
            return [
                client for client in clients
                if (client["title"] and
                    client["workspace"] and
                    not client["class"].startswith("conkyc") and
                    client["monitor"] == monitor_id)
            ]
        except Exception as e:
            logging.error(f"Ошибка при получении клиентов Hyprland: {e}")
            return []

    def find_application_by_class(self, app_class: str) -> Optional[Application]:
        for app in self.applications.apps:
            if app.id.lower().startswith(app_class):
                return app
        return None

    #Запускает анимацию shake для кнопки в доке
    def shake_animation(self, button: "AppItem") -> None:
        button.add_css_class("shake")
        GLib.timeout_add(500, lambda: button.remove_css_class("shake"))

    #Меняет местами приложения в доке и обновляет порядок закрепленных приложений
    def swap_apps(self, source_index: int, target_index: int) -> None:
        #    source_index: Индекс перетаскиваемого приложения
        #    target_index: Индекс целевой позиции

        if not (0 <= source_index < len(self.app_buttons) and
                0 <= target_index < len(self.app_buttons)):
            return

        # Определяем диапазоны закрепленных и незакрепленных приложений
        pinned_count = sum(1 for btn in self.app_buttons if btn.is_pinned)

        # Проверяем, что перемещение происходит в пределах одной секции
        source_is_pinned = source_index < pinned_count
        target_is_pinned = target_index < pinned_count
        if source_is_pinned != target_is_pinned:
            self.shake_animation(self.app_buttons[source_index])
            return

        # Меняем местами кнопки
        self.app_buttons[source_index], self.app_buttons[target_index] = \
            self.app_buttons[target_index], self.app_buttons[source_index]

        # Если это закрепленные приложения, обновляем их порядок в настройках
        if source_is_pinned and target_is_pinned:
            new_pinned_order = [
                btn.app.id for btn in self.app_buttons[:pinned_count]
                if btn.is_pinned
            ]
            settings.apps.reorder_pinned_apps(new_pinned_order)

        # Обновляем GUI
        self._update_gui()

    def is_menu_open(self) -> bool:
        if any(button.menu and button.menu.get_visible() for button in self.app_buttons):
            return True
        return (self.launcher_button and self.launcher_button.menu.get_visible())

    #Запуск прослушивания событий Hyprland
    def listen_for_events(self):
        if self.is_listening:
            return

        self.is_listening = True
        thread = Thread(target=self._event_listener, daemon=True)
        thread.start()

    #Слушатель событий Hyprland
    def _event_listener(self):
        socket_path = self._find_hyprland_socket()
        if not socket_path:
            logging.error("Не удалось найти сокет Hyprland")
            return

        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect(socket_path)
                self._process_socket_events(sock)
        except Exception as e:
            logging.error(f"Ошибка при подключении к сокету: {e}")

    def _find_hyprland_socket(self) -> Optional[str]:
        xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
        if not xdg_runtime_dir or not os.path.exists(xdg_runtime_dir):
            logging.error("XDG_RUNTIME_DIR не установлен или недоступен")
            return None

        hyprland_dir = os.path.join(xdg_runtime_dir, "hypr")
        if not os.path.exists(hyprland_dir):
            logging.error(f"Директория {hyprland_dir} не существует")
            return None

        instances = [f for f in os.listdir(hyprland_dir)
                    if os.path.isdir(os.path.join(hyprland_dir, f))]
        if not instances:
            logging.error("Не найдено экземпляров Hyprland")
            return None

        socket_path = os.path.join(hyprland_dir, instances[0], ".socket2.sock")
        if not os.path.exists(socket_path):
            logging.error(f"Сокет {socket_path} не существует")
            return None

        return socket_path

    #Обработка событий из сокета
    def _process_socket_events(self, sock):
        buffer = ""
        while True:
            data = sock.recv(4096).decode("utf-8").strip()
            if not data:
                continue

            buffer += data
            while ">>" in buffer:
                event_data = self._parse_event_data(buffer)
                if not event_data:
                    break

                event_type, event_payload, remaining = event_data
                buffer = remaining
                self._handle_event(f"{event_type}>>{event_payload}")

    #Разбор данных события из буфера
    def _parse_event_data(self, buffer: str) -> Optional[tuple]:
        idx = buffer.find(">>")
        if idx == -1:
            return None

        event_type = buffer[:idx]
        remaining = buffer[idx + 2:]

        newline_idx = remaining.find("\n")
        if newline_idx != -1:
            event_payload = remaining[:newline_idx]
            remaining = remaining[newline_idx + 1:]
        else:
            event_payload = remaining
            remaining = ""

        return event_type, event_payload, remaining

    #Обработка события Hyprland
    def _handle_event(self, event_data: str):
        parts = event_data.split(">>", 1)
        if len(parts) < 2:
            return

        event_type, event_payload = parts
        if event_type in ["openwindow", "closewindow", "movewindow"]:
            if hasattr(self, '_refresh_timeout'):
                GLib.source_remove(self._refresh_timeout)
            self._refresh_timeout = GLib.timeout_add(100, self._delayed_refresh)

        GLib.idle_add(self.check_window_overlap)

    #Отложенное обновление списка приложений
    def _delayed_refresh(self) -> bool:
        self.refresh_apps_list()
        if hasattr(self, '_refresh_timeout'):
            delattr(self, '_refresh_timeout')
        return False
