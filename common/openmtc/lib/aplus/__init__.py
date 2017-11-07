import sys
from logging import DEBUG
from threading import Thread
from traceback import print_stack

from futile.logging import LoggerMixin
from openmtc.exc import OpenMTCError

if sys.subversion[0] != "CPython":
    from inspect import ismethod, getargspec

# TODO: kca: can't pass in values for then/error currently


def log_error(error):
    if isinstance(error, OpenMTCError):
        return False
    return True


class Promise(LoggerMixin):
    """
    This is a class that attempts to comply with the
    Promises/A+ specification and test suite:

    http://promises-aplus.github.io/promises-spec/
    """

    __slots__ = ("_state", "value", "reason",
                 "_callbacks", "_errbacks", "name")

    # These are the potential states of a promise
    PENDING = -1
    REJECTED = 0
    FULFILLED = 1

    def __init__(self, name=None):
        """
        Initialize the Promise into a pending state.
        """
        self._state = self.PENDING
        self.value = None
        self.reason = None
        self._callbacks = []
        self._errbacks = []
        self.name = name

    def _fulfill(self, value):
        """
        Fulfill the promise with a given value.
        """

        assert self._state == self.PENDING, "Promise state is not pending"

        self._state = self.FULFILLED
        self.value = value
        for callback in self._callbacks:
            try:
                callback(value)
            except Exception:
                # Ignore errors in callbacks
                self.logger.exception("Error in callback %s", callback)
        # We will never call these callbacks again, so allow
        # them to be garbage collected.  This is important since
        # they probably include closures which are binding variables
        # that might otherwise be garbage collected.
        self._callbacks = []
        self._errbacks = []

    def fulfill(self, value):
        self._fulfill(value)
        return self

    def _reject(self, reason, bubbling=False):
        """
        Reject this promise for a given reason.
        """

        assert self._state == self.PENDING, "Promise state is not pending"

        if not bubbling and log_error(reason):
            exc_info = sys.exc_info()
            self.logger.debug("Promise (%s) rejected: %s", self.name, reason,
                              exc_info=exc_info[0] and exc_info or None)
            self.logger.debug(self._errbacks)
            if self.logger.isEnabledFor(DEBUG):
                print_stack()
        else:
            pass

        self._state = self.REJECTED
        self.reason = reason
        for errback in self._errbacks:
            try:
                errback(reason)
            except Exception:
                self.logger.exception("Error in errback %s", errback)
                # Ignore errors in callbacks

        # We will never call these errbacks again, so allow
        # them to be garbage collected.  This is important since
        # they probably include closures which are binding variables
        # that might otherwise be garbage collected.
        self._errbacks = []
        self._callbacks = []

    def reject(self, reason):
        self._reject(reason)
        return self

    def isPending(self):
        """Indicate whether the Promise is still pending."""
        return self._state == self.PENDING

    def isFulfilled(self):
        """Indicate whether the Promise has been fulfilled."""
        return self._state == self.FULFILLED

    def isRejected(self):
        """Indicate whether the Promise has been rejected."""
        return self._state == self.REJECTED

    def get(self, timeout=None):
        """Get the value of the promise, waiting if necessary."""
        self.wait(timeout)
        if self._state == self.FULFILLED:
            return self.value
        raise self.reason

    def wait(self, timeout=None):
        """
        An implementation of the wait method which doesn't involve
        polling but instead utilizes a "real" synchronization
        scheme.
        """
        import threading

        if self._state != self.PENDING:
            return

        e = threading.Event()
        self.addCallback(lambda v: e.set())
        self.addErrback(lambda r: e.set())
        e.wait(timeout)

    def addCallback(self, f):
        """
        Add a callback for when this promise is fulfilled.  Note that
        if you intend to use the value of the promise somehow in
        the callback, it is more convenient to use the 'then' method.
        """
        self._callbacks.append(f)

    def addErrback(self, f):
        """
        Add a callback for when this promise is rejected.  Note that
        if you intend to use the rejection reason of the promise
        somehow in the callback, it is more convenient to use
        the 'then' method.
        """
        self._errbacks.append(f)

    if sys.subversion[0] != "CPython":
        def _invoke(self, func, value):
            try:
                if value is None:
                    args, _, _, _ = getargspec(func)
                    arglen = len(args)
                    if not arglen or (arglen == 1 and ismethod(func)):
                        return func()

                return func(value)
            except Exception as e:
                if log_error(e):
                    self.logger.exception("Error in handler %s", func)
                else:
                    self.logger.debug("Error in handler %s: %s", func, e)
                raise
    else:
        def _invoke(self, func, value):
            try:
                if value is None:
                    try:
                        target = func.im_func
                    except AttributeError:
                        argcount = func.func_code.co_argcount
                    else:
                        argcount = target.func_code.co_argcount - 1

                    if argcount == 0:
                        return func()

                return func(value)
            except Exception as e:
                if log_error(e):
                    self.logger.exception("Error in handler %s", func)
                else:
                    self.logger.debug("Error in handler %s: %s", func, repr(e))
                raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self.isPending():
            if exc_value is not None:
                if log_error(exc_value):
                    self.logger.exception("Promise automatically rejected")
                self._reject(exc_value, bubbling=True)
                return True
            else:
                self.fulfill(None)

    def then(self, success=None, failure=None, name=None):
        """
        This method takes two optional arguments.  The first argument
        is used if the "self promise" is fulfilled and the other is
        used if the "self promise" is rejected.  In either case, this
        method returns another promise that effectively represents
        the result of either the first of the second argument (in the
        case that the "self promise" is fulfilled or rejected,
        respectively).

        Each argument can be either:
          * None - Meaning no action is taken
          * A function - which will be called with either the value
            of the "self promise" or the reason for rejection of
            the "self promise".  The function may return:
            * A value - which will be used to fulfill the promise
              returned by this method.
            * A promise - which, when fulfilled or rejected, will
              cascade its value or reason to the promise returned
              by this method.
          * A value - which will be assigned as either the value
            or the reason for the promise returned by this method
            when the "self promise" is either fulfilled or rejected,
            respectively.
        """

        if name is None:
            try:
                name = success.__name__
            except AttributeError:
                name = str(success)

        ret = Promise(name=name)

        state = self._state
        if state == self.PENDING:
            """
            If this is still pending, then add callbacks to the
            existing promise that call either the success or
            rejected functions supplied and then fulfill the
            promise being returned by this method
            """

            def callAndFulfill(v):
                """
                A callback to be invoked if the "self promise"
                is fulfilled.
                """
                try:
                    # From 3.2.1, don't call non-functions values
                    if callable(success):
                        newvalue = self._invoke(success, v)
                        if _isPromise(newvalue):
                            newvalue.then(ret._fulfill,
                                          ret._reject)
                        else:
                            ret._fulfill(newvalue)
                    else:
                        # From 3.2.6.4
                        ret._fulfill(v)
                except Exception as e:
                    ret._reject(e)

            def callAndReject(r):
                """
                A callback to be invoked if the "self promise"
                is rejected.
                """
                try:
                    if callable(failure):
                        newvalue = failure(r)
                        if _isPromise(newvalue):
                            newvalue.then(ret._fulfill,
                                          ret._reject)
                        else:
                            ret._fulfill(newvalue)
                    else:
                        # From 3.2.6.5
                        ret._reject(r)
                except Exception as e:
                    ret._reject(e)

            self._callbacks.append(callAndFulfill)
            self._errbacks.append(callAndReject)

        elif state == self.FULFILLED:
            # If this promise was already fulfilled, then
            # we need to use the first argument to this method
            # to determine the value to use in fulfilling the
            # promise that we return from this method.
            try:
                if callable(success):
                    newvalue = self._invoke(success, self.value)
                    if _isPromise(newvalue):
                        newvalue.then(ret._fulfill,
                                      lambda r: ret._reject(r, bubbling=True))
                    else:
                        ret._fulfill(newvalue)
                else:
                    # From 3.2.6.4
                    ret._fulfill(self.value)
            except Exception as e:
                ret._reject(e)
        else:
            # If this promise was already rejected, then
            # we need to use the second argument to this method
            # to determine the value to use in fulfilling the
            # promise that we return from this method.
            try:
                if callable(failure):
                    newvalue = self._invoke(failure, self.reason)
                    if _isPromise(newvalue):
                        newvalue.then(ret._fulfill,
                                      ret._reject)
                    else:
                        ret._fulfill(newvalue)
                else:
                    # From 3.2.6.5
                    ret._reject(self.reason, bubbling=True)
            except Exception as e:
                ret._reject(e)

        return ret


def _isPromise(obj):
    """
    A utility function to determine if the specified
    object is a promise using "duck typing".
    """
    if isinstance(obj, Promise):
        return True

    try:
        return callable(obj.fulfill) and callable(obj.reject) and\
            callable(obj.then)
    except AttributeError:
        return False


def listPromise(*args):
    """
    A special function that takes a bunch of promises
    and turns them into a promise for a vector of values.
    In other words, this turns an list of promises for values
    into a promise for a list of values.
    """
    ret = Promise()

    def handleSuccess(v, ret):
        for arg in args:
            if not arg.isFulfilled():
                return

        value = map(lambda p: p.value, args)
        ret._fulfill(value)

    for arg in args:
        arg.addCallback(lambda v: handleSuccess(v, ret))
        arg.addErrback(lambda r: ret.reject(r))

    # Check to see if all the promises are already fulfilled
    handleSuccess(None, ret)

    return ret


def dictPromise(m):
    """
    A special function that takes a dictionary of promises
    and turns them into a promise for a dictionary of values.
    In other words, this turns an dictionary of promises for values
    into a promise for a dictionary of values.
    """
    ret = Promise()

    def handleSuccess(v, ret):
        for p in m.values():
            if not p.isFulfilled():
                return

        value = {}
        for k in m:
            value[k] = m[k].value
        ret.fulfill(value)

    for p in m.values():
        p.addCallback(lambda v: handleSuccess(v, ret))
        p.addErrback(lambda r: ret.reject(r))

    # Check to see if all the promises are already fulfilled
    handleSuccess(None, ret)

    return ret


class BackgroundThread(Thread):
    def __init__(self, promise, func):
        self.promise = promise
        self.func = func
        Thread.__init__(self)

    def run(self):
        try:
            val = self.func()
            self.promise.fulfill(val)
        except Exception as e:
            self.promise.reject(e)


def background(f):
    p = Promise()
    t = BackgroundThread(p, f)
    t.start()
    return p


def spawn(f):
    from gevent import spawn

    p = Promise()

    def process():
        try:
            val = f()
            p.fulfill(val)
        except Exception as e:
            p.reject(e)

    spawn(process)
    return p


def FulfilledPromise(result):
    p = Promise()
    p.fulfill(result)
    return p


def RejectedPromise(error):
    p = Promise()
    p.reject(error)
    return p
