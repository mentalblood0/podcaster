import io
import pytube
import pydantic
import datetime
import functools
import http.client
import urllib.error
import pytube.exceptions

from .Audio    import Audio
from .Avatar   import Avatar
from .Retrier  import Retrier
from .Repeater import Repeater
from .Loggable import Loggable



@pydantic.dataclasses.dataclass(frozen = True, kw_only = True, config = {'arbitrary_types_allowed': True})
class Video(Loggable):

	source   : pytube.YouTube
	playlist : pytube.Playlist | None

	def __repr__(self):
		return f'Video(author=\'{self.source.author}\', title=\'{self.source.title}\')'

	@functools.cached_property
	def id(self):
		return f'{self.source.author} - {self.source.title}'

	def __hash__(self):
		return hash(self.id)

	def audio(self, avatar: Avatar):

		try:
			audio = Retrier(
				repeater   = Repeater(
					f        = lambda: self.source.streams.get_audio_only(),
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
			return None

		if audio is None:
			return audio

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

		return Audio(
			data     = raw.getvalue(),
			playlist = self.playlist,
			video    = self.source,
			avatar   = avatar
		).converted.tagged