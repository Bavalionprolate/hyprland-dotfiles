from ignis.widgets import Widget
from ignis.services.applications import Application, ApplicationAction
from ignis.app import IgnisApp
from .hidden_apps_manager import hide_app, show_app, is_hidden
from options import settings

app = IgnisApp.get_default()

class LaunchpadAppItem(Widget.Button):
    def __init__(self, application: Application, refresh_callback, icon_size=None):
        self._application = application
        self._refresh_callback = refresh_callback

        icon = application.icon or "application-x-executable"
        label_text = application.name
        icon_size = icon_size or settings.launchpad.icon_size

        super().__init__(
            on_click=lambda x: self.launch(),
            on_right_click=lambda x: self._menu.popup(),
            css_classes=["launchpad-app"],
            child=Widget.Box(
                vertical=True,
                child=[
                    Widget.Icon(image=icon, pixel_size=icon_size),
                    Widget.Label(
                        label=label_text,
                        css_classes=["launchpad-app-label"],
                        wrap=True,
                        wrap_mode="word_char",
                        justify="center",
                        ellipsize='end',
                        max_width_chars=14
                    )
                ],
            ),
        )
        self.__sync_menu()
        application.connect("notify::is-pinned", lambda x, y: self.__sync_menu())

    def launch(self) -> None:
        try:
            self._application.launch()
            app.close_window("ignis_LAUNCHPAD")
        except Exception as e:
            print(f"Error launching application: {e}")

    def launch_action(self, action: ApplicationAction) -> None:
        try:
            action.launch()
            app.close_window("ignis_LAUNCHPAD")
        except Exception as e:
            print(f"Error launching action: {e}")

    def toggle_hidden(self) -> None:
        app_id = self._application.id
        if is_hidden(app_id):
            show_app(app_id)
        else:
            hide_app(app_id)
        self._refresh_callback()

    def pin_app(self) -> None:
        app_id = self._application.id
        if not self.is_pinned():
            settings.apps.pin_app(app_id)
            self._application.pin()
            self.__sync_menu()

    def unpin_app(self) -> None:
        app_id = self._application.id
        if self.is_pinned():
            settings.apps.unpin_app(app_id)
            self._application.unpin()
            self.__sync_menu()

    def is_pinned(self) -> bool:
        return settings.apps.is_pinned(self._application.id)

    def __sync_menu(self) -> None:
        is_hidden_flag = is_hidden(self._application.id)
        is_pinned = self.is_pinned()

        menu_items = [
            Widget.MenuItem(
                label="Launch",
                on_activate=lambda x: self.launch()
            )
        ]

        # Добавление действий приложения в меню
        for action in self._application.actions:
            menu_items.append(
                Widget.MenuItem(
                    label=action.name,
                    on_activate=lambda x, action=action: self.launch_action(action),
                )
            )

        menu_items.extend([
            Widget.Separator(),
            Widget.MenuItem(
                label="󰤰 Unpin" if is_pinned else "󰤱 Pin",
                on_activate=lambda x: self.unpin_app() if is_pinned else self.pin_app()
            ),
            Widget.MenuItem(
                label="󰈈  Show" if is_hidden_flag else "󰈉  Hide",
                on_activate=lambda x: self.toggle_hidden(),
            ),
        ])

        self._menu = Widget.PopoverMenu(items=menu_items)
        if hasattr(self, 'child'):
            self.child.append(self._menu)
