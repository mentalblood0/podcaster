import logging
import pathlib
from dataclasses import dataclass

import click
import yoop

from .Bot import Bot
from .Cache import Cache


@click.group
def cli():
    pass


@cli.command(name="upload")
@click.option("--url", required=True, type=yoop.Url, help="Youtube channel or playlist URL")
@click.option(
    "-s", "--suffixes", required=False, type=str, help="Suffixes to generate additional urls", multiple=True, default=[]
)
@click.option("--token", required=True, type=str, help="Telegram bot token")
@click.option("--telegram", required=True, type=str, help="Telegram chat id")
@click.option("--cache", required=True, type=pathlib.Path, help="Path to cache file")
@click.option("--bitrate", required=False, type=yoop.Audio.Bitrate, default=80, help="Preferable audio bitrate")
@click.option("--format", required=False, type=yoop.Audio.Format, help="Preferable audio format")
@click.option(
    "--samplerate", required=False, type=yoop.Audio.Samplerate, default=32000, help="Preferable audio samplerate"
)
@click.option(
    "--channels",
    required=False,
    type=yoop.Audio.Channels,
    default=yoop.Audio.Channels.mono.value,
    help="Resulting audio channels",
)
@click.option(
    "--convert",
    required=False,
    type=click.Choice(["always", "reduce_size", "no"]),
    default="reduce_size",
    help="How to convert",
)
@click.option(
    "--order",
    required=False,
    type=click.Choice(["auto", "new_first", "old_first"]),
    default="auto",
    help="How to order",
)
@dataclass
class Uploader:
    url: yoop.Url
    suffixes: list[str]
    token: str
    telegram: str
    cache: pathlib.Path
    bitrate: yoop.Audio.Bitrate
    format: yoop.Audio.Format | None
    samplerate: yoop.Audio.Samplerate
    channels: yoop.Audio.Channels
    convert: str
    order: str
    first_uploaded: bool = False

    def __post_init__(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s  %(message)s")

        self.loaded_cache = Cache(self.cache)
        self.bot = Bot(self.token, self.telegram)
        if self.order == "auto":
            self.order = "new_first" if len(self.loaded_cache) else "old_first"
        for u in [self.url / s for s in self.suffixes] + [self.url]:
            self.upload(yoop.Playlist(u), self.order, self.order == "new_first")

    def upload(self, playlist: yoop.Playlist, order: str, break_on_first_cached: bool):
        for e in playlist if order == "new_first" else playlist[::-1]:
            match e:
                case yoop.Playlist():
                    if not e.available:
                        continue
                    if e in self.loaded_cache:
                        if order == "old_first":
                            continue
                        return
                    logging.info(f"<-- {e.url.value}")
                    self.upload(e, "new_first", order == "new_first")
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
                            (self.convert == "always")
                            or (
                                (self.convert == "reduce_size")
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
                        if "youtube.com" in e.url.value:
                            self.loaded_cache.add(e)
                        self.first_uploaded = True
                    except Exception as exception:
                        logging.warning(f"exception while uploading {e} from {playlist} from {self.url}: {exception}")


@cli.command(name="cache_all")
@click.option("--url", required=True, type=yoop.Url, help="Youtube channel or playlist URL")
@click.option(
    "-s", "--suffixes", required=False, type=str, help="Suffixes to generate additional urls", multiple=True, default=[]
)
@click.option("--cache", required=True, type=pathlib.Path, help="Path to cache file")
@click.option("--log", required=True, type=pathlib.Path, help="Path to log file")
@dataclass
class Cacher:
    url: yoop.Url
    suffixes: list[str]
    cache: pathlib.Path
    log: pathlib.Path

    def __post_init__(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s  %(message)s", filename=self.log)

        self.cache.unlink(missing_ok=True)
        self.loaded_cache = Cache(self.cache)

        for u in [self.url] + [self.url / s for s in self.suffixes]:
            self.cache_all(yoop.Playlist(u))
        logging.info(f"finished caching {self.url}")

    def cache_all(self, playlist: yoop.Playlist):
        for e in playlist.items[::-1]:
            if isinstance(e, yoop.Playlist) and ("youtube.com" in e.url.value):
                self.cache_all(e)
            else:
                try:
                    if not e.available:
                        continue
                    self.loaded_cache.add(e)
                    logging.info(f"{self.loaded_cache.source} <- {Cache.hash(e).hex()} for {e.url.value}")
                except Exception as ex:
                    logging.warning(f"exception while caching {e} from {playlist} from {self.url}: {ex}")


cli()
