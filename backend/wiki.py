"""Read only OI Wiki snapshot, isolated from templates, notes and user libraries."""
from pathlib import Path
import sqlite3
from paths import resource
from errors import APIError

def read(query='', identity=None, path=None):
    file = Path(path) if path else resource('oi-wiki.sqlite3')
    with sqlite3.connect(file.resolve().as_uri()+'?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        metadata = dict(db.execute('SELECT key,value FROM metadata'))
        if identity is not None:
            row = db.execute('SELECT id,title,category,url,revision,sha256,html FROM articles WHERE id=?', (identity,)).fetchone()
            if row is None: raise APIError(404, '没有找到这篇维基百科')
            return {'article':dict(row), 'capturedAt':metadata['capturedAt']}
        if not isinstance(query, str) or len(query)>200: raise APIError(400,'搜索内容过长')
        terms = query.casefold().split()
        rows = [dict(row) for row in db.execute('SELECT id,title,category,url,search_text FROM articles ORDER BY rowid') if all(term in (row['title']+' '+row['search_text']).casefold() for term in terms)]
        for row in rows: row.pop('search_text')
        return {'articles':rows, 'revision':metadata['revision'], 'capturedAt':metadata['capturedAt']}
