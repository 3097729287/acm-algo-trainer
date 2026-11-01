// Real MySQL backup/restore and old/new runtime compatibility, loopback only.
// Databases, dumps and evidence are retained for review. Never restores live data.
import assert from 'node:assert/strict';
import {randomUUID,createHash} from 'node:crypto';
import {execFile,spawn} from 'node:child_process';
import {promisify} from 'node:util';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,relative,isAbsolute,dirname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import mysql from 'mysql2/promise';
import {MySQLStore} from '../src/mysql-store.mjs';
import {createApiServer} from '../src/server.mjs';
import {preservedData,assertPreserved} from './audit-preserved-data.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const folder=resolve(process.argv[2]||'');
const owned=resolve(root,'.backups/next-150');
const within=(path,parent)=>{const part=relative(parent,path);return part&&!part.startsWith('..')&&!isAbsolute(part);};
assert(within(folder,owned),'Use an owned rehearsal directory');
await mkdir(folder,{recursive:true});
const port=Number(process.env.TB_MYSQL_TEST_PORT);assert.equal(port,33371,'Only the dedicated isolated server is allowed');
const options={host:'127.0.0.1',port,user:'root',password:process.env.TB_MYSQL_TEST_PASSWORD||'',charset:'utf8mb4',timezone:'Z'};
const executable=process.env.TB_MYSQL_TEST_DUMP;assert(executable,'Provide local mysqldump path');
const mysqlExecutable=process.env.TB_MYSQL_TEST_CLIENT;assert(mysqlExecutable,'Provide local mysql path');
const oldRoot=resolve(process.argv[3]||resolve(folder,'baseline-source'),'server/leaderboard');
assert(within(oldRoot,owned));
assert.equal(JSON.parse(await readFile(resolve(oldRoot,'package.json'),'utf8')).version,'1.2.9');
const {MySQLStore:OldStore}=await import(pathToFileURL(resolve(oldRoot,'src/mysql-store.mjs')));
const {createApiServer:createOldServer}=await import(pathToFileURL(resolve(oldRoot,'src/server.mjs')));
const frozen=Date.parse('2026-11-02T01:00:00Z');
const admin=await mysql.createConnection(options),live='tb_next150_'+randomUUID().replaceAll('-','');
let active=null;const pools=[];
const report={passed:false,loopbackOnly:true,productionChanged:false,originalSubmissions:0,
 baselineRuntime:'1.2.9',candidateRuntime:'1.4.0',baselineSource:'7715609b',databases:[],checks:[]};
const note=value=>report.checks.push(value);
const evidence=async(name,value)=>writeFile(resolve(folder,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
async function createDatabase(name){assert(/^tb_next150_[a-f0-9]{32}(?:_restored)?$/.test(name));await admin.query('CREATE DATABASE `'+name+'` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin');report.databases.push(name);return name;}
async function pool(name){const value=mysql.createPool({...options,database:name,connectionLimit:6});pools.push(value);return value;}
async function stop(){if(active){await new Promise((yes,no)=>active.server.close(error=>error?no(error):yes()));active=null;}}
async function start(database,old=false){
 await stop();const p=await pool(database),STORE=new (old?OldStore:MySQLStore)(p);
 const server=(old?createOldServer:createApiServer)({STORE,RATE_LIMIT_SALT:'isolated-rehearsal-only',TEST_NOW:frozen});
 await new Promise((yes,no)=>{server.once('error',no);server.listen(0,'127.0.0.1',yes);});
 active={server,STORE,pool:p,endpoint:`http://127.0.0.1:${server.address().port}`};return active;
}
async function call(path,body,auth,method=body===undefined?'GET':'POST'){
 const response=await fetch(active.endpoint+path,{method,headers:{'Content-Type':'application/json','X-TB-State-Protocol':'1',
  ...(auth?{'X-TB-User':auth.account.userId,Authorization:'Bearer '+auth.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
 return {status:response.status,value:await response.json()};
}
async function client(loginId){
 const credentials={loginId,nickname:loginId,password:'isolated-rehearsal-password'};
 assert.equal((await call('/v1/accounts/register',credentials)).status,201);
 const result=await call('/v1/accounts/login',{loginId,password:credentials.password});assert.equal(result.status,200,result.value.error);return result.value;
}
async function dump(database,name){
 const {stdout}=await promisify(execFile)(executable,['--host=127.0.0.1','--port='+port,'--user=root','--skip-password',
  '--single-transaction','--routines','--triggers','--no-tablespaces','--set-gtid-purged=OFF','--hex-blob',database],{encoding:'buffer',maxBuffer:16*1024*1024});
 assert(stdout.length>100);await writeFile(resolve(folder,name),stdout,{flag:'wx'});
 return {buffer:stdout,bytes:stdout.length,sha256:createHash('sha256').update(stdout).digest('hex')};
}
async function restore(database,data){
 const process=spawn(mysqlExecutable,['--host=127.0.0.1','--port='+port,'--user=root','--skip-password','--binary-mode=1',database],{stdio:['pipe','ignore','pipe'],windowsHide:true});
 let error='';process.stderr.on('data',chunk=>{if(error.length<4096)error+=chunk;});
 const finished=new Promise((yes,no)=>{process.once('error',no);process.once('exit',code=>code===0?yes():no(new Error('Restore failed: '+error)));});
 process.stdin.end(data);await finished;
}
async function schema(p){const [rows]=await p.query('SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT,EXTRA FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,ORDINAL_POSITION');return rows;}
try{
 const [[settings]]=await admin.query('SELECT @@datadir AS folder');
 assert(within(resolve(settings.folder),owned),'MySQL must use this worktree isolated datadir');
 await createDatabase(live);const database=await pool(live);
 const migrations=(await import('node:fs/promises')).readdir;
 const files=(await migrations(resolve(root,'server/leaderboard/mysql'))).filter(name=>/^\d{3}_.+\.sql$/.test(name)).sort();
 for(const name of files.filter(name=>Number(name.slice(0,3))<=12)){
  const source=await readFile(resolve(root,'server/leaderboard/mysql',name),'utf8');
  for(const sql of source.split(';').map(s=>s.trim()).filter(Boolean))await database.query(sql);
 }
 await start(live,true);const a=await client('legacy_150_a'),b=await client('legacy_150_b');
 const state={format:'tb-account-state-v1',publicAccounts:{},tables:{drafts:[{problem_id:'fixture::A',context:'',code:'// preserved code',saved_at:'2026-11-02T00:00:00Z'}],account_preferences:[{key:'fixture-setting',value:'original',updated_at:'2026-11-02T00:00:00Z'}]}};
 assert.equal((await call('/v1/accounts/state',{revision:0,state},a,'PUT')).status,200);
 const health=(await call('/v1/health')).value;assert.equal(health.version,'1.2.9');
 const beforeDump=await preservedData(database),oldSchema=await schema(database);
 const baseline=await dump(live,'mysql-before.sql');await evidence('before-backup-fingerprint.json',beforeDump);
 const recovered=await createDatabase(live+'_restored');await restore(recovered,baseline.buffer);const recoveredPool=await pool(recovered);
 assert.deepEqual(await preservedData(recoveredPool),beforeDump);note('Online consistent dump restored to a different database; all tables match');
 // A write after the backup must survive migration and runtime rollback.
 const later=structuredClone(state);later.tables.drafts[0].code='// later draft must survive rollback';
 assert.equal((await call('/v1/accounts/state',{revision:1,state:later},a,'PUT')).status,200);
 await stop();const before=await preservedData(database);
 await evidence('migration-before.json',before);
 for(let repeat=0;repeat<2;repeat++)for(const name of files.filter(name=>Number(name.slice(0,3))>=13)){
  const source=await readFile(resolve(root,'server/leaderboard/mysql',name),'utf8');
  for(const sql of source.split(';').map(s=>s.trim()).filter(Boolean))await database.query(sql);
 }
 const after=await preservedData(database);assertPreserved(before,after,{requireAvatar:true,requireLists:true,requireChunks:true,requireAdmin:true});
 const migratedSchema=await schema(database),oldNames=new Set(oldSchema.map(row=>row.TABLE_NAME));
 assert.deepEqual(migratedSchema.filter(row=>oldNames.has(row.TABLE_NAME)),oldSchema);
 await evidence('migration-after.json',after);note('013–015 applied twice: every original row, private snapshot, session, XP and column preserved');
 await start(live);assert.equal((await call('/v1/health')).value.gameplayProtocol,1);
 assert.deepEqual((await call('/v1/accounts/state',undefined,a)).value.state,later);
 assert.equal((await call('/v1/profile',undefined,b)).status,200);note('Old client state and profile APIs work with new runtime and original sessions');
 const operation={requestId:randomUUID(),day:'2026-11-02',taskId:'fixture:once',xp:30};
 assert.equal((await call('/v1/stickers/grant',operation,a)).status,200);
 assert.equal((await call('/v1/stickers/grant',operation,a)).status,200);
 const inventory=(await call('/v1/stickers',undefined,a)).value;assert.equal(inventory.units.length,1);
 assert.equal((await call('/v1/duels/join',{requestId:randomUUID(),handle:'fixture_a'},a)).status,200);
 assert.equal((await call('/v1/duels/join',{requestId:randomUUID(),handle:'fixture_b'},b)).status,200);
 const room=(await call('/v1/duels',undefined,a)).value;assert(room.match?.id,'Two real clients must share a room');
 assert.equal((await call('/v1/duels',undefined,b)).value.match.id,room.match.id);
 await stop();const gameBefore=await preservedData(database);
 await start(live,true);
 assert.equal((await call('/v1/health')).value.version,'1.2.9');
 assert.deepEqual((await call('/v1/accounts/state',undefined,a)).value.state,later);
 assert.equal((await call('/v1/profile',undefined,b)).status,200);
 const rollback=await preservedData(database);delete rollback.tables.request_limits;delete gameBefore.tables.request_limits;
 assert.deepEqual(rollback,gameBefore);note('Rollback changes runtime only; later drafts, new inventory and active match remain intact (request-rate counters excluded)');
 await start(live);assert.equal((await call('/v1/stickers',undefined,a)).value.units[0].id,inventory.units[0].id);
 assert.equal((await call('/v1/duels',undefined,a)).value.match.id,room.match.id);
 assert.equal((await call('/v1/stickers/grant',operation,a)).status,200);
 assert.equal((await call('/v1/stickers',undefined,a)).value.units.length,1);note('Re-upgrade recovers same inventory, match and idempotency receipt');
 await stop();const final=await preservedData(database),complete=await dump(live,'mysql-after.sql');
 // Recovery target is disposable and has not served any client since restore.
 for(const [name] of Object.entries((await preservedData(recoveredPool)).tables))assert(!name.startsWith('gameplay_'));
 const second='tb_next150_'+randomUUID().replaceAll('-','')+'_restored';await createDatabase(second);await restore(second,complete.buffer);
 assert.deepEqual(await preservedData(await pool(second)),final);note('Final dump restores all gameplay transactions and old personal data into a separate empty database');
 report.backups=[{file:'mysql-before.sql',bytes:baseline.bytes,sha256:baseline.sha256},{file:'mysql-after.sql',bytes:complete.bytes,sha256:complete.sha256}];
 report.passed=true;
}catch(error){report.error=error.message;process.exitCode=1;}
finally{
 await stop();for(const p of pools)await p.end();await admin.end();
 await writeFile(resolve(folder,'report.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
 console.log(JSON.stringify({...report,databases:report.databases.length},null,2));
}
