from signal import SIGTERM, SIGINT

import gevent.signal
from gevent import spawn_later
from gevent.event import Event as GEventEvent

from futile.logging import LoggerMixin


class AppRunner(LoggerMixin):
    def __init__(self, m2m_app, *args, **kw):
        super(AppRunner, self).__init__(*args, **kw)

        self._timers = set()
        self.m2m_app = m2m_app
        self.m2m_ep = None

    def run(self, m2m_ep):
        self.m2m_ep = m2m_ep

        try:
            self._run()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Exiting...")
        except Exception:
            self.logger.exception("Error")
            raise
        finally:
            self.logger.info("Shutting down.")
            self._shutdown_app()
            for timer in self._timers:
                timer.kill()

    def _run(self):
        self.m2m_app.run(self, self.m2m_ep)

        shutdown_event = GEventEvent()
        gevent.signal(SIGTERM, shutdown_event.set)
        gevent.signal(SIGINT, shutdown_event.set)
        shutdown_event.wait()

    def _shutdown_app(self):
        self.m2m_app.shutdown()

    def set_timer(self, t, f, *args, **kw):
        timer = None

        def wrapper():
            self._timers.discard(timer)
            f(*args, **kw)

        timer = spawn_later(t, wrapper)
        self._timers.add(timer)
        return timer

    def cancel_timer(self, timer):
        self._timers.discard(timer)
        timer.kill()
