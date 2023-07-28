import time
import typing
import pydantic
import datetime



T = typing.TypeVar('T')


@pydantic.dataclasses.dataclass(frozen = True, kw_only = True)
class Repeater(typing.Generic[T]):

	f        : typing.Callable[[], T]
	interval : datetime.timedelta

	def __call__(self, stop: typing.Callable[[T], bool] = lambda _: False):

		start = datetime.datetime.now()

		n = 0
		while True:

			if stop((result := self.f())):
				return result

			time.sleep(
				(
					self.interval -
					(
						(datetime.datetime.now() - start) -
						self.interval * n
					)
				).total_seconds()
			)
			n += 1