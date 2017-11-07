'''
Created on 18.08.2011

@author: kca
'''

from futile.logging import LoggerMixin
from ssl import wrap_socket, SSLSocket, SSLError, CERT_OPTIONAL, CERT_NONE
from socket import error
from futile import NOT_SET

class HTTPSMixin(LoggerMixin):
	certfile = keyfile = ca_certs = None
	cert_reqs = CERT_NONE
	
	def init_https(self, certfile, keyfile = None, ca_certs = None, cert_reqs = NOT_SET, secure = True):
		self.keyfile = keyfile
		self.certfile = certfile
		self.ca_certs = ca_certs
		if cert_reqs is NOT_SET:
			cert_reqs = ca_certs and CERT_OPTIONAL or CERT_NONE
		self.cert_reqs = cert_reqs
		if secure:
			self.enable_https()
			
	def enable_https(self):
		if not self.secure:
			if not self.certfile:
				raise SSLError("Certificate info missing.")
			if self.cert_reqs != CERT_NONE and not self.ca_certs:
				raise SSLError("Certificate validation requested but no ca certs available.")
			self.logger.debug("Enabling https with certfile=%s kefile=%s ca_certs=%s cert_reqs=%s", self.certfile, self.keyfile, self.ca_certs, self.cert_reqs)
			self.socket = wrap_socket(self.socket, server_side = True, keyfile = self.keyfile, certfile = self.certfile, ca_certs = self.ca_certs, cert_reqs = self.cert_reqs)
			
	def disable_https(self):
		if self.secure:
			self.socket = self.socket._sock

	def get_request(self):
		try:
			return self.socket.accept()
		except error, e:
			self.logger.exception("Error during accept(): %s", e)
			raise

	def is_secure(self):
		return isinstance(self.socket, SSLSocket)
	def set_secure(self, s):
		if s:
			self.enable_https()
		else:
			self.disable_https()
		return s
	secure = property(is_secure)
