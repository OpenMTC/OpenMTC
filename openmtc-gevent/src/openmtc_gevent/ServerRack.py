"""
Created on 31.12.2013

@author: kca
"""

# Adapted from https://gist.github.com/denik/1008826

from futile.logging import LoggerMixin
import sys
import gevent
import signal
from gevent.event import Event


class GEventServerRack(LoggerMixin):

    def __init__(self, servers, *args, **kw):
        super(GEventServerRack, self).__init__(*args, **kw)
        self.servers = servers
        e = self._shutdown_event = Event()
        e.set()

    def start(self):
        started = []
        try:
            for server in self.servers:
                name = self._server_name(server)
                server.start()
                started.append(server)
                self.logger.info('%s started on %s', name, server.address)
        except:
            self.logger.exception("Failed to start server %s", name)
            self.stop(started)
            raise

        self._shutdown_event.clear()

    @staticmethod
    def _server_name(server):
        return getattr(server, 'name', None) or server.__class__.__name__ or 'Server'

    def stop(self, servers=None):
        self.logger.info("Stopping listeners...")
        if servers is None:
            servers = self.servers
        for server in servers:
            try:
                server.stop()
            except:
                if hasattr(server, 'loop'):  # gevent >= 1.0
                    server.loop.handle_error(server.stop, *sys.exc_info())
                else:  # gevent <= 0.13
                    self.logger.exception("Error stopping server %s",
                                          self._server_name(server))

        self._shutdown_event.set()

    def serve_forever(self):
        gevent.signal(signal.SIGTERM, self.stop)
        gevent.signal(signal.SIGINT, self.stop)
        self.start()
        self._shutdown_event.wait()
