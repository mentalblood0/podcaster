import pathlib

import click
import yoop

from .Bot import Bot
from .Cache import Cache, Entry


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
    portioning_depth: int,
    convert: str,
):
    if playlist in cache:
        return
    for e in playlist[::1] if portioning_depth > 0 else playlist.items:
        match e:
            case yoop.Playlist():
                if not e.available:
                    continue
                if not len(e):
                    continue
                print(f"<-- {e.title}")
                _upload(
                    playlist=e,
                    bot=bot,
                    cache=cache,
                    bitrate=bitrate,
                    format=format,
                    samplerate=samplerate,
                    channels=channels,
                    portioning_depth=portioning_depth - 1,
                    convert=convert,
                )

            case yoop.Media():
                if not e.available:
                    continue
                if e in cache:
                    break

                print(f"<-- {e.title.simple} {e.uploaded}", end="", flush=True)

                try:
                    downloaded = e.audio(format if format is not None else bitrate)
                    print(f" {downloaded.megabytes}MB", end="", flush=True)

                    converted = downloaded
                    if (
                        (convert == "always")
                        or (
                            (convert == "reduce_size")
                            and downloaded.estimated_converted_size(bitrate) < len(downloaded)
                        )
                        or (downloaded.megabytes >= 50)
                    ):
                        converted = downloaded.converted(
                            bitrate=bitrate, samplerate=samplerate, format=yoop.Audio.Format.MP3, channels=channels
                        )

                    print(f" -> {converted.megabytes}MB")
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
                except ValueError as exception:
                    print(f"exception during processing {e}: {exception.__class__.__name__}: {exception}")


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
    "--portioning_depth",
    required=False,
    type=int,
    default=2,
    help="Depth of playlists for one-by-one items getting instead of getting all items at once",
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
    portioning_depth: int,
    convert: str,
):
    _cache = Cache(cache)
    for u in [url / s for s in suffixes] + [url]:
        _upload(
            playlist=yoop.Playlist(u, content=yoop.Playlist if url.value.endswith("/") else yoop.Media),
            cache=_cache,
            bitrate=yoop.Audio.Bitrate(bitrate),
            format=format,
            samplerate=yoop.Audio.Samplerate(samplerate),
            channels=yoop.Audio.Channels(channels),
            bot=Bot(token=token, chat=telegram),
            portioning_depth=portioning_depth,
            convert=convert,
        )


def _cache_all(playlist: yoop.Playlist, cache: Cache):
    for e in playlist.items:
        if isinstance(e, yoop.Playlist):
            _cache_all(e, cache)
        elif isinstance(e, yoop.Media):
            if e in cache:
                print(f"{e.url} already exists")
                continue
            entry = Entry.from_video(e)
            cache.add(entry)
            print(entry.row)


@cli.command(name="cache_all")
@click.option("--url", required=True, type=yoop.Url, help="Youtube channel or playlist URL")
@click.option(
    "-s", "--suffixes", required=False, type=str, help="Suffixes to generate additional urls", multiple=True, default=[]
)
@click.option("--cache", required=True, type=pathlib.Path, help="Path to cache file")
def cache_all(url: yoop.Url, suffixes: list[str], cache: pathlib.Path):
    _cache = Cache(cache)
    for u in [url] + [url / s for s in suffixes]:
        _cache_all(yoop.Playlist(u, content=yoop.Playlist if url.value.endswith("/") else yoop.Media), _cache)


@cli.command(name="clean")
@click.option("--cache", required=True, type=pathlib.Path, help="Path to cache file")
def clean(cache: pathlib.Path):
    Cache(cache).dump()


cli()
