"""Verify safe system recycling with tiny, closed, isolated filesystem items.

Existing bin metadata is hashed in memory and checked after each operation;
nothing empties, resizes, restores or removes existing bin contents.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from system_recycle import recycle


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work-dir',type=Path,required=True)
    args=parser.parse_args();root=args.work_dir.resolve()
    assert root.is_relative_to((ROOT/'.backups/next-150').resolve())
    root.mkdir(parents=True,exist_ok=False)
    bin_root=Path(os.environ['TB_RECYCLE_TEST_BIN'])
    assert bin_root.drive==root.drive and bin_root.parent.name=='$Recycle.Bin'
    def existing():
        # Explorer can briefly hold a new metadata entry exclusively after
        # IFileOperation returns; retry observation only, never the mutation.
        for attempt in range(20):
            try:return {path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in bin_root.glob('$I*') if path.is_file()}
            except PermissionError:
                if attempt==19:raise
                time.sleep(.05)
    before=existing();results=[]
    protected=root/'current.txt';protected.write_text('protected isolated current marker','utf8')
    candidates=[root/'原生回收验证.txt',root/'candidate']
    candidates[0].write_bytes(b'isolated-recycle-proof')
    candidates[1].mkdir();(candidates[1]/'fixture.txt').write_bytes(b'closed candidate fixture')
    for path in candidates:
        assert path.is_relative_to(root) and not path.is_symlink()
        recycled=recycle(path);after=existing()
        assert all(after.get(name)==digest for name,digest in before.items()),'An existing bin item changed'
        entry={'kind':'directory' if path==candidates[1] else 'file','recycled':recycled,'retained':path.exists(),'binProof':False}
        if recycled:
            assert not path.exists()
            for name in set(after)-set(before):
                data=(bin_root/name).read_bytes();version=struct.unpack_from('<Q',data)[0]
                original=data[28 if version==2 else 24:].decode('utf-16-le').rstrip('\0')
                if Path(original)==path:
                    assert (bin_root/('$R'+name[2:])).exists();entry['binProof']=True;break
            assert entry['binProof'],'System bin receipt did not identify the isolated target'
        else:assert path.exists(),'Unsuccessful recycling must retain the original'
        before=after;results.append(entry)
    assert protected.read_text('utf8')=='protected isolated current marker'
    report={'passed':True,'existingBinItemsPreserved':True,'permanentDeletion':False,'results':results,
            'freeGiB':{drive:round(shutil.disk_usage(drive+':\\').free/1024**3,3) for drive in ('C','D')}}
    (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(report,ensure_ascii=False,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
