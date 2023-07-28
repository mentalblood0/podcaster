import pytube
import pydantic
import pytube.exceptions

from .Video     import Video
from .Loggable  import Loggable



@pydantic.dataclasses.dataclass(frozen = True, kw_only = False, config = {'arbitrary_types_allowed': True})
class Playlist(Loggable):

	playlist: pytube.Playlist

	def __repr__(self):
		return f'{self.__class__.__name__}(title=\'{self.playlist.title}\')'

	@property
	def video(self):
		return (
			Video(
				source   = v,
				playlist = self.playlist
			)
			for v in self.playlist.videos_generator()
		)