import io
import pytube
import pydantic
import datetime
import http.client
import urllib.error
import pytube.exceptions

from .Cache     import Cache
from .Audio     import Audio
from .Avatar    import Avatar
from .Retrier   import Retrier
from .Loggable  import Loggable
from .Repeater  import Repeater



@pydantic.dataclasses.dataclass(frozen = True, kw_only = False, config = {'arbitrary_types_allowed': True})
class Playlist(Loggable):

	playlist: pytube.Playlist

	def __repr__(self):
		return f'{self.__class__.__name__}(title=\'{self.playlist.title}\')'

	def audio(self, avatar: Avatar, cache: Cache):

		for v in self.playlist.videos_generator():

			if v.video_id in cache:
				continue

			try:
				audio = Retrier(
					repeater   = Repeater(
						f        = lambda: v.streams.get_audio_only(),
						interval = datetime.timedelta(seconds = 3)
					),
					exceptions = {
						urllib.error.URLError
					}
				)()
			except (
				pytube.exceptions.AgeRestrictedError,
				pytube.exceptions.RegexMatchError,
				pytube.exceptions.LiveStreamError
			):
				continue

			if audio is None:
				continue

			raw = io.BytesIO()
			def download():
				raw.seek(0)
				audio.stream_to_buffer(raw)

			Retrier(
				repeater = Repeater(
					f        = download,
					interval = datetime.timedelta(seconds = 3)
				),
				exceptions = {
					http.client.IncompleteRead,
					http.client.RemoteDisconnected,
					urllib.error.URLError,
					pytube.exceptions.MaxRetriesExceeded
				}
			)()

			yield Audio(
				data     = raw.getvalue(),
				playlist = self.playlist,
				video    = v,
				avatar   = avatar
			).converted.tagged