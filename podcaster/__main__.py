import yoop
import click
import pathlib

from .Bot      import Bot
from .Cache    import Cache



@click.group
def cli():
	pass


def _upload(playlist: yoop.Playlist, bot: Bot, cache: Cache = Cache(pathlib.Path('cache.csv'))):

	print('playlist', playlist.title)

	if playlist in cache:
		return

	for e in playlist[::-1]:
		match e:
			case yoop.Playlist():
				_upload(e, bot, cache)
			case yoop.Video():
				if e.available and e not in cache:
					print('video', e.title.simple)
					bot.load(
						e.audio(
							yoop.Audio.Bitrate(90)
						).converted(
							bitrate    = yoop.Audio.Bitrate(75),
							samplerate = yoop.Audio.Samplerate(32000),
							format     = yoop.Audio.Format.MP3,
							channels   = yoop.Audio.Channels.one
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
@click.option('--url',      required = True,  type = yoop.Url, help = 'Youtube channel or playlist URL')
@click.option('--token',    required = True,  type = str,      help = 'Telegram bot token')
@click.option('--telegram', required = True,  type = str,      help = 'Telegram chat id')
def upload(url: yoop.Url, token: str, telegram: str):
	for p in (
		yoop.Playlist(url / 'playlists'),
		yoop.Playlist(url),
	):
		_upload(
			playlist = p,
			bot      = Bot(
				token = token,
				chat  = telegram
			)
		)


cli()