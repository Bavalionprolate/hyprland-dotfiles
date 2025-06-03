from pathlib import Path
from ignis.widgets import Widget
from ignis.services.mpris import MprisService, MprisPlayer
from ignis.utils import Utils
from ignis.app import IgnisApp

mpris = MprisService.get_default()
app = IgnisApp.get_default()

CURRENT_DIR = Path(__file__).parent
MEDIA_ART_FALLBACK = str(CURRENT_DIR.parent.parent / "misc/media-art-fallback.png")

class Player(Widget.Revealer):
    def __init__(self, player: MprisPlayer) -> None:
        self._player = player
        self._unique_id = f"{self._player.desktop_entry}-{self._player.track_id.split('/')[-1]}"
        art_url = self._player.art_url if self._player.art_url else MEDIA_ART_FALLBACK
        self._media_image = Widget.Box(
            css_classes=["media-image"],
            style=f"background-image: url('file:///{art_url}');",
            child=[
                Widget.Box(
                    css_classes=["wave-overlay"],
                    hexpand=True,
                    vexpand=True
                )
            ]
        )

        player.connect("closed", lambda x: self.destroy())
        player.connect("notify::art-url", lambda x, y: self._update_art())
        player.connect("notify::playback-status", self._update_playback_status)

        super().__init__(
            transition_type="slide_down",
            reveal_child=False,
            css_classes=["media"],
            child=Widget.Overlay(
                child=self._media_image,
                overlays=[
                    Widget.Box(
                        hexpand=True,
                        vexpand=True,
                        css_classes=["media-image-gradient"],
                    ),
                    Widget.Box(
                        vertical=True,
                        hexpand=True,
                        css_classes=["media-content"],
                        child=[
                            Widget.Box(
                                vexpand=True,
                                valign="center",
                                child=[
                                    Widget.Box(
                                        hexpand=True,
                                        vertical=True,
                                        child=[
                                            Widget.Label(
                                                ellipsize="end",
                                                label=player.bind("title"),
                                                max_width_chars=30,
                                                halign="start",
                                                css_classes=["media-title"],
                                            ),
                                            Widget.Label(
                                                label=player.bind("artist"),
                                                max_width_chars=30,
                                                ellipsize="end",
                                                halign="start",
                                                css_classes=["media-artist"],
                                            ),
                                        ],
                                    ),
                                    Widget.Button(
                                        child=Widget.Icon(
                                            image=player.bind(
                                                "playback_status",
                                                lambda value: "media-playback-pause-symbolic"
                                                if value == "Playing"
                                                else "media-playback-start-symbolic",
                                            ),
                                            pixel_size=18,
                                        ),
                                        on_click=lambda x: player.play_pause(),
                                        visible=player.bind("can_play"),
                                        css_classes=player.bind(
                                            "playback_status",
                                            lambda value: [
                                                "media-playback-button",
                                                "playing",
                                            ]
                                            if value == "Playing"
                                            else [
                                                "media-playback-button",
                                                "paused",
                                            ],
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    Widget.Box(
                        vexpand=True,
                        valign="end",
                        style="padding: 1rem;",
                        child=[
                            Widget.Scale(
                                value=player.bind("position"),
                                max=player.bind("length"),
                                hexpand=True,
                                css_classes=["media-scale"],
                                on_change=lambda x: player.set_position(x.value),
                                visible=player.bind(
                                    "position", lambda value: value != -1
                                ),
                            ),
                            Widget.Button(
                                child=Widget.Icon(
                                    image="media-skip-backward-symbolic",
                                    pixel_size=20,
                                ),
                                css_classes=["media-skip-button"],
                                on_click=lambda x: player.previous(),
                                visible=player.bind("can_go_previous"),
                                style="padding-left: 1rem;",
                            ),
                            Widget.Button(
                                child=Widget.Icon(
                                    image="media-skip-forward-symbolic",
                                    pixel_size=20,
                                ),
                                css_classes=["media-skip-button"],
                                on_click=lambda x: player.next(),
                                visible=player.bind("can_go_next"),
                                style="padding-left: 1rem;",
                            ),
                        ],
                    ),
                ],
            ),
        )

        self._update_playback_status()

    def destroy(self) -> None:
        self.set_reveal_child(False)
        Utils.Timeout(self.transition_duration, super().unparent)

    def _update_art(self) -> None:
        art_url = self._player.art_url if self._player.art_url else MEDIA_ART_FALLBACK
        self._media_image.style = f"background-image: url('file:///{art_url}');"

    def _update_playback_status(self, *args):
        wave_overlay = None
        if len(self._media_image.child) > 0:
            wave_overlay = self._media_image.child[0]

        if self._player.playback_status == "Playing":
            self._media_image.add_css_class("playing")
            if wave_overlay:
                wave_overlay.add_css_class("playing")
        else:
            self._media_image.remove_css_class("playing")
            if wave_overlay:
                wave_overlay.remove_css_class("playing")

def media() -> Widget.Box:
    def add_player(box: Widget.Box, obj: MprisPlayer) -> None:
        player = Player(obj)
        box.append(player)
        player.set_reveal_child(True)

    return Widget.Box(
        vertical=True,
        setup=lambda self: mpris.connect(
            "player_added", lambda x, player: add_player(self, player)
        ),
        css_classes=["rec-unset"],
    )
