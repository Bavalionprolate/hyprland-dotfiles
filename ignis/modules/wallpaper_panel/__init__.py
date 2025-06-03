from gi.repository import Gtk, GObject, Gdk, Gio
from ignis.widgets import Widget
from ignis.services.wallpaper import WallpaperService, WallpaperLayerWindow
from ignis.app import IgnisApp
from ignis.utils import Utils
from options import settings

import os
import threading, asyncio

app = IgnisApp.get_default()
wallpaper_service = WallpaperService.get_default()

class ScrollableBox(Widget.Scroll):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        event_controller = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.BOTH_AXES |
            Gtk.EventControllerScrollFlags.KINETIC
        )
        event_controller.connect("scroll", self.on_scroll)
        self.add_controller(event_controller)

    def on_scroll(self, controller, dx, dy):
        adj = self.get_hadjustment()
        new_value = adj.get_value() + (dy * 200)
        adj.set_value(new_value)
        return True

class LoadingIndicator(Widget.Box):
    def __init__(self):
        super().__init__(
            vertical=True,
            halign="center",
            spacing=5,
            css_classes=["loading-indicator"],
        )

        self.label = Widget.Label(
            label="",
            css_classes=["loading-label"],
        )

        self.child = [self.label]
        self.visible = False

    def start(self, message="", progress=0):
        self.visible = True
        self.label.label = f"Загрузка {progress}%"

    def stop(self):
        self.visible = False
        self.label.label = ""

class WallpaperPanel(Widget.Box):
    def __init__(self):
        super().__init__(
            vertical=True,
            css_classes=["wallpaper-panel"],
            spacing=10,
        )

        self.folder_button = Widget.Button(
            css_classes=["folder-button"],
            on_click=lambda x: self.choose_wallpaper_folder(),
            child=Widget.Box(
                child=[
                    Widget.Icon(image="folder-symbolic", pixel_size=20),
                    Widget.Label(label="Выбрать папку"),
                ],
                spacing=10,
            ),
        )

        self.loading_indicator = LoadingIndicator()

        self.wallpaper_box = Widget.Box(
            spacing=10,
            hexpand=True,
            css_classes=["wallpapers-container"],
        )

        self.scroll_area = ScrollableBox(
            hscrollbar_policy="always",
            vscrollbar_policy="never",
            hexpand=True,
            child=self.wallpaper_box,
        )

        self.child = [
            Widget.CenterBox(
                center_widget=self.loading_indicator,
                end_widget=self.folder_button,
            ),
            self.scroll_area
        ]
        self.update_wallpaper_list()

    def _get_monitor_wallpaper(self, monitor_id: int) -> str | None:
        """Получить путь к обоям для конкретного монитора"""
        wallpapers = settings.theme.monitor_wallpapers
        for item in wallpapers:
            if isinstance(item, dict) and str(monitor_id) in item:
                return item[str(monitor_id)]
        return None

    def _update_monitor_wallpapers(self, new_wallpapers: list) -> None:
        """Обновить список обоев"""
        settings.theme.monitor_wallpapers = new_wallpapers

    def show_loading(self, message="", progress=0):
        GObject.idle_add(self._show_loading, message, progress)

    def _show_loading(self, message, progress):
        self.loading_indicator.start(message, progress)
        return False

    def hide_loading(self):
        GObject.idle_add(self._hide_loading)

    def _hide_loading(self):
        self.loading_indicator.stop()
        return False

    def create_wallpaper_button(self, wallpaper_path):
        menu_items = []

        for monitor_id in range(Utils.get_n_monitors()):
            menu_items.append(
                Widget.MenuItem(
                    label=f"Set for Monitor {monitor_id + 1}",
                    on_activate=lambda x, mid=monitor_id: self.set_wallpaper(wallpaper_path, mid)
                )
            )

        menu = Widget.PopoverMenu(items=menu_items)

        button_box = Widget.Box(
            vertical=True,
            child=[
                Widget.Picture(
                    image=wallpaper_path,
                    width=220,
                    height=120,
                    content_fit="cover",
                    css_classes=["wallpaper-preview"],
                ),
                menu,
            ]
        )

        button = Widget.Button(
            css_classes=["wallpaper-button"],
            on_click=lambda x: self.set_wallpaper(wallpaper_path),
            on_right_click=lambda x: self._show_menu(menu, button),
            child=button_box,
        )

        return button

    def _show_menu(self, menu: Widget.PopoverMenu, button: Widget.Button):
        # Создаем прямоугольник для позиционирования
        rect = Gdk.Rectangle()

        rect.x = 0
        rect.y = -40
        rect.width = button.get_allocated_width()
        rect.height = 1

        menu.set_pointing_to(rect)
        menu.popup()

    def add_wallpaper_button(self, button):
        GObject.idle_add(self._add_wallpaper_button, button)

    def _add_wallpaper_button(self, button):
        self.wallpaper_box.append(button)
        return False

    def clear_wallpaper_box(self):
        GObject.idle_add(self._clear_wallpaper_box)

    def _clear_wallpaper_box(self):
        child = self.wallpaper_box.get_first_child()
        while child:
            self.wallpaper_box.remove(child)
            child = self.wallpaper_box.get_first_child()
        return False

    def set_wallpaper(self, wallpaper_path, monitor_id=None):
        if not os.path.exists(wallpaper_path):
            print(f"Error: не удалось установить {wallpaper_path} в качестве обоев - файл не существует")
            return

        try:
            current_wallpapers = list(settings.theme.monitor_wallpapers)

            if monitor_id is None:
                # Установка для всех мониторов
                current_wallpapers = []
                for mid in range(Utils.get_n_monitors()):
                    current_wallpapers.append({str(mid): wallpaper_path})
                    self._update_wallpaper_window(wallpaper_path, mid)
            else:
                monitor_str = str(monitor_id)
                found = False
                for i, item in enumerate(current_wallpapers):
                    if isinstance(item, dict) and monitor_str in item:
                        current_wallpapers[i] = {monitor_str: wallpaper_path}
                        found = True
                        break
                if not found:
                    current_wallpapers.append({monitor_str: wallpaper_path})
                self._update_wallpaper_window(wallpaper_path, monitor_id)

            self._update_monitor_wallpapers(current_wallpapers)
            print(f"Обои изменились на: {wallpaper_path}")
        except Exception as e:
            print(f"Error: не удалось установить {wallpaper_path} в качестве обоев: {e}")

    def _update_wallpaper_window(self, wallpaper_path, monitor_id):
        wallpaper_windows = getattr(self, '_wallpaper_windows', {})

        # Если окно для этого монитора существует, удаляем его
        if monitor_id in wallpaper_windows:
            wallpaper_windows[monitor_id].unrealize()

        # Создаём новое окно для обоев
        gdkmonitor = Utils.get_monitor(monitor_id)
        if gdkmonitor:
            geometry = gdkmonitor.get_geometry()
            window = WallpaperLayerWindow(
                wallpaper_path=wallpaper_path,
                gdkmonitor=gdkmonitor,
                width=geometry.width,
                height=geometry.height,
            )
            wallpaper_windows[monitor_id] = window

        # Сохраняем обновлённый словарь окон
        self._wallpaper_windows = wallpaper_windows

    def load_wallpapers_async(self):
        def load_wallpapers():
            try:
                self.clear_wallpaper_box()
                wallpaper_dir = settings.theme.wallpaper_dir

                wallpapers = [
                    os.path.join(wallpaper_dir, file)
                    for file in os.listdir(wallpaper_dir)
                    if file.lower().endswith((".png", ".jpg", ".jpeg"))
                ]

                total_wallpapers = len(wallpapers)
                for index, wp in enumerate(wallpapers, 1):
                    if os.path.exists(wp):
                        button = self.create_wallpaper_button(wp)
                        self.add_wallpaper_button(button)
                        progress = int((index / total_wallpapers) * 100)
                        GObject.idle_add(
                            self.show_loading,
                            f"Загрузка {progress}%",
                            progress
                        )

            except Exception as e:
                print(f"Ошибка загрузки обоев: {e}")
                GObject.idle_add(
                    self.show_loading,
                    f"Ошибка загрузки: {str(e)}",
                    0
                )
            finally:
                GObject.idle_add(self.hide_loading)

        thread = threading.Thread(target=load_wallpapers, daemon=True)
        thread.start()

    def update_wallpaper_list(self):
        self.load_wallpapers_async()

    def choose_wallpaper_folder(self):
        dialog = Widget.FileDialog(
            select_folder=True,
            initial_path=settings.theme.wallpaper_dir,
            on_file_set=self.on_folder_selected,
        )
        asyncio.create_task(dialog.open_dialog())

    def on_folder_selected(self, dialog, file):
        settings.theme.wallpaper_dir = file.get_path()
        self.update_wallpaper_list()

def wallpaper_panel() -> Widget.RevealerWindow:
    panel = WallpaperPanel()

    # Восстанавливаем обои для всех мониторов при запуске
    for monitor_id in range(Utils.get_n_monitors()):
        wallpaper_path = panel._get_monitor_wallpaper(monitor_id)
        if wallpaper_path and os.path.exists(wallpaper_path):
            try:
                panel._update_wallpaper_window(wallpaper_path, monitor_id)
            except Exception as e:
                print(f"Ошибка восстановления обоев для мониторов {monitor_id}: {e}")

    revealer = Widget.Revealer(
        child=panel,
        transition_duration=300,
        transition_type="slide_up",
        reveal_child=True,
        hexpand=True,
    )

    box = Widget.Box(
        child=[revealer],
    )

    return Widget.RevealerWindow(
        namespace="ignis_WALLPAPER_PANEL",
        visible=False,
        anchor=["left", "bottom", "right"],
        layer="top",
        child=box,
        revealer=revealer,
        popup=True
    )
