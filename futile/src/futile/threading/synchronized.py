'''
Created on 08.08.2011

@author: kca
'''

from threading import Condition

def synchronized(f):
	done = Condition()
	f.in_progress = False

	def sync(*args, **kw):
		done.acquire()
		if not f.in_progress:
			f.in_progress = True
			done.release()
			try:
				return f(*args, **kw)
			finally:
				f.in_progress = False
				with done:
					done.notify_all()
		else:
			done.wait()
			assert(not f.in_progress)
			done.release()
	return sync
