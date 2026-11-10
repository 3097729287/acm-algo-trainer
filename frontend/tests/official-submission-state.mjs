import assert from 'node:assert/strict';
import {createOfficialAttempt,officialReceiptMatches,reconcileOfficialSession} from '../src/lib/officialSubmissionState.js';

const attempt=Object.freeze({sessionId:'attempt-2',owner:'isolated-owner',problemId:'A',contestId:null,reviewId:null,language:'cpp17',code:'// exact second source\n'});
const judging={sessionId:attempt.sessionId,submissionId:'85470511',status:'judging'};
const receipt={id:'persisted-85470511',problemId:'A',contestId:null,language:'cpp17',mode:'submit',scope:'official',code:attempt.code,
  verdict:'CE',finishedAt:'2026-11-10T04:00:01Z',message:'原站确认提交 #85470511'};
const merge=(incoming=judging,rows=[receipt],previous=judging,owner=attempt.owner)=>reconcileOfficialSession(attempt,previous,incoming,rows,owner);
const finished=merge();assert.equal(finished.status,'finished');assert.equal(finished.verdict,'CE');assert.equal(finished.submission,receipt);
for(const verdict of ['AC','WA','CE','TLE','MLE','RE','OLE'])assert.equal(merge(judging,[{...receipt,verdict}]).verdict,verdict);
for(const change of [
  {message:'原站确认提交 #85470510'}, {code:'// previous code'}, {problemId:'B'}, {contestId:'another-contest'},
  {reviewId:'previous-review'}, {accountOwner:'another-owner'}, {sessionId:'previous-attempt'}, {language:'python3'},
  {scope:'local'}, {mode:'run'}, {verdict:'RUNNING'}, {finishedAt:null}, {finishedAt:'invalid'},
  {submissionId:'85470510'},
])assert.equal(merge(judging,[{...receipt,...change}]),judging,JSON.stringify(change));
assert.equal(merge(judging,[receipt],judging,'another-owner'),judging);
assert.equal(merge({...judging,sessionId:'previous-attempt',status:'finished',verdict:'CE'}),judging);
assert.equal(merge({...judging,submissionId:'85470510',status:'finished',verdict:'CE'}),judging);
assert.equal(merge({...judging,problemId:'B',status:'finished',verdict:'CE'}),judging);
assert.equal(merge({...judging,status:'finished',verdict:'CE',submission:{...receipt,code:'// wrong attempt'}}),judging);
const unknown={sessionId:attempt.sessionId,status:'loading'};
assert.equal(merge(unknown,[receipt],unknown),unknown,'An old receipt cannot supply the new attempt submission ID');
for(const status of ['loading','submitted','judging','error','finished'])assert.equal(merge({...judging,status,verdict:'CE'},[receipt],finished),finished,'Terminal state is monotonic');
const newAttempt={...attempt,sessionId:'attempt-3'},newState={sessionId:newAttempt.sessionId,status:'judging',submissionId:'85470512'};
assert.equal(reconcileOfficialSession(newAttempt,newState,newState,[receipt],attempt.owner),newState,'Even identical source cannot release a later submission');
assert(officialReceiptMatches(attempt,judging,receipt,attempt.owner),'The sent source, not later editor contents, binds the receipt');
const restored={...attempt,code:null,readOnlyRestore:true};
assert.equal(reconcileOfficialSession(restored,judging,judging,[receipt],attempt.owner),judging,'A recovered draft cannot be guessed from history');
assert.equal(reconcileOfficialSession(restored,judging,{...judging,submission:receipt},[],attempt.owner).status,'finished','The backend-bound restored SID may supply its own original source');
const editor={...attempt,code:'// current unsent editor source'};
const resumed=createOfficialAttempt(editor,{sessionId:attempt.sessionId,readOnlyRestore:true});
assert.equal(resumed.code,null);assert.equal(resumed.readOnlyRestore,true);
assert.equal(reconcileOfficialSession(resumed,judging,{...judging,submission:receipt},[],attempt.owner).status,'finished','An open response may attach an existing read-only SID instead of posting the new editor source');
assert.equal(editor.code,'// current unsent editor source');
assert.equal(createOfficialAttempt(editor,{sessionId:'new-attempt'}).code,editor.code,'A new submission keeps the exact sent source');
console.log('PASS official result identity, terminal monotonicity, all official verdicts and isolated recovery bindings; no network or private data.');
