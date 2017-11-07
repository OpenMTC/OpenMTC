try:
    from blist import sortedlist
except ImportError:
    from futile.logging import get_logger
    from heapq import heappush, heappop, heapify

    get_logger(__name__).warning("blist.sortedlist is not available. Using a fallback implementation")

    class sortedlist(object):
        def __init__(self, iterable=(), *args, **kw):
            super(sortedlist, self).__init__(*args, **kw)

            l = self._list = list(iterable)

            if iterable is not None:
                heapify(l)

        def add(self, v):
            heappush(self._list, v)

        def pop(self, index=-1):
            if index != 0:
                raise NotImplementedError()

            return heappop(self._list)

        def remove(self, object):
            self._list.remove(object)
            heapify(self._list)

        def __getitem__(self, index):
            if index != 0:
                raise NotImplementedError()

            return self._list[index]

        def __len__(self):
            return len(self._list)
