import hashlib
import pathlib
import typing
from dataclasses import dataclass, field

import yoop


@dataclass(frozen=False, kw_only=False)
class Cache:
    source: typing.Final[pathlib.Path]
    hashes: set[bytes] = field(default_factory=set)

    def __post_init__(self):
        self.load()

    def load(self):
        self.hashes.clear()
        if self.source.exists():
            with self.source.open(mode="rb") as f:
                while buffer := f.read(64):
                    self.hashes.add(buffer)

    @staticmethod
    def hash(o: yoop.Media | yoop.Playlist):
        if "youtube.com" in o.url.value:
            if not isinstance(o, yoop.Media):
                raise ValueError(o)
            return hashlib.sha512("".join([o.uploader, o.title.simple, str(o.uploaded)]).encode()).digest()

        return hashlib.sha512(o.url.value.encode()).digest()

    def add(self, o: yoop.Media | yoop.Playlist):
        if (h := self.hash(o)) not in self.hashes:
            with self.source.open(mode="ab") as f:
                f.write(h)
            self.hashes.add(h)

    def __contains__(self, o: yoop.Media | yoop.Playlist):
        if ("youtube.com" in o.url.value) and isinstance(o, yoop.Playlist):
            try:
                return self.hash(o[0]) in self.hashes
            except IndexError:
                return True
        return self.hash(o) in self.hashes

    def __len__(self):
        return len(self.hashes)
