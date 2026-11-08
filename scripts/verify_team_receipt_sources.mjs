// Read-only public source probe. No cookies, credentials, code or submissions.
import {writeFile} from 'node:fs/promises';
import {codeforcesStatus} from '../server/leaderboard/src/gameplay.mjs';
import {parseTeamReceipt,verifyTeamReceipt} from '../server/leaderboard/src/team-receipts.mjs';

const pause=()=>new Promise(done=>setTimeout(done,1300));
async function json(url){
 const response=await fetch(url,{signal:AbortSignal.timeout(10000),redirect:'error'});
 if(!response.ok)throw Error('HTTP '+response.status);
 const reader=response.body.getReader(),parts=[];let size=0;
 for(;;){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>4*1024*1024){await reader.cancel();throw Error('size');}parts.push(value);}
 return JSON.parse(Buffer.concat(parts).toString('utf8'));
}
const output={at:new Date().toISOString(),actualProblemSiteSubmissions:0,reads:[]};
for(const platform of ['codeforces','atcoder','nowcoder']){
 try{
  let request;
  if(platform==='codeforces'){
   const rows=await codeforcesStatus('tourist'),row=rows.find(r=>r.verdict==='OK'&&r.problem?.contestId&&r.problem?.index);
   if(!row)throw Error('no public terminal sample');
   request={handle:'tourist',submissionId:String(row.id),url:`https://codeforces.com/${row.problem.contestId>=100000?'gym':'contest'}/${row.problem.contestId}/problem/${row.problem.index}`,issuedAt:row.creationTimeSeconds*1000};
  }else if(platform==='atcoder'){
   const rows=await json('https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user=kenkoooo&from_second=0'),row=rows.find(r=>r.result==='AC');
   if(!row)throw Error('no public terminal sample');
   request={handle:'kenkoooo',submissionId:String(row.id),url:`https://atcoder.jp/contests/${row.contest_id}/tasks/${row.problem_id}`,issuedAt:row.epoch_second*1000};
  }else{
   const cid='141877',query=new URLSearchParams({currentContestId:cid,contestList:cid,rankScope:'ALL'});
   const payload=await json('https://ac.nowcoder.com/acm/contest/rank/submit-list?'+query);
   if(payload.code!==0)throw Error('public board unavailable');
   for(const group of payload.data?.submitDataList||[]){
    for(const row of group.submissions||[]){
     const letter=payload.data.problemData?.find(p=>String(p.problemId)===String(row.problemId))?.index;
     const candidate={handle:String(row.uid),submissionId:String(row.submissionId),url:`https://ac.nowcoder.com/acm/contest/${cid}/${letter}`,issuedAt:row.submitTime};
     if(parseTeamReceipt(platform,payload,candidate)){request=candidate;break;}
    }if(request)break;
   }
   if(!request)throw Error('no public individual terminal sample');
  }
  await pause();const fact=await verifyTeamReceipt(request);
  output.reads.push({platform,available:true,verified:Boolean(fact),...(fact?{source:fact.source,proofSha256:fact.proofSha256}:{} )});
 }catch(error){output.reads.push({platform,available:false,verified:false,reason:error.message.slice(0,100)});}
}
if(process.argv[2])await writeFile(process.argv[2],JSON.stringify(output,null,2)+'\n');console.log(JSON.stringify(output));
