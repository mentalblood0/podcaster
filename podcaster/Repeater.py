import time
import typing
import pydantic
import datetime



@pydantic.dataclasses.dataclass(frozen = True, kw_only = True)
class Repeater:

	f          : typing.Callable[[], None]
	interval   : datetime.timedelta

	def __call__(self):

		start = datetime.datetime.now()

		n = 0
		while True:
			self.f()
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