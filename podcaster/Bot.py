import dataclasses
import datetime
import logging
import math
import re
import typing

import requests
import urllib3.exceptions
import yoop

from .Repeater import Repeater
from .Retrier import Retrier


@dataclasses.dataclass(frozen=False)
class Bot:
    token: typing.Final[str]
    chat: typing.Final[str]
    first: bool = True

    @dataclasses.dataclass(frozen=True, kw_only=True)
    class Tags:
        artist: str
        album: str
        title: str
        date: datetime.datetime
        cover: bytes
        part: int | None = None

        @property
        def title_with_part(self):
            if self.part is None:
                return self.title
            else:
                return f"{self.title} - {self.part}"

        @classmethod
        def tag(cls, s: str):
            return "#" + "".join(word.title() for word in re.sub(r"[^\w\s]", "", s).split(" "))

        def __str__(self):
            result = [
                self.tag(self.artist),
                self.tag(self.album),
                self.tag(self.title),
                self.tag(f"Released_{self.date.year}_{self.date.month}_{self.date.day}")
                + f" {self.date.hour:02}:{self.date.minute:02}:{self.date.second:02}",
            ]
            if self.part is not None:
                result.append(self.tag(f"part{self.part}"))
            return "\n".join(result)

    def load(self, audio: yoop.Audio, tags: Tags):
        if audio.megabytes >= 49:
            for i, a in enumerate(audio.splitted(math.ceil(len(audio) / (49 * 1024 * 1024)))):
                self.load(a, dataclasses.replace(tags, part=i + 1))
        else:
            logging.info(f"--> {tags.title_with_part} {audio.megabytes}MB")
            while (
                status_code := Retrier(
                    exceptions={
                        requests.exceptions.ConnectTimeout,
                        urllib3.exceptions.TimeoutError,
                        urllib3.exceptions.ConnectTimeoutError,
                        urllib3.exceptions.MaxRetryError,
                    },
                    repeater=Repeater(
                        f=lambda: requests.post(
                            f"https://api.telegram.org/bot{self.token}/sendAudio",
                            data={
                                "chat_id": self.chat,
                                "caption": str(tags),
                                "title": tags.title_with_part,
                                "performer": tags.artist,
                                "duration": audio.duration.total_seconds() if audio.duration is not None else None,
                                "protect_content": False,
                                "disable_notification": not self.first,
                            },
                            files={"audio": audio.verified.data, "thumbnail": tags.cover},
                        ).status_code,
                        interval=datetime.timedelta(seconds=3),
                    ),
                )()
            ) != 200:
                logging.info(
                    f"Non-200 status code when uploading to telegram audio {tags.artist} - {tags.title}: {status_code}"
                )
        self.first = False
