import re
import yoop
import math
import loguru
import datetime
import requests
import pydantic

from .Retrier  import Retrier
from .Repeater import Repeater



@pydantic.dataclasses.dataclass(frozen = True, kw_only = False)
class Tag:

	source : str

	def __repr__(self):
		return '#' + ''.join(
			word.title()
			for word in re.sub(
				r'[^\w\s]',
				'',
				self.source
			).split(' ')
		)


@pydantic.dataclasses.dataclass(frozen = True, kw_only = True)
class Bot:

	token : str
	chat  : str

	def tags(self, audio: yoop.Audio):

		for t in (
			'artist',
			'album',
			'title'
		):
			yield Tag(f'{audio.tags[t][0]}')

		if (p := self.part(audio)) is not None:
			yield Tag(f'part_{p}')

	def part(self, audio: yoop.Audio):
		if audio.part is None:
			return None
		else:
			return f"{audio.part.current:{0}2}_{audio.part.total}"

	def title(self, audio: yoop.Audio):

		if (p := self.part(audio)) is None:
			return f"{audio.tags['title'][0]}"
		else:
			return f"{audio.tags['title'][0]} - {p}"

	def load(self, audio: yoop.Audio):

		if len(audio) >= 50 * 1000 * 1000:
			for part in audio.splitted(math.ceil(len(audio) / (50 * 1000 * 1000))):
				self.load(part)
		else:
			while (
				status_code := Retrier(
					exceptions = {requests.exceptions.ConnectTimeout},
					repeater   = Repeater(
						f = lambda: requests.post(
							f'https://api.telegram.org/bot{self.token}/sendAudio',
							data  = {
								'chat_id'   : self.chat,
								'caption'   : '\n'.join(map(str, self.tags(audio))),
								'title'     : self.title(audio),
								'performer' : audio.tags['artist'],
								'duration'  : audio.duration
							},
							files = {
								'audio'     : audio.data,
								# 'thumbnail' : audio.cover
							}
						).status_code,
						interval = datetime.timedelta(seconds = 3)
					)
				)()
			) != 200:
				loguru.logger.warning(f'{audio.tags["artist"][0]} - {audio.tags["title"][0]} {status_code}')