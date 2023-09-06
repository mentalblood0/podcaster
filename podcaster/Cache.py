import io
import csv
import yoop
import typing
import pathlib
import dataclasses



@dataclasses.dataclass(frozen = False, kw_only = False)
class Cache:

	source    : typing.Final[pathlib.Path]
	entries   : set['Entry']               = dataclasses.field(default_factory = set)
	urls      : set[yoop.Url]              = dataclasses.field(default_factory = set)
	delimiter : typing.Final[str]          = ','
	quote     : typing.Final[str]          = '"'
	escape    : typing.Final[str]          = '\\'

	@dataclasses.dataclass(frozen = False, kw_only = False)
	class Entry:

		uploader : str
		title    : str
		url      : yoop.Url

		@property
		def row(self):
			return (
				self.uploader,
				self.title,
				self.url.value
			)

		def __hash__(self):
			return hash(self.row[:-1])

		@classmethod
		def from_video(cls, v: yoop.Video):
			return cls(
				v.uploader,
				v.title.simple,
				v.url
			)

		@classmethod
		def from_row(cls, r: tuple[str, str, str] | list[str]) -> typing.Self:
			match r:
				case tuple():
					return cls(
						r[0],
						r[1],
						yoop.Url(r[2])
					)
				case list():
					if len(r) != 3:
						raise ValueError
					return Cache.Entry.from_row(tuple(r))

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

		if not self.source.exists():
			return

		self.entries.clear()
		self.urls.clear()
		with self.source.open(newline = '', encoding = 'utf8') as f:
			for row in self.reader(f):
				entry = Cache.Entry.from_row(row)
				self.entries.add(entry)
				self.urls.add(entry.url)

	def add(self, video: yoop.Video):

		if (video in self) and (video.url in self.urls):
			return

		entry = Cache.Entry.from_video(video)

		with self.source.open(mode = 'a', newline = '', encoding = 'utf8') as f:
			self.writer(f).writerow(entry.row)

		self.entries.add(entry)
		self.urls.add(entry.url)

	def __contains__(self, o: yoop.Video | yoop.Playlist):

		match o:

			case yoop.Video():

				if o.url in self.urls:
					return True

				if not o.available:
					self.urls.add(o.url)
					with self.source.open(mode = 'a', newline = '', encoding = 'utf8') as f:
						self.writer(f).writerow(
							Cache.Entry.from_row(('', '', o.url.value)).row
						)
					return o in self

				if Cache.Entry.from_video(o) in self.entries:
					return True

				return False

			case yoop.Playlist():
				return all(v in self for v in o)