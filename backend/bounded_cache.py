"""Small, byte-bounded caches for image-rich public statements and test bundles."""
from collections import OrderedDict,namedtuple
from functools import wraps
import sys
import threading

Info=namedtuple('CacheInfo','hits misses maxsize currsize')

def retained_size(value):
    seen=set()
    def size(item):
        identity=id(item)
        if identity in seen:return 0
        seen.add(identity);total=sys.getsizeof(item)
        if isinstance(item,dict):total+=sum(size(key)+size(value) for key,value in item.items())
        elif isinstance(item,(list,tuple,set,frozenset)):total+=sum(size(value) for value in item)
        return total
    return size(value)

def bounded_cache(maxsize=32,maxbytes=8*1024*1024):
    def decorate(function):
        items=OrderedDict();lock=threading.RLock()
        used=hits=misses=generation=0
        @wraps(function)
        def read(*args,**kwargs):
            nonlocal used,hits,misses
            key=(args,tuple(sorted(kwargs.items())))
            with lock:
                if key in items:
                    hits+=1;items.move_to_end(key);return items[key][0]
                misses+=1;before=generation
            value=function(*args,**kwargs);cost=retained_size(value)
            with lock:
                if generation==before and cost<=maxbytes:
                    if key in items:used-=items.pop(key)[1]
                    while items and (len(items)>=maxsize or used+cost>maxbytes):used-=items.popitem(last=False)[1][1]
                    items[key]=(value,cost);used+=cost
            return value
        def clear():
            nonlocal used,hits,misses,generation
            with lock:items.clear();used=hits=misses=0;generation+=1
        def info():
            with lock:return Info(hits,misses,maxsize,len(items))
        read.cache_clear=clear;read.cache_info=info
        read.cache_bytes=lambda:used
        return read
    return decorate
