import re
import pytube
import requests
import pydantic
import functools

from .Cache    import Cache
from .Avatar   import Avatar
from .Playlist import Playlist
from .Loggable import Loggable



@pydantic.dataclasses.dataclass(frozen = True, kw_only = False)
class Channel(Loggable):

	name : str

	@functools.cached_property
	def id(self):
		return re.findall(
			r'/channel/([^\"]+)',
			requests.get(f'https://www.youtube.com/@{self.name}/featured').content.decode()
		)[0]

	@property
	def address(self):
		return f'https://www.youtube.com/@{self.name}'

	@functools.cached_property
	def avatar(self):
		return Avatar(f'https://www.youtube.com/@{self.name}')

	def downloaded(self, cache: Cache):
		return next(iter(pytube.Channel(self.address).videos)).video_id in cache

	@property
	def playlists(self):
		return (
			Playlist(pytube.Playlist(f'https://www.youtube.com/playlist?list={id}'))
			for id in reversed(
				re.findall(
					r'/playlist\?list=([^"]+)',
					requests.get(f'{self.address}/playlists').content.decode()
				)
			)
		)