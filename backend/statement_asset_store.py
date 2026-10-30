"""Content-addressed original resources in SQLite; reading is still fully offline."""
import base64
import copy
import hashlib
import re

PREFIX = 'tb-asset:'
DATA = re.compile(r'^data:([^;,]+);base64,([A-Za-z0-9+/=\s]+)$')


def transform(value, convert):
    result = copy.deepcopy(value)
    for field in ('images', 'archivedImages'):
        if isinstance(result.get(field), dict):
            result[field] = {name:convert(data) for name,data in result[field].items()}
    if isinstance(result.get('attachments'), dict):
        for entry in result['attachments'].values():
            if isinstance(entry, dict) and isinstance(entry.get('data'), str):entry['data']=convert(entry['data'])
    pdf=result.get('statementPdf')
    if isinstance(pdf, dict) and isinstance(pdf.get('data'), str):pdf['data']=convert(pdf['data'])
    translation=result.get('translation')
    if isinstance(translation, dict) and isinstance(translation.get('images'), dict):
        translation['images']={name:convert(data) for name,data in translation['images'].items()}
    return result


def dehydrate(value, save):
    def convert(data):
        if not isinstance(data, str):return data
        match=DATA.fullmatch(data)
        if not match:return data
        raw=base64.b64decode(re.sub(r'\s+','',match[2]),validate=True)
        sha=hashlib.sha256(raw).hexdigest()
        save(sha,match[1],raw)
        return PREFIX+sha
    return transform(value,convert)


def references(value):
    result=set()
    def collect(data):
        if isinstance(data,str) and data.startswith(PREFIX):result.add(data[len(PREFIX):])
        return data
    transform(value,collect)
    return result


def hydrate(value, db):
    cache={}
    def convert(data):
        if not isinstance(data,str) or not data.startswith(PREFIX):return data
        sha=data[len(PREFIX):]
        if not re.fullmatch('[a-f0-9]{64}',sha):raise ValueError('Invalid offline statement asset identity')
        if sha not in cache:
            row=db.execute('SELECT mime,data FROM statement_assets WHERE sha256=?',(sha,)).fetchone()
            if not row:raise ValueError('Missing offline statement asset: '+sha)
            raw=bytes(row['data'])
            if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Offline statement asset hash mismatch')
            cache[sha]='data:'+row['mime']+';base64,'+base64.b64encode(raw).decode('ascii')
        return cache[sha]
    return transform(value,convert)
