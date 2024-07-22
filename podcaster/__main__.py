import logging
import argparse
import pathlib
from enum import Enum
from dataclasses import dataclass

import yoop

from .Bot import Bot
from .Cache import Cache


parser = argparse.ArgumentParser(
    prog="podcaster", description="Upload audio from youtube/bandcamp to telegram channels"
)
parser.add_argument("-l", "--log", type=pathlib.Path, required=False, default=None)

subparsers = parser.add_subparsers(dest="command")

upload_subparser = subparsers.add_parser("upload", help='Upload from youtube/bandcamp to telegram channel')
upload_subparser.add_argument("--url", required=True, type=yoop.Url, help="Youtube channel or playlist URL")
upload_subparser.add_argument(
    "-s", "--suffixes", required=False, type=str, nargs="+", help="Suffixes to generate additional urls", default=[]
)
upload_subparser.add_argument("--token", required=True, type=str, help="Telegram bot token")
upload_subparser.add_argument("--telegram", required=True, type=str, help="Telegram chat id")
upload_subparser.add_argument("--cache", required=True, type=pathlib.Path, help="Path to cache file")
upload_subparser.add_argument(
    "--bitrate",
    required=False,
    type=yoop.Audio.Bitrate,
    default=yoop.Audio.Bitrate(80),
    help="Preferable audio bitrate",
)
upload_subparser.add_argument(
    "--format",
    required=False,
    choices=[c.value for c in yoop.Audio.Format],
    default=None,
    help="Preferable audio format",
)
upload_subparser.add_argument(
    "--samplerate",
    required=False,
    type=yoop.Audio.Samplerate,
    default=yoop.Audio.Samplerate(32000),
    help="Preferable audio samplerate",
)
upload_subparser.add_argument(
    "--channels",
    required=False,
    choices=[c.value for c in yoop.Audio.Channels],
    default=yoop.Audio.Channels.mono.value,
    help="Resulting audio channels",
)


class ConvertMode(Enum):
    ALWAYS = "always"
    NEVER = "never"
    AUTO = "auto"


upload_subparser.add_argument(
    "--convert",
    required=False,
    choices=[c.value for c in ConvertMode],
    default=ConvertMode.AUTO.value,
    help="Convert to mp3 with preferable bitrate and samplerate",
)


class OrderMode(Enum):
    NEW_FIRST = "new_first"
    OLD_FIRST = "old_first"
    AUTO = "auto"


upload_subparser.add_argument(
    "--order",
    required=False,
    choices=[c.value for c in OrderMode],
    default=OrderMode.AUTO.value,
    help="Which items process first",
)

args = parser.parse_args()
if args.log is None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s  %(message)s")
else:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s  %(message)s", filename=args.log)

if args.command == "upload":
    Uploader(
        url=args.url,
        suffixes=args.suffixes,
        bot=Bot(args.token, args.telegram),
        cache=Cache(args.cache),
        bitrate=args.bitrate,
        format=args.format,
        samplerate=args.samplerate,
        channels=args.channels,
        convert=args.convert,
        order=args.order,
    )


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
    first_uploaded: bool = False

    def __post_init__(self):
        if self.order == OrderMode.AUTO:
            self.order = OrderMode.NEW_FIRST if len(self.loaded_cache) else OrderMode.OLD_FIRST

    def upload(self):
        for u in [self.url / s for s in self.suffixes] + [self.url]:
            self.upload(
                playlist=yoop.Playlist(u),
                order=self.order,
                break_on_first_cached=self.order == OrderMode.NEW_FIRST,
                root=True,
            )

    def _upload(self, playlist: yoop.Playlist, order: str, break_on_first_cached: bool, root=False):
        for e in playlist if order == OrderMode.NEW_FIRST else playlist[::-1]:
            match e:
                case yoop.Playlist():
                    if not e.available:
                        continue
                    if e in self.loaded_cache:
                        if order == OrderMode.OLD_FIRST:
                            continue
                        return
                    logging.info(f"<-- {e.url.value}")
                    self._upload(e, OrderMode.NEW_FIRST, order == OrderMode.NEW_FIRST)
                    if "bandcamp.com" in e.url.value:
                        self.loaded_cache.add(e)

                case yoop.Media():
                    if not e.available:
                        continue
                    if e in self.loaded_cache:
                        if not break_on_first_cached:
                            continue
                        break

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
                                album=playlist.title,
                                artist=e.uploader,
                                date=e.uploaded,
                                cover=e.thumbnail(150),
                            ),
                            disable_notification=self.first_uploaded,
                        )
                        if root or ("youtube.com" in e.url.value):
                            self.loaded_cache.add(e)
                        self.first_uploaded = True
                    except Exception as exception:
                        logging.warning(f"exception while uploading {e} from {playlist} from {self.url}: {exception}")


cache_subparser = subparsers.add_parser("cache", help='Cache all youtube/bandcamp items as if they were already uploaded')
cache_subparser.add_argument("--url", required=True, type=yoop.Url, help="Youtube channel or playlist URL")
cache_subparser.add_argument(
    "-s", "--suffixes", required=False, type=str, nargs="+", help="Suffixes to generate additional urls", default=[]
)
cache_subparser.add_argument("--telegram", required=True, type=str, help="Telegram chat id")
cache_subparser.add_argument("--cache", required=True, type=pathlib.Path, help="Path to cache file")

if args.command == "cache":
    Cacher(url=args.url, suffixes=args.suffixes, cache=Cache(args.cache))


@dataclass
class Cacher:
    url: yoop.Url
    suffixes: list[str]
    cache: Cache

    def cache_all(self):
        self.cache.source.unlink(missing_ok=True)
        for u in [self.url] + [self.url / s for s in self.suffixes]:
            self._cache_all(yoop.Playlist(u))

    def _cache_all(self, playlist: yoop.Playlist):
        for e in playlist.items[::-1]:
            if isinstance(e, yoop.Playlist) and ("youtube.com" in e.url.value):
                self._cache_all(e)
            else:
                try:
                    if not e.available:
                        continue
                    self.cache.add(e)
                    logging.info(f"{self.cache.source} <- {Cache.hash(e).hex()} for {e.url.value}")
                except Exception as ex:
                    logging.warning(f"exception while caching {e} from {playlist} from {self.url}: {ex}")
