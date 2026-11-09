// Explicit, paid opt-in. Provider credentials arrive on stdin and are never persisted.
import assert from 'node:assert/strict';
import {createHash,randomUUID} from 'node:crypto';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {performance} from 'node:perf_hooks';
import {startFixture} from '../tests/local-server.mjs';
import {createAIJudge,JudgeError} from '../src/pk-judge.mjs';

const args=process.argv.slice(2),flag=args.indexOf('--output');
if(!args.includes('--allow-paid-call')||flag<0||!args[flag+1]){
 process.stderr.write('Usage: node scripts/verify-thought-provider.mjs --allow-paid-call --output NEW_CASE/result.json < protected-stdin\n');process.exit(2);
}
const output=resolve(args[flag+1]),started=performance.now(),prefix='/api/pk/v1/';
await mkdir(dirname(output),{recursive:true});
// An exclusive placeholder prevents a retry from overwriting any prior evidence.
await writeFile(output,JSON.stringify({schema:1,status:'started',realProvider:true,maxProviderCalls:1})+'\n',{flag:'wx'});
const proof={schema:1,status:'failed',realProvider:true,maxProviderCalls:1,providerCalls:0,sourceBase:'5ca1f752',ordinaryProgramStarted:false,ordinaryAccountStateUsed:false,privateAnswersSent:false,credentialsPersisted:false,productionDeployed:false,checks:{}};
let fixture;
const digest=value=>createHash('sha256').update(value).digest('hex');
try{
 const chunks=[];let size=0;
 for await(const chunk of process.stdin){size+=chunk.length;assert(size<=16384,'credential input limit');chunks.push(chunk);}
 const config=JSON.parse(Buffer.concat(chunks).toString('utf8'));chunks.fill(null);
 const judge=createAIJudge({endpoint:config.endpoint,model:config.model,key:config.key});assert(judge,'provider required');
 proof.provider={name:config.provider||'custom',host:new URL(config.endpoint).hostname,model:config.model};
 const liveJudge=async(...values)=>{if(proof.providerCalls>=1)throw new JudgeError('PK_LIVE_BUDGET',{retryable:false});proof.providerCalls++;const began=performance.now();try{return await judge(...values);}catch(error){proof.providerError={code:error instanceof JudgeError?error.code:'PK_AI_UNKNOWN',...(Number.isInteger(error?.status)?{status:error.status}:{})};throw error;}finally{proof.providerElapsedMs=Math.round(performance.now()-began);}};
 config.key='';
 const pool=JSON.parse(await readFile(new URL('../src/thought-problems.json',import.meta.url),'utf8')).problems;
 const problem=pool.find(p=>p.id==='Div.2 1112::A');assert(problem);
 proof.problem={id:problem.id,title:problem.title,statementSha256:problem.sourceSha256,publicReferenceSha256:digest(problem.reference)};
 const database=resolve(dirname(output),'isolated.sqlite3');await writeFile(database,'',{flag:'wx'});
 let clock=Date.now();
 const configure=()=>{fixture.STORE.pk.problems=[problem];fixture.STORE.pk.configure({enabled:true,now:()=>fixture.env.TEST_NOW,judge:liveJudge});};
 const open=async()=>{fixture=await startFixture({database,now:clock});configure();};await open();
 const send=async(identity,path,body)=>{
  const response=await fetch(fixture.endpoint+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(identity?{'X-TB-User':identity.account.userId,Authorization:'Bearer '+identity.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
  return {status:response.status,value:await response.json()};
 };
 const account=async name=>{const password=randomUUID()+'-isolated';assert.equal((await send(null,'/v1/accounts/register',{loginId:name,nickname:name,password})).status,201);const result=await send(null,'/v1/accounts/login',{loginId:name,password});assert.equal(result.status,200);return result.value;};
 const suffix=randomUUID().slice(0,8),a=await account('thought_live_a_'+suffix),b=await account('thought_live_b_'+suffix),outsider=await account('thought_live_x_'+suffix);
 const call=(who,path,body)=>send(who,prefix+path,body===undefined?undefined:{requestId:randomUUID(),...body});
 assert.equal((await call(a,'match/join',{})).status,200);assert.equal((await call(b,'match/join',{})).status,200);
 const countdown=(await call(a,'state')).value;assert.equal(countdown.status,'countdown');assert.equal(countdown.match.problem,null);assert.equal(countdown.match.deadline-countdown.match.startedAt,900000);proof.checks.serverCountdownAndHiddenProblem=true;
 const id=countdown.match.id;clock=countdown.match.startedAt;fixture.env.TEST_NOW=clock;
 const active=(await call(a,'state')).value;assert.equal(active.status,'active');assert.equal(active.match.problem.id,problem.id);assert(!JSON.stringify(active).includes('"reference"'));proof.checks.publicFullStatementAndPrivateReference=true;
 const textA='所有 n 个元素移动后须填满 n 个内部位置，不能有元素出界。位置 1 只能由位置 2 填入，且原位置 1 的元素必须向右，所以第一对只能互换。删除第一对后归纳，相邻位置都必须两两互换，方向为右、左、右、左；因此 n 必须是偶数。令 H 为奇数位置重量的最小值，L 为偶数位置重量的最大值。必要且充分条件是存在整数 L<k<H，即 H-L>=2；成立时取 k=L+1，各对互换即覆盖全部内部位置，且没有重量等于 k。n 为奇数、H<=L、H=L+1 均输出 NO，n=2 也用同一判据。单次扫描维护 H,L，时间 O(n)，额外空间 O(1)，读取后即可更新，不排序；重量和差值用 long long 避免溢出。';
 const textB='如果 n 是偶数就输出 YES，因为元素可以两两交换，不需要读取各个重量的大小。n 为奇数输出 NO。判断的时间 O(1)，空间 O(1)。';
 assert.equal((await call(a,'game/draft',{matchId:id,revision:0,text:textA})).status,200);
 const privateView=(await call(b,'state')).value;assert.equal(privateView.match.players.find(p=>p.owner===a.account.userId).text,undefined);proof.checks.opponentDraftHidden=true;
 await fixture.close();fixture=null;await open();
 const restored=(await call(a,'state')).value,me=restored.match.players.find(p=>p.owner===a.account.userId);assert.equal(me.text,textA);assert.equal(me.revision,1);proof.checks.realDraftSurvivesServiceRestart=true;
 const payloadA={requestId:randomUUID(),matchId:id,revision:me.revision,text:textA},payloadB={requestId:randomUUID(),matchId:id,revision:0,text:textB};
 assert.equal((await send(a,prefix+'game/submit',payloadA)).status,200);assert.equal((await send(b,prefix+'game/submit',payloadB)).status,200);
 await Promise.all([...fixture.STORE.pk.running.values()]);
 const ended=(await call(a,'state')).value;assert.equal(ended.status,'finished');assert.equal(proof.providerCalls,1);assert.equal(ended.match.judgeFailed,false,'real provider did not yield a valid verdict');
 const room=ended.match,aIndex=room.players.findIndex(p=>p.owner===a.account.userId),aScore=room.verdict[aIndex===0?'player_a':'player_b'],bScore=room.verdict[aIndex===0?'player_b':'player_a'];
 assert.equal(aScore.correct_algorithm,true);assert.equal(aScore.time_feasible,true);assert.equal(bScore.correct_algorithm,false);assert.equal(room.winner,a.account.userId);proof.checks.realJudgeDistinguishesProvenAlgorithmAndCounterexample=true;
 const savedRatings=fixture.STORE.database.prepare('SELECT user_id,rating FROM pk_ratings ORDER BY user_id').all();
 const replay=await Promise.all(Array.from({length:4},()=>send(b,prefix+'game/submit',payloadB)));assert(replay.every(r=>r.status===200));assert.equal(fixture.STORE.database.prepare('SELECT COUNT(*) n FROM pk_records').get().n,1);assert.deepEqual(fixture.STORE.database.prepare('SELECT user_id,rating FROM pk_ratings ORDER BY user_id').all(),savedRatings);assert.equal((await call(outsider,'history/'+id)).status,404);proof.checks.replayedSubmissionsSettleExactlyOnce=true;proof.checks.otherAccountCannotReadRecord=true;
 const record=(await call(a,'history/'+id)).value.match;assert.equal(record.events.filter(e=>e.type==='pk:game_over').length,1);assert.equal(record.players.find(p=>p.owner===a.account.userId).text,textA);
 await fixture.close();fixture=null;await open();
 const persisted=(await call(a,'history/'+id)).value.match;assert.deepEqual(persisted.verdict,record.verdict);assert.deepEqual(fixture.STORE.database.prepare('SELECT user_id,rating FROM pk_ratings ORDER BY user_id').all(),savedRatings);assert.equal(fixture.STORE.database.prepare('SELECT COUNT(*) n FROM pk_records').get().n,1);proof.checks.verdictRatingAndBothAnswersSurviveServiceRestart=true;
 proof.verdict={winner:'correct-public-answer',playerA:{correctAlgorithm:aScore.correct_algorithm,timeFeasible:aScore.time_feasible,scores:aScore.scores,finalScore:aScore.final_score},playerB:{correctAlgorithm:bScore.correct_algorithm,timeFeasible:bScore.time_feasible,scores:bScore.scores,finalScore:bScore.final_score},ratingChanges:Object.values(room.ratingChanges).sort((x,y)=>x-y),validatedVerdictSha256:digest(JSON.stringify(record.verdict)),answerSha256:[digest(textA),digest(textB)]};
 proof.status='passed';
}catch(error){proof.error={code:error instanceof JudgeError?error.code:error?.code==='ERR_ASSERTION'?'LIVE_ASSERTION_FAILED':'LIVE_CHECK_FAILED'};}
finally{
 if(fixture)await fixture.close();proof.elapsedMs=Math.round(performance.now()-started);proof.finishedAt=new Date().toISOString();
 await writeFile(output,JSON.stringify(proof,null,2)+'\n');
 process.stdout.write(JSON.stringify({status:proof.status,providerCalls:proof.providerCalls,providerElapsedMs:proof.providerElapsedMs,checks:proof.checks,error:proof.error,proof:output})+'\n');
 if(proof.status!=='passed')process.exitCode=1;
}
