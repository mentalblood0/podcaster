import io
import pytube
import pydantic
import datetime
import functools
import http.client
import urllib.error
import pytube.exceptions

from .Audio    import Audio
from .Retrier  import Retrier
from .Channel  import Channel
from .Repeater import Repeater



@pydantic.dataclasses.dataclass(frozen = True, kw_only = True)
class Video:

	source   : pytube.YouTube
	playlist : pytube.Playlist | None

	@functools.cached_property
	def id(self):
		return self.source.video_id

	@property
	def audio(self):

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
			avatar   = Channel(self.source.channel_url).avatar
		).converted.tagged