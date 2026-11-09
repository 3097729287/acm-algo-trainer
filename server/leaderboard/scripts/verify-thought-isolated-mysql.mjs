// REVIEW FIRST. Default invocation is a static plan: no credentials or SQL.
// Execute only inside a one-shot existing Node image, with no network and a
// read-only MySQL socket/root-secret mount. Never pass an existing schema name.
import assert from 'node:assert/strict';
import {createHash,randomBytes,randomUUID} from 'node:crypto';
import {createRequire} from 'node:module';
import {readFile,statfs} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const args=process.argv.slice(2),execute=args.includes('--execute-isolated');
const option=(name,fallback)=>{const at=args.indexOf(name);return at<0?fallback:args[at+1];};
const sourceRoot=resolve(option('--source-root',fileURLToPath(new URL('../',import.meta.url))));
const sourceNames=['src/thought-duels.mjs','src/pk-judge.mjs','src/accounts.mjs','src/duel-points.mjs','src/thought-problems.json',
 'mysql/001_schema.sql','mysql/004_accounts.sql','mysql/017_thought_duels.sql','mysql/021_thought_judge_budget.sql'];
const sha=value=>createHash('sha256').update(value).digest('hex');
const plan={schema:1,mode:execute?'execute-isolated':'static-plan',candidateImplementationCommit:'1a5c4a23e40ab4e0a27dab958162aa1e154c57f4',
 onlyFreshSchemaPrefix:'tb_verify_thought_',existingSchemaOptionAccepted:false,existingBusinessSchemaWrites:false,
 rootCredentialMethod:'existing private secret file consumed in memory by mysql2; never printed, copied, or passed as argv/env',
 schemaLifecycle:'create random never-existing schema, seed synthetic rows, test, drop only the schema created by this invocation',
 migrations:['001_schema.sql','004_accounts.sql','017_thought_duels.sql','021_thought_judge_budget.sql'],
 checks:['old synthetic tables preserved by row/schema digests','017 and 021 repeat idempotently with populated counters',
  'two workers/eight concurrent reservations share exactly three allowed calls','budget survives pool/worker restart',
  'Beijing midnight starts a new day','quota exhaustion retains locked answers without a fabricated verdict or rating change'],
 realProviderCalls:0,requiresExplicitApprovalToExecute:true,sourceFiles:sourceNames};
if(!execute){process.stdout.write(JSON.stringify(plan,null,2)+'\n');process.exit(0);}

const schema='tb_verify_thought_'+randomBytes(12).toString('hex'),validSchema=value=>/^tb_verify_thought_[0-9a-f]{24}$/.test(value);
assert(validSchema(schema));
const receipt={...plan,status:'failed',isolatedSchema:schema,sourceSha256:{},checksPassed:[],syntheticAccounts:true,
 productionAccountRowsRead:false,providerCalls:0,createdByThisInvocation:false,droppedByThisInvocation:false};
let admin,pool,worker,other,created=false;
const names=new Set(['users','accounts','account_sessions','ac_events','request_limits','pk_lobby','pk_ratings','pk_queue','pk_matches','pk_members','pk_records','pk_operations','pk_judge_usage']);
const quote=value=>{assert(names.has(value));return '`'+value+'`';};
const checkedSchema=()=>{assert(created&&validSchema(schema)&&schema!=='tb_leaderboard'&&schema!=='mysql');return '`'+schema+'`';};
try{
 const space=await statfs('/app');receipt.diskFreeBytesBefore=Number(space.bavail)*Number(space.bsize);assert(receipt.diskFreeBytesBefore>=256*1024*1024,'insufficient space for an isolated schema');
 const sources={};let bytes=0;
 for(const name of sourceNames){const value=await readFile(resolve(sourceRoot,name));bytes+=value.length;assert(bytes<2*1024*1024);sources[name]=value.toString('utf8');receipt.sourceSha256[name]=sha(value);}
 const require=createRequire(resolve(option('--modules-root','/app'),'package.json')),mysql=require('mysql2/promise');
 const {ThoughtDuels}=await import(pathToFileURL(resolve(sourceRoot,'src/thought-duels.mjs')));
 const password=(await readFile(option('--root-secret-file','/run/secrets/tb_verify_mysql_root'),'utf8')).trim();
 const options={socketPath:option('--mysql-socket','/mysql.sock'),user:'root',password,charset:'utf8mb4',timezone:'Z',connectTimeout:10000,multipleStatements:false};
 admin=await mysql.createConnection(options);
 const [[existing]]=await admin.execute('SELECT COUNT(*) n FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=?',[schema]);assert.equal(Number(existing.n),0);
 await admin.query('CREATE DATABASE `'+schema+'` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin');created=true;receipt.createdByThisInvocation=true;process.stdout.write(JSON.stringify({phase:'isolated-schema-created',isolatedSchema:schema})+'\n');
 const connect=()=>mysql.createPool({...options,database:schema,connectionLimit:4,queueLimit:32});pool=connect();
 const ensure=async connection=>{const [[row]]=await connection.query('SELECT DATABASE() name');assert.equal(row.name,schema);};
 const migrate=async name=>{
  const connection=await pool.getConnection();try{
   await ensure(connection);
   for(const sql of sources['mysql/'+name].split('\n').filter(line=>!line.trimStart().startsWith('--')).join('\n').split(';').map(s=>s.trim()).filter(Boolean)){
    // These reviewed migrations need only unqualified CREATE TABLE and the
    // singleton seed. Reject USE, ALTER, DROP, cross-schema names and grants.
    assert(/^CREATE TABLE IF NOT EXISTS [a-z_]+\s*\(/i.test(sql)||/^INSERT IGNORE INTO pk_lobby\(singleton\) VALUES\(1\)$/i.test(sql));
    const match=/^CREATE TABLE IF NOT EXISTS ([a-z_]+)/i.exec(sql);if(match)assert(names.has(match[1]));
    assert(!/`|\b(?:USE|DROP|ALTER|RENAME|TRUNCATE|GRANT|REVOKE)\b|[a-z_]\.[a-z_]/i.test(sql));await connection.query(sql);
   }
  }finally{connection.release();}
 };
 const fingerprint=async tables=>{
  const result={};for(const table of tables){
   const [rows]=await pool.query('SELECT * FROM '+quote(table));const [definition]=await pool.query('SHOW CREATE TABLE '+quote(table));
   result[table]={rows:rows.length,rowSha256:sha(JSON.stringify(rows.map(row=>JSON.stringify(row)).sort())),schemaSha256:sha(definition[0]['Create Table'])};
  }return result;
 };
 const adapter={execute:(sql,values=[])=>pool.execute(sql,values),transaction:async action=>{
  const connection=await pool.getConnection();try{await ensure(connection);await connection.query('SET SESSION innodb_lock_wait_timeout=5');await connection.beginTransaction();const result=await action(connection);await connection.commit();return result;}
  catch(error){await connection.rollback();throw error;}finally{connection.release();}
 }};
 await migrate('001_schema.sql');await migrate('004_accounts.sql');
 const owners=[randomUUID(),randomUUID()],date='2026-11-09T00:00:00.000Z';
 for(const [index,id] of owners.entries()){
  await pool.execute('INSERT INTO users(user_id,nickname,token_hash,created_at,updated_at) VALUES(?,?,?,?,?)',[id,'synthetic-'+index,sha(id),date,date]);
  await pool.execute('INSERT INTO accounts(user_id,login_id,password_hash,created_at,updated_at) VALUES(?,?,?,?,?)',[id,'synthetic_'+index,'not-a-real-password-hash',date,date]);
 }
 await pool.execute('INSERT INTO request_limits(bucket,count,expires_at) VALUES(?,?,?)',['synthetic-old-limit',7,123456]);
 const baseline=['users','accounts','account_sessions','ac_events','request_limits'],before=await fingerprint(baseline);
 await migrate('017_thought_duels.sql');await migrate('021_thought_judge_budget.sql');assert.deepEqual(await fingerprint(baseline),before);receipt.checksPassed.push('old synthetic table content and definitions preserved');
 const now=Date.parse(date);worker=new ThoughtDuels(adapter,'mysql',{dailyCallLimit:3});other=new ThoughtDuels(adapter,'mysql',{dailyCallLimit:3});
 const reservations=await Promise.all(Array.from({length:8},(_,i)=>{const current=i%2?worker:other;return current.transaction(db=>current.reserveCall(db,now));}));assert.equal(reservations.filter(value=>value.reserved).length,3);
 const [[usage]]=await pool.execute('SELECT calls FROM pk_judge_usage WHERE usage_day=?',['2026-11-09']);assert.equal(usage.calls,3);receipt.checksPassed.push('eight reservations across two workers consume exactly three');
 const all=[...names],populated=await fingerprint(all);await migrate('017_thought_duels.sql');await migrate('021_thought_judge_budget.sql');assert.deepEqual(await fingerprint(all),populated);receipt.checksPassed.push('017 and 021 preserve populated tables on repeat');
 await worker.close();await other.close();worker=other=null;await pool.end();pool=connect();worker=new ThoughtDuels(adapter,'mysql',{dailyCallLimit:3});
 assert.equal((await worker.transaction(db=>worker.reserveCall(db,now))).reserved,undefined);receipt.checksPassed.push('pool and worker restart cannot reset the budget');
 let attemptedJudges=0;
 worker.configure({enabled:true,dailyCallLimit:3,now:()=>now,judge:async()=>{attemptedJudges++;throw Error('provider invocation forbidden in this migration test');}});
 const id=randomUUID(),room={id,status:'judging',startedAt:now-3000,deadline:now+900000,problem:{id:'public-test',title:'Synthetic public fixture'},players:owners.map((owner,index)=>({owner,rating:1000,nickname:'synthetic-'+index,text:'locked synthetic proof '+index,revision:1,submittedAt:now,lastSeen:now})),events:[],judgeAttempts:0};
 for(const owner of owners)await pool.execute('INSERT INTO pk_ratings(user_id,rating) VALUES(?,1000)',[owner]);
 await pool.execute('INSERT INTO pk_matches(match_id,status,updated_at,due_at,payload) VALUES(?,?,?,?,?)',[id,'judging',now,now,JSON.stringify(room)]);
 worker.launch(id);await Promise.all([...worker.running.values()]);
 const [[saved]]=await pool.execute('SELECT payload FROM pk_matches WHERE match_id=?',[id]),waiting=JSON.parse(saved.payload);
 assert.equal(waiting.status,'judging');assert.equal(waiting.judgeWaitingCode,'PK_AI_DAILY_LIMIT');assert.equal(waiting.judgeAttempts,0);assert.equal(waiting.verdict,undefined);assert.deepEqual(waiting.players.map(p=>p.text),room.players.map(p=>p.text));
 const [[records]]=await pool.query('SELECT COUNT(*) n FROM pk_records'),[[ratings]]=await pool.query('SELECT SUM(rating) n FROM pk_ratings');assert.equal(Number(records.n),0);assert.equal(Number(ratings.n),2000);assert.equal(attemptedJudges,0);receipt.checksPassed.push('quota keeps locked answers without fake verdict or rating writes');
 const midnight=Date.parse('2026-11-09T16:00:00Z');assert.equal((await worker.transaction(db=>worker.reserveCall(db,midnight-1))).remaining,0);assert.equal((await worker.transaction(db=>worker.reserveCall(db,midnight))).reserved,true);receipt.checksPassed.push('Beijing midnight opens a new durable budget day');
 assert.deepEqual(await fingerprint(baseline),before);receipt.checksPassed.push('old synthetic tables unchanged after the full exercise');receipt.status='passed';
}catch(error){receipt.errorCode=typeof error?.code==='string'?error.code:'ISOLATED_CHECK_FAILED';}
finally{
 for(const action of [()=>worker?.close(),()=>other?.close(),()=>pool?.end()]){try{await action();}catch{receipt.cleanupErrorCode='ISOLATED_CONNECTION_CLEANUP';receipt.status='failed';}}
 if(admin&&created){try{await admin.query('DROP DATABASE '+checkedSchema());receipt.droppedByThisInvocation=true;}catch{receipt.cleanupErrorCode='ISOLATED_SCHEMA_RETAINED';receipt.status='failed';}}
 if(admin){try{await admin.end();}catch{receipt.cleanupErrorCode='ISOLATED_ADMIN_CLEANUP';receipt.status='failed';}}receipt.finishedAt=new Date().toISOString();process.stdout.write(JSON.stringify(receipt,null,2)+'\n');if(receipt.status!=='passed')process.exitCode=1;
}
