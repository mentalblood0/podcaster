import io
import csv
import yoop
import typing
import pathlib
import dataclasses



@dataclasses.dataclass(frozen = False, kw_only = False)
class Cache:

	source    : typing.Final[pathlib.Path]
	hot       : set[tuple[str, str]]       = dataclasses.field(default_factory = set)
	delimiter : typing.Final[str]          = ','
	quote     : typing.Final[str]          = '"'
	escape    : typing.Final[str]          = '\\'

	def __post_init__(self):
		self.load()

	def reader(self, file: io.TextIOWrapper):
		return csv.reader(
			file,
			delimiter  = self.delimiter,
			quotechar  = self.quote,
			escapechar = self.escape
		)

	def writer(self, file: io.TextIOWrapper):
		return csv.writer(
			file,
			delimiter  = self.delimiter,
			quotechar  = self.quote,
			escapechar = self.escape,
			quoting    = csv.QUOTE_MINIMAL
		)

	def load(self):
		if self.source.exists():
			with self.source.open(newline = '', encoding = 'utf8') as f:
				self.hot = {
					tuple(row)
					for row in self.reader(f)
				}

	def id(self, video: yoop.Video):
		return (video.uploader, video.title.simple)

	def add(self, video: yoop.Video):

		if video in self:
			return

		with self.source.open(mode = 'a', newline = '', encoding = 'utf8') as f:
			self.writer(f).writerow(self.id(video))

		self.hot.add(self.id(video))

	def __contains__(self, o: yoop.Video | yoop.Playlist):
		match o:
			case yoop.Video():
				return (not o.available) or (self.id(o) in self.hot)
			case yoop.Playlist():
				return all(v in self for v in o)

	def filter(self, stream: typing.Iterable[yoop.Video | yoop.Playlist]):
		return (
			e
			for e in stream
			if e not in self
		)