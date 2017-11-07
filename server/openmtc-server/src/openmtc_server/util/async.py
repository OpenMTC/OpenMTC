from functools import update_wrapper
from decorator import decorator
from futile.logging import get_logger
from aplus import Promise

logger = get_logger(__name__)


class AsyncError(Exception):
    pass


class RPCError(AsyncError):
    pass


class MessageKeyError(KeyError):
    pass


class Message(object):
    __slots__ = ("_message", )

    def __init__(self, message, *args, **kw):
        super(Message, self).__init__(*args, **kw)
        self._message = message

    def reply(self, message, handler=None):
        return self._message.reply(message, handler)

    def __getitem__(self, k):
        try:
            return self._message.body[k]
        except KeyError as e:
            raise MessageKeyError("Missing message parameter: %s" % (e, ))

    def get(self, k, default=None):
        return self._message.body.get(k, default)

    def copy(self):
        return self._message.body.copy()

    def __str__(self):
        return str(self._message.body)


class AsyncResult(object):
    __slots__ = ("_result", "error")

    def __init__(self, result=None, error=None, *args, **kw):
        super(AsyncResult, self).__init__(*args, **kw)

        if error is not None and not isinstance(error, BaseException):
            error = AsyncError(error)

        self._result = result
        self.error = error

    @property
    def result(self):
        if self.error is not None:
            raise self.error
        return self._result


class RPCResult(AsyncResult):
    __slots__ = ("reply")

    def __init__(self, replyfunc, result=None, error=None, *args, **kw):
        super(RPCResult, self).__init__(result=None, error=None, *args, **kw)

        self.reply = replyfunc


def async_result_handler(func):
    def _handle_async_result(error, result):
        return func(AsyncResult(result, error))
    update_wrapper(_handle_async_result, func)
    return _handle_async_result


@decorator
def rpc_result_handler(func, result):
    if result.body["status"].lower() != "ok":
        return func(AsyncResult(replyfunc=result.reply,
                                error=RPCError(result.body["message"])))
    result = AsyncResult(replyfunc=result.reply, result=result.body["result"])
    return func(result)


@decorator
def rpc_handler(func, message):
    try:
        func(Message(message))
    except Exception as e:
        logger.exception("Error in RPC call")
        message.reply({"status": "error", "message": str(e)})


def async_all(promises, fulfill_with_none=False):
    p = Promise()
    num = len(promises)

    if num == 0:
        if fulfill_with_none:
            p.fulfill(None)
        else:
            p.fulfill([])
    else:
        results = []

        def _done(result):
            if not p.isRejected():
                results.append(result)
                if len(results) == num:
                    if fulfill_with_none:
                        #logger.debug("Fulfilling with None")
                        p.fulfill(None)
                    else:
                        #logger.debug("Fulfilling with %s", results)
                        p.fulfill(results)

        def _error(error):
            if p.isPending():
                p.reject(error)

        for promise in promises:
            promise.then(_done, _error)

    return p
