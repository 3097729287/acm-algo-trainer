"""Small Windows bridge: system TLS/PowerShell, pinned embedded Python helper."""
import argparse,hashlib,json,os,re,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def trusted_asset(item,version):
    """Bind optional public CDN transport to the exact trusted compact asset."""
    name=item['name']
    if not re.fullmatch(r'(?:ToBe|TB)-(?:(?:Full-)?Setup-'+re.escape(version)+r'-win64\.exe|Compact-Update-[\d.]+-to-'+re.escape(version)+r'-win64\.zip)',name):raise ValueError('Invalid asset name')
    if item['url']!='https://47.82.84.74/updates/assets/'+version+'/'+name or not re.fullmatch('[a-f0-9]{64}',item['sha256']) or type(item['size']) is not int or item['size']<=0:raise ValueError('Invalid trusted download')
    result={key:item[key] for key in ('name','url','size','sha256')}
    if 'downloadSources' in item:
        sources=item['downloadSources']
        required={'repository','commit','name','size','sha256','urls'}
        if not isinstance(sources,dict) or set(sources)!=required:raise ValueError('Invalid CDN binding')
        if sources['repository']!='3097729287/acm-algo-trainer' or not isinstance(sources['commit'],str) or not re.fullmatch('[a-f0-9]{40}',sources['commit']):raise ValueError('Invalid CDN ownership')
        if 'Compact-Update-' not in name or any(sources[key]!=item[key] for key in ('name','size','sha256')) or type(sources['size']) is not int:raise ValueError('CDN asset identity mismatch')
        expected='https://cdn.jsdelivr.net/gh/'+sources['repository']+'@'+sources['commit']+'/'+name
        if sources['urls']!=[expected]:raise ValueError('Invalid pinned CDN URL')
        result['downloadSources']={**sources,'urls':list(sources['urls'])}
    return result

def build(specification,stage,compiler):
    value=json.loads(specification.read_text('utf-8'));version=value['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Invalid version')
    def asset(item):return trusted_asset(item,version)
    profiles={}
    for base,item in value['profiles'].items():
        if not re.fullmatch(r'\d+\.\d+\.\d+',base):raise ValueError('Invalid baseline')
        profiles[base]=asset(item)
    runtime={}
    for base in map(Path,value['baselines']):
        for path in (base/'_internal/python3').rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                if path.is_symlink():raise ValueError('Redirected runtime')
                runtime.setdefault(path.relative_to(base).as_posix(),set()).add(sha(path))
    if not any(name.endswith('/python.exe') for name in runtime) or not any(name.endswith('.zip') for name in runtime):raise ValueError('Pinned Python runtime missing')
    stage.mkdir(parents=True,exist_ok=False)
    metadata={'schema':1,'version':version,'full':asset(value['full']),'profiles':profiles,'runtime':{name:sorted(hashes) for name,hashes in sorted(runtime.items())}}
    (stage/'release.json').write_text(json.dumps(metadata,ensure_ascii=True,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    with zipfile.ZipFile(stage/'compact-helper.pyz','x',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in [ROOT/'desktop/compact_update.py',ROOT/'desktop/binary_delta.py',ROOT/'desktop/public_field_patch.py',ROOT/'backend/system_recycle.py']:
            archive.writestr(zipfile.ZipInfo(path.name,(1980,1,1,0,0,0)),path.read_bytes(),compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr(zipfile.ZipInfo('__main__.py',(1980,1,1,0,0,0)),b'from compact_update import main\nraise SystemExit(main())\n',compress_type=zipfile.ZIP_DEFLATED)
    (stage/'apply.ps1').write_text((ROOT/'packaging/installer/compact-bootstrap.ps1').read_text('utf-8'),encoding='utf-8-sig')
    numbers=version.replace('.',',')+',0'
    rc=f'''#pragma code_page(65001)
1 ICON "{(ROOT/'desktop/tb.ico').as_posix()}"
101 RCDATA "compact-helper.pyz"
102 RCDATA "apply.ps1"
103 RCDATA "release.json"
1 VERSIONINFO
 FILEVERSION {numbers}
 PRODUCTVERSION {numbers}
 FILEFLAGSMASK 0x3fL
 FILEOS 0x40004L
 FILETYPE 0x1L
BEGIN
 BLOCK "StringFileInfo"
 BEGIN
  BLOCK "040904b0"
  BEGIN
   VALUE "FileDescription", "ToBe update"
   VALUE "FileVersion", "{version}"
   VALUE "ProductName", "ToBe"
   VALUE "ProductVersion", "{version}"
  END
 END
 BLOCK "VarFileInfo"
 BEGIN
  VALUE "Translation", 0x409, 1200
 END
END
'''
    (stage/'bootstrap.rc').write_text(rc,encoding='utf-8')
    compiler=compiler.resolve(strict=True);windres=compiler.with_name('windres.exe')
    env={**os.environ,'PATH':str(compiler.parent)+os.pathsep+os.environ.get('PATH','')}
    subprocess.run([str(windres),'-I',str(stage.resolve()),'-O','coff',str(stage/'bootstrap.rc'),str(stage/'bootstrap.res')],env=env,check=True)
    name=value.get('bridgeName',f'ToBe-Setup-{version}-win64.exe')
    if name not in (f'ToBe-Setup-{version}-win64.exe',f'TB-Setup-{version}-win64.exe'):raise ValueError('Invalid bridge name')
    output=stage/name
    subprocess.run([str(compiler),'-x','c','-municode','-mwindows','-Os','-s','-static','-Wl,--no-insert-timestamp','-finput-charset=UTF-8',str(ROOT/'packaging/installer/compact-bootstrap.c'),'-x','none',str(stage/'bootstrap.res'),'-o',str(output),'-lole32','-lshell32','-lcomctl32','-lgdi32','-luser32'],env=env,check=True)
    report={'version':version,'path':str(output.resolve()),'bytes':output.stat().st_size,'sha256':sha(output),'helperSha256':sha(stage/'compact-helper.pyz'),'powershellSha256':sha(stage/'apply.ps1'),'metadataSha256':sha(stage/'release.json'),'profiles':sorted(profiles),'runtimeFiles':len(runtime),'fullFallback':metadata['full']['name'],'compiler':str(compiler)}
    (stage/'bootstrap.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False),flush=True);return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--spec',type=Path,required=True);parser.add_argument('--stage',type=Path,required=True);parser.add_argument('--compiler',type=Path,required=True);args=parser.parse_args();build(args.spec,args.stage,args.compiler)
