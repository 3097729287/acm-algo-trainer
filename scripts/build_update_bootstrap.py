"""Build the small verified bridge used by pre-compact Windows clients."""
import argparse,hashlib,json,re,subprocess,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOMESTIC='https://47.82.84.74/updates/assets/'

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def literal(value):return "'"+str(value).replace("'","''")+"'"

def build(specification,stage,inno,app_id=None):
    value=json.loads(specification.read_text(encoding='utf-8'))
    version=value['version']
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Invalid version')
    assets=[value['full'],*value['profiles'].values()]
    for asset in assets:
        name=asset['name']
        if not re.fullmatch(r'(?:ToBe|TB)-(?:Setup-'+re.escape(version)+r'-win64\.exe|Compact-Update-[\d.]+-to-'+re.escape(version)+r'-win64\.zip)',name):raise ValueError('Invalid asset name')
        if asset['url']!=DOMESTIC+version+'/'+name or not re.fullmatch('[a-f0-9]{64}',asset['sha256']):raise ValueError('Untrusted download')
    stage.mkdir(parents=True,exist_ok=False)
    helper=stage/'compact-helper.pyz'
    with zipfile.ZipFile(helper,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name in ('compact_update.py','binary_delta.py'):
            archive.writestr(zipfile.ZipInfo(name,(1980,1,1,0,0,0)),(ROOT/'desktop'/name).read_bytes(),compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr(zipfile.ZipInfo('system_recycle.py',(1980,1,1,0,0,0)),(ROOT/'backend/system_recycle.py').read_bytes(),compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr(zipfile.ZipInfo('__main__.py',(1980,1,1,0,0,0)),b'from compact_update import main\nraise SystemExit(main())\n',compress_type=zipfile.ZIP_DEFLATED)
    runtime={}
    for base in map(Path,value['baselines']):
        directory=base/'_internal/python3'
        for path in directory.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                name=path.relative_to(base).as_posix()
                if path.is_symlink():raise ValueError('Redirected runtime')
                runtime.setdefault(name,set()).add(sha(path))
    if not any(name.endswith('/python.exe') for name in runtime) or not any(name.endswith('.zip') for name in runtime):raise ValueError('Missing pinned Python runtime')
    checks=[]
    for name,hashes in sorted(runtime.items()):
        path="ExpandConstant('{app}\\"+name.replace('/','\\')+"')"
        checks.append('  if not FileExists('+path+') then Exit;')
        checks.append('  Hash := GetSHA256OfFile('+path+');')
        checks.append('  if '+ ' and '.join('(CompareText(Hash, '+literal(h)+') <> 0)' for h in sorted(hashes))+' then Exit;')
    branches=[]
    for base,asset in sorted(value['profiles'].items()):
        if not re.fullmatch(r'\d+\.\d+\.\d+',base):raise ValueError('Invalid base version')
        branches.append('  if Trim(Installed) = '+literal(base)+' then begin\n    AssetURL := '+literal(asset['url'])+';\n    AssetName := '+literal(asset['name'])+';\n    AssetHash := '+literal(asset['sha256'])+';\n  end;')
    icon=(ROOT/'desktop/tb.ico').resolve()
    app_id=app_id or '{{53C5CEAE-D6A2-4B88-B8E1-53BCA577A168}'
    if not re.fullmatch(r'\{\{[A-Fa-f0-9-]+\}',app_id):raise ValueError('Invalid installer identity')
    source=f'''[Setup]
AppId={app_id}
AppName=ToBe
AppVersion={version}
AppPublisher=ToBe contributors
AppUpdatesURL=https://47.82.84.74/updates/stable/manifest-v1.json
DefaultDirName={{code:DefaultInstallDir}}
UsePreviousAppDir=no
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableWelcomePage=yes
DisableReadyPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
Uninstallable=no
CreateUninstallRegKey=no
CreateAppDir=no
CloseApplications=no
RestartApplications=no
SetupLogging=yes
WizardStyle=modern
OutputDir={stage.resolve()}
OutputBaseFilename=ToBe-Setup-{version}-win64
SetupIconFile={icon}
Compression=lzma2/max
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{helper.resolve()}"; Flags: dontcopy

[Code]
var
  AssetURL, AssetName, AssetHash: String;
  FullInstall: Boolean;

function DefaultInstallDir(Param: String): String;
var Existing: String;
begin
  Result := ExpandConstant('{{localappdata}}\\Programs\\TB');
  if RegQueryStringValue(HKCU, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{{0F82D178-AC2B-4696-96C1-1A210F72B509}}_is1', 'InstallLocation', Existing) then
    Result := Existing;
end;

function RuntimeVerified: Boolean;
var Hash: String;
begin
  Result := False;
{chr(10).join(checks)}
  Result := True;
end;

function DownloadProgress(const URL, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  Result := True;
end;

procedure DownloadAsset;
var LocalFile: String;
begin
  LocalFile := ExpandConstant('{{tmp}}\\') + AssetName;
  if FileExists(LocalFile) then begin
    if CompareText(GetSHA256OfFile(LocalFile), AssetHash) = 0 then Exit;
    RaiseException('Update download did not pass verification. Existing files are retained.');
  end;
  DownloadTemporaryFile(AssetURL, AssetName, AssetHash, @DownloadProgress);
end;

function HelperArguments(CheckOnly: Boolean): String;
begin
  Result := '-I -S "' + ExpandConstant('{{tmp}}\\compact-helper.pyz') + '" --bundle "' + ExpandConstant('{{tmp}}\\') + AssetName + '" --app "' + ExpandConstant('{{app}}') + '" --version {version}';
  if CheckOnly then Result := Result + ' --check';
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var Installed: AnsiString; ExitCode: Integer;
begin
  Result := '';
  try
    AssetName := '';
    FullInstall := True;
    if LoadStringFromFile(ExpandConstant('{{app}}\\VERSION'), Installed) and RuntimeVerified then begin
{chr(10).join(branches)}
      if AssetName <> '' then begin
        ExtractTemporaryFile('compact-helper.pyz');
        DownloadAsset;
        if not Exec(ExpandConstant('{{app}}\\_internal\\python3\\python.exe'), HelperArguments(True), ExpandConstant('{{tmp}}'), SW_HIDE, ewWaitUntilTerminated, ExitCode) then
          RaiseException('Could not start the verified update helper.');
        if ExitCode = 0 then FullInstall := False
        else if ExitCode <> 3 then RaiseException('Update verification failed. Existing files are retained.');
      end;
    end;
    if FullInstall then begin
      AssetURL := {literal(value['full']['url'])};
      AssetName := {literal(value['full']['name'])};
      AssetHash := {literal(value['full']['sha256'])};
      DownloadAsset;
    end;
  except
    Result := GetExceptionMessage;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var ExitCode: Integer; Started: Boolean;
begin
  if CurStep = ssPostInstall then begin
    if FullInstall then
      Started := Exec(ExpandConstant('{{tmp}}\\') + AssetName, '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /NOICONS /TASKS="" /DIR="' + ExpandConstant('{{app}}') + '"', ExpandConstant('{{tmp}}'), SW_HIDE, ewWaitUntilTerminated, ExitCode)
    else begin
      Started := Exec(ExpandConstant('{{app}}\\_internal\\python3\\python.exe'), HelperArguments(False), ExpandConstant('{{tmp}}'), SW_HIDE, ewWaitUntilTerminated, ExitCode);
      if Started and (ExitCode = 0) then
        Started := Exec(ExpandConstant('{{app}}\\ToBe.exe'), '--prepare-startup', ExpandConstant('{{app}}'), SW_HIDE, ewWaitUntilTerminated, ExitCode);
    end;
    if not Started or (ExitCode <> 0) then RaiseException('ToBe update did not complete. Personal data and recovery files are retained.');
  end;
end;
'''
    iss=stage/'compact-bootstrap.iss';iss.write_text(source,encoding='utf-8-sig')
    subprocess.run([str(inno),str(iss)],check=True)
    output=stage/f'ToBe-Setup-{version}-win64.exe'
    report={'version':version,'path':str(output.resolve()),'bytes':output.stat().st_size,'sha256':sha(output),'helperSha256':sha(helper),'runtimeFiles':len(runtime),'profiles':sorted(value['profiles']),'fullFallback':value['full']['name']}
    (stage/'bootstrap.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False),flush=True)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--spec',type=Path,required=True);parser.add_argument('--stage',type=Path,required=True);parser.add_argument('--inno',type=Path,required=True);parser.add_argument('--app-id');args=parser.parse_args()
    build(args.spec,args.stage,args.inno,args.app_id)
