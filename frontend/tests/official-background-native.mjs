// Real Windows/Edge window creation in a new empty test profile. No original
// site, login, cookies, submit form or ordinary browser profile is opened.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {mkdir,writeFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import net from 'node:net';
import {createInterface} from 'node:readline';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const out=resolve(root,'.backups/review-latest-ac-20261109/background-native',String(Date.now()));
await mkdir(out,{recursive:true});
const monitor=spawn(process.env.TB_PYTHON||'python',['-B','-u','-c',String.raw`
import ctypes,ctypes.wintypes as w,json,sys,threading,time
u=ctypes.WinDLL('user32');u.GetForegroundWindow.restype=w.HWND
u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
stop=threading.Event();threading.Thread(target=lambda:(sys.stdin.readline(),stop.set()),daemon=True).start()
print('ready',flush=True);pids=[]
while not stop.is_set():
 p=w.DWORD();u.GetWindowThreadProcessId(u.GetForegroundWindow(),ctypes.byref(p));pids.append(p.value);time.sleep(.01)
print(json.dumps(pids),flush=True)
`],{windowsHide:true,stdio:['pipe','pipe','pipe'],env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'}});
const lines=createInterface({input:monitor.stdout});const [ready]=await once(lines,'line');assert.equal(ready,'ready');
const reservation=net.createServer();reservation.listen(0,'127.0.0.1');await once(reservation,'listening');
const port=reservation.address().port;await new Promise(r=>reservation.close(r));
const executable=resolve(process.env['ProgramFiles(x86)']||'C:/Program Files (x86)','Microsoft/Edge/Application/msedge.exe');
const edge=spawn(executable,['--user-data-dir='+resolve(out,'profile'),'--remote-debugging-port='+port,'--remote-debugging-address=127.0.0.1','--no-first-run','--no-default-browser-check','--disable-background-mode','--mute-audio','--no-startup-window'],{windowsHide:true,stdio:'ignore'});
let cdp,closed=false;
class Connection{
 constructor(url){this.ws=new WebSocket(url);this.seq=0;this.pending=new Map();this.ws.addEventListener('message',event=>{const v=JSON.parse(event.data),p=this.pending.get(v.id);if(p){this.pending.delete(v.id);v.error?p.reject(Error(v.error.message)):p.resolve(v.result)}})}
 async ready(){if(this.ws.readyState!==1)await once(this.ws,'open')}
 async call(method,params={}){const id=++this.seq;return new Promise((resolve,reject)=>{this.pending.set(id,{resolve,reject});this.ws.send(JSON.stringify({id,method,params}))})}
 close(){this.ws.close()}
}
try{
 let version;for(let i=0;i<120;i++){try{version=await(await fetch('http://127.0.0.1:'+port+'/json/version')).json();break}catch{await new Promise(r=>setTimeout(r,100))}}
 assert.ok(version?.webSocketDebuggerUrl,'Owned Edge became ready');
 cdp=new Connection(version.webSocketDebuggerUrl);await cdp.ready();
 const browserPid=(await cdp.call('SystemInfo.getProcessInfo')).processInfo.find(p=>p.type==='browser').id;
 const protocol=await(await fetch('http://127.0.0.1:'+port+'/json/protocol')).json();
 assert.ok(protocol.domains.find(d=>d.domain==='Target').commands.find(c=>c.name==='createTarget').parameters.some(p=>p.name==='windowState'));
 const targets=[];
 for(let i=0;i<3;i++){
  const {targetId}=await cdp.call('Target.createTarget',{url:'about:blank',newWindow:true,background:true,windowState:'minimized'});
  const window=await cdp.call('Browser.getWindowForTarget',{targetId});assert.equal(window.bounds.windowState,'minimized');targets.push(targetId);
  await new Promise(r=>setTimeout(r,120));
 }
 await cdp.call('Browser.close');closed=true;
 const ended=once(monitor,'exit');const output=once(lines,'line');monitor.stdin.end('stop\n');const [samples]=await output;await ended;
 const foreground=JSON.parse(samples);assert.ok(foreground.length>=20);assert.ok(!foreground.includes(browserPid),'No test submission window was foregrounded');
 const result={ok:true,browser:version.Browser,windowState:'minimized',targets:targets.length,foregroundSamples:foreground.length,foregroundSteals:0,originalSiteRequests:0,out};
 await writeFile(resolve(out,'result.log'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{if(cdp&&!closed)try{await cdp.call('Browser.close')}catch{}cdp?.close();if(monitor.exitCode===null)monitor.stdin.end('stop\n');}
