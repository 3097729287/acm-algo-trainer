"""Bounded, server-local compression of already serialized catalogue responses."""
from collections import OrderedDict
import gzip
import hashlib
import threading


class GzipJSON(bytes):
    """A JSON response already encoded for a client that accepts gzip."""


def accepts_gzip(header):
    for coding in header.lower().split(','):
        name, *parameters = coding.strip().split(';')
        if name == 'gzip':
            try:
                return next((float(part.strip()[2:]) for part in parameters if part.strip().startswith('q=')), 1) > 0
            except ValueError:
                return False
    return False


class CompressedResponses:
    def __init__(self, max_bytes=4*1024*1024, max_entries=2):
        self.max_bytes=max_bytes
        self.max_entries=max_entries
        self._items=OrderedDict()
        self._bytes=0
        self._lock=threading.Lock()

    def compress(self, raw):
        # Hash the complete response, including session/date. Keeping the raw
        # 15-25 MiB catalogue as a dictionary key used more RAM than its gzip.
        if len(raw)>64*1024*1024:
            return gzip.compress(raw,compresslevel=1,mtime=0)
        key=hashlib.sha256(raw).digest()
        with self._lock:
            if key in self._items:
                self._items.move_to_end(key)
                return self._items[key]
            packed=gzip.compress(raw,compresslevel=1,mtime=0)
            size=len(key)+len(packed)
            if size<=self.max_bytes and self.max_entries>0:
                while self._items and (self._bytes+size>self.max_bytes or len(self._items)>=self.max_entries):
                    old,value=self._items.popitem(last=False)
                    self._bytes-=len(old)+len(value)
                self._items[key]=packed
                self._bytes+=size
            return packed

    def clear(self):
        with self._lock:
            self._items.clear()
            self._bytes=0
