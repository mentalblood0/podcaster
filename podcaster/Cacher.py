import logging
from dataclasses import dataclass

import yoop

from .Cache import Cache


@dataclass
class Cacher:
    url: yoop.Url
    suffixes: list[str]
    cache: Cache

    def cache_all(self):
        self.cache.source.unlink(missing_ok=True)
        for u in [self.url] + [self.url / s for s in self.suffixes]:
            self._cache_all(yoop.Playlist(u))

    def _cache_all(self, playlist: yoop.Playlist):
        for e in playlist.items[::-1]:
            if isinstance(e, yoop.Playlist) and ("youtube.com" in e.url.value):
                self._cache_all(e)
            else:
                try:
                    if not e.available:
                        continue
                    self.cache.add(e)
                    logging.info(f"{self.cache.source} <- {Cache.hash(e).hex()} for {e.url.value}")
                except Exception as ex:
                    logging.warning(f"exception while caching {e} from {playlist} from {self.url}: {ex}")
