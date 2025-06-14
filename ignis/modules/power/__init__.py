from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.app import IgnisApp
import asyncio

app = IgnisApp.get_default()

# Меню управления питанием и сеансом пользователя с основными системными действиями
class PowerMenu(Widget.Box):
    def __init__(self):
        super().__init__(
            valign="center",
            vertical=False,
            spacing=20,
            halign="center",
            css_classes=["power-menu"],
            child=[
                self.create_button(
                    label="Restart",
                    icon_name="system-reboot-symbolic",
                    action=self.restart,
                ),
                self.create_button(
                    label="Shutdown",
                    icon_name="system-shutdown-symbolic",
                    action=self.shutdown,
                ),
                self.create_button(
                    label="Sleep",
                    icon_name="preferences-desktop-screensaver",
                    action=self.sleep,
                ),
                self.create_button(
                    label="Lock",
                    icon_name="lock-symbolic",
                    action=self.lock,
                ),
                self.create_button(
                    label="Log out",
                    icon_name="system-log-out",
                    action=self.log_out,
                ),
            ],
        )

    # Создание кнопки действия с иконкой и текстом
    def create_button(self, label: str, icon_name: str, action: callable) -> Widget.Button:
        return Widget.Button(
            css_classes=["power-button"],
            on_click=lambda x: action(),
            child=Widget.Box(
                vertical=True,
                spacing=5,
                halign="center",
                child=[
                    Widget.Icon(image=icon_name, pixel_size=48),
                    Widget.Label(label=label),
                ],
            ),
        )

    def restart(self):
        try:
            asyncio.create_task(Utils.exec_sh_async("systemctl reboot"))
        except Exception as e:
            print(f"Error during restart: {e}")
        finally:
            app.close_window("ignis_POWER")

    def shutdown(self):
        try:
           asyncio.create_task( Utils.exec_sh_async("systemctl poweroff"))
        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            app.close_window("ignis_POWER")

    def sleep(self):
        try:
           asyncio.create_task( Utils.exec_sh_async("systemctl suspend"))
        except Exception as e:
            print(f"Error during sleep: {e}")
        finally:
            app.close_window("ignis_POWER")

    def lock(self):
        try:
            asyncio.create_task(Utils.exec_sh_async("hyprlock"))
        except Exception as e:
            print(f"Error during lock: {e}")
        finally:
            app.close_window("ignis_POWER")

    def log_out(self):
        try:
           asyncio.create_task(Utils.exec_sh_async("hyprctl dispatch exit"))
        except Exception as e:
            print(f"Error during sleep: {e}")
        finally:
            app.close_window("ignis_POWER")

# Создание модального окна управления питанием с затемнением фона
def power():
    return Widget.Window(
        namespace="ignis_POWER",
        visible=False,
        popup=True,
        kb_mode="on_demand",
        layer='top',
        anchor=['left', 'right', 'top', 'bottom'],
        child=Widget.Overlay(
            css_classes=["power-window"],
            child=Widget.Button(
                vexpand=True,
                hexpand=True,
                can_focus=False,
                on_click=lambda x: app.close_window("ignis_POWER"),
            ),
            overlays=[PowerMenu()],
        ),
    )
