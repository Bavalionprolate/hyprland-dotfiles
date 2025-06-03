from ignis.widgets import Widget
from gi.repository import GObject
from typing import Callable

class QSButton(Widget.Button):
    def __init__(
        self,
        label: str,
        icon_name: str,
        on_activate: Callable | None = None,
        on_deactivate: Callable | None = None,
        content: Widget.Revealer | None = None,
        **kwargs,
    ):
        self.on_activate = on_activate
        self.on_deactivate = on_deactivate
        self._active = False
        self._content = content
        self._icon = Widget.Icon(image=icon_name)
        self._label = Widget.Label(label=label, css_classes=["qs-button-label"])
        super().__init__(
            child=Widget.Box(
                child=[
                    self._icon,
                    self._label,
                    Widget.Arrow(
                        halign="end",
                        hexpand=True,
                        pixel_size=20,
                        rotated=content.bind("reveal_child"),
                    )
                    if content
                    else None,
                ]
            ),
            on_click=self.__callback,
            css_classes=["qs-button"],
            hexpand=True,
            **kwargs,
        )

    def __callback(self, *args) -> None:
        if self.active:
            if self.on_deactivate:
                self.on_deactivate(self)
        else:
            if self.on_activate:
                self.on_activate(self)

    def set_property(self, prop, value):
        if prop == "label":
            self._label.label = value
        elif prop == "icon_name":
            self._icon.image = value
        elif prop == "active":
            self._active = value
            if value:
                self.add_css_class("active")
            else:
                self.remove_css_class("active")
        else:
            super().set_property(prop, value)

    @GObject.Property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        self.set_property("active", value)

    @GObject.Property
    def content(self) -> Widget.Revealer | None:
        return self._content
