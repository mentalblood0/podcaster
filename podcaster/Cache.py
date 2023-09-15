import io
import csv
import yoop
import typing
import pathlib
import dataclasses


@dataclasses.dataclass(frozen = False, kw_only = False, unsafe_hash = True)
class Entry:

	uploader : str      = dataclasses.field(hash = True)
	title    : str      = dataclasses.field(hash = True)
	url      : yoop.Url = dataclasses.field(hash = False)
	uploaded : str      = dataclasses.field(hash = True)
	duration : str      = dataclasses.field(hash = True)

	def __eq__(self, another: object):
		match another:
			case Entry():
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
					uploader = r[0],
					title    = r[1],
					url      = yoop.Url(r[2]),
					uploaded = r[3],
					duration = r[4]
				)
			case list():
				if len(r) != 5:
					raise ValueError
				return Entry.from_row(tuple[str, str, str, str, str](r))

@dataclasses.dataclass(frozen = False, kw_only = False, unsafe_hash = True)
class Entries:

	by_url : dict[yoop.Url, Entry]    = dataclasses.field(default_factory = dict)
	plain  : set[Entry]               = dataclasses.field(default_factory = set)

	def add(self, e: Entry):

		if (
			(e in self.plain) and
			(old := ({e} & self.plain).pop().url) != e.url
		):
			del self.by_url[old]
			self.plain.remove(e)

		self.by_url[e.url] = e
		self.plain.add(e)

	def remove(self, e: Entry):
		del self.by_url[e.url]
		self.plain.remove(e)

	def url(self, e: typing.Union[Entry, yoop.Video]):
		return e.url in self.by_url

	def available(self, e: typing.Union[Entry, yoop.Video]):
		return self.by_url[e.url].title

	def clear(self):
		self.by_url.clear()
		self.plain.clear()

	def __contains__(self, e: Entry):
		return e in self.plain


@dataclasses.dataclass(frozen = False, kw_only = True)
class Cache:

	source       : typing.Final[pathlib.Path]
	unavailable  : bool
	entries      : Entries                  = Entries()
	delimiter    : typing.Final[str]          = ','
	quote        : typing.Final[str]          = '"'
	escape       : typing.Final[str]          = '\\'

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
		with self.source.open(newline = '', encoding = 'utf8') as f:
			for row in self.reader(f):
				self.entries.add(Entry.from_row(row))

	def add(self, o: yoop.Video | Entry | yoop.Playlist):

		match o:

			case yoop.Video():
				self.add(Entry.from_video(o))

			case Entry():

				with self.source.open(mode = 'a', newline = '', encoding = 'utf8') as f:
					self.writer(f).writerow(o.row)

				if self.entries.url(o):
					self.entries.remove(o)
				self.entries.add(o)

			case yoop.Playlist():
				for v in o:
					self.add(v)

	def __contains__(self, o: yoop.Video | yoop.Playlist):

		print(f'contains {o}')

		match o:

			case yoop.Video():

				if (
					self.entries.url(o) and
					(
						self.unavailable or
						self.entries.available(o)
					)
				):
					return True

				if not o.available:
					self.add(o)
					return True

				if Entry.from_video(o) in self.entries:
					if not self.entries.url(o):
						self.add(o)
					return True

				return False

			case yoop.Playlist():
				return all(v in self for v in o)