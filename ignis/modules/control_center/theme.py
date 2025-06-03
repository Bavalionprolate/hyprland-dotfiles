from typing import Callable
from ignis.app import IgnisApp
from options import settings
from .qs_button import QSButton

import os
import logging
import subprocess

app = IgnisApp.get_default()

class ThemeManager:
    def __init__(self):
        self.config_dir = os.path.expanduser("~/.config/ignis")
        self.scss_path = os.path.join(self.config_dir, "scss/_theme_vars.scss")
        self.style_path = os.path.join(self.config_dir, "style.scss")
        self.callbacks: list[Callable] = []

        settings.theme.connect_option("dark_mode", self._on_theme_change)

    def _write_theme_scss(self, is_dark: bool) -> bool:
        try:
            content = f"@function dark-mode() {{ @return {'true' if is_dark else 'false'}; }}"
            os.makedirs(os.path.dirname(self.scss_path), exist_ok=True)
            with open(self.scss_path, "w") as f:
                f.write(content)
            logging.info(f"Theme SCSS updated: {'dark' if is_dark else 'light'} mode")
            return True
        except Exception as e:
            logging.error(f"Failed to write theme SCSS: {e}")
            return False

    def _recompile_css(self) -> bool:
        app.remove_css(self.style_path)
        try:
            app.apply_css(self.style_path)
            logging.info("Theme CSS recompiled successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to recompile CSS: {e}")
            return False

    def _sync_system_theme(self, is_dark: bool) -> bool:
        try:
            command = [
                "gsettings", "set",
                "org.gnome.desktop.interface",
                "color-scheme",
                "prefer-dark" if is_dark else "prefer-light"
            ]
            subprocess.run(command, check=True, capture_output=True)
            logging.info(f"System theme synchronized: {'dark' if is_dark else 'light'} mode")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"System theme sync failed: {e.stderr.decode()}")
            return False
        except Exception as e:
            logging.error(f"System theme sync error: {e}")
            return False

    def _on_theme_change(self):
        is_dark = settings.theme.dark_mode
        if self._write_theme_scss(is_dark):
            self._recompile_css()
            self._sync_system_theme(is_dark)
            for callback in self.callbacks:
                try:
                    callback(is_dark)
                except Exception as e:
                    logging.error(f"Theme change callback error: {e}")

    def toggle_theme(self) -> bool:
        try:
            settings.theme.dark_mode = not settings.theme.dark_mode
            return True
        except Exception as e:
            logging.error(f"Theme toggle failed: {e}")
            return False

    def initialize(self) -> None:
        try:
            is_dark = settings.theme.dark_mode
            if self._write_theme_scss(is_dark):
                self._recompile_css()
                self._sync_system_theme(is_dark)
            logging.info(f"Theme initialized: {'dark' if is_dark else 'light'} mode")
        except Exception as e:
            logging.error(f"Theme initialization failed: {e}")

    def register_callback(self, callback: Callable[[bool], None]) -> None:
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[bool], None]) -> None:
        if callback in self.callbacks:
            self.callbacks.remove(callback)

theme_manager = ThemeManager()

def theme_button() -> QSButton:
    def update_button_state(is_dark: bool):
        button.set_property("label", "Dark" if is_dark else "Light")
        button.set_property("icon_name",
            "weather-clear-night-symbolic" if is_dark else "weather-clear-symbolic"
        )
        button.active = is_dark

    button = QSButton(
        label="Dark" if settings.theme.dark_mode else "Light",
        icon_name="weather-clear-night-symbolic" if settings.theme.dark_mode else "weather-clear-symbolic",
        on_activate=lambda x: theme_manager.toggle_theme(),
        on_deactivate=lambda x: theme_manager.toggle_theme(),
        active=settings.theme.dark_mode
    )
    theme_manager.register_callback(update_button_state)
    return button

theme_manager.initialize()
