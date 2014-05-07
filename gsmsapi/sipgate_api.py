#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SIPGate API documentation
http://www.sipgate.de/img/sipgate_api_documentation.pdf
Implemented SIPGate API Version 1.06 21. August 2007
"""

import decimal
import xmlrpclib

VERSION = 0.10
VENDOR = "Cygnus Networks GmbH"

SERVER_STATUS_CODES = {
	200: 'Method success',
	400: 'Method not supported',
	401: 'Request denied (no reason specified)',
	402: 'Internal error',
	403: 'Invalid arguments',
	404: 'Resources exceeded (this MUST not be used to indicate parameters in error)',
	405: 'Invalid parameter name',
	406: 'Invalid parameter type',
	407: 'Invalid parameter value',
	408: 'Attempt to set a non-writable parameter',
	409: 'Notification request rejected.',
	410: 'Parameter exceeds maximum size.',
	411: 'Missing parameter.',
	412: 'Too many requests.',
	500: 'Date out of range.',
	501: 'Uri does not belong to user.',
	502: 'Unknown type of service.',
	503: 'Selected payment method failed.',
	504: 'Selected currency not supported.',
	505: 'Amount exceeds limit.',
	506: 'Malformed SIP URI.',
	507: 'URI not in list.',
	508: 'Format is not valid E.164.',
	509: 'Unknown status.',
	510: 'Unknown ID.',
	511: 'Invalid timevalue.',
	512: 'Referenced session not found.',
	513: 'Only single default per TOS allowed.',
	514: 'Malformed VCARD format.',
	515: 'Malformed PID format.',
	516: 'Presence information not available.',
	517: 'Invalid label name.',
	518: 'Label not assigned.',
	519: 'Label doesn’t exist.',
	520: 'Parameter includes invalid characters.',
	521: 'Bad password. (Rejected due to security concerns.)',
	522: 'Malformed timezone format.',
	523: 'Delay exceeds limit.',
	524: 'Requested VPN type not available.',
	525: 'Requested TOS not available.',
	526: 'Unified messaging not available.',
	527: 'URI not available for registration.',
}

TYPE_OF_SERVICE = {
	'fax': 'pages',
	'text': 'characters',
	'video': 'seconds',
	'voice': 'seconds',
}


class SipgateAPIException(BaseException):
	pass


class SipgateAPIResponse(dict):
	def __init__(self, response):
		assert "StatusCode" in response
		assert "StatusString" in response
		self.status_code, self. status_string = int(response["StatusCode"]), response["StatusString"]
		self.success = self.status_code == 200
		if self.status_code in SERVER_STATUS_CODES:
			self.status_message = SERVER_STATUS_CODES[self.status_code]
		else:
			self.status_message = None
		dict.__init__(self, response)


class SipgateAPI(object):
	basicurl = "https://%(username)s:%(password)s@samurai.sipgate.net/RPC2"
	teamurl = "https://%(username)s:%(password)s@api.sipgate.net/RPC2"
	identify_client_name = "Python-SipgateAPI"

	def __init__(self, username, password, api="team"):
		assert api in ["team", "basic", "plus"]
		baseurl = self.teamurl if api == "team" else self.basicurl
		self.identified = False
		url = baseurl % dict(username=username, password=password)
		self.rpc = xmlrpclib.Server(url)

	def __rpc_call(self, function, dict=None, init=False):
		if self.identified is False and init is False:
			self.client_identify()
			self.identified = True
		try:
			if dict is not None:
				result = SipgateAPIResponse(function(dict))
			else:
				result = SipgateAPIResponse(function())
		except xmlrpclib.Error, exc:
			raise SipgateAPIException("xmlrpclib error during sipgate identify: %s" % str(exc))
		return result

	def client_identify(self):
		result = self.__rpc_call(self.rpc.samurai.ClientIdentify, dict(ClientName=self.identify_client_name, ClientVersion=VERSION, ClientVendor=VENDOR), init=True)

	def get_balance(self):
		result = self.__rpc_call(self.rpc.samurai.BalanceGet)
		return decimal.Decimal(result["CurrentBalance"]["TotalIncludingVat"])

	def send_sms(self, phone, message, sender=None):
		# Sipgate does not allow to send sms by using + sign in front
		if phone.startswith("+"):
			phone = phone[1:]
		if sender is not None:
			self.__rpc_call(self.rpc.samurai.SessionInitiate, dict(RemoteUri="sip:%s@sipgate.net" % phone, TOS="text", Content=message, LocalURI=sender))
		else:
			self.__rpc_call(self.rpc.samurai.SessionInitiate, dict(RemoteUri="sip:%s@sipgate.net" % phone, TOS="text", Content=message))

	def own_uri_list(self):
		result = self.__rpc_call(self.rpc.samurai.OwnUriListGet)
		return result