import io
import csv
import typing
import pathlib
import pydantic
import dataclasses

from .Video import Video



@pydantic.dataclasses.dataclass(frozen = False, kw_only = False)
class Cache:

	source    : typing.Final[pathlib.Path]
	hot       : set[str]                   = dataclasses.field(default_factory = set)
	delimiter : typing.Final[str]          = ','
	quote     : typing.Final[str]          = '"'
	escape    : typing.Final[str]          = '\\'

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
					row[0]
					for row in self.reader(f)
				}

	def add(self, video: Video):

		with self.source.open(mode = 'a', newline = '', encoding = 'utf8') as f:
			self.writer(f).writerow((video.id,))

		self.hot.add(video.id)

	def __contains__(self, video: Video):
		return video.id in self.hot

	def filter(self, stream: typing.Iterable[Video]):
		return (
			e
			for e in stream
			if e not in self
		)