'''
Created on 14.07.2011

@author: kca
'''

from . import issubclass

def errorstr(e):
	try:
		message = e.message
	except AttributeError:
		message = str(e)
	else:
		if not message:
			message = str(e)
	return message

def raise_error(e):
	if isinstance(e, Exception) or (isinstance(e, type) and issubclass(e, Exception)):
		raise e	
	raise Exception(e)
