param([string]$WorkDir,[string]$AppDir,[switch]$Restart)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$result=@{ok=$false;privateJournalDirectlyWritten=$false;credentialsRead=$false;restartRequested=[bool]$Restart;appStarted=$false}
$clock=[Diagnostics.Stopwatch]::StartNew()
function Progress([int]$stage,[long]$done=0,[long]$total=0){[IO.File]::WriteAllText((Join-Path $WorkDir 'progress.txt'),"$stage|$done|$total",[Text.Encoding]::ASCII)}
function Hash([string]$path){return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Plain([string]$path){return -not ([IO.File]::GetAttributes($path) -band [IO.FileAttributes]::ReparsePoint)}
function Run([string]$file,[string]$arguments,[string]$name){
    $process=Start-Process -FilePath $file -ArgumentList $arguments -WorkingDirectory $WorkDir -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput (Join-Path $WorkDir ($name+'.out.log')) -RedirectStandardError (Join-Path $WorkDir ($name+'.error.log'))
    return $process.ExitCode
}
function Get-DownloadMirrors($asset){
    $property=$asset.PSObject.Properties['downloadSources']
    if(-not $property){return}
    $sources=$property.Value
    if(-not $sources -or [string]$asset.name -cnotmatch '\AToBe-Compact-Update-[0-9]+(?:\.[0-9]+)*-to-[0-9]+(?:\.[0-9]+)*-win64\.zip\z'){throw 'Untrusted update source binding'}
    foreach($required in @('repository','commit','name','size','sha256','urls')){
        if(-not $sources.PSObject.Properties[$required]){throw 'Incomplete update source binding'}
    }
    if([string]$sources.repository -cne '3097729287/acm-algo-trainer' -or [string]$sources.commit -cnotmatch '\A[a-f0-9]{40}\z' -or [string]$sources.name -cne [string]$asset.name -or [long]$sources.size -ne [long]$asset.size -or [string]$sources.sha256 -cne [string]$asset.sha256){throw 'Untrusted update source binding'}
    $urls=@($sources.urls)
    $expected='https://cdn.jsdelivr.net/gh/3097729287/acm-algo-trainer@'+$sources.commit+'/'+$asset.name
    $expectedRaw='https://raw.githubusercontent.com/3097729287/acm-algo-trainer/'+$sources.commit+'/'+$asset.name
    if($urls.Count -lt 1 -or $urls.Count -gt 2 -or $urls[0] -isnot [string] -or $urls[0] -cne $expected -or ($urls.Count -eq 2 -and ($urls[1] -isnot [string] -or $urls[1] -cne $expectedRaw))){throw 'Untrusted update source URL'}
    return [string[]]$urls
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
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;
public static class ToBeDownload {
  sealed class Candidate {
    public string Url,File; public long Received;
    readonly List<string> created=new List<string>();
    public Candidate(string url,string destination) { Url=url;File=destination+".download-"+Guid.NewGuid().ToString("N"); }
    public FileStream Create(string path) {
      var file=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.None,65536,true);
      lock(created)created.Add(path);
      return file;
    }
    public void Cleanup() { lock(created)foreach(string path in created)try { System.IO.File.Delete(path); }catch(IOException) {}catch(UnauthorizedAccessException) {} }
  }
  sealed class ProgressState {
    readonly string path; readonly long total; readonly object gate=new object();
    readonly List<Candidate> active=new List<Candidate>(); readonly Stopwatch clock=Stopwatch.StartNew();
    long lastWrite=-100;
    public ProgressState(string file,long size) { path=file;total=size;Write(0); }
    void Write(long done) {
      // A progress reader can briefly deny a writer on Windows. Such a UI
      // sharing collision must not turn a valid payload into a failed source.
      for(int retry=0;retry<4;retry++) {
        try { File.WriteAllText(path,"1|"+done+"|"+total,System.Text.Encoding.ASCII);break; }
        catch(IOException) { if(retry<3)Thread.Sleep(2); }
      }
      lastWrite=clock.ElapsedMilliseconds;
    }
    public void Add(Candidate candidate) { lock(gate)active.Add(candidate); }
    public void Report(Candidate candidate,int amount) {
      long received=Interlocked.Add(ref candidate.Received,amount);
      lock(gate) { if(received!=amount&&clock.ElapsedMilliseconds-lastWrite<80)return;Write(Best()); }
    }
    long Best() { long best=0;foreach(var candidate in active)best=Math.Max(best,Interlocked.Read(ref candidate.Received));return Math.Min(total,best); }
    public void Failed(Candidate candidate) { lock(gate) { active.Remove(candidate);Write(Best()); } }
    public void Complete() { lock(gate)Write(total); }
  }
  static HttpClient Client() {
    var handler=new HttpClientHandler {AllowAutoRedirect=false,UseProxy=false,UseCookies=false,UseDefaultCredentials=false,PreAuthenticate=false,Credentials=null,AutomaticDecompression=DecompressionMethods.None};
    return new HttpClient(handler) {Timeout=Timeout.InfiniteTimeSpan};
  }
  static async Task Part(HttpClient client,Candidate candidate,string file,long start,long end,long total,bool range,ProgressState progress,CancellationToken token) {
    using(var request=new HttpRequestMessage(HttpMethod.Get,candidate.Url)) {
      request.Headers.TryAddWithoutValidation("Accept-Encoding","identity");
      if(range)request.Headers.Range=new RangeHeaderValue(start,end);
      using(var response=await client.SendAsync(request,HttpCompletionOption.ResponseHeadersRead,token).ConfigureAwait(false)) {
        if(range) {
          var r=response.Content.Headers.ContentRange;
          if(response.StatusCode!=HttpStatusCode.PartialContent||r==null||r.From!=start||r.To!=end||r.Length!=total)throw new IOException("Invalid update byte range");
        }else if(response.StatusCode!=HttpStatusCode.OK)throw new IOException("Update HTTP "+(int)response.StatusCode);
        if(response.Content.Headers.ContentLength.HasValue&&response.Content.Headers.ContentLength.Value!=end-start+1)throw new IOException("Invalid update content length");
        foreach(string encoding in response.Content.Headers.ContentEncoding)if(!String.Equals(encoding,"identity",StringComparison.OrdinalIgnoreCase))throw new IOException("Encoded update response");
        long count=0;
        // Disposing the response bounds body reads on Windows .NET Framework,
        // where cancelling a Stream.ReadAsync token alone may leave a read pending.
        using(token.Register(delegate { response.Dispose(); }))
        using(var input=await response.Content.ReadAsStreamAsync().ConfigureAwait(false))
        using(var output=candidate.Create(file)) {
          byte[] buffer=new byte[65536];int n;
          while((n=await input.ReadAsync(buffer,0,buffer.Length,token).ConfigureAwait(false))!=0){
            count+=n;if(count>end-start+1)throw new IOException("Oversized update response");
            await output.WriteAsync(buffer,0,n,token).ConfigureAwait(false);progress.Report(candidate,n);
          }
          if(count!=end-start+1)throw new IOException("Truncated update response");
          output.Flush(true);
        }
      }
    }
  }
  static async Task Observe(IEnumerable<Task<Candidate>> tasks) { foreach(var task in tasks)try { await task.ConfigureAwait(false); }catch(Exception) {} }
  static async Task Transfer(Candidate candidate,long size,string sha256,ProgressState progress,bool ranges,CancellationToken token) {
    progress.Add(candidate);
    try {
      using(var client=Client()) {
        if(ranges) {
          using(var stop=CancellationTokenSource.CreateLinkedTokenSource(token)) {
            var tasks=new List<Task>();long width=(size+3)/4;
            for(int i=0;i<4;i++)tasks.Add(Part(client,candidate,candidate.File+".part"+i,i*width,Math.Min(size-1,(i+1)*width-1),size,true,progress,stop.Token));
            Exception rangeError=null;
            try {
              var pending=new List<Task>(tasks);
              while(pending.Count>0) { var completed=await Task.WhenAny(pending).ConfigureAwait(false);pending.Remove(completed);await completed.ConfigureAwait(false); }
            }catch(Exception error) { rangeError=error;stop.Cancel(); }
            if(rangeError!=null) {
              // Join every range before cleanup or the ordinary GET fallback;
              // failed/late parts cannot race against a replacement attempt.
              try { await Task.WhenAll(tasks).ConfigureAwait(false); }catch(Exception) {}
              throw new IOException("Update range attempt did not complete",rangeError);
            }
            using(var output=candidate.Create(candidate.File)) {
              for(int i=0;i<4;i++)using(var input=File.OpenRead(candidate.File+".part"+i))input.CopyTo(output);
              output.Flush(true);
            }
          }
        }else await Part(client,candidate,candidate.File,0,size-1,size,false,progress,token).ConfigureAwait(false);
      }
      token.ThrowIfCancellationRequested();
      using(var input=File.OpenRead(candidate.File))
      using(var hash=SHA256.Create()) {
        string actual=BitConverter.ToString(hash.ComputeHash(input)).Replace("-","").ToLowerInvariant();
        if(input.Length!=size||actual!=sha256)throw new IOException("Update SHA-256 verification failed");
      }
      token.ThrowIfCancellationRequested();
    }catch { progress.Failed(candidate);candidate.Cleanup();throw; }
  }
  static async Task<Candidate> Attempt(Candidate candidate,long size,string sha256,ProgressState progress,bool ranges,CancellationToken token) {
    await Transfer(candidate,size,sha256,progress,ranges,token).ConfigureAwait(false);return candidate;
  }
  static async Task<Candidate> Race(List<Candidate> mirrors,long size,string sha256,ProgressState progress,int timeout) {
    using(var stop=new CancellationTokenSource(timeout)) {
      var tasks=new List<Task<Candidate>>();
      foreach(var mirror in mirrors)tasks.Add(Attempt(mirror,size,sha256,progress,false,stop.Token));
      var pending=new List<Task<Candidate>>(tasks);
      Candidate winner=null;Exception failure=null;
      try {
        while(pending.Count>0) {
          var completed=await Task.WhenAny(pending).ConfigureAwait(false);pending.Remove(completed);
          try { winner=await completed.ConfigureAwait(false); }
          catch(Exception) { /* A failed or corrupt fast source cannot cancel a reliable one. */ }
          if(winner!=null)break;
        }
      }catch(Exception error) { failure=error; }
      stop.Cancel();await Observe(tasks).ConfigureAwait(false);
      if(failure!=null)throw new IOException("Update source race failed",failure);
      return winner;
    }
  }
  static string FetchCore(string primaryUrl,string[] mirrorUrls,string destination,long size,string sha256,string progressPath,int mirrorTimeout,int primaryTimeout) {
    if(size<=0||String.IsNullOrEmpty(sha256)||!System.Text.RegularExpressions.Regex.IsMatch(sha256,"\\A[a-f0-9]{64}\\z"))throw new ArgumentException("Invalid update identity");
    if(File.Exists(destination))throw new IOException("Existing update destination retained");
    var progress=new ProgressState(progressPath,size);var attempts=new List<Candidate>();
    try {
      var mirrors=new List<Candidate>();
      foreach(string url in mirrorUrls) { var mirror=new Candidate(url,destination);mirrors.Add(mirror);attempts.Add(mirror); }
      Candidate winner=mirrors.Count==0?null:Race(mirrors,size,sha256,progress,mirrorTimeout).GetAwaiter().GetResult();
      if(winner==null) {
        // At most one range attempt and one complete GET. Downloads may retry;
        // installation is outside this method and runs only after acceptance.
        Exception last=null;
        int tries=size>=262144?2:1;
        for(int i=0;i<tries;i++) {
          var candidate=new Candidate(primaryUrl,destination);attempts.Add(candidate);
          using(var stop=new CancellationTokenSource(primaryTimeout)) {
            try { winner=Attempt(candidate,size,sha256,progress,tries==2&&i==0,stop.Token).GetAwaiter().GetResult();break; }
            catch(Exception error) { last=error; }
          }
        }
        if(winner==null)throw new IOException("No update source passed complete size and SHA-256 verification",last);
      }
      File.Move(winner.File,destination);progress.Complete();return winner.Url;
    }finally { foreach(var candidate in attempts)candidate.Cleanup(); }
  }
  public static string Fetch(string primaryUrl,string[] verifiedMirrorUrls,string destination,long size,string sha256,string progressPath) {
    foreach(string url in new List<string>(verifiedMirrorUrls) {primaryUrl}) {
      Uri uri;
      if(!Uri.TryCreate(url,UriKind.Absolute,out uri)||uri.Scheme!="https"||uri.Port!=443||uri.UserInfo.Length!=0||uri.Query.Length!=0||uri.Fragment.Length!=0)throw new ArgumentException("Untrusted update transport URL");
    }
    return FetchCore(primaryUrl,verifiedMirrorUrls,destination,size,sha256,progressPath,10000,90000);
  }
}
'@
    function Fetch($asset){
        $name=[string]$asset.name
        if($name -cnotmatch '\A(?:ToBe|TB)-(?:Compact-Update-[0-9]+(?:\.[0-9]+)*-to-[0-9]+(?:\.[0-9]+)*-win64\.zip|(?:Full-)?Setup-[0-9]+(?:\.[0-9]+)*-win64\.exe)\z' -or $asset.url -cne ('https://47.82.84.74/updates/assets/'+$release.version+'/'+$name) -or $asset.sha256 -cnotmatch '\A[a-f0-9]{64}\z' -or [long]$asset.size -le 0){throw 'Untrusted update asset'}
        [string[]]$mirrors=@()
        try{$mirrors=@(Get-DownloadMirrors $asset)}catch{$result.fastSourceRejected=$_.Exception.Message}
        $cached=Join-Path $AppDir ('cache\updates\'+$name)
        if((Test-Path -LiteralPath $cached) -and (Plain $cached) -and (Get-Item -LiteralPath $cached).Length -eq $asset.size -and (Hash $cached) -eq $asset.sha256){return $cached}
        $drive=[IO.DriveInfo]::new([IO.Path]::GetPathRoot($WorkDir))
        if($drive.AvailableFreeSpace -lt (2*[long]$asset.size+268435456)){throw 'Insufficient update space; existing files retained'}
        $file=Join-Path $WorkDir $name
        $result.downloadSource=[ToBeDownload]::Fetch([string]$asset.url,$mirrors,$file,[long]$asset.size,[string]$asset.sha256,(Join-Path $WorkDir 'progress.txt'))
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
    if($Restart){
        Start-Process -FilePath (Join-Path $AppDir 'ToBe.exe') -WorkingDirectory $AppDir -WindowStyle Normal -ErrorAction Stop
        $result.appStarted=$true
    }
    $result.ok=$true;$result.fullFallback=$full;$result.version=$release.version
}catch{$result.error=$_.Exception.Message}
$result.seconds=$clock.Elapsed.TotalSeconds
$json=$result | ConvertTo-Json -Depth 5
[IO.File]::WriteAllText((Join-Path $WorkDir 'result.json'),$json,[Text.UTF8Encoding]::new($false))
if($env:TB_OFFLINE -eq '1' -and $env:TB_UPDATE_TEST_REPORT){[IO.File]::WriteAllText($env:TB_UPDATE_TEST_REPORT,$json,[Text.UTF8Encoding]::new($false))}
if($result.ok){exit 0}else{exit 1}
