from gi.repository import GLib, Gtk
from ignis.widgets import Widget
from ignis.services.applications import ApplicationsService
from ignis.utils import Utils
from options import settings
from ignis.app import IgnisApp
from .app_item import LaunchpadAppItem
from .search_button import SearchWebButton
from .hidden_apps_manager import is_hidden

app = IgnisApp.get_default()

class ScrollableBox(Widget.Scroll):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.current_page = 0
        self.scrolling = False
        self.animation_id = None
        self.scroll_start_time = None

        event_controller = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.BOTH_AXES |
            Gtk.EventControllerScrollFlags.KINETIC
        )
        event_controller.connect("scroll", self.on_scroll)
        self.add_controller(event_controller)

    def on_scroll(self, controller, dx, dy):
        if self.scrolling:
            return True

        adj = self.get_hadjustment()
        page_size = adj.get_page_size()

        # Determine scroll direction
        if (dy > 0) == settings.launchpad.invert_scroll:  # Scroll left
            target_page = max(0, self.current_page + 1)
        else:  # Scroll right
            max_page = int((adj.get_upper() - adj.get_page_size()) / page_size)
            target_page = min(max_page, self.current_page - 1)

        if target_page != self.current_page:
            self.current_page = target_page
            self.scroll_to_page(target_page)

        return True

    def scroll_to_page(self, page_number):
        if self.animation_id:
            GLib.source_remove(self.animation_id)

        adj = self.get_hadjustment()
        target = page_number * adj.get_page_size()

        self.scrolling = True
        self.scroll_start_time = GLib.get_monotonic_time()
        self.scroll_start_pos = adj.get_value()
        self.scroll_target = target

        self.animation_id = GLib.timeout_add(16, self.animate_scroll)  # ~60fps

    def animate_scroll(self):
        adj = self.get_hadjustment()
        current_time = GLib.get_monotonic_time()
        progress = min(1.0, (current_time - self.scroll_start_time) / 300000.0)  # 300ms duration

        # Ease-out cubic function
        t = 1 - progress
        ease = 1 - (t * t * t)

        current = self.scroll_start_pos + (self.scroll_target - self.scroll_start_pos) * ease
        adj.set_value(current)

        if progress >= 1.0:
            self.scrolling = False
            self.animation_id = None
            return False

        return True

def launchpad() -> Widget.Window:
    current_query = ""

    def update_launchpad(*args):
        nonlocal COLUMNS, ROWS, APPS_PER_PAGE
        COLUMNS = settings.launchpad.columns
        ROWS = settings.launchpad.rows
        APPS_PER_PAGE = COLUMNS * ROWS
        if apps_container:
            refresh_app_list(apps_container, current_query)

    # Подключаем отслеживание изменений настроек
    settings.launchpad.connect_option("columns", update_launchpad)
    settings.launchpad.connect_option("rows", update_launchpad)
    settings.launchpad.connect_option("grid_spacing_x", update_launchpad)
    settings.launchpad.connect_option("grid_spacing_y", update_launchpad)
    settings.launchpad.connect_option("margin", update_launchpad)
    settings.launchpad.connect_option("app_size", update_launchpad)
    settings.launchpad.connect_option("icon_size", update_launchpad)
    settings.launchpad.connect_option("page_scale_x", update_launchpad)
    settings.launchpad.connect_option("page_scale_y", update_launchpad)

    COLUMNS = settings.launchpad.columns
    ROWS = settings.launchpad.rows
    APPS_PER_PAGE = COLUMNS * ROWS

    monitor = Utils.get_monitor(0)
    if monitor:
        geometry = monitor.get_geometry()
        monitor_width = geometry.width
        monitor_height = geometry.height

    def get_filtered_apps(query: str):
        if applications is None:
            return []

        apps = applications.apps if query == "" else applications.search(applications.apps, query)
        return [app for app in apps if not is_hidden(app.id)] if not query else apps

    def create_apps_page(apps: list, page_index: int) -> Widget.Box:
        start_idx = page_index * APPS_PER_PAGE
        page_apps = apps[start_idx:start_idx + APPS_PER_PAGE]

        grid = Widget.Grid(
            css_classes=["launchpad-page-grid"],
            column_homogeneous=False,
            row_homogeneous=False,
            column_spacing=settings.launchpad.grid_spacing_x,
            row_spacing=settings.launchpad.grid_spacing_y,
            margin_start=settings.launchpad.margin,
            margin_end=settings.launchpad.margin,
            margin_top=settings.launchpad.margin,
            margin_bottom=settings.launchpad.margin
        )

        for i, app in enumerate(page_apps):
            row = i // COLUMNS
            col = i % COLUMNS
            app_item = LaunchpadAppItem(app, lambda: refresh_app_list(apps_container, current_query), icon_size=settings.launchpad.icon_size)
            app_item.set_size_request(settings.launchpad.app_size, settings.launchpad.app_size)
            grid.attach(app_item, col, row, 1, 1)

        page_box = Widget.Box(
            css_classes=["launchpad-page"],
            child=[grid]
        )

        page_width = int((monitor_width - 200) * settings.launchpad.page_scale_x)
        page_height = int((monitor_height - 200) * settings.launchpad.page_scale_y)
        page_box.set_size_request(page_width, page_height)

        return page_box

    def create_pages_container(apps: list) -> Widget.Box:
        pages_box = Widget.Box(
            css_classes=["launchpad-pages-container"],
            spacing=0,
            homogeneous=True
        )

        total_pages = (len(apps) + APPS_PER_PAGE - 1) // APPS_PER_PAGE

        for i in range(total_pages):
            page = create_apps_page(apps, i)
            pages_box.append(page)

        return pages_box

    def refresh_app_list(container: Widget.Box, query: str = "") -> None:
        nonlocal current_query
        current_query = query

        while child := container.get_first_child():
            container.remove(child)

        apps = get_filtered_apps(query)

        if not apps and not query:
            container.append(
                Widget.Label(
                    label="No applications available.",
                    css_classes=["launchpad-empty-label"]
                )
            )
        elif not apps:
            container.append(SearchWebButton(query))
        else:
            if query:
                container.append(create_pages_container(apps))
            else:
                container.append(create_pages_container(apps))

    def on_open(window: Widget.Window, entry: Widget.Entry, container: Widget.Box) -> None:
        if not window.visible:
            return
        entry.text = current_query
        entry.grab_focus()
        refresh_app_list(container, current_query)

    applications = ApplicationsService.get_default()

    apps_container = Widget.Box(
        css_classes=["launchpad-apps-container"],
        vertical=True,
    )

    search_entry = Widget.Entry(
        hexpand=True,
        placeholder_text="Search",
        css_classes=["launchpad-search"],
        on_change=lambda x: refresh_app_list(apps_container, x.text),
        on_accept=lambda x: apps_container.child[0].launch()
        if len(apps_container.child) > 0 and hasattr(apps_container.child[0], 'launch')
        else None,
    )

    refresh_app_list(apps_container)

    scroll_area = ScrollableBox(
        hscrollbar_policy="always",
        vscrollbar_policy="never",
        hexpand=True,
        css_classes=["launchpad-scroll"],
        child=apps_container,
    )

    # Создаем основной контейнер
    main_box = Widget.Box(
        vertical=True,
        valign="start",
        halign="center",
        css_classes=["launchpad-container"],
        child=[
            # Блок поиска
            Widget.Box(
                css_classes=["launchpad-search-container"],
                valign="start",
                halign="center",
                child=[
                    Widget.Icon(
                        icon_name="system-search-symbolic",
                        pixel_size=16,
                        css_classes=["launchpad-search-icon"],
                    ),
                    search_entry,
                ],
            ),
            # Блок с приложениями
            scroll_area,
        ],
    )

    main_box.set_size_request(monitor_width - 200, monitor_height - 200)

    window = Widget.Window(
        namespace="ignis_LAUNCHPAD",
        visible=False,
        popup=True,
        kb_mode="on_demand",
        css_classes=["launchpad"],
        anchor=["top", "right", "bottom", "left"],
        child=main_box,
        exclusivity="ignore"
    )
    return window
