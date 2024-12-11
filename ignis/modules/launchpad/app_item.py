from ignis.widgets import Widget
from ignis.services.applications import Application, ApplicationAction
from ignis.app import IgnisApp
from .hidden_apps_manager import hide_app, show_app, is_hidden

app = IgnisApp.get_default()


class LaunchpadAppItem(Widget.Button):
    def __init__(self, application, refresh_callback):
        self._application = application
        self._refresh_callback = refresh_callback

        icon = application.icon or "application-x-executable"
        label_text = application.name

        super().__init__(
            on_click=lambda x: self.launch(),
            on_right_click=lambda x: self._menu.popup(),
            css_classes=["launchpad-app"],
            child=Widget.Box(
                vertical=True,
                spacing=10,
                child=[
                    Widget.Icon(image=icon, pixel_size=110),
                    Widget.Label(
                        label=label_text,
                        css_classes=["launchpad-app-label"],
                        wrap=True,
                        wrap_mode="word",
                        justify="center",
                    ),
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

    def __sync_menu(self) -> None:
        is_hidden_flag = is_hidden(self._application.id)

        self._menu = Widget.PopoverMenu(
            items=[
                Widget.MenuItem(label="Launch", on_activate=lambda x: self.launch()),
            ]
            + [
                Widget.MenuItem(
                    label=i.name,
                    on_activate=lambda x, action=i: self.launch_action(action),
                )
                for i in self._application.actions
            ]
            + [
                Widget.Separator(),
                Widget.MenuItem(
                    label="󰤱 Pin", on_activate=lambda x: self._application.pin()
                )
                if not self._application.is_pinned
                else Widget.MenuItem(
                    label="󰤰 Unpin", on_activate=lambda x: self._application.unpin()
                ),
                Widget.MenuItem(
                    label="  Show" if is_hidden_flag else "  Hide",
                    on_activate=lambda x: self.toggle_hidden(),
                ),
            ]
        )
        self.child.append(self._menu)
