import io
import csv
import typing
import pathlib
import pydantic
import dataclasses

from .Cache    import Cache
from .Channel  import Channel
from .Loggable import Loggable



@pydantic.dataclasses.dataclass(frozen = True, kw_only = False)
class Task:

	youtube  : Channel
	telegram : str
	cache    : Cache


@pydantic.dataclasses.dataclass(frozen = True, kw_only = False)
class Tasks(Loggable):

	source    : typing.Final[pathlib.Path]
	delimiter : typing.Final[str]          = dataclasses.field(default = ',', repr = False)
	quotechar : typing.Final[str]          = dataclasses.field(default = '|', repr = False)

	def reader(self, file: io.TextIOWrapper):
		return csv.reader(
			file,
			delimiter = self.delimiter,
			quotechar = self.quotechar
		)

	def load(self):
		if self.source.exists():
			with self.source.open(newline = '') as f:
				for row in self.reader(f):
					yield Task(
						youtube  = Channel(row[0]),
						telegram = row[1],
						cache    = Cache(pathlib.Path(row[2]))
					)
		else:
			return ()