"""Locate validated TEXT fields in SQLite rowid records (builder only).

The file-format rules are documented at https://sqlite.org/fileformat2.html.
Each returned span is checked against SQLite's independently decoded value.
"""
import hashlib,mmap,sqlite3
from contextlib import closing
from pathlib import Path

TABLES={'solutions','detailed_solutions'}

def varint(raw,at):
    value=0
    for n in range(9):
        byte=raw[at+n]
        if n==8:return (value<<8)|byte,at+n+1
        value=(value<<7)|(byte&127)
        if not byte&128:return value,at+n+1
    raise ValueError('Invalid SQLite varint')

def serial_bytes(value):
    if value>=12:return (value-12)//2
    if value in (0,8,9):return 0
    if 1<=value<=4:return value
    if value==5:return 6
    if value in (6,7):return 8
    raise ValueError('Reserved SQLite serial type')

def image_spans(database,requested):
    database=Path(database).resolve(strict=True);result=[]
    with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as db,database.open('rb') as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as raw:
        if raw[:16]!=b'SQLite format 3\0' or int.from_bytes(raw[56:60],'big')!=1:raise ValueError('Only ordinary UTF-8 SQLite files are supported')
        size=int.from_bytes(raw[16:18],'big');size=65536 if size==1 else size;usable=size-raw[20]
        if size<512 or size>65536 or size&(size-1) or usable<480 or len(raw)%size:raise ValueError('Invalid SQLite page size')
        pages=len(raw)//size
        def page(number):
            if not 1<=number<=pages:raise ValueError('Invalid SQLite page reference')
            return (number-1)*size
        def record(cell):
            length,at=varint(raw,cell);identity,at=varint(raw,at)
            if identity>=1<<63:identity-=1<<64
            if length>32*1024**2:raise ValueError('Public row too large')
            local=length
            if length>usable-35:
                minimum=((usable-12)*32//255)-23;candidate=minimum+(length-minimum)%(usable-4)
                local=candidate if candidate<=usable-35 else minimum
            spans=[(at,0,local)];read=local;chain=set()
            if length>local:
                next_page=int.from_bytes(raw[at+local:at+local+4],'big')
                while read<length:
                    if next_page in chain:raise ValueError('SQLite overflow cycle')
                    chain.add(next_page);start=page(next_page);amount=min(usable-4,length-read)
                    spans.append((start+4,read,amount));read+=amount;next_page=int.from_bytes(raw[start:start+4],'big')
                if next_page:raise ValueError('Unexpected SQLite overflow tail')
            data=b''.join(raw[start:start+n] for start,offset,n in spans)
            if len(data)!=length:raise ValueError('Truncated SQLite record')
            return identity,data,spans
        for table,entries in requested.items():
            if table not in TABLES:raise ValueError('Only public editorial images may be reused')
            columns=[row[1] for row in db.execute('PRAGMA table_info('+table+')')];column=columns.index('images')
            root=db.execute('SELECT rootpage FROM sqlite_schema WHERE type=? AND name=?',('table',table)).fetchone()[0]
            lookup={row[0]:(row[1],row[2].encode('utf-8')) for row in db.execute('SELECT rowid,problem_id,images FROM '+table) if row[1] in entries}
            pending=[root];visited=set();found=set()
            while pending:
                number=pending.pop()
                if number in visited:raise ValueError('SQLite btree cycle')
                visited.add(number);start=page(number);header=start+(100 if number==1 else 0);kind=raw[header]
                cells=int.from_bytes(raw[header+3:header+5],'big')
                if kind not in (5,13) or cells>(usable-8)//2:raise ValueError('Unsupported SQLite table btree')
                pointers=header+(12 if kind==5 else 8)
                if kind==5:pending.append(int.from_bytes(raw[header+8:header+12],'big'))
                for i in range(cells):
                    cell=start+int.from_bytes(raw[pointers+i*2:pointers+i*2+2],'big')
                    if kind==5:pending.append(int.from_bytes(raw[cell:cell+4],'big'));continue
                    length,at=varint(raw,cell);rowid,at=varint(raw,at);rowid=rowid-(1<<64) if rowid>=1<<63 else rowid
                    if rowid not in lookup:continue
                    rowid,data,spans=record(cell);identity,expected=lookup[rowid]
                    header_size,pos=varint(data,0);types=[]
                    while pos<header_size:
                        serial,pos=varint(data,pos);types.append(serial)
                    if pos!=header_size or column>=len(types) or types[column]<13 or not types[column]&1:raise ValueError('Invalid editorial image field')
                    offset=header_size+sum(serial_bytes(t) for t in types[:column]);amount=serial_bytes(types[column])
                    if data[offset:offset+amount]!=expected:raise ValueError('SQLite field differs from decoded SQL value')
                    pieces=[]
                    for file_at,record_at,n in spans:
                        first=max(offset,record_at);last=min(offset+amount,record_at+n)
                        if first<last:pieces.append([file_at+first-record_at,first-offset,last-first])
                    if b''.join(raw[a:a+n] for a,b,n in pieces)!=expected:raise ValueError('SQLite field spans failed verification')
                    result.append({'table':table,'id':identity,'sha256':hashlib.sha256(expected).hexdigest(),'bytes':len(expected),'spans':pieces});found.add(identity)
            if found!=set(entries):raise ValueError('Public image row was not found')
    return result
