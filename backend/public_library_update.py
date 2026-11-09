"""Apply an authenticated small public seed without replacing the installed base.

Only a release-owned descriptor enables this path. Account state, submissions,
drafts and fetched overrides retain LibraryDatabase.merge_seed semantics.
"""
from contextlib import closing
import gzip,hashlib,json,os,re,sqlite3,uuid
from pathlib import Path
from paths import resource,STATE
from seed_identity import identity

TABLES={'library_meta','bundled_items','problems','problem_urls','solutions','detailed_solutions','solution_methods','statements','statement_assets','remote_statement_assets','lectures','training_lists','problem_lectures','catalog_generation'}
MAX_WIRE=32*1024**2;MAX_DATABASE=64*1024**2
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def valid_sha(value):return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None
def load_descriptor(path):
    path=Path(path).resolve(strict=True)
    if path.stat().st_size>256*1024:raise ValueError('Public update descriptor is too large')
    value=json.loads(path.read_text('utf8'))
    if (isinstance(value,dict) and set(value)=={'schema','mode','targetSeedSha256'}
            and value['schema']==1 and value['mode']=='complete-seed' and valid_sha(value['targetSeedSha256'])):
        return value,None,None
    required={'schema','baseSeeds','targetSeedSha256','payload','payloadSha256','payloadBytes','databaseSha256','databaseBytes','membership','rowCounts','baseInlineAssets'}
    if not isinstance(value,dict) or set(value)!=required or value['schema']!=1:raise ValueError('Invalid public update descriptor')
    if (not isinstance(value['baseSeeds'],list) or not 1<=len(value['baseSeeds'])<=16
            or not all(valid_sha(item) for item in value['baseSeeds']) or len(set(value['baseSeeds']))!=len(value['baseSeeds'])
            or any(not valid_sha(value[key]) for key in ('targetSeedSha256','payloadSha256','databaseSha256'))):raise ValueError('Invalid public update identity')
    if (type(value['payloadBytes']) is not int or not 1<=value['payloadBytes']<=MAX_WIRE
            or type(value['databaseBytes']) is not int or not 1<=value['databaseBytes']<=MAX_DATABASE):raise ValueError('Invalid public update size')
    if value['payload']!='public-library-update-'+value['payloadSha256']+'.sqlite3.gz':raise ValueError('Invalid public update payload name')
    membership=value['membership']
    if (not isinstance(membership,dict) or set(membership)!={'lectureIds','problemLectureSubjects'}
            or any(not isinstance(items,list) or len(items)>100000 or any(not isinstance(item,str) or not item or len(item)>2048 for item in items)
                   or len(set(items))!=len(items) for items in membership.values())):raise ValueError('Invalid public update membership')
    if (not isinstance(value['rowCounts'],dict) or set(value['rowCounts'])!=TABLES
            or any(type(count) is not int or not 0<=count<=1000000 for count in value['rowCounts'].values())):raise ValueError('Invalid public update row counts')
    reused=value['baseInlineAssets']
    if not isinstance(reused,dict) or set(reused)!=set(value['baseSeeds']):raise ValueError('Invalid public resource reuse bases')
    for assets in reused.values():
        if (not isinstance(assets,list) or len(assets)>4096
                or any(not isinstance(item,dict) or set(item)!={'sha256','mime','bytes'}
                       or not valid_sha(item['sha256']) or not isinstance(item['mime'],str) or len(item['mime'])>128
                       or type(item['bytes']) is not int or not 1<=item['bytes']<=MAX_DATABASE for item in assets)
                or len({item['sha256'] for item in assets})!=len(assets)
                or sum(item['bytes'] for item in assets)>MAX_DATABASE):raise ValueError('Invalid public resource reuse identities')
    payload=path.parent/value['payload']
    if payload.is_symlink() or payload.stat().st_size!=value['payloadBytes'] or sha(payload)!=value['payloadSha256']:raise ValueError('Public update payload checksum mismatch')
    composition=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return value,payload,composition

def validate_database(path,value):
    if Path(path).stat().st_size!=value['databaseBytes'] or sha(path)!=value['databaseSha256']:raise ValueError('Public update database checksum mismatch')
    with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row
        schema=list(db.execute("SELECT name,type,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"))
        if {row['name'] for row in schema if row['type']=='table'}!=TABLES or any(row['type']=='view' or 'VIRTUAL TABLE' in (row['sql'] or '').upper() for row in schema):raise ValueError('Public update contains an unsupported schema')
        if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Public update database is corrupt')
        from library import SCHEMA
        with closing(sqlite3.connect(':memory:')) as expected:
            expected.executescript(SCHEMA+'CREATE TABLE catalog_generation(id INTEGER PRIMARY KEY, identity TEXT NOT NULL, generation INTEGER NOT NULL);')
            for table in TABLES:
                columns=lambda connection:tuple(row[1] for row in connection.execute('PRAGMA table_info('+table+')'))
                if columns(db)!=columns(expected):raise ValueError('Public update contains unsupported columns')
        for table in TABLES:
            if db.execute('SELECT count(*) FROM '+table).fetchone()[0]!=value['rowCounts'][table]:raise ValueError('Public update row count mismatch')
        for raw, in db.execute('SELECT raw FROM problems'):
            record=json.loads(raw)
            if record.get('状态')!='未做' or record.get('日期'):raise ValueError('Public update contains personal progress')
        for digest,mime,data in db.execute('SELECT sha256,mime,data FROM statement_assets'):
            if not valid_sha(digest) or hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Public update resource checksum mismatch')
        from public_assets import validate_reference
        for row in db.execute('SELECT sha256,mime,bytes,url FROM remote_statement_assets'):validate_reference(*row)
        subjects=set(value['membership']['problemLectureSubjects'])
        for pid, in db.execute('SELECT DISTINCT problem_id FROM problem_lectures'):
            if pid not in subjects:raise ValueError('Public update link membership mismatch')

def inline_assets(seed, specifications):
    """Recover approved images already embedded in the immutable installed seed."""
    if not specifications:return {}
    from statement_asset_store import dehydrate,inline_documents
    wanted={item['sha256']:item for item in specifications};found={}
    def collect(digest,mime,data):
        if digest not in wanted:return
        item=wanted[digest]
        if mime!=item['mime'] or len(data)!=item['bytes']:raise ValueError('Installed inline resource identity changed')
        found[digest]=(mime,data)
    with closing(sqlite3.connect(Path(seed).resolve().as_uri()+'?mode=ro',uri=True)) as db:
        for content in inline_documents(db):dehydrate(content,collect)
    if set(found)!=set(wanted):raise ValueError('An approved inline public resource is missing')
    return found

def unpack(value,payload,cache):
    cache=Path(cache).resolve();cache.mkdir(parents=True,exist_ok=True)
    target=cache/(value['databaseSha256']+'.sqlite3')
    if target.is_symlink():raise ValueError('Public update cache is redirected')
    if target.exists():
        try:validate_database(target,value);return target
        except (ValueError,sqlite3.Error):
            # Preserve an unrecognized existing file. Only our new verified
            # temporary becomes the source; nothing is read from that file.
            target=cache/(value['databaseSha256']+'-recovered-'+uuid.uuid4().hex+'.sqlite3')
    temporary=cache/('.public-update-'+uuid.uuid4().hex+'.part');digest=hashlib.sha256();count=0
    try:
        with gzip.open(payload,'rb') as source,temporary.open('xb') as destination:
            while block:=source.read(65536):
                count+=len(block)
                if count>value['databaseBytes']:raise ValueError('Public update expands beyond its approved size')
                digest.update(block);destination.write(block)
            destination.flush();os.fsync(destination.fileno())
        if count!=value['databaseBytes'] or digest.hexdigest()!=value['databaseSha256']:raise ValueError('Public update expanded checksum mismatch')
        validate_database(temporary,value);os.replace(temporary,target);return target
    finally:
        if temporary.exists():temporary.unlink()

def merge_public_seed(library,seed,fingerprint=None,*,descriptor=None,cache=None):
    descriptor=Path(descriptor or resource('public-library-update.json'))
    if not descriptor.exists():return library.merge_seed(seed,fingerprint=fingerprint)
    value,payload,composition=load_descriptor(descriptor)
    seed_sha=identity(seed)
    if value.get('mode')=='complete-seed':
        if seed_sha!=value['targetSeedSha256']:raise ValueError('The complete public seed does not match its release identity')
        return library.merge_seed(seed,fingerprint=fingerprint)
    if seed_sha==value['targetSeedSha256']:return library.merge_seed(seed,fingerprint=fingerprint)
    if seed_sha not in value['baseSeeds']:raise ValueError('The installed public base does not match this content update')
    previous=library.metadata().get('bundled_sha256')
    if previous==composition:return False
    source=unpack(value,payload,cache or STATE.parent/'cache/public-updates')
    reused=inline_assets(seed,value['baseInlineAssets'][seed_sha])
    if previous not in value['baseSeeds']:
        library.merge_seed(seed,fingerprint=seed_sha)
    return library.merge_seed(source,fingerprint=composition,_partial=value['membership'],_assets=reused)
