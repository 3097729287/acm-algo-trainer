import test from 'node:test';
import assert from 'node:assert/strict';
import {parseTeamReceipt,teamPlatform,validTeamHandle} from '../src/team-receipts.mjs';

const when=Date.parse('2026-11-08T00:00:05Z');
test('public receipt verification requires the exact owner, problem and submission, never sample verdict text',()=>{
 const request={handle:'FixtureHandle',submissionId:'12345',url:'https://codeforces.com/contest/123/problem/A'};
 const row={id:12345,problem:{contestId:123,index:'A'},author:{members:[{handle:'FixtureHandle'}]},creationTimeSeconds:when/1000,verdict:'OK'};
 const fact=parseTeamReceipt('codeforces',[row],request);
 assert.equal(fact.verdict,'AC');assert.equal(fact.submittedAt,when);assert.match(fact.proofSha256,/^[a-f0-9]{64}$/);
 for(const change of [{id:12346},{problem:{contestId:123,index:'B'}},{author:{members:[{handle:'other'}]}},{verdict:'TESTING'},{creationTimeSeconds:null}])
  assert.equal(parseTeamReceipt('codeforces',[{...row,...change}],request),null);
 assert.equal(parseTeamReceipt('codeforces',[{...row,verdict:'WRONG_ANSWER',message:'AC'}],request).verdict,'WA');
 assert.equal(parseTeamReceipt('codeforces',{status:'FAILED',result:[row]},request),null);
 assert.equal(parseTeamReceipt('codeforces',[{...row,id:Number.MAX_SAFE_INTEGER+1}],{...request,submissionId:String(Number.MAX_SAFE_INTEGER+1)}),null);
});
test('AtCoder public records retain their third-party source and cannot credit another contest or user',()=>{
 const request={handle:'FixtureAt',submissionId:'56789',url:'https://atcoder.jp/contests/abc123/tasks/abc123_a'};
 const row={id:56789,user_id:'fixtureat',contest_id:'abc123',problem_id:'abc123_a',epoch_second:when/1000,result:'AC'};
 const fact=parseTeamReceipt('atcoder',[row],request);assert.equal(fact.verdict,'AC');assert.equal(fact.source,'AtCoder Problems public receipts');
 for(const change of [{user_id:'other'},{problem_id:'abc123_b'},{contest_id:'abc124'},{result:'WJ'},{id:'56780'}])assert.equal(parseTeamReceipt('atcoder',[{...row,...change}],request),null);
});
test('Nowcoder checks the public contest roster, individual uid, full-case AC and terminal status',()=>{
 const request={handle:'12345',submissionId:'78901',url:'https://ac.nowcoder.com/acm/contest/456/A'};
 const submission={uid:12345,submissionId:78901,problemId:987,status:5,rightCaseRate:1,submitTime:when};
 const payload={code:0,data:{problemData:[{problemId:987,index:'A'}],submitDataList:[{basicInfo:{contestId:456},signUpUsers:[{uid:12345,team:false}],submissions:[submission]}]}};
 assert.equal(parseTeamReceipt('nowcoder',payload,request).verdict,'AC');
 for(const change of [{uid:987},{problemId:988},{submissionId:78902},{rightCaseRate:.5},{status:1}]){
  const changed=structuredClone(payload);changed.data.submitDataList[0].submissions[0]={...submission,...change};assert.equal(parseTeamReceipt('nowcoder',changed,request),null);
 }
 const team=structuredClone(payload);team.data.submitDataList[0].signUpUsers[0].team=true;assert.equal(parseTeamReceipt('nowcoder',team,request),null);
 const wrong=structuredClone(payload);wrong.data.submitDataList[0].basicInfo.contestId=123;assert.equal(parseTeamReceipt('nowcoder',wrong,request),null);
});
test('only exact supported HTTPS task identities become provider requests',()=>{
 assert.equal(teamPlatform('https://codeforces.com/gym/106799/problem/A').id,'codeforces');
 assert.equal(teamPlatform('https://atcoder.jp/contests/practice2/tasks/practice2_j').id,'atcoder');
 for(const url of ['http://codeforces.com/contest/123/problem/A','https://evil.test/contest/123/problem/A','https://codeforces.com@evil.test/contest/123/problem/A','https://codeforces.com/contest/123/problem/A?target=elsewhere','https://codeforces.com:444/contest/123/problem/A'])assert.equal(teamPlatform(url),null);
 assert.equal(validTeamHandle('nowcoder','12345'),true);assert.equal(validTeamHandle('nowcoder','1/../2'),false);assert.equal(validTeamHandle('codeforces','name?extra'),false);
});
