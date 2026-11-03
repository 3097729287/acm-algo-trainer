"""Create a small release delta against a verified public package manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/name) for name in ('desktop','backend','backend/common')]
from update_patch import safe_name

def sha256(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def prepare_compat14(package, path, *, legacy=False):
    """One cumulative program payload for original schema-1 1.4 updaters.

    The unchanged compiler is excluded. Old helpers validate fromVersion,
    every archive member and every target path, then back up touched files.
    Version-only base selection also admits locally shipped 1.4 rebuilds.
    """
    package,path=Path(package),Path(path)
    if path.exists():raise ValueError('Use a new compatibility payload')
    sources={}
    for file in sorted(package.rglob('*')):
        if not file.is_file():continue
        name=file.relative_to(package).as_posix()
        try:safe_name(name)
        except ValueError:continue
        if name in ('ToBe.exe','ToBeLoader.exe','TB新版.exe'):continue
        sources[name]=file
    sources['TB新版.exe']=package/'ToBeLoader.exe'
    if legacy:sources['resources/legacy-upgrade/ToBe.exe']=package/'ToBe.exe'
    else:
        sources['ToBe.exe']=package/'ToBe.exe'
        sources['resources/legacy-upgrade/ToBeLoader.exe']=package/'ToBeLoader.exe'
    files={name:sha256(file) for name,file in sources.items()}
    total=sum(file.stat().st_size for file in sources.values())
    if total+4*1024**2>1024**3:raise ValueError('Payload exceeds the original 1.4 updater size limit')
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,file in sources.items():archive.write(file,'files/'+name)
    with zipfile.ZipFile(path) as archive:prefix=archive.start_dir
    return {'schema':1,'version':(package/'VERSION').read_text().strip(),'legacy':legacy,'files':files,'prefixBytes':prefix,'uncompressedBytes':total,'path':str(path)}

def write_compat14(payload, from_version):
    """Reuse the compressed core, changing only its small manifest and index."""
    import re
    match=re.fullmatch(r'1\.4\.(\d+)',from_version)
    if not match or not 0<=int(match[1])<=36 or payload['legacy']!=(int(match[1])<14):raise ValueError('Unsupported original updater layout')
    path=Path(payload['path'])
    with zipfile.ZipFile(path) as archive:entries=[item for item in archive.infolist() if item.filename!='update.json']
    manifest={'schema':1,'version':payload['version'],'fromVersion':from_version,'base':{},'files':payload['files'],'changed':sorted(payload['files']),'kind':'cumulative-program','compiler':'unchanged'}
    with path.open('r+b') as stream:
        stream.seek(payload['prefixBytes']);stream.truncate()
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
            archive.filelist=entries;archive.NameToInfo={item.filename:item for item in entries}
            archive.writestr('update.json',json.dumps(manifest,ensure_ascii=False))
    return {'fromVersion':from_version,'version':payload['version'],'bytes':path.stat().st_size,'sha256':sha256(path),'path':str(path)}


def build(package, baseline, from_version, output):
    version = (package / 'VERSION').read_text().strip()
    if version == from_version:
        raise ValueError('同版本维护请使用完整安装包；增量更新必须包含版本变化')
    def public(values):
        result = {}
        for name, sha in values.items():
            try: safe_name(name)
            except ValueError: continue
            result[name] = sha
        return result
    baseline_files=json.loads(baseline.read_text(encoding='utf-8'))
    package_files={p.relative_to(package).as_posix(): sha256(p) for p in package.rglob('*') if p.is_file()}
    if {n:h for n,h in baseline_files.items() if n.startswith('compiler/')} != {n:h for n,h in package_files.items() if n.startswith('compiler/')}:
        raise ValueError('编译工具发生变化，需要单独发布工具链升级，不能隐藏在程序增量中')
    base = public(baseline_files)
    files = public(package_files)
    changed = sorted(name for name in files if files[name] != base.get(name))
    manifest = {'schema': 1, 'version': version, 'fromVersion': from_version, 'base': base, 'files': files, 'changed': changed}
    output.mkdir(parents=True, exist_ok=True)
    path = output / f'ToBe-Update-{from_version}-to-{version}-win64.zip'
    with zipfile.ZipFile(path, 'x', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr('update.json', json.dumps(manifest, ensure_ascii=False))
        for name in changed: archive.write(package / name, 'files/' + name)
    print(json.dumps({'path': str(path), 'bytes': path.stat().st_size, 'changedFiles': len(changed), 'sha256': sha256(path)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--package', required=True, type=Path)
    p.add_argument('--baseline', type=Path)
    p.add_argument('--compat-14',action='store_true',help='Cumulative core accepted by original 1.4.x updaters')
    p.add_argument('--from-version', required=True)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    if args.compat_14:
        import re
        match=re.fullmatch(r'1\.4\.(\d+)',args.from_version)
        if not match or not 0<=int(match[1])<=36:p.error('Compatibility updates cover 1.4.0 through 1.4.36')
        prefix='TB' if int(match[1])<14 else 'ToBe'
        args.output.mkdir(parents=True,exist_ok=True)
        target=args.output/(prefix+'-Update-'+args.from_version+'-to-'+(args.package/'VERSION').read_text().strip()+'-win64.zip')
        print(json.dumps(write_compat14(prepare_compat14(args.package,target,legacy=int(match[1])<14),args.from_version)))
    else:
        if args.baseline is None:p.error('--baseline is required for a differential update')
        build(args.package, args.baseline, args.from_version, args.output)
