'''
Created on 14.07.2011

@author: kca
'''
from futile import ObjectProxy

class closing(ObjectProxy):
	def __enter__(self):
		return self._o

	def __exit__(self, exc_type, exc_val, exc_tb):
		self._o.close()

		
class exiting(ObjectProxy):
	def __enter__(self):
		return self._o
	
	def __exit__(self, exc_type, exc_val, exc_tb):
		self._o.__exit__(exc_type, exc_val, exc_tb)