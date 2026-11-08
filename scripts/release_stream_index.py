"""Author range proofs from a public local file and its exact GitHub digest.

No upload or user-selected upstream URL is implemented here. The serving code
always derives the original URL from the fixed public repository and filename.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

CHUNK_BYTES=1024*1024
MAX_INDEX_BYTES=1024*1024
PUBLIC_NAME=re.compile(r'(?:ToBe|TB)-(?:(?:Full-)?Setup-\d+\.\d+\.\d+-win64\.exe|(?:Compact-)?Update-\d+\.\d+\.\d+-to-\d+\.\d+\.\d+-win64\.zip)')
SHA=re.compile('[a-f0-9]{64}')


def validate_asset(item):
    if (not isinstance(item,dict)or not re.fullmatch(r'\d+\.\d+\.\d+',item.get('version')or'')
        or not PUBLIC_NAME.fullmatch(item.get('name')or'')or not PUBLIC_NAME.fullmatch(item.get('sourceName')or item['name'])
        or type(item.get('size'))is not int or not 0<item['size']<=2*1024**3
        or not SHA.fullmatch(item.get('sha256')or'')):
        raise ValueError('Invalid public release asset')
    if 'chunkBytes'in item or 'chunkSha256'in item:
        chunks=item.get('chunkSha256')
        if (item.get('chunkBytes')!=CHUNK_BYTES or item.get('githubDigest')!='sha256:'+item['sha256']
            or not isinstance(chunks,list)or len(chunks)!=(item['size']+CHUNK_BYTES-1)//CHUNK_BYTES
            or not all(isinstance(sha,str)and SHA.fullmatch(sha)for sha in chunks)):
            raise ValueError('Invalid reviewed release range proofs')
    return item


def reviewed_stream_asset(asset,version,github_asset,*,name=None):
    asset=Path(asset)
    if asset.is_symlink()or not asset.is_file():raise ValueError('Expected a regular local public release file')
    source_name=github_asset.get('name')if isinstance(github_asset,dict)else None
    if source_name!=asset.name:raise ValueError('Local and GitHub public release names differ')
    if type(github_asset.get('size'))is not int or github_asset['size']!=asset.stat().st_size:raise ValueError('Local and GitHub public release sizes differ')
    validate_asset({'version':version,'name':name or asset.name,'sourceName':source_name,
                    'size':asset.stat().st_size,'sha256':'0'*64})
    h=hashlib.sha256();chunks=[];count=0
    with asset.open('rb')as stream:
        while block:=stream.read(CHUNK_BYTES):
            h.update(block);count+=len(block);chunks.append(hashlib.sha256(block).hexdigest())
    digest=h.hexdigest()
    if github_asset.get('digest')!='sha256:'+digest:raise ValueError('GitHub digest differs from the complete local public file')
    item={'version':version,'name':name or asset.name,'size':count,'sha256':digest,
          'githubDigest':github_asset['digest'],'chunkBytes':CHUNK_BYTES,'chunkSha256':chunks}
    if item['name']!=source_name:item['sourceName']=source_name
    return validate_asset(item)


def merge_stream_index(existing,additions):
    if not isinstance(existing,dict)or existing.get('schema')!=1 or not isinstance(existing.get('assets'),list):
        raise ValueError('Invalid existing public release index')
    result={}
    for position,item in enumerate([*existing['assets'],*additions]):
        validate_asset(item);key=item['version'],item['name']
        if key in result:
            if position<len(existing['assets']):raise ValueError('Duplicate identity in approved release history')
            before=result[key]
            if any(before.get(field)!=item.get(field)for field in ['size','sha256'])or before.get('sourceName',before['name'])!=item.get('sourceName',item['name']):
                raise ValueError('An immutable public release identity cannot change its source bytes')
            if 'chunkSha256'in before and 'chunkSha256'not in item:continue
        result[key]=dict(item)
    if len(result)>100:raise ValueError('Public release index exceeds approved item count')
    value={'schema':1,'assets':list(result.values())}
    if len((json.dumps(value,indent=2)+'\n').encode())>MAX_INDEX_BYTES:raise ValueError('Public release index exceeds approved byte limit')
    return value


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset',type=Path,required=True)
    parser.add_argument('--version',required=True)
    parser.add_argument('--github-release',type=Path,required=True,help='Captured gh release view --json tagName,isDraft,assets result')
    parser.add_argument('--existing',type=Path,help='Existing approved index; every old entry is retained')
    parser.add_argument('--name',help='Optional public route alias; original source filename stays explicit')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('Choose a new index output path')
    release=json.loads(args.github_release.read_text('utf8'))
    if release.get('isDraft')is not False or release.get('tagName')!='v'+args.version or not isinstance(release.get('assets'),list):
        raise ValueError('Expected the exact published GitHub release metadata')
    matching=[item for item in release['assets']if item.get('name')==args.asset.name]
    if len(matching)!=1:raise ValueError('Expected one exact GitHub public release asset')
    item=reviewed_stream_asset(args.asset,args.version,matching[0],name=args.name)
    previous=json.loads(args.existing.read_text('utf8'))if args.existing else{'schema':1,'assets':[]}
    value=merge_stream_index(previous,[item])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf8',newline='\n')as stream:stream.write(json.dumps(value,indent=2)+'\n')
    print(json.dumps({'assets':len(value['assets']),'rangeProofs':len(item['chunkSha256']),'bytes':item['size'],'sha256':item['sha256'],'githubDigestVerified':True,'uploaded':False}))
