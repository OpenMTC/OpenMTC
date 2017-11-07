from abc import ABCMeta, abstractmethod
from futile.logging import LoggerMixin


class TaskRunner(LoggerMixin):
    __metaclass__ = ABCMeta

    @abstractmethod
    def run_task(self, task, *args, **kw):
        raise NotImplementedError()

    def stop(self):
        pass

    def _execute(self, func, args, kw):
        try:
            func(*args, **kw)
        except Exception:
            self.logger.exception("Error in background task")
