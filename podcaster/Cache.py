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

	@dataclasses.dataclass(frozen = False, kw_only = False, unsafe_hash = True)
	class Entry:

		uploader : str      = dataclasses.field(hash = True)
		title    : str      = dataclasses.field(hash = True)
		url      : yoop.Url = dataclasses.field(hash = False)
		uploaded : str      = dataclasses.field(hash = True)
		duration : str      = dataclasses.field(hash = True)

		def __eq__(self, another: object):
			match another:
				case Cache.Entry():
					return hash(self) == hash(another)
				case _:
					return False

		@property
		def row(self):
			return (
				self.uploader,
				self.title,
				self.url.value,
				self.uploaded,
				self.duration
			)

		@classmethod
		def from_video(cls, v: yoop.Video):
			if v.available:
				return cls(
					v.uploader,
					v.title.simple,
					v.url,
					str(v.uploaded),
					str(int(v.duration.total_seconds()))
				)
			else:
				return cls('', '', v.url, '', '')

		@classmethod
		def from_row(cls, r: tuple[str, str, str, str, str] | list[str]) -> typing.Self:
			match r:
				case tuple():
					return cls(
						r[0],
						r[1],
						yoop.Url(r[2]),
						r[3],
						r[4]
					)
				case list():
					if len(r) != 5:
						raise ValueError
					return Cache.Entry.from_row(tuple[str, str, str, str, str](r))

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

	def add(self, o: yoop.Video | Entry | yoop.Playlist):

		match o:

			case yoop.Video():
				self.add(Cache.Entry.from_video(o))

			case Cache.Entry():

				with self.source.open(mode = 'a', newline = '', encoding = 'utf8') as f:
					self.writer(f).writerow(o.row)

				self.entries.add(o)
				self.urls.add(o.url)

			case yoop.Playlist():
				for v in o:
					self.add(v)

	def __contains__(self, o: yoop.Video | yoop.Playlist):

		match o:

			case yoop.Video():

				if o.url in self.urls:
					return True

				if (not o.available) or (Cache.Entry.from_video(o) in self.entries):
					self.add(o)
					return True

				return False

			case yoop.Playlist():
				return all(v in self for v in o)