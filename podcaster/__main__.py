import logging
import pathlib
from dataclasses import dataclass

import click
import yoop

from .Bot import Bot
from .Cache import Cache, Entry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s  %(message)s")


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
        self.loaded_cache = Cache(self.cache)
        self.bot = Bot(self.token, self.telegram)
        if self.order == "auto":
            self.order = "new_first" if len(self.loaded_cache) else "old_first"
        for u in [self.url / s for s in self.suffixes] + [self.url]:
            self.upload(yoop.Playlist(u))

    def upload(self, playlist: yoop.Playlist):
        for e in playlist if self.order == "new_first" else playlist[::-1]:
            match e:
                case yoop.Playlist():
                    if not e.available:
                        continue
                    if e in self.loaded_cache:
                        if self.order == "old_first":
                            continue
                        return
                    logging.info(f"<-- {e.url.value}")
                    self.upload(e)

                case yoop.Media():
                    if not e.available:
                        continue
                    if e in self.loaded_cache:
                        if self.order == "old_first":
                            continue
                        break

                    logging.info(f"<-- {e.title.simple} {e.uploaded}")

                    try:
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
                        self.loaded_cache.add(Entry.from_video(e))
                        self.first_uploaded = True
                    except Exception as exception:
                        logging.error(f"exception during processing {e}: {exception.__class__.__name__}: {exception}")
                        raise


def _cache_all(playlist: yoop.Playlist, cache: Cache):
    for e in playlist.items:
        if isinstance(e, yoop.Playlist):
            _cache_all(e, cache)
        elif isinstance(e, yoop.Media):
            if e in cache:
                logging.warning(f"{e.url} already exists")
                continue
            entry = Entry.from_video(e)
            cache.add(entry)
            logging.info(entry.row)


@cli.command(name="cache_all")
@click.option("--url", required=True, type=yoop.Url, help="Youtube channel or playlist URL")
@click.option(
    "-s", "--suffixes", required=False, type=str, help="Suffixes to generate additional urls", multiple=True, default=[]
)
@click.option("--cache", required=True, type=pathlib.Path, help="Path to cache file")
def cache_all(url: yoop.Url, suffixes: list[str], cache: pathlib.Path):
    _cache = Cache(cache)
    for u in [url] + [url / s for s in suffixes]:
        _cache_all(yoop.Playlist(u), _cache)


@cli.command(name="clean")
@click.option("--cache", required=True, type=pathlib.Path, help="Path to cache file")
def clean(cache: pathlib.Path):
    Cache(cache).dump()


cli()
