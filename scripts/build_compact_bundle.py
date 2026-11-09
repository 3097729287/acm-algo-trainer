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
from compact_update import ROOT_FILES,PREFIXES,public_path,PUBLIC_SEED,PUBLIC_IDENTITY,PUBLIC_DESCRIPTOR,preserved_public_profiles
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


def build(package,baselines,output,tool,prebuilt=(),field_delta=None,*,preserve_public_seed=False,approved_stale_seed_identities=(),preserve_existing_public_profiles=False):
    if preserve_public_seed and preserve_existing_public_profiles:raise ValueError('Choose one public preservation mode')
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
    approved=set(approved_stale_seed_identities);stale=set()
    if len(approved)>8 or any(not isinstance(pair,tuple) or len(pair)!=2 or any(not isinstance(item,str) or not re.fullmatch('[a-f0-9]{64}',item) for item in pair) for pair in approved):
        raise ValueError('Use exact reviewed public seed and identity file hashes')
    content_update=None;public_profiles=None;metadata_updates={}
    if preserve_existing_public_profiles:
        if versions!={'1.6.11'}:raise ValueError('Existing public profile preservation requires approved 1.6.11 baselines')
        sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
        from public_library_update import load_descriptor
        from seed_identity import describe,identity
        target_sha=target.get(PUBLIC_SEED,{}).get('sha256')
        descriptor,_,_=load_descriptor(package/PUBLIC_DESCRIPTOR)
        if descriptor.get('targetSeedSha256')!=target_sha:raise ValueError('The canonical program has a different public target')
        public_profiles={'targetSeedSha256':target_sha,'combinations':[]}
        for directory,base in zip(baselines,old):
            if not all(name in base for name in (PUBLIC_SEED,PUBLIC_IDENTITY,PUBLIC_DESCRIPTOR)):
                raise ValueError('An approved public profile is incomplete')
            seed=base[PUBLIC_SEED];marker=base[PUBLIC_IDENTITY]
            previous,payload,_=load_descriptor(directory/PUBLIC_DESCRIPTOR)
            if previous['targetSeedSha256']!=target_sha:raise ValueError('An existing public profile has a different target')
            if json.loads(marker['path'].read_text('utf8'))!=describe(seed['path']):
                pair=(seed['sha256'],marker['sha256'])
                if pair not in approved or identity(seed['path'],descriptor=marker['path'])!=seed['sha256']:
                    raise ValueError('An existing public seed identity is not approved')
                stale.add(pair)
            combination={name:base[name]['sha256'] for name in (PUBLIC_SEED,PUBLIC_IDENTITY,PUBLIC_DESCRIPTOR)}
            if payload is None:
                if seed['sha256']!=target_sha:raise ValueError('A complete public profile does not contain its target seed')
            else:
                if seed['sha256'] not in previous['baseSeeds']:raise ValueError('A row profile does not approve its physical seed')
                name=payload.relative_to(directory).as_posix()
                if name not in base or base[name]['sha256']!=previous['payloadSha256']:raise ValueError('A preserved public payload differs')
                combination[name]=base[name]['sha256']
            if combination not in public_profiles['combinations']:public_profiles['combinations'].append(combination)
        preserved_public_profiles({'files':{},'preservedPublicProfiles':public_profiles})
        excluded=set().union(*(set(item) for item in public_profiles['combinations']))
        for name in excluded:target.pop(name,None)
        policy_sha=hashlib.sha256(json.dumps(public_profiles,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        for name in ('BUILD-INFO.json','resources/BUILD-INFO.json'):
            if name not in target:continue
            info=json.loads(target[name]['path'].read_text('utf8'))
            if info.get('publicLibrarySha256',target_sha)!=target_sha:raise ValueError('Build metadata has a different public target')
            info.pop('publicLibrarySha256',None)
            info.update(publicLibraryMode='preserved-verified-public-profiles',publicLibraryTargetSha256=target_sha,
                        publicLibraryProfilesSha256=policy_sha,publicLibraryContentEquivalent=True)
            metadata_updates[name]=(json.dumps(info,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    if preserve_public_seed:
        sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
        from public_library_update import load_descriptor
        from seed_identity import describe,identity
        descriptor_path=package/'resources/public-library-update.json'
        descriptor,_,_=load_descriptor(descriptor_path)
        if descriptor.get('mode')=='complete-seed':raise ValueError('A preserved public base needs a row-update profile, not the full installer marker')
        if target.get('data/library.sqlite3',{}).get('sha256')!=descriptor['targetSeedSha256']:
            raise ValueError('The full package and public content update have different targets')
        for index,base in enumerate(old):
            seed=base.get('data/library.sqlite3')
            if not seed or seed['sha256'] not in descriptor['baseSeeds']:
                raise ValueError('An installed public seed is not approved by this content update')
            marker=base.get('resources/library-seed-identity.json')
            if marker and json.loads(marker['path'].read_text('utf8'))!=describe(seed['path']):
                pair=(seed['sha256'],marker['sha256'])
                # Some historical updates retained an older hint file. Keep
                # those exact bytes only after review and prove the unchanged
                # runtime rejects the hint and hashes the actual public seed.
                if pair not in approved or identity(seed['path'],descriptor=marker['path'])!=seed['sha256']:
                    raise ValueError('An installed public seed identity does not match its actual bytes')
                stale.add(pair)
        for name in ('data/library.sqlite3','resources/library-seed-identity.json'):
            if any(name in base for base in old) and not all(name in base for base in old):
                raise ValueError('Separate compact payloads are required for missing public seed identity files')
            if all(name in base for base in old):anchors[name]=sorted({base[name]['sha256'] for base in old})
            target.pop(name,None)
        content_update={'mode':'public-row-overlay','baseSeeds':descriptor['baseSeeds'],
                        'targetSeedSha256':descriptor['targetSeedSha256'],'descriptorSha256':sha(descriptor_path),
                        'preservedFiles':['data/library.sqlite3','resources/library-seed-identity.json']}
    if stale!=approved:raise ValueError('A stale identity approval was not used by these exact public baselines')
    payloads={};files={};blobs={};cache={}
    scratch=Path(tempfile.mkdtemp(prefix='ToBe-compact-payload-'))
    for index,(name,raw) in enumerate(metadata_updates.items()):
        path=scratch/('public-profile-build-info-'+str(index)+'.json');path.write_bytes(raw)
        target[name]={'path':path,'sha256':sha(path),'bytes':len(raw)}
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
    if content_update:value['publicLibrary']=content_update
    if public_profiles:value['preservedPublicProfiles']=public_profiles
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        archive.writestr('compact.json',json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')))
        for name in sorted(payloads):archive.write(blobs[name],name)
    return {'version':version,'fromVersion':next(iter(versions)),'path':str(output.resolve()),'sha256':sha(output),'bytes':output.stat().st_size,'managedFiles':len(files),'payloads':len(payloads),'scratch':str(scratch),
            'retainedStaleSeedIdentities':[{'seedSha256':seed,'descriptorSha256':marker,'runtimeUsesVerifiedFullHash':True} for seed,marker in sorted(stale)]}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--base',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--bsdiff-tool',type=Path,required=True);p.add_argument('--prebuilt',type=Path,action='append',default=[]);p.add_argument('--field-delta-receipt',type=Path);p.add_argument('--preserve-public-seed',action='store_true');p.add_argument('--preserve-existing-public-profiles',action='store_true');p.add_argument('--reviewed-stale-seed-identity',action='append',default=[],metavar='SEED_SHA:IDENTITY_FILE_SHA');p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
    value=build(a.package,a.base,a.output,a.bsdiff_tool,a.prebuilt,a.field_delta_receipt,preserve_public_seed=a.preserve_public_seed,preserve_existing_public_profiles=a.preserve_existing_public_profiles,approved_stale_seed_identities=[tuple(value.split(':')) for value in a.reviewed_stale_seed_identity]);a.receipt.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');print(json.dumps(value),flush=True)
