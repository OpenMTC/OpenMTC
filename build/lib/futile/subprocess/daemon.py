'''
Created on 02.02.2012

@author: kca
'''

from time import sleep
from abc import ABCMeta, abstractproperty, abstractmethod
from futile import Base
from futile.path import Path
from . import check_call, STDOUT

class DaemonController(Base):
	__metaclass__ = ABCMeta
	
	def __init__(self, sleep = 5, stop_sleep = 3, *args, **kw):
		super(DaemonController, self).__init__(*args, **kw)
		self.__sleep = int(sleep)
		self.__stop_sleep = int(stop_sleep)

	@abstractproperty
	def is_running(self):
		raise NotImplementedError()

	def start(self):
		self._start()
		sleep(self.__sleep)

	@abstractmethod
	def _start(self):
		raise NotImplementedError()

	def stop(self):
		self._stop()
		sleep(self.__stop_sleep)

	@abstractmethod
	def _stop(self):
		raise NotImplementedError()
	
	def __enter__(self):
		self.start()
		return self
	
	def __exit__(self, exc_type, exc_val, exc_tb):
		self.stop()

class DummyController(DaemonController):
	def __init__(self, sleep = 0, stop_sleep = 0, *args, **kw):
		super(DummyController).__init__(sleep = sleep, stop_sleep = stop_sleep, *args, **kw)
	
	def _start(self):
		pass
	_stop = _start

	@property
	def is_running(self):
		return False

import os
import errno

class CheckPIDFileController(DaemonController):
	def __init__(self, pidfile, *args, **kw):
		super(CheckPIDFileController, self).__init__(*args, **kw)
		self.__pidfile = Path(pidfile)

	@property
	def pidfile(self):
		return self.__pidfile

	@property
	def is_running(self):
		if not self.pidfile.exists():
			return False

		if not self.pidfile.isfile():
			raise Exception("pidfile '%s' is not a file" % (self.pidfile, ))

		try:
			pid = int(self.__pidfile.open().readline(16))
		except:
			self.logger.exception("Error reading pidfile %s" % (self.pidfile))
			raise

		try:
			os.kill(pid, 0)
			return True
		except OSError, e:
			if e.errno == errno.ESRCH:
				return False
			raise

class StartStopDaemonController(CheckPIDFileController):
	def __init__(self, executable, fork = False, workingdir = None, pidfile = None, makepidfile = False, daemonargs = None, ssd = "/sbin/start-stop-daemon", ldpath = None, outfile = "/dev/null", *args, **kw):
		if not pidfile:
			pidfile = "/tmp/" + executable.replace("/", "_") + ".pid"
		super(StartStopDaemonController, self).__init__(pidfile = pidfile, *args, **kw)

		self.__executable = unicode(executable)
		self.__workingdir = workingdir and unicode(workingdir) or None

		if ldpath is not None:
			if not isinstance(ldpath, (list, set, tuple, frozenset)):
				ldpath = [ ldpath ]
			ldpath = tuple(set(ldpath))
		self.__ldpath = ldpath

		self.__makepidfile = makepidfile
		self.__daemonargs = daemonargs
		self.__fork = fork
		self.__ssd = ssd
		self.__outfile = outfile

	def get_daemonargs(self):
		return self.__daemonargs
	def set_daemonargs(self, da):
		self.__daemonargs = da
	daemonargs = property(get_daemonargs, set_daemonargs)

	def __make_cmd(self, cmd, test):
		cmd = [ self.__ssd, cmd, '-x', self.__executable, '-p', self.pidfile, '-o' ]

		if self.__workingdir:
			cmd += [ '-d', self.__workingdir ]

		if test:
			cmd.append('-t')
	
		env = None
		if self.__ldpath:
			env = dict(LD_LIBRARY_PATH = ':'.join(self.__ldpath))

		return cmd, env

	def __check_cmd(self, cmd, env):
		self.logger.debug("ssd env: " + str(env))

		outfile = self.__outfile
		if outfile:
			outfile = Path(outfile).open("a")

		try:
			check_call(cmd, stdout = outfile, stderr = STDOUT, close_fds = True, cwd = self.__workingdir, env = env)
		finally:
			if outfile is not None:
				outfile.close()

	def _start(self):
		cmd, env = self.__make_cmd("-S", False)
		if self.__makepidfile:
			cmd.append('-m')

		if self.__fork:
			cmd.append('-b')

		if self.__daemonargs:
			cmd += [ '--' ] + list(self.__daemonargs)

		self.__check_cmd(cmd, env)

	def _stop(self):
		cmd, env = self.__make_cmd("-K", False)
		self.__check_cmd(cmd, env)

