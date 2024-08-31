import argparse
import logging
import pathlib

import yoop

from .enums import ConvertMode, LinkType, OrderMode

parser = argparse.ArgumentParser(
    prog="podcaster", description="Upload audio from youtube/bandcamp to telegram channels"
)
parser.add_argument("-l", "--log", type=pathlib.Path, required=False, default=None)

subparsers = parser.add_subparsers(dest="command")

upload_subparser = subparsers.add_parser("upload", help="Upload from youtube/bandcamp to telegram channel")
upload_subparser.add_argument("--url", required=True, type=yoop.Url, help="Channel or playlist URL")
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
    type=yoop.Audio.Format,
    choices=[c for c in yoop.Audio.Format],
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
    type=yoop.Audio.Channels,
    choices=[c for c in yoop.Audio.Channels],
    default=yoop.Audio.Channels.mono.value,
    help="Resulting audio channels",
)
upload_subparser.add_argument(
    "--convert",
    required=False,
    type=ConvertMode,
    choices=[c for c in ConvertMode],
    default=ConvertMode.AUTO.value,
    help="Convert to mp3 with preferable bitrate and samplerate",
)
upload_subparser.add_argument(
    "--order",
    required=False,
    type=OrderMode,
    choices=[c for c in OrderMode],
    default=OrderMode.AUTO.value,
    help="Which items process first",
)
upload_subparser.add_argument(
    "--link_type",
    required=False,
    type=LinkType,
    choices=[c for c in LinkType],
    default=LinkType.PLAYLIST,
    help="Link content type",
)
cache_subparser = subparsers.add_parser(
    "cache", help="Cache all youtube/bandcamp items as if they were already uploaded"
)
cache_subparser.add_argument("--url", required=True, type=yoop.Url, help="Youtube channel or playlist URL")
cache_subparser.add_argument(
    "-s", "--suffixes", required=False, type=str, nargs="+", help="Suffixes to generate additional urls", default=[]
)
cache_subparser.add_argument("--cache", required=True, type=pathlib.Path, help="Path to cache file")

args = parser.parse_args()
if not args.command:
    parser.print_help()
    exit()

if args.log is None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s  %(message)s")
else:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s  %(message)s", filename=args.log)

from .Cache import Cache

if args.command == "upload":
    from .Bot import Bot
    from .Uploader import Uploader

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
        link_type=args.link_type,
    ).upload()
if args.command == "cache":
    from .Cacher import Cacher

    Cacher(url=args.url, suffixes=args.suffixes, cache=Cache(args.cache)).cache_all()
