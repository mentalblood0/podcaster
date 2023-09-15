import yoop
import click
import pytags
import pathlib

from .Bot   import Bot
from .Cache import Cache



@click.group
def cli():
	pass


def _upload(
	playlist   : yoop.Playlist,
	bot        : Bot,
	cache      : Cache,
	bitrate    : yoop.Audio.Bitrate,
	samplerate : yoop.Audio.Samplerate,
	channels   : yoop.Audio.Channels
):

	if not playlist.available:
		cache.add(playlist)
		return

	if playlist in cache:
		return

	print(f'playlist {playlist.title}')

	for e in playlist[::-1]:

		match e:

			case yoop.Playlist():
				_upload(e, bot, cache, bitrate, samplerate, channels)

			case yoop.Video():

				if e not in cache:

					if not e.available:
						continue

					print(f'video {e.title.simple} {e.uploaded}')

					try:
						bot.load(
							e.audio().converted(
								bitrate    = bitrate,
								samplerate = samplerate,
								format     = yoop.Audio.Format.MP3,
								channels   = channels
							).tagged(
								title    = e.title.simple,
								album    = playlist.title,
								artist   = e.uploader,
								date     = str(e.uploaded)
							).covered(
								playlist.uploader.avatar.resized(150)
							)
						)
						cache.add(e)
					except pytags.Media.ValueError as exception:
						print(f'exception during processing {e}: {exception.__class__.__name__}: {exception}')
						pass

@cli.command(name = 'upload')
@click.option('--url',        required = True,  type = yoop.Url,                                                                                       help = 'Youtube channel or playlist URL')
@click.option('--token',      required = True,  type = str,                                                                                            help = 'Telegram bot token')
@click.option('--telegram',   required = True,  type = str,                                                                                            help = 'Telegram chat id')
@click.option('--cache',      required = True,  type = pathlib.Path,                                                                                   help = 'Path to cache file')
@click.option('--bitrate',    required = False, type = yoop.Audio.Bitrate,                                   default = 80,                             help = 'Resulting audio bitrate')
@click.option('--samplerate', required = False, type = yoop.Audio.Samplerate,                                default = 32000,                          help = 'Resulting audio samplerate')
@click.option('--channels',   required = False, type = click.Choice([c.value for c in yoop.Audio.Channels]), default = yoop.Audio.Channels.mono.value, help = 'Resulting audio channels')
@click.option('--previously-unavailable/--no-previously-unavailable', default=False)
def upload(
	url                    : yoop.Url,
	token                  : str,
	telegram               : str,
	cache                  : pathlib.Path,
	bitrate                : yoop.Audio.Bitrate,
	samplerate             : yoop.Audio.Samplerate,
	channels               : str,
	previously_unavailable : bool
):

	if yoop.Playlist(url)[0] in (
		_cache := Cache(
			source      = cache,
			unavailable = not previously_unavailable
		)
	):
		return

	for address in (
		url / 'playlists',
		url,
	):
		_upload(
			playlist   = yoop.Playlist(address),
			cache      = _cache,
			bitrate    = bitrate,
			samplerate = samplerate,
			channels   = yoop.Audio.Channels(channels),
			bot        = Bot(
				token = token,
				chat  = telegram
			)
		)


cli()