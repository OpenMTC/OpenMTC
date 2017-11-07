from time import time

def timeit(f):
	def _timeit(*args, **kw):
		_timeit.__runs__ += 1
		start = time()
		try:
			return f(*args, **kw)
		finally:
			spent = _timeit.__last_time__ = time() - start
			_timeit.__total_time__ += spent
	_timeit.__runs__ = 0
	_timeit.__total_time__ = 0.0
	_timeit.__last_time__ = None
	_timeit.__name__ = f.__name__
	return _timeit