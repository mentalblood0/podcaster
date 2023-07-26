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
			requests.get(f'{self.address}/featured').content.decode()
		)[0]

	@property
	def address(self):
		return f'https://www.youtube.com/@{self.name}'

	@functools.cached_property
	def avatar(self):
		return Avatar(self.address)

	@property
	def last(self):
		return next(
			re.finditer(
				r'\/watch\?v=([^"]+)',
				requests.get(f'{self.address}/videos').text
			)
		).groups()[0]

	def downloaded(self, cache: Cache):
		return self.last in cache

	@property
	def playlists(self):
		return (
			Playlist(pytube.Playlist(f'https://www.youtube.com/playlist?list={id}'))
			for id in re.findall(
				r'/playlist\?list=([^"]+)',
				requests.get(f'{self.address}/playlists?sort=lad').text
			)
		)