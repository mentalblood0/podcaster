import yoop
import click

from .Bot      import Bot



@click.group
def cli():
	pass


def _upload(playlist: yoop.Playlist, bot: Bot):
	for e in playlist:
		match e:
			case yoop.Video():
				bot.load(
					e.audio(yoop.Audio.Bitrate(90)).converted.tagged(
						title  = e.title.simple,
						album  = playlist.title,
						artist = e.uploader
					)
				)
			case yoop.Playlist():
				_upload(e, bot)

@cli.command(name = 'upload')
@click.option('--url',      required = True,  type = yoop.Url, help = 'Youtube channel or playlist URL')
@click.option('--token',    required = True,  type = str,      help = 'Telegram bot token')
@click.option('--telegram', required = True,  type = str,      help = 'Telegram chat id')
def upload(url: yoop.Url, token: str, telegram: str):
	_upload(
		playlist = yoop.Playlist(url / 'playlists'),
		bot      = Bot(
			token = token,
			chat  = telegram
		)
	)


# def _tasks(token: str, files: tuple[Tasks, ...]):
# 	for tasks in files:
# 		for t in tasks.load():
# 			_upload(
# 				playlist = t.youtube,
# 				cache   = t.cache,
# 				bot     = Bot(
# 					token = token,
# 					chat  = t.telegram
# 				)
# 			)

# @cli.command(name = 'tasks')
# @click.option('--token', required = True, type = str,   help = 'Telegram bot token')
# @click.argument('files', required = True, type = Tasks, nargs = -1)
# def tasks(token: str, files: tuple[Tasks, ...]):
# 	_tasks(token, files)


cli()