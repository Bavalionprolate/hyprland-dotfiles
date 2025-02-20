from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.services.audio import AudioService

audio = AudioService.get_default()

class OSD(Widget.Window):
    def __init__(self):
        self._timer = None
        super().__init__(
            layer="overlay",
            anchor=["bottom"],
            namespace="ignis_OSD",
            visible=False,
            css_classes=["rec-unset"],
            child=Widget.Box(
                css_classes=["osd"],
                child=[
                    Widget.Icon(
                        pixel_size=16,
                        style="margin-right: 0.5rem;",
                        image=audio.speaker.bind("icon_name"),
                    ),
                    Widget.Scale(
                        value=audio.speaker.bind("volume"),
                        css_classes=["volume-slider"],
                        sensitive=False,
                        hexpand=True,
                    ),
                    Widget.Label(
                        css_classes=["volume-slider-indicator"],
                        label=audio.speaker.bind("volume", transform=lambda value: str(value))
                    ),
                ],
            ),
        )

    def set_property(self, property_name, value):
        if property_name == "visible":
            if self._timer:
                self._timer.cancel()
                self._timer = None

            self._timer = Utils.Timeout(1000, self.set_visible, False)

        super().set_property(property_name, value)