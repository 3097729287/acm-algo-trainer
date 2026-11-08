"""Preserve a public seed's storage layout while proving identical content."""
from contextlib import closing
import argparse,hashlib,json,os,shutil,sqlite3
from pathlib import Path

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def build(canonical,library,output):
    canonical=canonical.resolve(strict=True);library=library.resolve(strict=True)
    if output.exists():raise ValueError('Use a new public profile directory')
    with closing(sqlite3.connect((canonical/'data/library.sqlite3').as_uri()+'?mode=ro',uri=True)) as base,closing(sqlite3.connect(library.as_uri()+'?mode=ro',uri=True)) as profile:
        tables={row[0] for row in base.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if tables!={row[0] for row in profile.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}:raise ValueError('Public schema differs')
        if tables&{'training','drafts','submissions','documents','accounts','ranking_profile'}:raise ValueError('Private state cannot be a public layout profile')
        for table in tables-{'statement_assets','remote_statement_assets'}:
            info=base.execute('PRAGMA table_info('+table+')').fetchall()
            if info!=profile.execute('PRAGMA table_info('+table+')').fetchall():raise ValueError('Public columns differ: '+table)
            order=','.join(str(i+1) for i in range(len(info)))
            if list(base.execute('SELECT * FROM '+table+' ORDER BY '+order))!=list(profile.execute('SELECT * FROM '+table+' ORDER BY '+order)):raise ValueError('Public content differs: '+table)
        def assets(db):
            result={}
            for identity,mime,raw in db.execute('SELECT sha256,mime,data FROM statement_assets'):
                if hashlib.sha256(raw).hexdigest()!=identity:raise ValueError('Invalid public resource')
                result[identity]=(mime,len(raw))
            for identity,mime,size,url in db.execute('SELECT sha256,mime,bytes,url FROM remote_statement_assets'):
                if identity in result:raise ValueError('Duplicate resource storage')
                result[identity]=(mime,size)
            return result
        resource_map=assets(base)
        if resource_map!=assets(profile):raise ValueError('Public resource contents differ')
        if profile.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or profile.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Invalid public profile')
        counts={table:profile.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in ('problems','statements','solutions','detailed_solutions')}
    output.mkdir(parents=True)
    for path in canonical.rglob('*'):
        if not path.is_file():continue
        relative=path.relative_to(canonical)
        if relative.parts[0] in {'state','cache','logs','backups'} or path.is_symlink():raise ValueError('Private or redirected package input')
        target=output/relative;target.parent.mkdir(parents=True,exist_ok=True)
        try:os.link(path,target)
        except OSError:shutil.copyfile(path,target)
    def replace(name,data=None,source=None):
        target=output/name;temporary=target.with_name(target.name+'.profile-next')
        if source:shutil.copyfile(source,temporary)
        else:temporary.write_bytes(data)
        os.replace(temporary,target)
    library_sha=sha(library);canonical_sha=sha(canonical/'data/library.sqlite3')
    replace('data/library.sqlite3',source=library)
    with library.open('rb') as stream:header=stream.read(100)
    identity={'schema':1,'bytes':library.stat().st_size,'sha256':library_sha,'headerSha256':hashlib.sha256(header).hexdigest()}
    replace('resources/library-seed-identity.json',(json.dumps(identity,sort_keys=True)+'\n').encode())
    for name in ('BUILD-INFO.json','resources/BUILD-INFO.json'):
        value=json.loads((canonical/name).read_text('utf8'));value.update(publicLibrarySha256=library_sha,publicLibraryVariantOf=canonical_sha,publicLibraryContentEquivalent=True)
        replace(name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return {'ok':True,'profile':str(output.resolve()),'librarySha256':library_sha,'canonicalLibrarySha256':canonical_sha,'samePublicTables':sorted(tables-{'statement_assets','remote_statement_assets'}),'sameResourceContents':len(resource_map),'counts':counts,'privateStateReadOrWritten':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--canonical',type=Path,required=True);p.add_argument('--library',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();v=build(a.canonical,a.library,a.output);a.receipt.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(v,ensure_ascii=False),flush=True)
