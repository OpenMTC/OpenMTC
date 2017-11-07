from Queue import Queue, Empty
from threading import Thread

from openmtc_server.TaskRunner import TaskRunner


class AsyncTaskRunner(TaskRunner):
    timeout = 5

    def __init__(self, pool_size=20, *args, **kw):
        super(AsyncTaskRunner, self).__init__(*args, **kw)
        self._queue = Queue()
        self._running = True
        worker = self._worker = Thread(target=self._dispatcher)

        worker.start()

    def _dispatcher(self):
        #TODO: kca: Should we process the whole queue before exiting?
        while self._running:
            try:
                func, args, kw = self._queue.get(timeout=self.timeout)
            except Empty:
                continue

            self._execute(func, args, kw)

    def run_task(self, func, *args, **kw):
        self._queue.put((func, args, kw))

    def stop(self):
        self._running = False
        self.logger.debug("Waiting for worker to finish")
        self._worker.join(self.timeout + 1)
        self.logger.debug("Worker finished")
        super(AsyncTaskRunner, self).stop()
