from ignis.services.applications import ApplicationsService
from ignis.widgets import Widget

from .app_item import LaunchpadAppItem
from .search_button import SearchWebButton
from .utils import is_url

def launchpad() -> Widget.Window:
    def search(entry: Widget.Entry, app_list: Widget.Grid) -> None:
        query = entry.text

        if applications is None:
            app_list.child = [Widget.Label(label="Applications unavailable")]
            return

        if query == "":
            apps = applications.apps
            app_list.visible = True
            app_list.child = [LaunchpadAppItem(i) for i in apps]
        else:
            apps = applications.search(applications.apps, query)
            if apps == []:
                app_list.child = [SearchWebButton(query)]
            else:
                app_list.visible = True
                app_list.child = [LaunchpadAppItem(i) for i in apps]

    def on_open(window: Widget.Window, entry: Widget.Entry) -> None:
        if not window.visible:
            return

        entry.text = ""
        entry.grab_focus()

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

    search(entry, app_list)

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
            "notify::visible", lambda x, y: on_open(self, entry)
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
