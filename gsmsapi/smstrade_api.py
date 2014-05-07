# -*- python -*-
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014  Jan Dittberner
# License: MIT

from base64 import b16encode
from locale import getpreferredencoding
import decimal
import requests

#: characters allowed in GSM 03.38
GSM0338_CHARS = (
	u'@£$¥èéùìòÇ\nØø\rÅå'
	u'Δ_ΦΓΛΩΠΨΣΘΞ' + unichr(27) + u'ÆæÉ'
								  u' !"#¤%&\'()*+,-./'
								  u'0123456789:;<=>?'
								  u'¡ABCDEFGHIJKLMNO'
								  u'PQRSTUVWXYZÄÖÑÜ§'
								  u'abcdefghijklmno'
								  u'pqrstuvwxyzäöñüà'
)

#: characters allowed in GSM 03.38 that occupy two octets
GSM0338_TWO_OCTET_CHARS = u'€' + unichr(12) + ur'[\]^{|}~'

# Message types defined in API documentation
#: Message type flash
MESSAGE_TYPE_FLASH = 'flash'
#: Message type unicode
MESSAGE_TYPE_UNICODE = 'unicode'
#: Message type binary
MESSAGE_TYPE_BINARY = 'binary'
#: Message type voice
MESSAGE_TYPE_VOICE = 'voice'

# Route names defined in API documentation
#: Route basic
ROUTE_BASIC = 'basic'
#: Route gold
ROUTE_GOLD = 'gold'
#: Route direct
ROUTE_DIRECT = 'direct'

# Status codes defined in API documentation
#: Status receiver number not valid
STATUS_INVALID_RECEIVER_NUMBER = 10
#: Status sender number not valid
STATUS_INVALID_SENDER_NUMBER = 20
#: Status message text not valid
STATUS_INVALID_MESSAGE_TEXT = 30
#: Status message type not valid
STATUS_INVALID_MESSAGE_TYPE = 31
#: Status SMS route not valid
STATUS_INVALID_SMS_ROUTE = 40
#: Status identification failed
STATUS_IDENTIFICATION_FAILED = 50
#: Status not enough balance in account
STATUS_NOT_ENOUGH_BALANCE = 60
#: Status network does not support the route
STATUS_NETWORK_NOT_SUPPORTED_BY_ROUTE = 70
#: Status feature is not possible by the route
STATUS_FEATURE_NOT_POSSIBLE_FOR_ROUTE = 71
#: Status handover to SMSC failed
STATUS_SMSC_HANDOVER_FAILED = 80
#: Status SMS has been sent successfully
STATUS_OK = 100


class SMSTradeError(Exception):
	"""
	Custom exception type.

	"""

	def __str__(self):
		return self.message.encode(getpreferredencoding())


class SMSTradeAPI(object):
	"""
	Abstraction of the `smstrade.eu <http://smstrade.eu>`_ http(s) mail sending
	API.

	"""

	def __init__(self, key, sender, route="basic", debug=False, reports=False, concat=False, charset='ascii', response=False):
		"""
		Initialize a new SMSTradeAPI instance.

		:param ConfigParser config:
			use the specified configuration instead of the default
			configuration

		:param str section:
			use the specified section in the configuration

		"""
		assert route in [ROUTE_BASIC, ROUTE_GOLD, ROUTE_DIRECT]

		self.reference = None
		self.senddate = None
		self.messagetype = None
		self.udh = None

		self.key = key

		self.url = "https://gateway.smstrade.de/"
		self.debug = debug
		self.cost = True
		self.message_id = True
		self.count = True
		self.reports = reports
		self.response = response
		self.concat = concat
		self.charset = charset

		self.sender = sender
		self.route = route

	def _handle_response_body(self, body):
		"""
		Handle parsing of response body.

		:param str body:
			response body
		"""
		lines = body.splitlines()
		try:
			retval = {
				'status': int(lines[0]),
			}
			if self.message_id:
				retval['message_id'] = lines[1]
			if self.cost:
				retval['cost'] = decimal.Decimal(lines[2])
			if self.count:
				retval['count'] = int(lines[3])
		except IndexError:
			raise SMSTradeError('malformed response')
		return retval

	def _add_optional_flags(self, request_params):
		if self.debug:
			request_params['debug'] = 1
		if self.cost:
			request_params['cost'] = 1
		if self.message_id:
			request_params['message_id'] = 1
		if self.count:
			request_params['count'] = 1
		if self.reports:
			request_params['dlr'] = 1
		if self.response and self.route == ROUTE_BASIC:
			request_params['response'] = 1
		return request_params

	def _add_optional_fields(self, request_params):
		if self.reference is not None:
			request_params['ref'] = self.reference
		if self.senddate is not None:
			request_params['senddate'] = self.senddate
		if self.messagetype is not None:
			request_params['messagetype'] = self.messagetype
		return request_params

	def _build_request_parameters(self, recipient):
		"""
		Build the request parameter dictionary based on fields in this
		SMSTradeAPI instance.

		:param str recipient:
			recipient calling number

		"""
		request_params = {
			'key': self.key,
			'to': recipient,
			'route': self.route,
		}
		if self.route in (ROUTE_GOLD, ROUTE_DIRECT):
			request_params['from'] = self.sender.encode(self.charset)
		if self.charset != 'ascii':
			request_params['charset'] = self.charset
		request_params = self._add_optional_flags(request_params)
		request_params = self._add_optional_fields(request_params)
		return request_params

	def _send_normal_message(self, recipient, text):
		"""
		Send a normal SMS message to the given recipient.

		:param str recipient:
			recipient calling number

		:param unicode text:
			unicode SMS message text

		"""
		request_params = self._build_request_parameters(recipient)
		request_params['message'] = text.encode(self.charset)
		if self.concat:
			request_params['concat'] = 1
		print "DEBUG data is", request_params
		response = requests.post(self.url, data=request_params)
		response.raise_for_status()
		return self._handle_response_body(response.text)

	def _send_unicode_message(self, recipient, text):
		"""
		Send a unicode SMS message to the given recipient.

		:param str recipient:
			recipient calling number

		:param unicode text:
			unicode SMS message text

		"""
		request_params = self._build_request_parameters(recipient)
		request_params['message'] = b16encode(text.encode('utf_16_be'))
		response = requests.post(self.url, data=request_params)
		response.raise_for_status()
		return self._handle_response_body(response.text)

	def _send_binary_message(self, recipient, text):
		"""
		Send a binary SMS message to the given recipient.

		:param str recipient:
			recipient calling number

		:param str text:
			hexadecimal representation of the binary data

		"""
		request_params = self._build_request_parameters(recipient)
		request_params['message'] = text
		if self.udh is not None:
			request_params['udh'] = self.udh
		response = requests.post(self.url, data=request_params)
		response.raise_for_status()
		return self._handle_response_body(response.text)

	def _send_voice_message(self, recipient, text):
		"""
		Send a voice SMS message to the given recipient.

		:param str recipient:
			recipient calling number

		:param unicode text:
			the message text

		"""
		request_params = self._build_request_parameters(recipient)
		request_params['message'] = text.encode(self.charset)
		response = requests.post(self.url, data=request_params)
		response.raise_for_status()
		return self._handle_response_body(response.text)

	def _send_message(self, recipient, text):
		"""
		Send an SMS to a single recipient.

		:param str recipient:
			recipient calling number

		:param str text:
			SMS message text

		"""
		if ((self.messagetype is None) or
				(self.messagetype == MESSAGE_TYPE_FLASH)):
			return self._send_normal_message(recipient, text)
		elif self.messagetype == MESSAGE_TYPE_UNICODE:
			return self._send_unicode_message(recipient, text)
		elif self.messagetype == MESSAGE_TYPE_BINARY:
			return self._send_binary_message(recipient, text)
		elif self.messagetype == MESSAGE_TYPE_VOICE:
			return self._send_voice_message(recipient, text)
		else:
			raise SMSTradeError(u"unknown message type %s" %
								self.messagetype)

	@staticmethod
	def _gsm0338_length(text):
		charcount = 0
		for char in text:
			if char in GSM0338_CHARS:
				charcount += 1
			elif char in GSM0338_TWO_OCTET_CHARS:
				charcount += 2
			else:
				raise SMSTradeError(
					u"character %s is not allowed in GSM messages." % char)
		return charcount

	def _check_normal_message(self, text):
		"""
		Perform a plausibility check on the given message text.

		:param str text:
			the message to check

		"""
		charcount = self._gsm0338_length(text)
		if ((self.concat and charcount > 1530) or
				(not self.concat and charcount > 160)):
			message = "too many characters in message"
			if not self.concat and charcount <= 1530:
				message += ", you may try to use concat"
			raise SMSTradeError(message)
		try:
			text.encode(self.charset)
		except ValueError:
			raise SMSTradeError((
									"The message can not be encoded with the chosen character set"
									" %s") % self.charset)

	@staticmethod
	def _check_unicode_message(text):
		"""
		Perform a plausibility check on the given unicode message text.

		:param str text:
			the message to check

		"""
		for char in text:
			code = ord(char)
			if (0xd800 <= code <= 0xdfff) or (code > 0xffff):
				raise SMSTradeError(
					u"the message can not be represented in UCS2")
		if len(text) > 70:
			raise SMSTradeError(
				u"too many characters in message, unicode SMS may contain up"
				u" to 70 characters")

	@staticmethod
	def _check_binary_message(text):
		"""
		Perform a plausibility check on the given binary message text.

		:param str text:
			the message to check

		"""
		try:
			length = len(text.lower().decode('hex'))
			if length > 140:
				raise SMSTradeError(
					u'too many bytes in message, binary messages may contain'
					u' up to 140 bytes')
		except:
			raise SMSTradeError('message cannot be encoded as bytes')

	def _check_voice_message(self, text):
		"""
		Perform a plausibility check on the give message intended to be sent as
		voice message.

		:param str text:
			the message to check

		"""
		if self._gsm0338_length(text) > 160:
			raise SMSTradeError(u'too many GSM characters in message')

	def _check_message(self, text):
		if ((self.messagetype is None) or
				(self.messagetype == MESSAGE_TYPE_FLASH)):
			self._check_normal_message(text)
		elif self.messagetype == MESSAGE_TYPE_UNICODE:
			self._check_unicode_message(text)
		elif self.messagetype == MESSAGE_TYPE_BINARY:
			self._check_binary_message(text)
		elif self.messagetype == MESSAGE_TYPE_VOICE:
			self._check_voice_message(text)
		else:
			raise SMSTradeError(
				u"message type %s is unknown" % self.messagetype)

	def send_sms(self, to, text):
		"""
		Send an SMS to recipients in the to parameter.

		:param list to:
			list of recipient calling numbers

		:param str text:
			SMS message text

		:param dict kwargs:
			keyword arguments that override values in the configuration files

		"""
		# convert to unicode
		if not self.messagetype == 'binary':
			text = text.decode(getpreferredencoding())

		if isinstance(to, str) or isinstance(to, basestring):
			to = [to]

		retval = {}
		for recipient in to:
			self._check_message(text)
			retval[recipient] = self._send_message(recipient, text)
		return retval

	def get_balance(self):
		response = requests.get(self.url + "credits/", params={'key': self.key})
		response.raise_for_status()
		return decimal.Decimal(response.text)
