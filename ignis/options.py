from ignis.options_manager import OptionsManager, OptionsGroup, TrackedList
from ignis.services.notifications import NotificationService
import os
import json

notifications = NotificationService.get_default()

# Менеджер пользовательских опций для постоянных настроек пользователя
class IgnisOptions(OptionsManager):
    def __init__(self):
        config_path = os.path.expanduser("~/.config/ignis/settings.json")

        if not os.path.exists(config_path):
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump({}, f)

        super().__init__(file=config_path, hot_reload=True)

    # Группа настроек темы
    class ThemeSettings(OptionsGroup):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.dark_mode = True
            self.monitor_wallpapers = TrackedList(self, "monitor_wallpapers")
            self.wallpaper_dir = os.path.expanduser("~/Pictures/Wallpapers")

    # Группа настроек приложения
    class AppSettings(OptionsGroup):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.pinned_apps = TrackedList(self, "pinned_apps")
            self.hidden_apps = TrackedList(self, "hidden_apps")

        def pin_app(self, app_id: str) -> bool:
            if app_id not in self.pinned_apps:
                self.pinned_apps.append(app_id)
                return True
            return False

        def unpin_app(self, app_id: str) -> bool:
            if app_id in self.pinned_apps:
                self.pinned_apps.remove(app_id)
                return True
            return False

        def is_pinned(self, app_id: str) -> bool:
            return app_id in self.pinned_apps

        def hide_app(self, app_id: str) -> bool:
            if app_id not in self.hidden_apps:
                self.hidden_apps.append(app_id)
                return True
            return False

        def show_app(self, app_id: str) -> bool:
            if app_id in self.hidden_apps:
                self.hidden_apps.remove(app_id)
                return True
            return False

        def is_hidden(self, app_id: str) -> bool:
            return app_id in self.hidden_apps

        # Обновление порядка закрепленных приложений
        def reorder_pinned_apps(self, new_order: list[str]) -> None:
            if set(new_order) == set(self.pinned_apps):
                self.pinned_apps = new_order

    # Группа настроек уведомлений
    class NotificationSettings(OptionsGroup):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.dnd = kwargs.get('dnd', False)
                self.notification_sound = kwargs.get('notification_sound', True)

                self.connect_option("dnd", self._on_dnd_changed)

            def _on_dnd_changed(self):
                try:
                    notifications.dnd = self.dnd
                except Exception as e:
                    print(f"Error updating DND status: {e}")

    # Группа настроек дока
    class DockSettings(OptionsGroup):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.auto_hide = True
            self.icon_size = 44
            self.animation_speed = 200

    # Группа настроек лаунчпада
    class LaunchpadSettings(OptionsGroup):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.columns = 7  # Количество колонок в сетке
            self.rows = 3  # Количество рядов в сетке
            self.grid_spacing_x = 160  # Горизонтальный отступ между элементами сетки
            self.grid_spacing_y = 140  # Вертикальный отступ между элементами сетки
            self.margin = 140  # Отступ сетки от краев
            self.app_size = 160  # Размер элемента приложения
            self.icon_size = 48  # Размер иконки приложения
            self.invert_scroll = True  # Инвертировать направление прокрутки
            self.page_scale_x = 0.8  # Масштаб страницы относительно основного контейнера
            self.page_scale_y = 1  # Масштаб страницы относительно основного контейнера

    # Инициализация групп
    theme = ThemeSettings()
    apps = AppSettings()
    notifications = NotificationSettings()
    dock = DockSettings()
    launchpad = LaunchpadSettings()

    def __post_init__(self):
        self.save_to_file(self._file)

settings = IgnisOptions()
