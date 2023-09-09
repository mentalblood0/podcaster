import re
import yoop
import math
import datetime
import requests
import dataclasses
import urllib3.exceptions

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
					audio.tags.artist,
					audio.tags.album,
					audio.tags.title,
					f"Released_{audio.tags.date.year}_{audio.tags.date.month}_{audio.tags.date.day}",
					f'part {audio.part}' if audio.part else ''
				)
			)
		)

	def title(self, audio: yoop.Audio):
		if audio.part is None:
			return audio.tags.title
		else:
			return f'{self.title(dataclasses.replace(audio, part = None))} - {audio.part}'

	def load(self, audio: yoop.Audio):
		if len(audio) >= 50 * 1000 * 1000:
			for a in [
				*audio.splitted(
					math.ceil(
						len(audio) / (50 * 1000 * 1000)
					)
				)
			]:
				self.load(a)
		else:
			while (
				status_code := Retrier(
					exceptions = {
						requests.exceptions.ConnectTimeout,
						urllib3.exceptions.TimeoutError,
						urllib3.exceptions.ConnectTimeoutError,
						urllib3.exceptions.MaxRetryError
					},
					repeater   = Repeater(
						f = lambda: requests.post(
							f'https://api.telegram.org/bot{self.token}/sendAudio',
							data  = {
								'chat_id'              : self.chat,
								'caption'              : '\n'.join(map(str, self.tags(audio))),
								'title'                : self.title(audio),
								'performer'            : audio.tags.artist,
								'duration'             : audio.tags.duration,
								'protect_content'      : False
							},
							files = {
								'audio'     : audio.source.data,
								'thumbnail' : audio.tags.cover or b''
							}
						).status_code,
						interval = datetime.timedelta(seconds = 3)
					)
				)()
			) != 200:
				print(f'Non-200 status code when uploading to telegram audio {audio.tags.artist} - {audio.tags.title}: {status_code}')