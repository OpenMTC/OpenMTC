'''
Created on 17.07.2011

@author: kca
'''

from wsgiref.simple_server import WSGIRequestHandler, WSGIServer as _WSGIServer
from SocketServer import ThreadingMixIn, ForkingMixIn

class WSGIServer(_WSGIServer):
	def __init__(self, server_address, app = None, RequestHandlerClass = WSGIRequestHandler):
		_WSGIServer.__init__(self, server_address, RequestHandlerClass)
		self.set_app(app)

class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
	pass

class ForkingWSGIServer(ForkingMixIn, WSGIServer):
	pass
