'''
Created on 21.01.2012

@author: kca
'''

from wsgiref.simple_server import WSGIServer
from SocketServer import ThreadingMixIn, ForkingMixIn

class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
	pass

class ForkingWSGIServer(ForkingMixIn, WSGIServer):
	pass
