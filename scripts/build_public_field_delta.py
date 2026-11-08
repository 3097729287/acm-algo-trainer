"""Build a byte-exact seed patch which reuses existing public illustration data."""
from contextlib import closing
import argparse,gzip,hashlib,json,shutil,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'desktop'),str(ROOT/'scripts')]
from sqlite_public_fields import image_spans
from build_binary_delta import build as binary_build
from binary_delta import file_delta

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def build(source,target,output,tool):
    if output.exists():raise ValueError('Choose a new public-field build directory')
    output.mkdir(parents=True);resources=output/'resources';resources.mkdir();requested={};values={}
    with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)) as old,closing(sqlite3.connect(target.resolve().as_uri()+'?mode=ro',uri=True)) as current:
        for table in ('solutions','detailed_solutions'):
            previous={row[0]:hashlib.sha256(row[1].encode('utf8')).hexdigest() for row in old.execute('SELECT problem_id,images FROM '+table)}
            requested[table]=set()
            for identity,text in current.execute('SELECT problem_id,images FROM '+table):
                raw=text.encode('utf8');digest=hashlib.sha256(raw).hexdigest()
                if len(raw)<8192 or previous.get(identity)==digest:continue
                requested[table].add(identity);values[digest]=raw
    located=image_spans(target,requested);fields={};template=output/'template.sqlite3';shutil.copyfile(target,template)
    with template.open('r+b') as stream:
        for entry in located:
            digest=entry['sha256'];field=fields.setdefault(digest,{'sha256':digest,'bytes':entry['bytes'],'candidates':[],'spans':[]})
            field['candidates'].append({'table':entry['table'],'id':entry['id']});field['spans']+=entry['spans']
            for at,offset,n in entry['spans']:stream.seek(at);stream.write(bytes(n))
    for digest,item in fields.items():
        raw=gzip.compress(values[digest],compresslevel=9,mtime=0);compressed=hashlib.sha256(raw).hexdigest();path=resources/(compressed+'.bin')
        path.write_bytes(raw);item.update(compressedSha256=compressed,compressedBytes=len(raw),url='https://47.82.84.74/updates/library-assets/'+compressed+'.bin')
        item['spans'].sort()
    patch=output/'library-public-fields.tbbd';proof=binary_build(source,template,patch,tool)
    verified=output/'verified.sqlite3';file_delta(source,patch,verified,expected_target=sha(template))
    with verified.open('r+b') as stream:
        for digest,item in fields.items():
            raw=values[digest]
            for at,offset,n in item['spans']:stream.seek(at);stream.write(raw[offset:offset+n])
    if sha(verified)!=sha(target):raise ValueError('Public fields did not reconstruct the exact seed')
    report={'ok':True,'source':str(source.resolve()),'target':str(target.resolve()),'sourceSha256':sha(source),'targetSha256':sha(target),'templateSha256':sha(template),'patch':str(patch.resolve()),'patchBytes':patch.stat().st_size,'fields':list(fields.values()),'uniquePublicFields':len(fields),'fieldOccurrences':len(located),'reusablePublicBytes':sum(sum(s[2] for s in item['spans']) for item in fields.values()),'fallbackResourceBytes':sum(item['compressedBytes'] for item in fields.values()),'resourceDirectory':str(resources.resolve()),'byteExactRoundTrip':True,'privateStateReadOrWritten':False}
    (output/'receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='fields'},ensure_ascii=False),flush=True);return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--target',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--bsdiff-tool',type=Path,required=True);a=p.parse_args();build(a.source,a.target,a.output,a.bsdiff_tool)
