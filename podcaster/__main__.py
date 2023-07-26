import click

from .Bot     import Bot
from .Tasks   import Tasks
from .Cache   import Cache
from .Channel import Channel



@click.group
def cli():
	pass


def _upload(youtube: Channel, bot: Bot, cache: Cache):

	cache.load()
	if youtube.downloaded(cache):
		return

	for p in youtube.playlists:

		for a in p.audio(youtube.avatar, cache):
			bot.load(a)
			cache.add(a.id)

@cli.command(name = 'upload')
@click.option('--youtube',  required = True,  type = Channel, help = 'Youtube channel name as it is in browser address line')
@click.option('--token',    required = True,  type = str,     help = 'Telegram bot token')
@click.option('--telegram', required = True,  type = str,     help = 'Telegram chat id')
@click.option('--cache',    required = True,  type = Cache,   help = 'Path to cache file to not repeat uploads')
def upload(youtube: Channel, token: str, telegram: str, cache: Cache):
	return _upload(
		youtube = youtube,
		cache   = cache,
		bot     = Bot(
			token = token,
			chat  = telegram
		)
	)


@cli.command(name = 'tasks')
@click.option('--token', required = True, type = str,               help = 'Telegram bot token')
@click.argument('files', required = True, type = Tasks, nargs = -1)
def tasks(token: str, files: tuple[Tasks, ...]):

	for tasks in files:
		for t in tasks.load():
			_upload(
				youtube = t.youtube,
				cache   = t.cache,
				bot     = Bot(
					token = token,
					chat  = t.telegram
				)
			)

cli()