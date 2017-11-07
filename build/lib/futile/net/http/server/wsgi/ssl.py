'''
Created on 22.08.2011

@author: kca
'''

from ..ssl import HTTPSMixin
from ..wsgi import WSGIServer
from SocketServer import ThreadingMixIn, ForkingMixIn
from wsgiref.simple_server import WSGIRequestHandler
from futile import NOT_SET

class SecureWSGIServer(HTTPSMixin, WSGIServer):
	def __init__(self, server_address, certfile, keyfile = None, ca_certs = None, cert_reqs = NOT_SET, app = None, RequestHandlerClass = WSGIRequestHandler):
		WSGIServer.__init__(self, server_address, app = app, RequestHandlerClass = RequestHandlerClass)
		self.init_https(certfile, keyfile, ca_certs = ca_certs, cert_reqs = cert_reqs)
		
class SecureThreadingWSGIServer(ThreadingMixIn, SecureWSGIServer):
	pass

class SecureForkingWSGIServer(ForkingMixIn, SecureWSGIServer):
	pass
