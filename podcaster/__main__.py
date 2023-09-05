import yoop
import click
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

	print('playlist', playlist.title)

	if playlist in cache:
		return

	for e in playlist[::-1]:
		match e:
			case yoop.Playlist():
				_upload(e, bot, cache, bitrate, samplerate, channels)
			case yoop.Video():
				if e.available and e not in cache:
					print('video', e.title.simple)
					bot.load(
						e.audio(
							yoop.Audio.Bitrate(90)
						).converted(
							bitrate    = bitrate,
							samplerate = samplerate,
							format     = yoop.Audio.Format.MP3,
							channels   = channels
						).tagged(
							title  = e.title.simple,
							album  = playlist.title,
							artist = e.uploader
						).covered(
							playlist.uploader.avatar.resized(150)
						)
					)
				cache.add(e)

@cli.command(name = 'upload')
@click.option('--url',        required = True,  type = yoop.Url,                                                      help = 'Youtube channel or playlist URL')
@click.option('--token',      required = True,  type = str,                                                           help = 'Telegram bot token')
@click.option('--telegram',   required = True,  type = str,                                                           help = 'Telegram chat id')
@click.option('--cache',      required = True,  type = pathlib.Path,                                                  help = 'Path to cache file')
@click.option('--bitrate',    required = False, type = yoop.Audio.Bitrate,    default = yoop.Audio.Bitrate(80),       help = 'Resulting audio bitrate')
@click.option('--samplerate',	print('playlist', playlist.title)

	if playlist in cache:
		return

	for e in playlist[::-1]:
		match e:
			case yoop.Playlist():
				_upload(e, bot, cache, bitrate, samplerate, channels)
			case yoop.Video():
				if e.available and e not in cache:
					print('video', e.title.simple)
					bot.load(
						e.audio(
							yoop.Audio.Bitrate(90)
						).converted(
							bitrate    = bitrate,
							samplerate = samplerate,
							format     = yoop.Audio.Format.MP3,
							channels   = channels
						).tagged(
							title  = e.title.simple,
							album  = playlist.title,
							artist = e.uploader
						).covered(
							playlist.uploader.avatar.resized(150)
						)
					)
				cache.add(e) required = False, type = yoop.Audio.Samplerate, default = yoop.Audio.Samplerate(32000), help = 'Resulting audio samplerate')
@click.option('--channels',   required = False, type = click.Choice([c.name for c in yoop.Audio.Channels]),   default = yoop.Audio.Channels.mono,     help = 'Resulting audio channels')
def upload(
	url           : yoop.Url,
	token         : str,
	telegram      : str,
	cache         : pathlib.Path,
	bitrate       : yoop.Audio.Bitrate,
	samplerate    : yoop.Audio.Samplerate,
	channels_name : str
):
	for p in (
		yoop.Playlist(url / 'playlists'),
		yoop.Playlist(url),
	):
		_upload(
			playlist   = p,
			cache      = Cache(cache),
			bitrate    = bitrate,
			samplerate = samplerate,
			channels   = yoop.Audio.Channels(channels_name),
			bot        = Bot(
				token = token,
				chat  = telegram
			)
		)


cli()