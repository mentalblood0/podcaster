import base64
import csv
import dataclasses
import datetime
import io
import logging
import pathlib
import time
import typing
import zlib

import yoop


@dataclasses.dataclass(frozen=False, kw_only=False, unsafe_hash=True)
class Entry:
    id: "Id" = dataclasses.field(hash=False)
    uploaded: datetime.datetime = dataclasses.field(hash=True)
    duration: datetime.timedelta = dataclasses.field(hash=True)

    @dataclasses.dataclass(frozen=True, kw_only=False)
    class Id:
        value: str

        @classmethod
        def from_url(cls, url: yoop.Url):
            if "youtube.com" in url.value:
                if "watch?v=" in url.value:
                    return cls(url.value.split("watch?v=")[-1])
                return cls(url.value.split("/")[-1])
            return cls(
                base64.b64encode(zlib.adler32(url.value.encode()).to_bytes(length=4, byteorder="big"))[:-2].decode()
            )

    def __eq__(self, another: object):
        if not isinstance(another, Entry):
            return False
        return hash(self) == hash(another)

    @property
    def row(self):
        return (
            self.id.value,
            base64.b64encode(int(self.uploaded.timestamp()).to_bytes(length=6, byteorder="big")).decode("ascii"),
            base64.b64encode(int(self.duration.total_seconds()).to_bytes(length=3, byteorder="big")).decode("ascii"),
        )

    @classmethod
    def from_video(cls, v: yoop.Media):
        return cls(Entry.Id.from_url(v.url), v.uploaded, v.duration)

    @classmethod
    def from_row(cls, r: tuple[str, str, str] | list[str]):
        if isinstance(r, tuple):
            return cls(
                id=Entry.Id(r[0]),
                uploaded=datetime.datetime.fromtimestamp(int.from_bytes(base64.b64decode(r[1]))),
                duration=datetime.timedelta(seconds=int.from_bytes(base64.b64decode(r[2]))),
            )
        elif isinstance(r, list):
            if len(r) != 3:
                raise ValueError
            return Entry.from_row(tuple[str, str, str](r))


@dataclasses.dataclass(frozen=False, kw_only=False, unsafe_hash=True)
class Entries:
    by_id: dict[Entry.Id, Entry] = dataclasses.field(default_factory=dict)
    plain: set[Entry] = dataclasses.field(default_factory=set)

    def add(self, e: Entry):
        if (e in self.plain) and (old := ({e} & self.plain).pop().id) != e.id:
            del self.by_id[old]
            self.plain.remove(e)

        self.by_id[e.id] = e
        self.plain.add(e)

    def remove(self, e: Entry):
        del self.by_id[e.id]
        if e in self.plain:
            self.plain.remove(e)

    def url(self, e: typing.Union[Entry, yoop.Media]):
        if isinstance(e, Entry):
            return e.id in self.by_id
        elif isinstance(e, yoop.Media):
            return Entry.Id.from_url(e.url) in self.by_id

    def clear(self):
        self.by_id.clear()
        self.plain.clear()

    def __contains__(self, e: Entry):
        return e in self.plain


@dataclasses.dataclass(frozen=False, kw_only=False)
class Cache:
    source: typing.Final[pathlib.Path]
    entries: Entries = Entries()
    delimiter: typing.Final[str] = ","
    quote: typing.Final[str] = '"'
    escape: typing.Final[str] = "\\"

    def __post_init__(self):
        self.load()

    def reader(self, file: io.TextIOWrapper):
        return csv.reader(file, delimiter=self.delimiter, quotechar=self.quote, escapechar=self.escape)

    def writer(self, file: io.TextIOWrapper):
        return csv.writer(
            file, delimiter=self.delimiter, quotechar=self.quote, escapechar=self.escape, quoting=csv.QUOTE_MINIMAL
        )

    def load(self):
        if not self.source.exists():
            return

        self.entries.clear()
        start = time.time()
        with self.source.open(newline="", encoding="utf8") as f:
            for row in self.reader(f):
                self.entries.add(Entry.from_row(row))
        end = time.time()
        logging.info(f"{self.source} loading took {end - start} seconds")

    def dump(self):
        temp = self.source.with_suffix(".temp")
        with temp.open(mode="w", newline="", encoding="utf8") as f:
            writer = self.writer(f)
            for e in self.entries.plain:
                writer.writerow(e.row)
        temp.rename(self.source)

    def add(self, o: Entry):
        with self.source.open(mode="a", newline="", encoding="utf8") as f:
            self.writer(f).writerow(o.row)

        if self.entries.url(o):
            self.entries.remove(o)
        self.entries.add(o)

    def __contains__(self, o: yoop.Media | yoop.Playlist):
        if isinstance(o, yoop.Media):
            if self.entries.url(o):
                return True

            try:
                e = Entry.from_video(o)
                if e in self.entries:
                    if not self.entries.url(o):
                        self.add(e)
                    return True
            except:
                return True

            return False

        elif isinstance(o, yoop.Playlist):
            try:
                return o[0] in self
            except IndexError:
                return True
