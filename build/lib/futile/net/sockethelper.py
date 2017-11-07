'''
Created on 14.07.2011

@author: kca
'''

from socket import socket as _socket, AF_INET, SOCK_STREAM
from futile.contextlib import closing

def socket(family = AF_INET, type = SOCK_STREAM, proto = 0):
	return closing(_socket(family, type, proto))
		
	