"""Prepare pinned small Windows formatters at build time; runtime never downloads."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,urllib.request,zipfile

ROOT=Path(__file__).resolve().parent.parent
MANIFEST=ROOT/'backend/resources/code-formatters.json'

def tools():
    value=json.loads(MANIFEST.read_text('utf8'))
    assert value['schema']==1 and value['platform']=='win_amd64'
    return value['tools']

def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def verify(directory):
    directory=Path(directory).resolve()
    for item in tools().values():
        path=directory/item['fileName']
        if not path.is_file() or path.stat().st_size!=item['bytes'] or digest(path)!=item['sha256']:
            raise RuntimeError('Missing or unverified formatter: '+item['name'])
    return directory

def prepare(directory,download=False):
    directory=Path(directory).resolve();directory.mkdir(parents=True,exist_ok=True)
    for item in tools().values():
        wheel=item['wheel'];archive=directory/wheel['filename']
        if not archive.exists():
            if not download:raise RuntimeError('Pinned wheel missing; use --download only during build preparation')
            if not wheel['url'].startswith('https://files.pythonhosted.org/packages/') or wheel['bytes']>32*1024**2:
                raise RuntimeError('Unexpected formatter source')
            with urllib.request.urlopen(wheel['url'],timeout=30) as response:
                payload=response.read(wheel['bytes']+1)
            if len(payload)!=wheel['bytes'] or hashlib.sha256(payload).hexdigest()!=wheel['sha256']:
                raise RuntimeError('Formatter wheel digest differs from the pinned official PyPI digest')
            archive.write_bytes(payload)
        if archive.stat().st_size!=wheel['bytes'] or digest(archive)!=wheel['sha256']:
            raise RuntimeError('Formatter wheel digest mismatch')
        target=directory/item['fileName']
        if not target.exists():
            with zipfile.ZipFile(archive) as bundle:payload=bundle.read(wheel['executableMember'])
            if len(payload)!=item['bytes'] or hashlib.sha256(payload).hexdigest()!=item['sha256'] or not payload.startswith(b'MZ'):
                raise RuntimeError('Pinned native executable mismatch')
            target.write_bytes(payload)
    verify(directory)
    shutil.copy2(MANIFEST,directory/'manifest.json')
    for item in tools().values():
        output=subprocess.check_output([str(directory/item['fileName']),'--version'],timeout=5,
                                       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)).decode('utf8','replace')
        if item['version'] not in output:raise RuntimeError('Unexpected formatter version')
    return directory

def copy_to_package(source,package):
    source=verify(source);package=Path(package).resolve();target=package/'resources/formatters'
    if target.exists():raise RuntimeError('Formatter package target already exists')
    target.mkdir(parents=True)
    for item in tools().values():shutil.copy2(source/item['fileName'],target/item['fileName'])
    shutil.copy2(MANIFEST,target/'manifest.json')
    (target/'licenses').mkdir()
    for item in tools().values():
        for license in item['licenseFiles']:
            source_license=ROOT/license['path']
            if digest(source_license)!=license['sha256']:raise RuntimeError('Formatter license digest mismatch')
            shutil.copy2(source_license,target/'licenses'/source_license.name)
    verify(target)
    return target

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--download',action='store_true')
    parser.add_argument('--copy-to-package',type=Path)
    args=parser.parse_args()
    directory=prepare(args.output,args.download)
    target=copy_to_package(directory,args.copy_to_package) if args.copy_to_package else directory
    print(json.dumps({'directory':str(target),'bytes':sum(t['bytes'] for t in tools().values()),'verified':True}))

if __name__=='__main__':main()
