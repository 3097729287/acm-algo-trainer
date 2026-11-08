"""Build a version-specific, deduplicated compact installer payload."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'desktop'),str(ROOT/'scripts')]
from compact_update import ROOT_FILES,PREFIXES,public_path
from build_binary_delta import build as binary_build


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def inventory(root):
    result={}
    for prefix in PREFIXES:
        directory=root/prefix
        if not directory.exists():continue
        for path in directory.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and not path.is_symlink():
                name=path.relative_to(root).as_posix();public_path(root,name);result[name]={'sha256':sha(path),'bytes':path.stat().st_size,'path':path}
    for name in [*ROOT_FILES,'data/library.sqlite3']:
        path=public_path(root,name)
        if path.is_file():result[name]={'sha256':sha(path),'bytes':path.stat().st_size,'path':path}
    return result


def asset_key(name):
    if not name.startswith('frontend/dist/assets/'):return None
    p=Path(name);match=re.fullmatch(r'(.+)-[A-Za-z0-9_-]{8}'+re.escape(p.suffix),p.name)
    return (match[1],p.suffix) if match else None


def build(package,baselines,output,tool,prebuilt=(),field_delta=None):
    package=package.resolve(strict=True);baselines=[b.resolve(strict=True) for b in baselines]
    if output.exists():raise ValueError('Use a new compact payload destination')
    target=inventory(package);versions={(b/'VERSION').read_text(encoding='utf-8').strip() for b in baselines}
    if len(versions)!=1:raise ValueError('Build one payload per installed version')
    old=[inventory(b) for b in baselines];version=(package/'VERSION').read_text(encoding='utf-8').strip()
    for base in old:
        if any(base.get(k,{}).get('sha256')!=v['sha256'] for k,v in target.items() if k.startswith('compiler/')):
            raise ValueError('Compiler changes need an explicit complete toolchain upgrade')
    anchors={}
    common=set.intersection(*(set(b) for b in old))
    for name in sorted(common):
        if name in {'ToBe.exe','VERSION'} or name.startswith('_internal/'):
            anchors[name]=sorted({b[name]['sha256'] for b in old}|({target[name]['sha256']} if name in target else set()))
    payloads={};files={};blobs={};cache={}
    scratch=Path(tempfile.mkdtemp(prefix='ToBe-compact-payload-'))
    supplied={}
    field_proof=json.loads(field_delta.read_text('utf8')) if field_delta else None
    for path in prebuilt:
        with path.open('rb') as f:
            if f.read(8)!=b'TBBD1\r\n\x00':raise ValueError('Prebuilt delta format mismatch')
            import struct
            size=struct.unpack('<I',f.read(4))[0]
            if size>4*1024**2:raise ValueError('Prebuilt delta header too large')
            info=json.loads(f.read(size))
        supplied[(info['sourceSha256'],info['targetSha256'])]=path
    def add(path):
        digest=sha(path);name='payloads/'+digest+'.bin'
        payloads[name]={'sha256':digest,'bytes':path.stat().st_size};blobs[name]=path
        return name
    def binary(before,after):
        key=(before['sha256'],after['sha256'])
        if key not in cache:
            if key in supplied:path=supplied[key]
            else:
                path=scratch/(key[0]+'-'+key[1]+'.tbbd');binary_build(before['path'],after['path'],path,tool)
            cache[key]=add(path)
        return cache[key]
    asset_indices=[]
    for base in old:
        indexed={}
        for name,value in base.items():
            key=asset_key(name)
            if key:indexed.setdefault(key,[]).append((name,value))
        asset_indices.append(indexed)
    for position,(name,entry) in enumerate(sorted(target.items()),1):
        variants=[];literal=False
        for base,assets in zip(old,asset_indices):
            previous=base.get(name)
            if previous and previous['sha256']==entry['sha256']:continue
            candidates=[(name,previous)] if previous else assets.get(asset_key(name),[])
            candidates=sorted([(path,item) for path,item in candidates if item and item['bytes'] and entry['bytes']>=512],key=lambda pair:abs(pair[1]['bytes']-entry['bytes']))
            if not candidates:literal=True;continue
            best=None
            for source,item in candidates[:4]:
                if field_proof and item['sha256']==field_proof['sourceSha256'] and entry['sha256']==field_proof['targetSha256']:
                    payload=add(Path(field_proof['patch']));candidate={'format':'binary','source':source,'sourceSha256':item['sha256'],'payload':payload}
                    if field_proof['fields']:
                        candidate.update(templateSha256=field_proof['templateSha256'],publicFields=field_proof['fields'])
                    elif field_proof['templateSha256']!=entry['sha256']:
                        raise ValueError('An empty public-field proof must reconstruct the final file directly')
                else:
                    payload=binary(item,entry);candidate={'format':'binary','source':source,'sourceSha256':item['sha256'],'payload':payload}
                if best is None or payloads[payload]['bytes']<payloads[best['payload']]['bytes']:best=candidate
            if best not in variants:variants.append(best)
        if literal:
            variants.append({'format':'literal','payload':add(entry['path'])})
        files[name]={'sha256':entry['sha256'],'bytes':entry['bytes'],'variants':variants,'unchanged':not variants}
        if position%500==0:print(json.dumps({'scanned':position,'total':len(target),'payloadBytes':sum(v['bytes'] for v in payloads.values())}),flush=True)
    # Discard losing candidates from the transport, retaining their local proofs.
    used={v['payload'] for entry in files.values() for v in entry['variants']};payloads={k:v for k,v in payloads.items() if k in used}
    value={'schema':1,'version':version,'fromVersion':next(iter(versions)),'anchors':anchors,'files':files,'payloads':payloads,'privateData':'excluded','compiler':'unchanged'}
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        archive.writestr('compact.json',json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')))
        for name in sorted(payloads):archive.write(blobs[name],name)
    return {'version':version,'fromVersion':next(iter(versions)),'path':str(output.resolve()),'sha256':sha(output),'bytes':output.stat().st_size,'managedFiles':len(files),'payloads':len(payloads),'scratch':str(scratch)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--base',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--bsdiff-tool',type=Path,required=True);p.add_argument('--prebuilt',type=Path,action='append',default=[]);p.add_argument('--field-delta-receipt',type=Path);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    value=build(a.package,a.base,a.output,a.bsdiff_tool,a.prebuilt,a.field_delta_receipt);a.receipt.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');print(json.dumps(value),flush=True)
