"""Bounded, server-local compression of already serialized catalogue responses."""
from collections import OrderedDict
import gzip
import threading


class CompressedResponses:
    def __init__(self, max_bytes=32*1024*1024, max_entries=4):
        self.max_bytes=max_bytes
        self.max_entries=max_entries
        self._items=OrderedDict()
        self._bytes=0
        self._lock=threading.Lock()

    def compress(self, raw):
        # Account tokens remain part of the exact byte key. Different sessions,
        # dates and catalogue revisions can never reuse the wrong response.
        if len(raw)>self.max_bytes//2:
            return gzip.compress(raw,compresslevel=1,mtime=0)
        with self._lock:
            if raw in self._items:
                self._items.move_to_end(raw)
                return self._items[raw]
            packed=gzip.compress(raw,compresslevel=1,mtime=0)
            size=len(raw)+len(packed)
            if size<=self.max_bytes and self.max_entries>0:
                while self._items and (self._bytes+size>self.max_bytes or len(self._items)>=self.max_entries):
                    key,value=self._items.popitem(last=False)
                    self._bytes-=len(key)+len(value)
                self._items[raw]=packed
                self._bytes+=size
            return packed

    def clear(self):
        with self._lock:
            self._items.clear()
            self._bytes=0
