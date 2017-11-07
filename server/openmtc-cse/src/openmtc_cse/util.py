import aplus
from openmtc.exc import OpenMTCNetworkError
from openmtc_onem2m.exc import CSEError
from openmtc_onem2m.transport import OneM2MErrorResponse
from futile.logging import LoggerMixin
from threading import Timer
import time
from openmtc.util import datetime_the_future
import abc


def log_error(error):
    try:
        return error.status_code == 500
    except AttributeError:
        return not isinstance(error, (OpenMTCNetworkError, CSEError,
                                      OneM2MErrorResponse))

aplus.log_error = log_error


class ResourceUpdater(LoggerMixin):
    """ Baseclass for automatic resource updating"""

    def __init__(self, send_update=None, interval=None, offset=None,
                 *args, **kw):
        """
            @param send_update: send_update function for update requests
            @param interval: refresh interval in seconds
            @param offset: additional offset for expirationTime in seconds
        """
        super(ResourceUpdater, self).__init__(*args, **kw)
        self.__interval = interval or 60 * 60
        self.__offset = offset or 60 * 60
        self.__timers = {}
        self.__shutdown = False
        self.send_update = send_update

    @abc.abstractmethod
    def start(self, instance, fields=None, restore=None, send_update=None ):
        return

    @abc.abstractmethod
    def stop(self):
        return

    @property
    def offset(self):
        return self.__offset

    @property
    def interval(self):
        return self.__interval

    @property
    def timers(self):
        return self.__timers


class ExpTimeUpdater(ResourceUpdater):
    """ Utility class to update mtc resources' expirationTime periodically.
        Based on python Timers.
    """
    def __init__(self, send_update=None, interval=None, offset=None,
                 *args, **kw):
        """
            @param send_update: send_update function for update requests
            @param interval: refresh interval in seconds
            @param offset: additional offset for expirationTime in seconds
        """
        super(ExpTimeUpdater, self).__init__(send_update=send_update,
                                             interval=interval, offset=offset,
                                             *args, **kw)

    def start(self, instance, fields=None, restore=None, send_update=None):
        """ Starts a threading.Timer chain,
            to repeatedly update a resource instances's expirationTime.

            @param instance: resource instance
            @param fields: additional fields mandatory during update
            @param restore: function that will restore the instance, if it has
                            expired accidentally. Has to restart the refresher.
            @param send_update:
        """
        self.logger.debug("starting expTimeUpdater: %s %s" % (instance,
                                                              fields))
        self.__shutdown = False
        interval = (time.mktime(instance.expirationTime.timetuple()) -
                    (time.time() + time.timezone))
        if interval > self.offset:
            interval -= self.offset
        else:
            interval -= (interval/10)

        send_update = send_update or self.send_update or None

        kwargs = {"instance": instance, "fields": fields, "restore": restore,
                  "send_update": send_update}
        t = Timer(interval, self.__updateExpTime, kwargs=kwargs)
        t.start()

        self.timers[instance.path] = t

    def __updateExpTime(self, instance, future=None, fields=[], restore=None,
                        send_update=None):
        """ Updates a resource instance's expirationTime to future.

            @note: Starts a new Timer.
            @param instance: resource instance to update
            @param future: new expirationTime value (optional)
            @param fields: additional fields mandatory during update
            @param restore: function that will restore the instance, if it has
                            expired accidentally. Has to restart the refresher.
        """
        self.logger.debug("__updateExpTime: %s" % instance )
        if self.__shutdown:
            return

        interval = self.interval
        offset = self.offset
        future = datetime_the_future(interval + offset)

        instance.expirationTime = future

        if send_update:
            send_update(instance)
        else:
            return

        # NOTE: expirationTime might have been changed by CSE at this point.
        # update could/should return the updated instance in this case,
        #   but does it?
        # => additional GET to confirm expirationTime ?
        kwargs = {"instance": instance, "fields": fields, "restore": restore,
                  "send_update": send_update}
        t = Timer(interval, self.__updateExpTime, kwargs=kwargs)
        t.start()
        self.timers[instance.path] = t
        # hopefully, GC will delete the old timer

    def stop(self):
        self.__shutdown = True
        self.logger.debug("Killing timers: %s" % self.timers)
        for t in self.timers.values():
            t.cancel()


def main():
    """
    Testing code
    """

    def update_function(instance):
        pass

    e = ExpTimeUpdater(send_update=update_function, interval=5, offset=1)

    from openmtc_onem2m.model import Container
    from openmtc.util import datetime_now
    from time import sleep

    instance = Container(
        expirationTime=datetime_now(),
        path="/test/path"
    )
    e.start(instance)
    sleep(10)

if __name__ == "__main__":
    main()
