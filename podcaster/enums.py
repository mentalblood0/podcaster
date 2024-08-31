from enum import Enum


class ConvertMode(Enum):
    ALWAYS = "always"
    NEVER = "never"
    AUTO = "auto"

    def __str__(self):
        return self.value


class OrderMode(Enum):
    NEW_FIRST = "new_first"
    OLD_FIRST = "old_first"
    AUTO = "auto"

    def __str__(self):
        return self.value


class LinkType(Enum):
    PLAYLIST = "playlist"
    TRACK = "track"

    def __str__(self):
        return self.value
