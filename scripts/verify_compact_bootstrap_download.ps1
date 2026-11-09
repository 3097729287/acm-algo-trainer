param([string]$BootstrapPath=(Join-Path $PSScriptRoot '..\packaging\installer\compact-bootstrap.ps1'),[string]$OutputDirectory)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if(-not $OutputDirectory){$OutputDirectory=Join-Path $env:TEMP ('ToBe-bootstrap-download-check-'+[guid]::NewGuid().ToString('N'))}
if(Test-Path -LiteralPath $OutputDirectory){throw 'Use a new isolated verification directory'}
New-Item -ItemType Directory -Path $OutputDirectory|Out-Null
$tokens=$null;$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($BootstrapPath,[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw 'Bootstrap PowerShell syntax check failed'}
$policy=$ast.Find({param($node)$node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Get-DownloadMirrors'},$false)
if(-not $policy){throw 'Production source policy was not found'}
# Load only the production validator and inline C# class. Never evaluate the
# bootstrap's top-level code, installer selection, app discovery, or apply path.
Invoke-Expression $policy.Extent.Text
$source=[IO.File]::ReadAllText($BootstrapPath)
$initialBootstrapSha256=(Get-FileHash -LiteralPath $BootstrapPath -Algorithm SHA256).Hash.ToLowerInvariant()
$match=[regex]::Match($source,"(?s)Add-Type -ReferencedAssemblies 'System.Net.Http.dll' -TypeDefinition @'\r?\n(.*?)\r?\n'@")
if(-not $match.Success){throw 'Production downloader C# was not found'}
$valid=@'
{"name":"ToBe-Compact-Update-1.6.7-to-1.6.11-win64.zip","size":4671854,"sha256":"72f9a33edc0adcc0f3e8a13987ee82f89ae9a1de304fbf234b7c132984f4c73e","url":"https://47.82.84.74/updates/assets/1.6.11/ToBe-Compact-Update-1.6.7-to-1.6.11-win64.zip","downloadSources":{"repository":"3097729287/acm-algo-trainer","commit":"d54ac2e65143b240d2f559588de6bcb8ed17123b","name":"ToBe-Compact-Update-1.6.7-to-1.6.11-win64.zip","size":4671854,"sha256":"72f9a33edc0adcc0f3e8a13987ee82f89ae9a1de304fbf234b7c132984f4c73e","urls":["https://cdn.jsdelivr.net/gh/3097729287/acm-algo-trainer@d54ac2e65143b240d2f559588de6bcb8ed17123b/ToBe-Compact-Update-1.6.7-to-1.6.11-win64.zip"]}}
'@
$policyResults=@()
$cases=@(
    @{name='owned exact immutable ZIP accepted';reject=$false;change={param($asset)}},
    @{name='legacy fixed origin remains supported';reject=$false;change={param($asset)$asset.PSObject.Properties.Remove('downloadSources')}},
    @{name='wrong repository rejected';reject=$true;change={param($asset)$asset.downloadSources.repository='someone/else'}},
    @{name='branch instead of commit rejected';reject=$true;change={param($asset)$asset.downloadSources.commit='main'}},
    @{name='source name mismatch rejected';reject=$true;change={param($asset)$asset.downloadSources.name='other.zip'}},
    @{name='source size mismatch rejected';reject=$true;change={param($asset)$asset.downloadSources.size++}},
    @{name='source SHA mismatch rejected';reject=$true;change={param($asset)$asset.downloadSources.sha256='0'*64}},
    @{name='credential URL rejected';reject=$true;change={param($asset)$asset.downloadSources.urls[0]=$asset.downloadSources.urls[0].Replace('https://','https://user:password@')}},
    @{name='query URL rejected';reject=$true;change={param($asset)$asset.downloadSources.urls[0]+='?proxy=1'}},
    @{name='HTTP URL rejected';reject=$true;change={param($asset)$asset.downloadSources.urls[0]=$asset.downloadSources.urls[0].Replace('https://','http://')}},
    @{name='lookalike host rejected';reject=$true;change={param($asset)$asset.downloadSources.urls[0]=$asset.downloadSources.urls[0].Replace('cdn.jsdelivr.net','cdn.jsdelivr.net.invalid')}},
    @{name='fastly redirect host rejected';reject=$true;change={param($asset)$asset.downloadSources.urls[0]=$asset.downloadSources.urls[0].Replace('cdn.jsdelivr.net','fastly.jsdelivr.net')}},
    @{name='unconfirmed testingcf host rejected';reject=$true;change={param($asset)$asset.downloadSources.urls[0]=$asset.downloadSources.urls[0].Replace('cdn.jsdelivr.net','testingcf.jsdelivr.net')}},
    @{name='duplicate candidates rejected';reject=$true;change={param($asset)$asset.downloadSources.urls=@($asset.downloadSources.urls[0],$asset.downloadSources.urls[0])}},
    @{name='missing binding rejected';reject=$true;change={param($asset)$asset.downloadSources.PSObject.Properties.Remove('sha256')}},
    @{name='null binding rejected';reject=$true;change={param($asset)$asset.downloadSources=$null}},
    @{name='commit with trailing newline rejected';reject=$true;change={param($asset)$asset.downloadSources.commit+="`n"}},
    @{name='ZIP name with trailing newline rejected';reject=$true;change={param($asset)$asset.name+="`n";$asset.downloadSources.name=$asset.name}}
)
foreach($case in $cases){
    $asset=$valid|ConvertFrom-Json
    & $case.change $asset
    $rejected=$false;$errorText=$null
    try{$urls=@(Get-DownloadMirrors $asset);if(-not $case.reject -and $asset.PSObject.Properties['downloadSources'] -and $urls.Count -ne 1){throw 'Expected exactly one pinned mirror'}}catch{$rejected=$true;$errorText=$_.Exception.Message}
    $policyResults+=[pscustomobject]@{name=$case.name;passed=($rejected -eq $case.reject);rejected=$rejected;error=$errorText}
}
$harness=@'
namespace BootstrapDownloadChecks {
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Net.Security;
using System.Reflection;
using System.Security.Authentication;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
public sealed class CheckResult { public string name,error,source;public bool passed;public double seconds; }
sealed class Fixture : IDisposable {
  readonly TcpListener listener;readonly Thread thread;readonly byte[] payload;
  readonly List<TcpClient> clients=new List<TcpClient>();readonly Dictionary<string,int> hits=new Dictionary<string,int>();
  volatile bool disposed;public int RangeRequests,WholeRequests,CredentialHeaders;public readonly string Base;
  public Fixture(byte[] data) {
    payload=data;listener=new TcpListener(IPAddress.Loopback,0);listener.Start();
    Base="http://127.0.0.1:"+((IPEndPoint)listener.LocalEndpoint).Port;
    thread=new Thread(Accept);thread.IsBackground=true;thread.Start();
  }
  public string Url(string mode) { return Base+"/"+mode; }
  public int Hits(string mode) { lock(hits)return hits.ContainsKey(mode)?hits[mode]:0; }
  void Accept() {
    while(!disposed)try { var client=listener.AcceptTcpClient();lock(clients)clients.Add(client);ThreadPool.QueueUserWorkItem(delegate { Handle(client); }); }catch(SocketException) { if(disposed)return; }catch(ObjectDisposedException) { return; }
  }
  void Wait(int milliseconds) { for(int elapsed=0;elapsed<milliseconds&&!disposed;elapsed+=20)Thread.Sleep(20); }
  void Handle(TcpClient client) {
    try {
      using(client)using(var stream=client.GetStream()) {
        stream.ReadTimeout=3000;stream.WriteTimeout=3000;
        var header=new StringBuilder();
        while(header.Length<16384&&!header.ToString().EndsWith("\r\n\r\n",StringComparison.Ordinal)) { int value=stream.ReadByte();if(value<0)return;header.Append((char)value); }
        string request=header.ToString();string route=request.Split(' ')[1].TrimStart('/');
        lock(hits) { if(!hits.ContainsKey(route))hits[route]=0;hits[route]++; }
        if(Regex.IsMatch(request,@"\r\n(?:Authorization|Cookie|Proxy-Authorization):",RegexOptions.IgnoreCase))Interlocked.Increment(ref CredentialHeaders);
        var range=Regex.Match(request,@"\r\nRange:\s*bytes=(\d+)-(\d+)",RegexOptions.IgnoreCase);
        if(range.Success)Interlocked.Increment(ref RangeRequests);else Interlocked.Increment(ref WholeRequests);
        if(route=="header-stall")Wait(1800);
        if(disposed)return;
        if(route=="failed") { Send(stream,"503 Service Unavailable","",new byte[0]);return; }
        if(route=="redirect") { Send(stream,"302 Found","Location: "+Url("redirect-target")+"\r\n",new byte[0]);return; }
        long start=range.Success?Int64.Parse(range.Groups[1].Value):0;
        long end=range.Success?Int64.Parse(range.Groups[2].Value):payload.Length-1;
        bool partial=range.Success&&route!="no-range";
        if(!partial) { start=0;end=payload.Length-1; }
        int count=(int)(end-start+1);byte[] body=new byte[count];Buffer.BlockCopy(payload,(int)start,body,0,count);
        if(route=="bad-sha")body[0]^=0x5a;
        string extra="Set-Cookie: isolated-download-check=must-not-return\r\n";
        if(partial)extra+="Content-Range: bytes "+start+"-"+end+"/"+(payload.Length+(route=="bad-range"?1:0))+"\r\n";
        if(route=="short"||route=="oversized") {
          string raw="HTTP/1.1 200 OK\r\nConnection: close\r\n"+extra+"\r\n";byte[] bytes=Encoding.ASCII.GetBytes(raw);stream.Write(bytes,0,bytes.Length);
          int length=route=="short"?body.Length-1:body.Length;stream.Write(body,0,length);if(route=="oversized")stream.WriteByte(1);return;
        }
        string status=partial?"206 Partial Content":"200 OK";
        int declared=count+(route=="bad-length"||partial&&route=="bad-range-length"?1:0);
        byte[] headers=Encoding.ASCII.GetBytes("HTTP/1.1 "+status+"\r\nConnection: close\r\nContent-Length: "+declared+"\r\n"+extra+"\r\n");
        stream.Write(headers,0,headers.Length);stream.Flush();
        if(route=="body-stall") { int first=Math.Min(4096,body.Length);stream.Write(body,0,first);stream.Flush();Wait(1800);if(disposed)return;stream.Write(body,first,body.Length-first); }
        else if(route=="drip") { for(int offset=0;offset<body.Length&&!disposed;offset+=16384) { stream.Write(body,offset,Math.Min(16384,body.Length-offset));stream.Flush();Wait(30); } }
        else stream.Write(body,0,body.Length);
      }
    }catch(IOException) {}catch(SocketException) {}catch(ObjectDisposedException) {}
  }
  static void Send(Stream stream,string status,string extra,byte[] body) { byte[] header=Encoding.ASCII.GetBytes("HTTP/1.1 "+status+"\r\nConnection: close\r\nContent-Length: "+body.Length+"\r\n"+extra+"\r\n");stream.Write(header,0,header.Length);stream.Write(body,0,body.Length); }
  public void Dispose() { disposed=true;listener.Stop();lock(clients)foreach(var client in clients)client.Close();thread.Join(1000); }
}
sealed class UntrustedTlsFixture : IDisposable {
  readonly TcpListener listener;readonly Thread thread;readonly X509Certificate2 certificate;readonly RSA rsa;volatile bool disposed;public int HttpRequests;public readonly string Url;
  public UntrustedTlsFixture() {
    rsa=RSA.Create();rsa.KeySize=2048;
    var request=new CertificateRequest("CN=untrusted-download-fixture.invalid",rsa,HashAlgorithmName.SHA256,RSASignaturePadding.Pkcs1);
    certificate=request.CreateSelfSigned(DateTimeOffset.UtcNow.AddDays(-1),DateTimeOffset.UtcNow.AddDays(1));
    listener=new TcpListener(IPAddress.Loopback,0);listener.Start();Url="https://127.0.0.1:"+((IPEndPoint)listener.LocalEndpoint).Port+"/not-trusted";
    thread=new Thread(delegate() { while(!disposed)try { using(var client=listener.AcceptTcpClient())using(var stream=new SslStream(client.GetStream(),false)) { client.ReceiveTimeout=1500;client.SendTimeout=1500;stream.AuthenticateAsServer(certificate,false,SslProtocols.Tls12,false);if(stream.ReadByte()>=0)Interlocked.Increment(ref HttpRequests); } }catch(Exception) { if(disposed)return; } });
    thread.IsBackground=true;thread.Start();
  }
  public void Dispose() { disposed=true;listener.Stop();thread.Join(2000);certificate.Dispose();rsa.Dispose(); }
}
public static class Checks {
  static byte[] payload;static string digest;static readonly MethodInfo core=typeof(ToBeDownload).GetMethod("FetchCore",BindingFlags.Static|BindingFlags.NonPublic);
  static void Require(bool value,string message) { if(!value)throw new Exception(message); }
  static string Hash(string path) { using(var input=File.OpenRead(path))using(var hash=SHA256.Create())return BitConverter.ToString(hash.ComputeHash(input)).Replace("-","").ToLowerInvariant(); }
  static string Download(string primary,string[] mirrors,string directory,int mirrorMs=500,int primaryMs=2500) {
    try { return (string)core.Invoke(null,new object[] {primary,mirrors,Path.Combine(directory,"update.zip"),(long)payload.Length,digest,Path.Combine(directory,"progress.txt"),mirrorMs,primaryMs}); }
    catch(TargetInvocationException error) { throw error.InnerException; }
  }
  static void Accepted(string directory) {
    Require(Hash(Path.Combine(directory,"update.zip"))==digest,"Accepted output SHA mismatch");
    Require(File.ReadAllText(Path.Combine(directory,"progress.txt"))=="1|"+payload.Length+"|"+payload.Length,"Final progress is not exact");
    Require(Directory.GetFiles(directory,"*.download-*").Length==0,"Attempt or range files remained after completion");
  }
  static CheckResult Run(string root,string name,Func<string,string> check) {
    var result=new CheckResult {name=name};string directory=Path.Combine(root,name);Directory.CreateDirectory(directory);var clock=Stopwatch.StartNew();
    try { result.source=check(directory);result.passed=true; }catch(Exception error) { result.error=error.ToString(); }
    result.seconds=clock.Elapsed.TotalSeconds;return result;
  }
  public static CheckResult[] RunAll(string root) {
    using(var memory=new MemoryStream()) {
      using(var zip=new System.IO.Compression.ZipArchive(memory,System.IO.Compression.ZipArchiveMode.Create,true))using(var content=zip.CreateEntry("public-test-content.bin",System.IO.Compression.CompressionLevel.NoCompression).Open()) {
        byte[] data=new byte[393217];for(int i=0;i<data.Length;i++)data[i]=(byte)(i*31+17);content.Write(data,0,data.Length);
      }
      payload=memory.ToArray();
    }
    using(var hash=SHA256.Create())digest=BitConverter.ToString(hash.ComputeHash(payload)).Replace("-","").ToLowerInvariant();
    var results=new List<CheckResult>();
    results.Add(Run(root,"fast-wins-and-cancels-stalled-body",delegate(string dir) {
      using(var server=new Fixture(payload)) { var clock=Stopwatch.StartNew();string source=Download(server.Url("good"),new[] {server.Url("body-stall"),server.Url("good")},dir,1500);Require(source==server.Url("good"),"Fast complete mirror did not win");Require(clock.ElapsedMilliseconds<1200,"Loser body read was not promptly cancelled");Require(server.RangeRequests==0,"Main origin ran despite verified mirror");Accepted(dir);return source; }
    }));
    results.Add(Run(root,"wrong-sha-does-not-cancel-good-mirror",delegate(string dir) {
      using(var server=new Fixture(payload)) { string source=Download(server.Url("failed"),new[] {server.Url("bad-sha"),server.Url("drip")},dir,2500);Require(source==server.Url("drip"),"Corrupt fast candidate defeated verified candidate");Require(server.Hits("failed")==0,"Unneeded origin fallback");Accepted(dir);return source; }
    }));
    results.Add(Run(root,"bad-fast-sha-falls-back-to-origin",delegate(string dir) {
      using(var server=new Fixture(payload)) { string source=Download(server.Url("good"),new[] {server.Url("bad-sha")},dir);Require(source==server.Url("good")&&server.RangeRequests>0,"SHA error did not reach origin");Accepted(dir);return source; }
    }));
    results.Add(Run(root,"failed-fast-source-falls-back-to-origin",delegate(string dir) {
      using(var server=new Fixture(payload)) { string source=Download(server.Url("good"),new[] {server.Url("failed")},dir);Require(source==server.Url("good"),"Origin fallback failed");Accepted(dir);return source; }
    }));
    foreach(string mode in new[] {"no-range","bad-range","bad-range-length","bad-length"}) {
      string testMode=mode;
      results.Add(Run(root,"origin-"+mode+"-uses-bounded-whole-get",delegate(string dir) {
        using(var server=new Fixture(payload)) { string primary=server.Url(testMode=="bad-length"?"good":testMode);string[] mirrors=testMode=="bad-length"?new[] {server.Url("bad-length")}:new string[0];string source=Download(primary,mirrors,dir);Require(source==primary,"Wrong source accepted");if(testMode!="bad-length")Require(server.RangeRequests>0&&server.WholeRequests==1,"Invalid ranges did not get exactly one complete GET");Accepted(dir);string final=File.ReadAllText(Path.Combine(dir,"progress.txt"));Thread.Sleep(100);Require(File.ReadAllText(Path.Combine(dir,"progress.txt"))==final,"Late range wrote over completed progress");return source; }
      }));
    }
    foreach(string mode in new[] {"short","oversized","header-stall","body-stall","redirect"}) {
      string testMode=mode;
      results.Add(Run(root,"mirror-"+mode+"-rejected-with-origin-fallback",delegate(string dir) {
        using(var server=new Fixture(payload)) { var clock=Stopwatch.StartNew();string source=Download(server.Url("good"),new[] {server.Url(testMode)},dir,350);Require(source==server.Url("good"),"Bad response prevented origin fallback");Require(clock.ElapsedMilliseconds<1800,"Fast-source total time budget not enforced");Require(server.Hits("redirect-target")==0,"Followed HTTP redirect");Accepted(dir);return source; }
      }));
    }
    results.Add(Run(root,"actual-partial-progress-before-completion",delegate(string dir) {
      using(var server=new Fixture(payload)) {
        var pending=Task.Run(delegate { return Download(server.Url("failed"),new[] {server.Url("drip")},dir,3000); });bool partial=false;
        while(!pending.IsCompleted) { try { string[] frame=File.ReadAllText(Path.Combine(dir,"progress.txt")).Split('|');long done,total;if(frame.Length==3&&Int64.TryParse(frame[1],out done)&&Int64.TryParse(frame[2],out total)&&done>0&&done<total&&total==payload.Length)partial=true; }catch(IOException) {}Thread.Sleep(10); }
        string source=pending.GetAwaiter().GetResult();Require(partial,"No real partial byte progress was visible");Accepted(dir);return source;
      }
    }));
    results.Add(Run(root,"all-invalid-sources-leave-no-accepted-output",delegate(string dir) {
      using(var server=new Fixture(payload)) { bool failed=false;try { Download(server.Url("bad-sha"),new[] {server.Url("bad-sha")},dir); }catch(IOException) { failed=true; }Require(failed&&!File.Exists(Path.Combine(dir,"update.zip")),"Invalid payload became installable output");Require(server.RangeRequests<=4&&server.WholeRequests==2,"Unbounded transfer retries");Require(Directory.GetFiles(dir,"*.download-*").Length==0,"Failed transfer files retained");return null; }
    }));
    results.Add(Run(root,"existing-output-is-never-overwritten",delegate(string dir) {
      string output=Path.Combine(dir,"update.zip");File.WriteAllText(output,"existing retained artifact");using(var server=new Fixture(payload)) { bool failed=false;try { Download(server.Url("good"),new string[0],dir); }catch(IOException) { failed=true; }Require(failed&&File.ReadAllText(output)=="existing retained artifact"&&server.Hits("good")==0,"Existing artifact was overwritten or downloaded over");return null; }
    }));
    results.Add(Run(root,"system-proxy-and-credentials-not-used",delegate(string dir) {
      using(var server=new Fixture(payload))using(var proxy=new Fixture(payload)) { var previous=WebRequest.DefaultWebProxy;try { WebRequest.DefaultWebProxy=new WebProxy(proxy.Base);string source=Download(server.Url("good"),new[] {server.Url("bad-sha")},dir);Require(proxy.RangeRequests+proxy.WholeRequests==0,"Used arbitrary system proxy");Require(server.CredentialHeaders==0,"Sent credentials or cookies");Accepted(dir);return source; }finally { WebRequest.DefaultWebProxy=previous; } }
    }));
    results.Add(Run(root,"untrusted-TLS-certificate-not-accepted",delegate(string dir) {
      using(var server=new Fixture(payload))using(var tls=new UntrustedTlsFixture()) { string source=Download(server.Url("good"),new[] {tls.Url},dir,1000);Require(source==server.Url("good")&&tls.HttpRequests==0,"Accepted untrusted TLS certificate");Accepted(dir);return source; }
    }));
    results.Add(Run(root,"production-entry-rejects-plain-http",delegate(string dir) {
      using(var server=new Fixture(payload)) { bool rejected=false;try { ToBeDownload.Fetch(server.Url("good"),new string[0],Path.Combine(dir,"update.zip"),payload.Length,digest,Path.Combine(dir,"progress.txt")); }catch(ArgumentException) { rejected=true; }Require(rejected&&server.Hits("good")==0,"Production transport accepted plaintext HTTP");return null; }
    }));
    return results.ToArray();
  }
}
}
'@
Add-Type -AssemblyName System.Net.Http,System.IO.Compression
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
[Net.ServicePointManager]::DefaultConnectionLimit=8
Add-Type -ReferencedAssemblies 'System.Net.Http.dll','System.IO.Compression.dll' -TypeDefinition ($match.Groups[1].Value+"`n"+$harness)
$clock=[Diagnostics.Stopwatch]::StartNew()
$httpResults=@([BootstrapDownloadChecks.Checks]::RunAll($OutputDirectory))
$clock.Stop()
foreach($functionName in @('Hash','Plain','Fetch')){
    $definition=$ast.Find({param($node)$node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $functionName},$true)
    if(-not $definition){throw ('Missing production function: '+$functionName)}
    Invoke-Expression $definition.Extent.Text
}
# Exercise the actual PowerShell cache/source-policy call site, still without
# app discovery or any installer code. Invalid mirror metadata must not block
# an independently SHA-verified cached asset from the fixed-origin profile.
$cacheCheck=Join-Path $OutputDirectory 'rejected-source-keeps-valid-cache'
$AppDir=Join-Path $cacheCheck 'app';$WorkDir=Join-Path $cacheCheck 'work'
New-Item -ItemType Directory -Path (Join-Path $AppDir 'cache\updates'),$WorkDir|Out-Null
$asset=$valid|ConvertFrom-Json
$cached=Join-Path $AppDir ('cache\updates\'+$asset.name)
[IO.File]::WriteAllText($cached,'isolated public downloader cache fixture')
$asset.size=(Get-Item -LiteralPath $cached).Length;$asset.sha256=Hash $cached
$asset.downloadSources.size=$asset.size;$asset.downloadSources.sha256=$asset.sha256
$asset.downloadSources.urls[0]='https://untrusted.invalid/never-request'
$release=[pscustomobject]@{version='1.6.11'};$result=@{}
$cacheError=$null;$cachePassed=$false
try{$selected=Fetch $asset;$cachePassed=($selected -eq $cached -and $result.ContainsKey('fastSourceRejected'))}catch{$cacheError=$_.Exception.Message}
$policyResults+=[pscustomobject]@{name='rejected mirror binding preserves independently verified cache';passed=$cachePassed;rejected=$true;error=$cacheError}
$failed=@($policyResults|Where-Object{-not $_.passed}).Count+@($httpResults|Where-Object{-not $_.passed}).Count
$finalBootstrapSha256=(Get-FileHash -LiteralPath $BootstrapPath -Algorithm SHA256).Hash.ToLowerInvariant()
if($initialBootstrapSha256 -ne $finalBootstrapSha256){$failed++}
$report=[ordered]@{schema=1;ok=($failed -eq 0);bootstrapPath=[IO.Path]::GetFullPath($BootstrapPath);bootstrapSha256=$finalBootstrapSha256;productionSourceUnmodifiedDuringTests=($initialBootstrapSha256 -eq $finalBootstrapSha256);network='Windows C# HttpClient against real loopback TcpListener and self-signed TLS fixture; no public requests';productionTestBypassAdded=$false;applicationOrInstallerStarted=$false;sourcePolicy=$policyResults;http=$httpResults;failed=$failed;httpSeconds=$clock.Elapsed.TotalSeconds;output=$OutputDirectory}
[IO.File]::WriteAllText((Join-Path $OutputDirectory 'report.json'),($report|ConvertTo-Json -Depth 8),(New-Object Text.UTF8Encoding($false)))
[pscustomobject]@{ok=$report.ok;policyChecks=$policyResults.Count;httpChecks=$httpResults.Count;failed=$failed;seconds=$report.httpSeconds;report=(Join-Path $OutputDirectory 'report.json')}|ConvertTo-Json -Compress
if($failed){$httpResults|Where-Object{-not $_.passed}|Select-Object name,error|ConvertTo-Json -Compress;throw 'Downloader verification failed'}
