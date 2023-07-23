import io
import csv
import typing
import pathlib
import pydantic
import dataclasses



@pydantic.dataclasses.dataclass(frozen = False, kw_only = False)
class Cache:

	source    : typing.Final[pathlib.Path]
	hot       : set[str]                   = dataclasses.field(default_factory = set)
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

	def load(self):
		if not self.source.exists():
			self.hot.clear()
		else:
			with self.source.open(newline = '') as f:
				self.hot = {
					row[0]
					for row in self.reader(f)
				}

	def add(self, value: str):

		with self.source.open(mode = 'a', newline = '') as f:
			self.writer(f).writerow((value,))

		self.hot.add(value)

	def __contains__(self, value: str):
		return value in self.hot