// Reopen only the fresh profile from a completed isolated zero-window fixture.
// No CDP, --load-extension, normal profile, job, official URL, or account DB.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {readFile,writeFile} from 'node:fs/promises';
import {resolve,join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const out=resolve(process.argv[2]||'');
assert(/^D:\\Temp\\T13HFix-20261110\\native-connected-[a-f0-9-]{36}$/i.test(out),'Only a prior owned isolated fixture is permitted');
const prior=JSON.parse(await readFile(join(out,'result.json'),'utf8'));
assert.equal(prior.ok,true);assert.equal(prior.ownedBrowserExitCode,0);assert.equal(prior.ownedFixtureExitCode,0);
const config=await readFile(join(out,'extension','connection_config.js'),'utf8');
const match=config.match(/^const TB_CONNECTION_BASE="http:\/\/127\.0\.0\.1:(\d+)";\s*$/);assert(match);
const port=Number(match[1]),base='http://127.0.0.1:'+port;
const python=process.env.TB_PYTHON||'C:/Users/lenovo/AppData/Local/Programs/Python/Python313/python.exe';
const edge=process.env.TB_TEST_EDGE||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const fixture=spawn(python,['-B','-u','desktop/tests/connected_zero_window_server.py','--port',String(port),'--handshake-only'],
  {cwd:root,env:{...process.env,TB_OFFLINE:'1',PYTHONDONTWRITEBYTECODE:'1',PYTHONIOENCODING:'utf-8'},windowsHide:true,stdio:['pipe','pipe','pipe']});
let child,fixtureError='',edgeError='';fixture.stderr.on('data',b=>fixtureError=(fixtureError+b).slice(-8192));
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const result={ok:false,kind:'isolated-standard-no-startup-window-wake',out,noCdp:true,noLoadExtensionFlag:true,
  syntheticJobsCreated:0,realOriginalSiteRequests:0,realProviderRequests:0,ordinaryProfilesUsed:false,personalDatabasesOpened:false};
const started=Date.now();
try{
  await new Promise((ok,no)=>{let text='';fixture.stdout.on('data',b=>{text+=b;if(text.includes('\n')){assert.equal(JSON.parse(text.split('\n')[0]).port,port);ok()}});fixture.once('exit',code=>no(Error('FIXTURE_START_FAILED_'+code)))});
  result.arguments=['--no-startup-window','--profile-directory=Default','--user-data-dir='+join(out,'profile')];
  child=spawn(edge,result.arguments,{windowsHide:true,stdio:['ignore','ignore','pipe']});
  child.stderr.on('data',b=>edgeError=(edgeError+b).slice(-8192));result.ownedLauncherPid=child.pid;
  const deadline=Date.now()+15000;
  while(Date.now()<deadline){
    const response=await fetch(base+'/fixture/proof');assert.equal(response.status,200);result.bridgeProof=await response.json();
    if(result.bridgeProof.register.length&&result.bridgeProof.queueWithoutWindow>0)break;
    if(child.exitCode!==null){result.launcherExitedBeforeHandshake=true;break}
    await pause(100);
  }
  assert.equal(result.bridgeProof.savedReceipts,0);assert.equal(result.bridgeProof.pendingReceipts,0);
  if(!result.bridgeProof.register.length||!result.bridgeProof.queueWithoutWindow){
    result.status='blocked';result.limitation='Command-line unpacked-extension installation may not persist; this does not establish behavior of a normally installed extension.';
    throw Error('NO_BACKGROUND_HANDSHAKE_WITHIN_15_SECONDS');
  }
  assert(result.bridgeProof.register.every(v=>v.protocol===4&&v.backgroundWindows));
  result.ok=true;result.status='passed';
}catch(error){result.status??='failed';result.failureCode=error.message}
finally{
  result.observationSeconds=(Date.now()-started)/1000;
  if(child&&child.exitCode===null){child.kill();result.ownIsolatedBrowserTerminatedAfterObservation=true;await Promise.race([new Promise(r=>child.once('exit',r)),pause(5000)])}
  fixture.stdin.end('stop\n');if(fixture.exitCode===null)await Promise.race([new Promise(r=>fixture.once('exit',r)),pause(5000)]);
  if(fixture.exitCode===null){fixture.kill();result.ownFixtureTerminated=true}
  result.ownedBrowserExitCode=child?.exitCode;result.ownedFixtureExitCode=fixture.exitCode;
  await writeFile(join(out,'wake-no-flags.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  await writeFile(join(out,'wake-no-flags-edge.log'),edgeError,{flag:'wx'});
  await writeFile(join(out,'wake-no-flags-fixture.log'),fixtureError,{flag:'wx'});
  console.log(JSON.stringify(result));
}
if(!result.ok)process.exitCode=1;
