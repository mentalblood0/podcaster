import pathlib
import sys

import click
import yoop

from .Bot import Bot
from .Cache import Cache


@click.group
def cli():
    pass


def _upload(
    playlist: yoop.Playlist,
    bot: Bot,
    cache: Cache,
    bitrate: yoop.Audio.Bitrate,
    samplerate: yoop.Audio.Samplerate,
    channels: yoop.Audio.Channels,
):
    if not playlist.available:
        cache.add(playlist)
        return

    for e in playlist[::1]:
        match e:
            case yoop.Playlist():
                if not len(playlist):
                    continue
                if playlist in cache:
                    print(f"{e.title} already exists")
                    continue
                print(f"<-- {e.title}")
                _upload(e, bot, cache, bitrate, samplerate, channels)

            case yoop.Media():
                if e.liveness not in (yoop.Media.Liveness.was, yoop.Media.Liveness.no):
                    continue
                if e in cache:
                    break
                if not e.available:
                    print(f"{e.title.simple} not available")
                    continue

                print(f"<-- {e.title.simple} {e.uploaded}", end="")
                sys.stdout.flush()

                try:
                    downloaded = e.audio(bitrate)
                    if (downloaded.megabytes >= 50) or (downloaded.estimated_converted_size(bitrate) < len(downloaded)):
                        converted = downloaded.converted(
                            bitrate=bitrate, samplerate=samplerate, format=yoop.Audio.Format.MP3, channels=channels
                        )
                    else:
                        converted = downloaded

                    print(f" {downloaded.megabytes}MB -> {converted.megabytes}MB")
                    bot.load(
                        audio=converted,
                        tags=Bot.Tags(
                            cover=playlist.uploader.avatar.resized(150),
                            title=e.title.simple,
                            album=playlist.title,
                            artist=e.uploader,
                            date=e.uploaded,
                        ),
                    )
                    cache.add(e)
                except ValueError as exception:
                    print(f"exception during processing {e}: {exception.__class__.__name__}: {exception}")
                    raise
                    pass


@cli.command(name="upload")
@click.option("--url", required=True, type=yoop.Url, help="Youtube channel or playlist URL")
@click.option("--token", required=True, type=str, help="Telegram bot token")
@click.option("--telegram", required=True, type=str, help="Telegram chat id")
@click.option("--cache", required=True, type=pathlib.Path, help="Path to cache file")
@click.option("--bitrate", required=False, type=yoop.Audio.Bitrate, default=80, help="Resulting audio bitrate")
@click.option(
    "--samplerate", required=False, type=yoop.Audio.Samplerate, default=32000, help="Resulting audio samplerate"
)
@click.option(
    "--channels",
    required=False,
    type=click.Choice([c.value for c in yoop.Audio.Channels]),
    default=yoop.Audio.Channels.mono.value,
    help="Resulting audio channels",
)
def upload(
    url: yoop.Url,
    token: str,
    telegram: str,
    cache: pathlib.Path,
    bitrate: yoop.Audio.Bitrate,
    samplerate: yoop.Audio.Samplerate,
    channels: str,
):
    _cache = Cache(source=cache, unavailable=False)
    for address in (url / "streams", url / "playlists", url):
        _upload(
            playlist=yoop.Playlist(address),
            cache=_cache,
            bitrate=bitrate,
            samplerate=samplerate,
            channels=yoop.Audio.Channels(channels),
            bot=Bot(token=token, chat=telegram),
        )


@cli.command(name="clean")
@click.option("--cache", required=True, type=pathlib.Path, help="Path to cache file")
def clean(cache: pathlib.Path):
    Cache(source=cache, unavailable=True).dump()


cli()
