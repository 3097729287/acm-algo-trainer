"""Replay-only deduplication by reviewed original/mirror links; no progress rewrite."""
from functools import lru_cache
import json
from paths import resource
from insights import canonical_url
@lru_cache(maxsize=1)
def mirrors():return {canonical_url(key):canonical_url(value) for key,value in json.loads(resource('replay-mirrors.json').read_text(encoding='utf8')).items()}
def unique_replay_rows(rows):
    mapping=mirrors();groups={}
    for index,row in enumerate(rows):
        key=canonical_url(row.get('url')) or row.get('id') or ('anonymous',index);key=mapping.get(key,key)
        groups.setdefault(key,[]).append(row)
    result=[]
    for entries in groups.values():
        chosen=min(entries,key=lambda row:(not bool(row.get('catalogContentReady')),row.get('platform') not in {'Codeforces','codeforces'},row.get('source')=='remote'))
        value=dict(chosen)
        value['tags']=list(dict.fromkeys(tag for row in entries for tag in row.get('tags',[])))
        result.append(value)
    return result
