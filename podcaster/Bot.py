import re
import yoop
import math
import loguru
import datetime
import requests
import dataclasses

from .Retrier  import Retrier
from .Repeater import Repeater



@dataclasses.dataclass(frozen = True, kw_only = False)
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


@dataclasses.dataclass(frozen = True, kw_only = True)
class Bot:

	token : str
	chat  : str

	def tags(self, audio: yoop.Audio):
		return filter(
			lambda t: not str(t).endswith('#'),
			map(
				Tag,
				(
					audio.tags['artist'][0],
					audio.tags['album'][0],
					audio.tags['title'][0],
					f'part {audio.part}' if audio.part else ''
				)
			)
		)

	def load(self, audio: yoop.Audio):
		if len(audio) >= 50 * 1000 * 1000:
			for a in audio.splitted(
				math.ceil(
					len(audio) / (50 * 1000 * 1000)
				)
			):
				self.load(a)
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
								'title'     : audio.title,
								'performer' : audio.tags['artist'],
								'duration'  : audio.duration
							},
							files = {
								'audio'     : audio.data,
								'thumbnail' : audio.cover
							}
						).status_code,
						interval = datetime.timedelta(seconds = 3)
					)
				)()
			) != 200:
				loguru.logger.warning(f'{audio.tags["artist"][0]} - {audio.tags["title"][0]} {status_code}')