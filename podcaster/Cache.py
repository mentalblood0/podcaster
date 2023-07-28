import io
import csv
import pytube
import typing
import pathlib
import pydantic
import dataclasses

from .Video import Video



@pydantic.dataclasses.dataclass(frozen = False, kw_only = False)
class Cache:

	source    : typing.Final[pathlib.Path]
	hot       : set[Video]                 = dataclasses.field(default_factory = set)
	delimiter : typing.Final[str]          = ' '
	quotechar : typing.Final[str]          = '|'

	def reader(self, file: io.TextIOWrapper):
		return csv.reader(
			file,
			delimiter = self.delimiter,
			quotechar = self.quotechar
		)

	def writer(self, file: io.TextIOWrapper):
		return csv.writer(
			file,
			delimiter = self.delimiter,
			quotechar = self.quotechar,
			quoting   = csv.QUOTE_MINIMAL
		)

	@classmethod
	def video(cls, id: str):
		return Video(
			source   = pytube.YouTube.from_id(id),
			playlist = None
		)

	def load(self):
		if not self.source.exists():
			self.hot.clear()
		else:
			with self.source.open(newline = '') as f:
				self.hot = {
					self.video(row[0])
					for row in self.reader(f)
				}

	def add(self, value: str):

		with self.source.open(mode = 'a', newline = '') as f:
			self.writer(f).writerow((value,))

		self.hot.add(self.video(value))

	def __contains__(self, value: Video):
		return value in self.hot

	def filter(self, stream: typing.Iterable[Video]):
		return (
			e
			for e in stream
			if e not in self
		)