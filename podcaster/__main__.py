import logging
import pathlib

import click
import yoop

from .Bot import Bot
from .Cache import Cache, Entry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s  %(message)s")


@click.group
def cli():
    pass


def _upload(
    playlist: yoop.Playlist,
    bot: Bot,
    cache: Cache,
    bitrate: yoop.Audio.Bitrate,
    format: yoop.Audio.Format | None,
    samplerate: yoop.Audio.Samplerate,
    channels: yoop.Audio.Channels,
    convert: str,
    order: str,
):
    if order == "new_first":
        if playlist in cache:
            return
    for e in playlist if order == "new_first" else playlist[::-1]:
        match e:
            case yoop.Playlist():
                if not e.available:
                    continue
                if not len(e):
                    continue
                logging.info(f"<-- {e.title}")
                _upload(
                    playlist=e,
                    bot=bot,
                    cache=cache,
                    bitrate=bitrate,
                    format=format,
                    samplerate=samplerate,
                    channels=channels,
                    convert=convert,
                    order=order,
                )

            case yoop.Media():
                if not e.available:
                    continue
                if e in cache:
                    if order == "old_first":
                        continue
                    break

                logging.info(f"<-- {e.title.simple} {e.uploaded}")

                try:
                    downloaded = e.audio(format if format is not None else bitrate)

                    converted = downloaded
                    if (
                        (convert == "always")
                        or (
                            (convert == "reduce_size")
                            and downloaded.estimated_converted_size(bitrate) < 0.9 * len(downloaded)
                        )
                        or (downloaded.megabytes >= 50)
                    ):
                        converted = downloaded.converted(
                            bitrate=bitrate, samplerate=samplerate, format=yoop.Audio.Format.MP3, channels=channels
                        )
                    bot.load(
                        audio=converted,
                        tags=Bot.Tags(
                            title=e.title.simple,
                            album=playlist.title,
                            artist=e.uploader,
                            date=e.uploaded,
                            cover=e.thumbnail(150),
                        ),
                    )
                    cache.add(Entry.from_video(e))
                except Exception as exception:
                    logging.error(f"exception during processing {e}: {exception.__class__.__name__}: {exception}")


@cli.command(name="upload")
@click.option("--url", required=True, type=yoop.Url, help="Youtube channel or playlist URL")
@click.option(
    "-s", "--suffixes", required=False, type=str, help="Suffixes to generate additional urls", multiple=True, default=[]
)
@click.option("--token", required=True, type=str, help="Telegram bot token")
@click.option("--telegram", required=True, type=str, help="Telegram chat id")
@click.option("--cache", required=True, type=pathlib.Path, help="Path to cache file")
@click.option("--bitrate", required=False, type=int, default=80, help="Preferable audio bitrate")
@click.option("--format", required=False, type=yoop.Audio.Format, help="Preferable audio format")
@click.option("--samplerate", required=False, type=int, default=32000, help="Preferable audio samplerate")
@click.option(
    "--channels",
    required=False,
    type=click.Choice([c.value for c in yoop.Audio.Channels]),
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
def upload(
    url: yoop.Url,
    suffixes: str,
    token: str,
    telegram: str,
    cache: pathlib.Path,
    bitrate: int,
    format: yoop.Audio.Format | None,
    samplerate: int,
    channels: str,
    convert: str,
    order: str,
):
    _cache = Cache(cache)
    if order == "auto":
        order = "new_first" if len(_cache) else "old_first"
    for u in [url / s for s in suffixes] + [url]:
        _upload(
            playlist=yoop.Playlist(u),
            cache=_cache,
            bitrate=yoop.Audio.Bitrate(bitrate),
            format=format,
            samplerate=yoop.Audio.Samplerate(samplerate),
            channels=yoop.Audio.Channels(channels),
            bot=Bot(token=token, chat=telegram),
            convert=convert,
            order=order,
        )


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
