"""Bind a small public update to an otherwise identical complete program build."""
import argparse,hashlib,json,os,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from public_library_update import load_descriptor

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def build(canonical,rows,output):
    canonical=Path(canonical).resolve(strict=True);rows=Path(rows).resolve(strict=True);output=Path(output)
    if output.exists():raise ValueError('Use a new public row profile destination')
    value,payload,_=load_descriptor(rows/'public-library-update.json')
    if value.get('mode')=='complete-seed':raise ValueError('A compact profile needs a public row payload')
    target_sha=sha(canonical/'data/library.sqlite3')
    if target_sha!=value['targetSeedSha256']:raise ValueError('The full build and compact public update have different targets')
    old_marker=canonical/'resources/public-library-update.json';excluded={'resources/public-library-update.json'}
    if old_marker.exists():
        marker,old_payload,_=load_descriptor(old_marker)
        if old_payload is not None:excluded.add(old_payload.relative_to(canonical).as_posix())
    output.mkdir(parents=True)
    def copy(source,target):
        target.parent.mkdir(parents=True,exist_ok=True)
        try:os.link(source,target)
        except OSError:shutil.copyfile(source,target)
    for path in canonical.rglob('*'):
        if not path.is_file():continue
        relative=path.relative_to(canonical);name=relative.as_posix()
        if relative.parts[0] in {'state','cache','logs','backups'} or path.is_symlink():raise ValueError('Private or redirected profile input')
        if name in excluded:continue
        if name.startswith('resources/public-library-update-') and name.endswith('.sqlite3.gz'):raise ValueError('An unrecognized old row payload must be reviewed')
        copy(path,output/relative)
    for source in (rows/'public-library-update.json',payload):copy(source,output/'resources'/source.name)
    for name in ('BUILD-INFO.json','resources/BUILD-INFO.json'):
        original=canonical/name
        if not original.is_file():continue
        info=json.loads(original.read_text('utf8'));info.pop('publicLibrarySha256',None)
        info.update(publicLibraryMode='preserved-base-with-public-row-update',publicLibraryTargetSha256=target_sha,
                    publicLibraryBaseSeeds=value['baseSeeds'],publicLibraryUpdateSha256=sha(rows/'public-library-update.json'),
                    publicLibraryContentEquivalent=True)
        target=output/name;temporary=target.with_name(target.name+'.row-profile-next')
        temporary.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf8');os.replace(temporary,target)
    result={'ok':True,'profile':str(output.resolve()),'fullBuild':str(canonical),'targetSeedSha256':target_sha,
            'baseSeeds':value['baseSeeds'],'rowPayloadBytes':payload.stat().st_size,'replacedPublicMetadataOnly':True,
            'privateStateReadOrWritten':False,'preservedSeedFilesArePinnedByCompactBuilder':True}
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--canonical',type=Path,required=True);parser.add_argument('--rows',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--receipt',type=Path,required=True);args=parser.parse_args()
    result=build(args.canonical,args.rows,args.output);args.receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(result,ensure_ascii=False),flush=True)
