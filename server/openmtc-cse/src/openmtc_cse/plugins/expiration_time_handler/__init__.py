from openmtc_server.Plugin import Plugin
from datetime import timedelta
from futile.collections.sortedlist import sortedlist
from openmtc_onem2m.model import ExpiringResource
from openmtc.util import datetime_now


class ExpirationTimeHandler(Plugin):
    DEFAULT_LIFETIME = 24 * 60 * 60  # 1day

    timeout = 5

    _timer = None

    def _init(self):
        # todo(rst): transform to onem2m
        raise RuntimeError('needs to be revised.')
        self.events.resource_created.register_handler(
            self._handle_expiration_time, ExpiringResource)
        self.events.resource_deleted.register_handler(self._handle_delete,
                                                      ExpiringResource)
        self.events.resource_updated.register_handler(self._handle_update,
                                                      ExpiringResource)

        self.default_lifetime = timedelta(
            seconds=self.config.get("default_lifetime", self.DEFAULT_LIFETIME))

        self._timetable = sortedlist()
        self._purged = set()

        shelve = self.get_shelve("resources")

        for path, expiration_time in shelve.items():
            self._do_handle_expiration_time(path, expiration_time, shelve)

        shelve.commit()
        self._initialized()

    def _start(self):
        self._running = True
        self._check_timetable()
        self._started()

    def _stop(self):
        self._running = False
        if self._timer is not None:
            self.api.cancel_timer(self._timer)
        self._stopped()

    def _handle_expiration_time(self, instance, req_ind):
        shelve = self.get_shelve("resources")
        self._do_handle_expiration_time(instance.path, instance.expirationTime,
                                        shelve)
        shelve.commit()

    def _do_handle_expiration_time(self, path, expiration_time, shelve):
        if expiration_time is not None:
            shelve[path] = expiration_time
            self.logger.debug("Adding resource to timetable: %s", path)
            self._timetable.add((expiration_time, path))

    def _handle_delete(self, instance, req_ind):
        self._purged.discard(req_ind.path)
        shelve = self.get_shelve("resources")
        self._do_delete(req_ind.path, shelve)
        shelve.commit()

    def _do_delete(self, path, shelve):
        try:
            expiration_time = shelve.pop(path)
        except KeyError:
            self.logger.debug("Resource %s is unknown", path)
        else:
            self.logger.debug("Removing resource from timetable: %s", path)
            try:
                self._timetable.remove((expiration_time, path))
            except ValueError:
                pass

    def _handle_update(self, instance, req_ind):
        if instance.path in self._purged:
            return

        shelve = self.get_shelve("resources")
        try:
            self._do_delete(instance.path, shelve)
            self._do_handle_expiration_time(instance.path,
                                            instance.expirationTime, shelve)
            shelve.commit()
        except:
            shelve.rollback()
            raise

    def _purge(self, path):
        self._purged.add(path)
        # ri = DeleteRequestIndication(path, reason="expired")
        # return self.api.handle_request_indication(ri)

    def _check_timetable(self):
        if not self._running:
            return

        now = datetime_now()
        sleeptime = self.timeout

        while len(self._timetable) > 0 and now >= self._timetable[0][0]:
            expired_path = self._timetable.pop(0)[1]
            # self._resources.pop(expired_path)
            self.logger.info("Resource has expired: %s", expired_path)
            self._purge(expired_path)
        try:
            td = self._timetable[0][0] - now
            try:
                td = td.total_seconds()
            except AttributeError:
                # Jython does not have timedelta.total_seconds()
                td = td.seconds + (td.days * 24 * 60 * 60)
            sleeptime = min(td, sleeptime)
        except IndexError:
            pass

        self._timer = self.api.set_timer(sleeptime, self._check_timetable)
