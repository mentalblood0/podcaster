import time
import loguru
import typing
import pydantic
import datetime



T = typing.TypeVar('T')


@pydantic.dataclasses.dataclass(frozen = True, kw_only = True)
class Retrier(typing.Generic[T]):

	f          : typing.Callable[[], T]
	interval   : datetime.timedelta = datetime.timedelta(seconds = 3)
	exceptions : set[typing.Type[Exception]]

	def __call__(self):

		while True:

			try:
				return self.f()

			except Exception as e:

				if not any(
					isinstance(e, E)
					for E in self.exceptions
				):
					raise

				time.sleep(self.interval.total_seconds())

				loguru.logger.warning(f'Retrying {self.f} on exception {e.__class__.__name__}: {e}')