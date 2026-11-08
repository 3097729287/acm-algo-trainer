"""Prepare reviewed required-input distribution; never upload or unretire a task."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from required_downloads import CHUNK_BYTES,load_manifest


def verify_zip(source,item):
    h=hashlib.sha256();count=0
    with source.open('rb')as f:
        for expected in item['chunkSha256']:
            block=f.read(CHUNK_BYTES)
            if not block or hashlib.sha256(block).hexdigest()!=expected:raise ValueError('Original input block checksum mismatch')
            h.update(block);count+=len(block)
        if f.read(1):raise ValueError('Original input archive is too long')
    if count!=item['bytes']or h.hexdigest()!=item['sha256']:raise ValueError('Original input archive checksum mismatch')
    expected={entry['name']:entry for entry in item['members']}
    with zipfile.ZipFile(source)as archive:
        members=archive.infolist()
        if len(members)!=len(expected)or {entry.filename for entry in members}!=set(expected):raise ValueError('Original input ZIP inventory mismatch')
        for entry in members:
            record=expected[entry.filename]
            if entry.flag_bits&1 or entry.is_dir()or entry.file_size!=record['bytes']:raise ValueError('Original input member metadata mismatch')
            sha=hashlib.sha256();size=0
            with archive.open(entry)as f:
                while block:=f.read(CHUNK_BYTES):
                    size+=len(block)
                    if size>record['bytes']:raise ValueError('Original input member exceeds reviewed size')
                    sha.update(block)
            if size!=record['bytes']or sha.hexdigest()!=record['sha256']:raise ValueError('Original input member checksum mismatch')
    return {'sha256':item['sha256'],'bytes':count,'verifiedZipMembers':len(expected),'allMembersCrcAndSha256Verified':True}


def prepare(destination,*,manifest_path=None,source_root=None,repository_root=ROOT):
    repository_root=Path(repository_root).resolve()
    manifest_path=Path(manifest_path or ROOT/'backend/resources/reviewed-required-downloads.json').resolve()
    source_root=Path(source_root or ROOT/'data/required-downloads').resolve()
    destination=Path(destination).resolve()
    if destination.exists():raise ValueError('Choose a new required-download staging directory')
    items=load_manifest(manifest_path)
    verified=[]
    for item in items.values():
        source=source_root/(item['sha256']+'.zip')
        if source.is_symlink()or source.resolve().parent!=source_root:raise ValueError('Invalid canonical input archive location')
        record_path=item.get('reviewRecord')
        if not isinstance(record_path,str):raise ValueError('Missing manual source-review record')
        review=(repository_root/record_path).resolve(strict=True)
        if not review.is_relative_to(repository_root/'content-updates')or review.is_symlink():raise ValueError('Invalid source-review location')
        raw=review.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item['reviewSha256']:raise ValueError('Manual source-review checksum mismatch')
        proof=json.loads(raw)
        if (proof.get('sha256')!=item['sha256']or proof.get('bytes')!=item['bytes']
            or proof.get('allTenOriginalFilesCrcAndBoundsValidated')is not True
            or item['problemId']!='luogu-training-'+proof.get('nativeProblemId','')
            or proof.get('nativeSource',{}).get('url')!=item['sourceUrl']
            or proof.get('nativeSource',{}).get('originalDownloadUrl')!=item['originalDownloadUrl']
            or proof.get('reviewedStatementSha256')!=item['statementSha256']):
            raise ValueError('Required input source-review binding mismatch')
        original=item.get('original',{})
        if (proof.get('sourceRepository')!=original.get('repository')or proof.get('commit')!=original.get('commit')
            or proof.get('gitBlobSha1')!=original.get('blobSha1')or proof.get('path')!=original.get('path')
            or proof.get('nativeSource',{}).get('sha256')!=original.get('nativeJsonSha256')):
            raise ValueError('Original Git/native source binding mismatch')
        checked=verify_zip(source,item)
        verified.append((item,source,review,checked))
    # Validate every original before creating any deployable output.
    destination.mkdir(parents=True)
    archives=destination/'required-downloads';archives.mkdir()
    proofs=destination/'proofs';proofs.mkdir()
    report=[]
    for item,source,review,checked in verified:
        target=archives/(item['sha256']+'.zip')
        with source.open('rb')as f,target.open('xb')as out:shutil.copyfileobj(f,out,CHUNK_BYTES)
        shutil.copyfile(review,proofs/(item['sha256']+'.json'))
        report.append(dict(checked,problemId=item['problemId'],archive=target.relative_to(destination).as_posix(),
                           route='/updates/required-downloads/'+item['sha256']+'.zip',
                           sourceRepository=item['original']['repository'],sourceCommit=item['original']['commit'],
                           originalGitBlobSha1=item['original']['blobSha1']))
    shutil.copyfile(manifest_path,destination/'public-required-downloads.json')
    result={'schema':1,'deployed':False,'ordinaryAssetLimitBytes':32*1024*1024,
        'inputArchives':report,'manifest':'public-required-downloads.json',
        'serverCode':'server/leaderboard/src/required-downloads.mjs plus server.mjs route registration',
        'proxyCode':'server/leaderboard/Caddyfile: required_inputs forwards the stripped /required-downloads/* path to the reviewed Node route',
        'serverConfiguration':{'REQUIRED_DOWNLOADS_FILE':'public-required-downloads.json','REQUIRED_DOWNLOADS_DIR':'required-downloads'},
        'catalogueRetirementChanged':False,'privateStateReadOrWritten':False}
    (destination/'deployment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--source-root',type=Path)
    args=parser.parse_args()
    result=prepare(args.output,manifest_path=args.manifest,source_root=args.source_root)
    print(json.dumps({'archives':len(result['inputArchives']),'bytes':sum(x['bytes']for x in result['inputArchives']),'deployed':False,'catalogueRetirementChanged':False}))
