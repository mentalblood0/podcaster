from enum import Enum


class ConvertMode(Enum):
    ALWAYS = "always"
    NEVER = "never"
    AUTO = "auto"


class OrderMode(Enum):
    NEW_FIRST = "new_first"
    OLD_FIRST = "old_first"
    AUTO = "auto"
