import sys
import loguru
import pydantic



loguru.logger.remove()
loguru.logger.add(
	sink   = sys.stderr,
	format = "{time} | {message}"
)


@pydantic.dataclasses.dataclass(frozen = True, kw_only = False)
class Loggable:

	def __post_init__(self):
		loguru.logger.info(self)