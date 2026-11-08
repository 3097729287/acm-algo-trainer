param([string]$WorkDir,[string]$AppDir)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$result=@{ok=$false;privateJournalDirectlyWritten=$false;credentialsRead=$false}
$clock=[Diagnostics.Stopwatch]::StartNew()
function Progress([int]$stage,[long]$done=0,[long]$total=0){[IO.File]::WriteAllText((Join-Path $WorkDir 'progress.txt'),"$stage|$done|$total",[Text.Encoding]::ASCII)}
function Hash([string]$path){return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Plain([string]$path){return -not ([IO.File]::GetAttributes($path) -band [IO.FileAttributes]::ReparsePoint)}
function Run([string]$file,[string]$arguments,[string]$name){
    $process=Start-Process -FilePath $file -ArgumentList $arguments -WorkingDirectory $WorkDir -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput (Join-Path $WorkDir ($name+'.out.log')) -RedirectStandardError (Join-Path $WorkDir ($name+'.error.log'))
    return $process.ExitCode
}
try{
    Progress 0
    $release=Get-Content -LiteralPath (Join-Path $WorkDir 'release.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if([string]::IsNullOrWhiteSpace($AppDir)){
        $AppDir=Join-Path $env:LOCALAPPDATA 'Programs\TB'
        $registered=Get-ItemProperty -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{0F82D178-AC2B-4696-96C1-1A210F72B509}_is1' -ErrorAction SilentlyContinue
        if($registered){
            $location=$registered.PSObject.Properties['InstallLocation']
            if($location -and $location.Value){$AppDir=$location.Value}
        }
    }
    $AppDir=[IO.Path]::GetFullPath($AppDir).TrimEnd('\')
    if($AppDir.Contains('"') -or $AppDir.Length -lt 4){throw 'Invalid program directory'}
    $profile=$null
    if(Test-Path -LiteralPath (Join-Path $AppDir 'VERSION')){
        $installed=[IO.File]::ReadAllText((Join-Path $AppDir 'VERSION')).Trim()
        $property=$release.profiles.PSObject.Properties[$installed]
        if($property){$profile=$property.Value}
    }
    if($profile){
        foreach($entry in $release.runtime.PSObject.Properties){
            $path=Join-Path $AppDir $entry.Name
            if(-not (Test-Path -LiteralPath $path) -or -not (Plain $path) -or @($entry.Value) -notcontains (Hash $path)){$profile=$null;break}
        }
    }
    if($profile){
        # Stop before any replacement when a manually started update meets a
        # still-running Windows image; automatic updates already waited for it.
        $image=[IO.File]::Open((Join-Path $AppDir 'ToBe.exe'),[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
        $image.Dispose()
    }
    Add-Type -AssemblyName System.Net.Http
    [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
    [Net.ServicePointManager]::DefaultConnectionLimit=8
    Add-Type -ReferencedAssemblies 'System.Net.Http.dll' -TypeDefinition @'
using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;
public static class ToBeDownload {
  static long received; static readonly object gate=new object();
  static void Progress(string path,long amount,long total) {
    Interlocked.Add(ref received,amount);
    lock(gate)File.WriteAllText(path,"1|"+Interlocked.Read(ref received)+"|"+total,System.Text.Encoding.ASCII);
  }
  static async Task Part(HttpClient client,string url,string file,long start,long end,long total,bool range,string progress,CancellationToken token) {
    using(var request=new HttpRequestMessage(HttpMethod.Get,url)) {
      request.Headers.TryAddWithoutValidation("Accept-Encoding","identity");
      if(range)request.Headers.Range=new RangeHeaderValue(start,end);
      using(var response=await client.SendAsync(request,HttpCompletionOption.ResponseHeadersRead,token).ConfigureAwait(false)) {
        if(range) {
          var r=response.Content.Headers.ContentRange;
          if(response.StatusCode!=HttpStatusCode.PartialContent||r==null||r.From!=start||r.To!=end||r.Length!=total)throw new IOException("Invalid update byte range");
        }else if(response.StatusCode!=HttpStatusCode.OK)throw new IOException("Update HTTP "+(int)response.StatusCode);
        long count=0;
        using(var input=await response.Content.ReadAsStreamAsync().ConfigureAwait(false))
        using(var output=new FileStream(file,FileMode.Create,FileAccess.Write,FileShare.None,65536,true)) {
          byte[] buffer=new byte[65536];int n;
          while((n=await input.ReadAsync(buffer,0,buffer.Length,token).ConfigureAwait(false))!=0){
            count+=n;if(count>end-start+1)throw new IOException("Oversized update response");
            await output.WriteAsync(buffer,0,n,token).ConfigureAwait(false);Progress(progress,n,total);
          }
          if(count!=end-start+1)throw new IOException("Truncated update response");
          output.Flush(true);
        }
      }
    }
  }
  public static void Fetch(string url,string destination,long size,string progress) {
    using(var handler=new HttpClientHandler {AllowAutoRedirect=false,UseProxy=false,AutomaticDecompression=DecompressionMethods.None})
    using(var client=new HttpClient(handler))
    using(var stop=new CancellationTokenSource(TimeSpan.FromMinutes(8))) {
      client.Timeout=Timeout.InfiniteTimeSpan;int parts=size>=262144?4:1;received=0;
      try {
        var tasks=new Task[parts];long width=(size+parts-1)/parts;
        for(int i=0;i<parts;i++)tasks[i]=Part(client,url,destination+".part"+i,i*width,Math.Min(size-1,(i+1)*width-1),size,parts>1,progress,stop.Token);
        Task.WhenAll(tasks).GetAwaiter().GetResult();
      }catch {
        // A server without byte ranges gets one ordinary bounded GET. No
        // installation can use partial or unverified output from either path.
        received=0;parts=1;
        Part(client,url,destination+".part0",0,size-1,size,false,progress,stop.Token).GetAwaiter().GetResult();
      }
      using(var output=new FileStream(destination,FileMode.CreateNew,FileAccess.Write,FileShare.None)) {
        for(int i=0;i<parts;i++)using(var input=File.OpenRead(destination+".part"+i))input.CopyTo(output);
        output.Flush(true);
      }
    }
  }
}
'@
    function Fetch($asset){
        $name=[string]$asset.name
        if($name -notmatch '^(?:ToBe|TB)-(?:Compact-Update-[\d.]+-to-[\d.]+-win64\.zip|(?:Full-)?Setup-[\d.]+-win64\.exe)$' -or $asset.url -ne ('https://47.82.84.74/updates/assets/'+$release.version+'/'+$name) -or $asset.sha256 -notmatch '^[a-f0-9]{64}$'){throw 'Untrusted update asset'}
        $cached=Join-Path $AppDir ('cache\updates\'+$name)
        if((Test-Path -LiteralPath $cached) -and (Plain $cached) -and (Get-Item -LiteralPath $cached).Length -eq $asset.size -and (Hash $cached) -eq $asset.sha256){return $cached}
        $drive=[IO.DriveInfo]::new([IO.Path]::GetPathRoot($WorkDir))
        if($drive.AvailableFreeSpace -lt (2*[long]$asset.size+268435456)){throw 'Insufficient update space; existing files retained'}
        $file=Join-Path $WorkDir $name
        [ToBeDownload]::Fetch([string]$asset.url,$file,[long]$asset.size,(Join-Path $WorkDir 'progress.txt'))
        if((Get-Item -LiteralPath $file).Length -ne $asset.size -or (Hash $file) -ne $asset.sha256){throw 'Update SHA-256 verification failed'}
        return $file
    }
    $full=$true
    $result.bridgeSetupSeconds=$clock.Elapsed.TotalSeconds
    if($profile){
        $download=[Diagnostics.Stopwatch]::StartNew();$bundle=Fetch $profile;$download.Stop()
        $result.downloadSeconds=$download.Elapsed.TotalSeconds;$result.downloadBytes=$profile.size
        $python=Join-Path $AppDir '_internal\python3\python.exe';$helper=Join-Path $WorkDir 'compact-helper.pyz'
        $parameters='-I -S "'+$helper+'" --bundle "'+$bundle+'" --app "'+$AppDir+'" --version '+$release.version
        Progress 2
        $applyClock=[Diagnostics.Stopwatch]::StartNew()
        $applied=Run $python $parameters 'apply'
        $result.applySeconds=$applyClock.Elapsed.TotalSeconds
        if($applied -eq 0){
            $full=$false
        }elseif($applied -ne 3){throw 'Update payload validation failed; recovery files retained'}
    }
    if($full){
        $installer=Fetch $release.full
        $parameters='/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /NOICONS /TASKS="" /DIR="'+$AppDir+'"'
        if((Run $installer $parameters 'complete-install') -ne 0){throw 'Complete installation did not finish'}
    }else{
        Progress 3
        $prepareClock=[Diagnostics.Stopwatch]::StartNew()
        if((Run (Join-Path $AppDir 'ToBe.exe') '--prepare-startup' 'prepare-startup') -ne 0){throw 'Startup preparation did not finish; personal data retained'}
        $result.prepareStartupSeconds=$prepareClock.Elapsed.TotalSeconds
    }
    if([IO.File]::ReadAllText((Join-Path $AppDir 'VERSION')).Trim() -ne $release.version){throw 'Installed version mismatch'}
    $result.ok=$true;$result.fullFallback=$full;$result.version=$release.version
}catch{$result.error=$_.Exception.Message}
$result.seconds=$clock.Elapsed.TotalSeconds
$json=$result | ConvertTo-Json -Depth 5
[IO.File]::WriteAllText((Join-Path $WorkDir 'result.json'),$json,[Text.UTF8Encoding]::new($false))
if($env:TB_OFFLINE -eq '1' -and $env:TB_UPDATE_TEST_REPORT){[IO.File]::WriteAllText($env:TB_UPDATE_TEST_REPORT,$json,[Text.UTF8Encoding]::new($false))}
if($result.ok){exit 0}else{exit 1}
