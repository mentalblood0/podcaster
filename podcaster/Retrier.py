import typing
import dataclasses

from .Repeater import Repeater


T = typing.TypeVar("T")


@dataclasses.dataclass(frozen=True, kw_only=True)
class Retrier(typing.Generic[T]):
    repeater: Repeater[T]
    exceptions: set[typing.Type[Exception]]

    def execute(self):
        try:
            return self.repeater.f()

        except Exception as e:
            if not any(isinstance(e, E) for E in self.exceptions):
                raise

            print(f"Will retry {self.repeater.f} as it failed with exception {e.__class__.__name__}: {e}")
            return False

    def __call__(self):
        return self.repeater(stop=lambda result: result is not False)
