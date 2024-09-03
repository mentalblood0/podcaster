import logging
from dataclasses import dataclass

import yoop

from .Bot import Bot
from .Cache import Cache
from .enums import ConvertMode, LinkType, OrderMode


@dataclass
class Uploader:
    url: yoop.Url
    suffixes: list[str]
    bot: Bot
    cache: Cache
    bitrate: yoop.Audio.Bitrate
    format: yoop.Audio.Format | None
    samplerate: yoop.Audio.Samplerate
    channels: yoop.Audio.Channels
    convert: ConvertMode
    order: OrderMode
    link_type: LinkType
    first_uploaded: bool = False

    def __post_init__(self):
        if self.order == OrderMode.AUTO:
            self.order = OrderMode.NEW_FIRST if len(self.cache) else OrderMode.OLD_FIRST

    def upload(self):
        if self.link_type == LinkType.PLAYLIST:
            for u in [self.url] + [self.url / s for s in self.suffixes]:
                self._upload(
                    something=yoop.Playlist(u),
                    order=self.order,
                    break_on_first_cached=self.order == OrderMode.NEW_FIRST,
                    root=True,
                )
        elif self.link_type == LinkType.TRACK:
            self._upload(
                something=yoop.Media(self.url),
                order=self.order,
                break_on_first_cached=self.order == OrderMode.NEW_FIRST,
                root=True,
            )

    def _upload(
        self,
        something: yoop.Playlist | yoop.Media,
        order: OrderMode,
        break_on_first_cached: bool,
        root=False,
        album_title: str | None = None,
    ):
        if isinstance(something, yoop.Playlist):
            for e in something if order == OrderMode.NEW_FIRST else something[::-1]:
                if not e.available:
                    logging.info(f"{e} not available")
                    continue
                match e:
                    case yoop.Playlist():
                        if e in self.cache:
                            if order == OrderMode.OLD_FIRST:
                                continue
                            return
                        logging.info(f"<-- {e.url.value}")
                        self._upload(e, OrderMode.NEW_FIRST, order == OrderMode.NEW_FIRST)
                        if "bandcamp.com" in e.url.value:
                            self.cache.add(e)

                    case yoop.Media():
                        if e in self.cache:
                            if not break_on_first_cached:
                                continue
                            break
                        self._upload(e, order, break_on_first_cached, root, something.title)
        elif isinstance(something, yoop.Media):
            e = something
            try:
                logging.info(f"<-- {e.url.value}")
                downloaded = e.audio(self.format if self.format is not None else self.bitrate)
                converted = downloaded
                if (
                    (self.convert == ConvertMode.ALWAYS)
                    or (
                        (self.convert == ConvertMode.AUTO)
                        and downloaded.estimated_converted_size(self.bitrate) < 0.9 * len(downloaded)
                    )
                    or (downloaded.megabytes >= 49)
                ):
                    converted = downloaded.converted(
                        bitrate=self.bitrate,
                        samplerate=self.samplerate,
                        format=yoop.Audio.Format.MP3,
                        channels=self.channels,
                    )
                self.bot.load(
                    audio=converted,
                    tags=Bot.Tags(
                        title=e.title.simple,
                        album=album_title or "UnknownAlbum",
                        artist=e.uploader,
                        date=e.uploaded,
                        cover=e.thumbnail(150),
                    ),
                )
                if root or ("youtube.com" in e.url.value):
                    self.cache.add(e)
                self.first_uploaded = True
            except Exception as exception:
                logging.warning(f"exception while uploading {e} from {something} from {self.url}: {exception}")
                if "bandcamp.com" in e.url.value:
                    exit()
