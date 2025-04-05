import textwrap
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf
from ignis.widgets import Widget
from .utils import focus_window, close_window
import logging
import os

icon_size = 44

class AppItem(Widget.Button):
    def __init__(
        self,
        app: "Application",
        instances: list[dict],
        is_pinned: bool,
        dock_manager: "DockManager"
    ):
        self.app = app
        self.instances = instances
        self.dock_manager = dock_manager
        self.is_pinned = is_pinned
        self.icon = app.icon

        indicator = (
            Widget.Label(label="-", css_classes=["app-item-indicator-start"])
            if instances
            else Widget.Label(label="", css_classes=["app-item-indicator-start"])
        )
        self.menu = self._build_menu()
        self.app.connect("pinned", lambda _: self._sync_menu())
        self.app.connect("unpinned", lambda _: self._sync_menu())
        super().__init__(
            child=Widget.Box(
                child=[
                    Widget.Icon(
                        image=self.icon,
                        pixel_size=45,
                        css_classes=["app-item-dock-button"],
                    ),
                    indicator,
                    self.menu,
                ],
                vertical=True,
            ),
            on_click=lambda x: self.handle_click(),
            on_right_click=lambda x: self.menu.popup(),
            css_classes=["app-item-dock"],
        )
        self.drag_source = Gtk.DragSource.new()
        self.drag_source.set_actions(Gdk.DragAction.MOVE)
        self.drag_source.connect("prepare", self.on_drag_prepare)
        self.drag_source.connect("begin", self.on_drag_begin)
        self.drag_source.connect("end", self.on_drag_end)
        self.drag_source.connect("cancel", self.on_drag_cancel)
        self.add_controller(self.drag_source)

        self.drop_target = Gtk.DropTarget.new(GObject.TYPE_PYOBJECT, Gdk.DragAction.MOVE)
        self.drop_target.connect("enter", self.on_drop_target_enter)
        self.drop_target.connect("leave", self.on_drop_target_leave)
        self.drop_target.connect("drop", self.on_drop)
        self.add_controller(self.drop_target)

    def handle_click(self):
        if self.instances:
            address = self.instances[0]["address"]
            logging.info(f"Фокусировка на окне приложения {self.app.id} с адресом {address}.")
            focus_window(address)
        else:
            logging.info(f"Запуск приложения {self.app.id}.")
            self.app.launch()

    def close_all_instances(self):
        for instance in self.instances:
            addr = instance["address"]
            close_window(addr)

    def on_drop_target_enter(self, drop_target, x, y):
        self.add_css_class("drop-target")
        current_index = self.dock_manager.app_buttons.index(self)

        value = drop_target.get_value()
        dragged_index = value.get("index", -1) if value else -1
        pinned_count = sum(1 for btn in self.dock_manager.app_buttons if btn.is_pinned)
        if (dragged_index < pinned_count and current_index >= pinned_count) or \
            (dragged_index >= pinned_count and current_index < pinned_count):
            self.add_css_class("drop-prohibited")
        else:
            self.add_css_class("drop-target")

    def on_drop_target_leave(self, drop_target):
        self.remove_css_class("drop-target")
        self.remove_css_class("drop-prohibited")

    def on_drag_prepare(self, drag_source, x, y):
        return Gdk.ContentProvider.new_for_value({
            "index": self.dock_manager.app_buttons.index(self),
            "app_id": self.app.id,
        })

    def on_drag_begin(self, drag_source, gesture):
        self.add_css_class("dragging")
        display = self.get_display()

        icon_theme = Gtk.IconTheme.get_for_display(display)

        icon_info = icon_theme.lookup_icon(self.icon, [], icon_size, 1, Gtk.TextDirection.NONE, 0)
        file_path = icon_info.get_file().get_path()
        if file_path and os.path.exists(file_path):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(file_path, icon_size, icon_size)
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            drag_source.set_icon(texture, 0, 0)

        self.show()

    def on_drag_end(self, drag_source, drag):
        self.remove_css_class("dragging")
        self.show()

    def on_drag_cancel(self, drag_source, _):
        self.remove_css_class("dragging")
        self.show()

    def on_drop(self, drop_target, value, x, y):
        dragged_index = value["index"]
        target_index = self.dock_manager.app_buttons.index(self)
        if 0 <= dragged_index < len(self.dock_manager.app_buttons) and \
            0 <= target_index < len(self.dock_manager.app_buttons):
            self.dock_manager.swap_apps(dragged_index, target_index)
        return True

    def _build_menu(self) -> Widget.PopoverMenu:
        menu_items = [
            Widget.MenuItem(
                label="Launch",
                on_activate=lambda x: self.app.launch(),
            )
        ]
        for action in self.app.actions:
            menu_items.append(
                Widget.MenuItem(
                    label=action.name,
                    on_activate=lambda x, act=action: act.launch(),
                )
            )

        if self.app.is_pinned:
            menu_items.append(
                Widget.MenuItem(
                    label="󰤰 Unpin",
                    on_activate=lambda x: self.unpin_app(),
                )
            )
        else:
            menu_items.append(
                Widget.MenuItem(
                    label="󰤱 Pin",
                    on_activate=lambda x: self.pin_app(),
                )
            )

        if self.instances:
            menu_items.append(Widget.Separator())
        if len(self.instances) > 1:
            for instance in self.instances:
                truncated_title = textwrap.shorten(instance.get("title", "Unknown"), width=35, placeholder="...")
                menu_items.append(
                    Widget.MenuItem(
                        label=truncated_title,
                        on_activate=lambda x, addr=instance["address"]: focus_window(addr),
                    )
                )

        menu_items.append(Widget.Separator())

        for instance in self.instances:
            truncated_title = textwrap.shorten(instance.get('title', 'Unknown'), width=35, placeholder="...")
            menu_items.append(
                Widget.MenuItem(
                    label=f"Close {truncated_title}",
                    on_activate=lambda x, addr=instance["address"]: close_window(addr),
                )
            )

        if len(self.instances) > 1:
            menu_items.append(
                Widget.MenuItem(
                    label="Close All",
                    on_activate=lambda x: self.close_all_instances(),
                )
            )

        menu = Widget.PopoverMenu(items=menu_items)
        menu.connect("notify::visible", lambda x, y: self.dock_manager.check_window_overlap())
        return menu

    def pin_app(self):
        self.app.pin()
        self.is_pinned = True
        self._sync_menu()

    def unpin_app(self):
        self.app.unpin()
        self.is_pinned = False
        self._sync_menu()

    def _sync_menu(self):
        if self.menu and self.menu.get_parent():
            self.menu.get_parent().remove(self.menu)
        self.menu = self._build_menu()
        if not self.menu.get_parent():
            self.child.append(self.menu)
