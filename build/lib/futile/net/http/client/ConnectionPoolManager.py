'''
Created on 19.03.2013

@author: kca
'''

from logging import DEBUG, WARNING
import futile.logging
import urllib3.connectionpool
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from futile.logging import LoggerMixin
from futile import ObjectProxy

if not futile.logging.get_logger().isEnabledFor(DEBUG):
	urllib3.connectionpool.log.setLevel(WARNING)

class Urllib3ResponseWrapper(ObjectProxy):
	def getheader(self, header, default=None):
		return self._o.getheader(header.lower(), default)
	
	def __enter__(self):
		return self
		
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close()
		
	def close(self):
		self._o.release_conn()
		
	def isclosed(self):
		return False

class ConnectionPoolManager(LoggerMixin):
	def __init__(self, host, port, certfile = None, keyfile = None, cacertfile=None, force_ssl = False, *args, **kw):
		super(ConnectionPoolManager, self).__init__(*args, **kw)
		
		self.logger.debug("Creating ConnectionPoolManager for %s:%s", host, port)

		if certfile or keyfile or force_ssl:
			#https://docs.python.org/2/library/ssl.html#ssl.SSLContext
			from ssl import SSLContext, PROTOCOL_SSLv23
			ssl_context=SSLContext(PROTOCOL_SSLv23)
			ssl_context.load_cert_chain(certfile = certfile, keyfile = keyfile)
			ssl_context.load_verify_locations(cafile=cacertfile)
			#https://docs.python.org/2/library/httplib.html
			self.__pool = HTTPSConnectionPool(host, port, maxsize = 16, context = ssl_context)
		else:
			self.__pool = HTTPConnectionPool(host, port, maxsize = 16)
			
	def request(self, method, path, body, headers, timeout):
		return Urllib3ResponseWrapper(self.__pool.urlopen(method, path, body, 
			headers, timeout = timeout, pool_timeout = 30, preload_content = False, assert_same_host = False))
			
		
		