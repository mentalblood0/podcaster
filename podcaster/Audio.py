import io
import math
import pytube
import pydantic
import functools
import subprocess
import dataclasses
import mutagen.mp3
import mutagen.id3
import mutagen.easyid3
import pytube.exceptions

from .Avatar   import Avatar
from .Loggable import Loggable



@pydantic.dataclasses.dataclass(frozen = True, kw_only = False)
class PartNumber:

	current : int
	total   : int


@pydantic.dataclasses.dataclass(frozen = True, kw_only = True, config = {'arbitrary_types_allowed': True})
class Audio(Loggable):

	data     : bytes
	playlist : pytube.Playlist | None
	video    : pytube.YouTube
	avatar   : Avatar
	part     : PartNumber      | None = None

	def __repr__(self):
		return f'{self.__class__.__name__}(playlist=\'{self.playlist.title if self.playlist else ''}\', title=\'{self.video.title}\', part={self.part}, size={self.size})'

	@functools.cached_property
	def id(self):
		return self.video.video_id

	@property
	def converted(self):
		return dataclasses.replace(
			self,
			data = subprocess.run(
				args = (
					'ffmpeg',
					'-y',
					'-hide_banner', '-loglevel', 'error',
					'-i', '-',
					'-vn', '-ar', '32000', '-ac', '1', '-b:a', '96k',
					'-f', 'mp3',
					'-'
				),
				input          = self.data,
				capture_output = True
			).stdout
		)

	def splitted(self, parts: int):
		return (
			dataclasses.replace(
				self,
				data = subprocess.run(
					args = (
						'ffmpeg',
						'-y',
						'-hide_banner', '-loglevel', 'error',
						'-ss', str(math.floor(self.duration / parts * n)),
						'-i', '-',
						'-t', str(math.ceil(self.duration / parts)),
						'-vn', '-ar', '32000', '-ac', '1', '-b:a', '96k',
						'-f', 'mp3',
						'-'
					),
					input          = self.data,
					capture_output = True
				).stdout,
				part = PartNumber(n + 1, parts)
			).tagged
			for n in range(parts)
		)

	@property
	def io(self):
		return io.BytesIO(self.data)

	@functools.cached_property
	def duration(self):
		return mutagen.mp3.MP3(self.io).info.length

	@functools.cached_property
	def cover(self) -> bytes:
		return mutagen.id3.ID3(self.io).getall('APIC')[0].data

	@functools.cached_property
	def tags(self):
		return mutagen.easyid3.EasyID3(self.io)

	@property
	def size(self):
		return len(self.data)

	@property
	def tagged(self):

		data_io = self.io
		tags    = mutagen.easyid3.EasyID3(data_io)

		tags.update({
			'title'    : self.video.title,
			'artist'   : self.video.author,
			'composer' : self.video.author,
			'album'    : self.playlist.title if self.playlist else 'Unknown Album'
		})
		tags.save(data_io)

		data_io.seek(0)
		_tags = mutagen.id3.ID3(data_io)
		_tags.add(
			mutagen.id3.APIC(
				3,
				'image/jpeg',
				3,
				'Front cover',
				self.avatar.data
			)
		)
		_tags.save(data_io)

		return dataclasses.replace(
			self,
			data = data_io.getvalue()
		)