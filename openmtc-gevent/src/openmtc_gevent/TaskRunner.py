from gevent.pool import Pool, Greenlet
from openmtc_server.TaskRunner import TaskRunner


class GEventTaskRunner(TaskRunner):
    timeout = 5

    def __init__(self, pool_size=200, *args, **kw):
        super(GEventTaskRunner, self).__init__(*args, **kw)
        self._pool = Pool(pool_size)

    def run_task(self, func, *args, **kw):
        self.logger.debug("Adding task %s to pool of size %s", func,
                          self._pool.free_count())
        self._pool.start(Greenlet(func, *args, **kw))
        self.logger.debug("Task added")

    def stop(self):
        self.logger.debug("Waiting for background queue to finish")
        self._pool.join(self.timeout)
        self.logger.debug("background queue finished")
        super(GEventTaskRunner, self).stop()
