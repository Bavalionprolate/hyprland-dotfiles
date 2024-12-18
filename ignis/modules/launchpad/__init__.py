from ignis.services.applications import ApplicationsService
from ignis.widgets import Widget
from .app_item import LaunchpadAppItem
from .search_button import SearchWebButton
from .hidden_apps_manager import is_hidden


def launchpad() -> Widget.Window:
    def get_filtered_apps(query: str):
        if applications is None:
            return []

        if query == "":
            return [app for app in applications.apps if not is_hidden(app.id)]
        else:
            return applications.search(applications.apps, query)

    def refresh_app_list(app_list: Widget.Grid, query: str = "") -> None:
        apps = get_filtered_apps(query)

        if not apps and not query:
            app_list.child = [Widget.Label(label="No applications available.")]
        elif not apps:
            app_list.child = [SearchWebButton(query)]
        else:
            app_list.visible = True
            app_list.child = [LaunchpadAppItem(i, refresh_app_list) for i in apps]

    def search(entry: Widget.Entry, app_list: Widget.Grid) -> None:
        query = entry.text
        refresh_app_list(app_list, query)

    def on_open(window: Widget.Window, entry: Widget.Entry, app_list: Widget.Grid) -> None:
        if not window.visible:
            return

        entry.text = ""
        entry.grab_focus()
        refresh_app_list(app_list)

    applications = ApplicationsService.get_default()

    app_list = Widget.Grid(
        child=Widget.Box(vertical=False, style="margin-top: 1rem;"),
        column_num=8,
    )

    entry = Widget.Entry(
        hexpand=True,
        placeholder_text="Search",
        css_classes=["launchpad-search"],
        on_change=lambda x: search(x, app_list),
        on_accept=lambda x: app_list.child[0].launch()
        if len(app_list.child) > 0
        else None,
    )

    refresh_app_list(app_list)

    main_box = Widget.Box(
        vertical=True,
        valign="start",
        halign="center",
        css_classes=["overview"],
        spacing=10,
        child=[
            Widget.Box(
                css_classes=["launchpad-search-box"],
                valign="start",
                halign="center",
                child=[
                    Widget.Icon(
                        icon_name="system-search-symbolic",
                        pixel_size=16,
                        style="margin-right: 0.5rem;",
                    ),
                    entry,
                ],
            ),
            Widget.Scroll(css_classes=["launchpad-scroll"], child=app_list),
        ],
    )

    return Widget.Window(
        namespace="ignis_LAUNCHPAD",
        visible=False,
        popup=True,
        kb_mode="on_demand",
        css_classes=["launchpad"],
        setup=lambda self: self.connect(
            "notify::visible", lambda x, y: on_open(self, entry, app_list)
        ),
        anchor=["top", "right", "bottom", "left"],
        child=Widget.Overlay(
            child=Widget.Button(
                vexpand=True,
                hexpand=True,
                can_focus=False,
            ),
            overlays=[main_box],
        ),
    )
