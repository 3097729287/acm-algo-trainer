"""Build memory-bounded, independently verifiable binary update blocks."""
import argparse
import collections
import hashlib
import json
import mmap
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'desktop'))
from binary_delta import MAGIC,file_delta


def build(source,target,destination,tool):
    sys.path.insert(0,str(tool));import bsdiff4
    source,target,destination=map(Path,(source,target,destination))
    if destination.exists():raise ValueError('差分目标已存在')
    block_size=4*1024**2;index={};zero=hashlib.sha256(bytes(4092)).digest();patches=[];blocks=[]
    with source.open('rb') as a,target.open('rb') as b:
        with mmap.mmap(a.fileno(),0,access=mmap.ACCESS_READ) as old,mmap.mmap(b.fileno(),0,access=mmap.ACCESS_READ) as new:
            for offset in range(0,len(old)-4095,4096):
                key=hashlib.sha256(old[offset+4:offset+4096]).digest()
                if key!=zero:index.setdefault(key,offset)
            for offset in range(0,len(new),block_size):
                data=new[offset:offset+block_size];counts=collections.Counter()
                for at in range(offset,offset+len(data)-4095,16384):
                    reference=index.get(hashlib.sha256(new[at+4:at+4096]).digest())
                    if reference is not None:counts[reference-at]+=1
                shift=counts.most_common(1)[0][0] if counts else 0
                start=max(0,min(offset+shift,len(old)));base=old[start:start+len(data)+65536]
                patch=bsdiff4.diff(base,data)
                assert bsdiff4.patch(base,patch)==data
                patches.append(patch);blocks.append({'sourceOffset':start,'sourceBytes':len(base),'targetBytes':len(data),'patchBytes':len(patch),'patchSha256':hashlib.sha256(patch).hexdigest()})
            info={'schema':1,'sourceBytes':len(old),'sourceSha256':hashlib.sha256(old).hexdigest(),'targetBytes':len(new),'targetSha256':hashlib.sha256(new).hexdigest(),'blocks':blocks}
    header=json.dumps(info,sort_keys=True,separators=(',',':')).encode()
    with destination.open('xb') as stream:
        stream.write(MAGIC);stream.write(struct.pack('<I',len(header)));stream.write(header)
        for patch in patches:stream.write(patch)
    return {'payload':str(destination),'bytes':destination.stat().st_size,'sourceSha256':info['sourceSha256'],'targetSha256':info['targetSha256'],'blocks':len(blocks)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--target',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--bsdiff-tool',type=Path,required=True);p.add_argument('--verify',action='store_true');a=p.parse_args()
    result=build(a.source,a.target,a.output,a.bsdiff_tool)
    if a.verify:
        check=a.output.with_name(a.output.name+'.verified-output')
        file_delta(a.source,a.output,check,expected_target=result['targetSha256']);result['verifiedOutput']=str(check)
    print(json.dumps(result),flush=True)
