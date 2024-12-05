from ignis.widgets import Widget
from ignis.utils import Utils
from gi.repository import Gio
from ignis.app import IgnisApp

from .utils import is_url

app = IgnisApp.get_default()


class SearchWebButton(Widget.Button):
    def __init__(self, query: str):
        self._query = query
        self._url = ""

        try:
            browser_desktop_file = Utils.exec_sh(
                "xdg-settings get default-web-browser"
            ).stdout.replace("\n", "")

            app_info = Gio.DesktopAppInfo.new(desktop_id=browser_desktop_file)
        except Exception as e:
            print(f"Error determining default browser: {e}")
            app_info = None

        icon_name = "applications-internet-symbolic"
        if app_info:
            icon_string = app_info.get_string("Icon")
            if icon_string:
                icon_name = icon_string

        if not query.startswith(("http://", "https://")) and "." in query:
            query = "https://" + query

        if is_url(query):
            label = "Visit " + query
            self._url = query
        else:
            label = "Search in Google"
            self._url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

        super().__init__(
            on_click=lambda x: self.launch(),
            css_classes=["launchpad-app"],
            child=Widget.Box(
                child=[
                    Widget.Icon(image=icon_name, pixel_size=48),
                    Widget.Label(
                        label=label,
                        css_classes=["launchpad-app-label"],
                    ),
                ]
            ),
        )

    def launch(self) -> None:
        try:
            Utils.exec_sh_async(f"xdg-open {self._url}")
            app.close_window("ignis_LAUNCHPAD")
        except Exception as e:
            print(f"Error launching browser: {e}")
