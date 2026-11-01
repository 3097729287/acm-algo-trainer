import assert from 'node:assert/strict';
import {binaryBoundaryTrace,windowExtremaTrace,bruteTraceResult} from '../src/pages/algorithm-lab/templateTraceModels.js';
import {guidedMini} from '../src/pages/algorithm-lab/templateGuidedModels.js';
import {matchesTemplateProblem} from '../src/lib/templateProblemMatch.js';
import GUIDED from '../../backend/resources/template-guided.json' with {type:'json'};

let traces=0;
function* arrays(n,alphabet){if(!n){yield [];return;}for(const head of alphabet)for(const rest of arrays(n-1,alphabet))yield [head,...rest];}
for(let n=0;n<=6;n++)for(const a of arrays(n,[-1,0,1])){
 const sorted=[...a].sort((x,y)=>x-y);
 for(const target of [-2,-1,0,1,2])for(const upper of [false,true]){
  const trace=binaryBoundaryTrace(sorted,target,upper);
  assert.equal(trace.result,bruteTraceResult('binary-search',sorted,target,upper?'upper':'lower'));
  for(const frame of trace.frames){assert(frame.left<=frame.right);assert(frame.left>=0&&frame.right<=n);if(frame.middle!=null)assert(frame.middle>=0&&frame.middle<n);}
  traces++;
 }
 for(let width=1;width<=n;width++)for(const mode of ['minimum','maximum','earliest']){
  const trace=windowExtremaTrace(a,width,mode);
  assert.deepEqual(trace.result,bruteTraceResult('window-extrema',a,width,mode));
  for(const frame of trace.frames){assert(frame.queue.every((v,i)=>!i||v>frame.queue[i-1]));if(frame.action==='output')assert(frame.queue.every(v=>v>=frame.left&&v<=frame.right));}
  traces++;
 }
}
assert(binaryBoundaryTrace([2,1],1).error);
assert(windowExtremaTrace([1],0).error);
const expected={P2249:2,B3691:2,P1678:17,P2920:2,P8873:1,P1886:[[-1,-3,-3,-3,3,3],[3,3,5,5,6,7]],P2251:[5,5,5,5,5,8,8],P1440:[0,7,7,1,1,3],P1714:5,CF547B:[5,4,4,3,3,2,2,1,1]};
for(const tasks of Object.values(GUIDED)){
 assert.equal(tasks.length,5);
 for(const task of tasks)assert.deepEqual(guidedMini(task.kind,task.values,task.parameter,task.extra).result,expected[task.pid],task.pid);
}
assert.equal(guidedMini('bounded-sum',[-4,-2,-7],2).result,-2);
assert.equal(guidedMini('lookup',[1,3,3],4).result,-1);
assert.equal(guidedMini('nearest',[1,5],9).result,4);
assert.equal(guidedMini('cuts',[2,2,2],0,[2]).result,0);
assert.deepEqual(guidedMini('previous',[7,1,2],2).result,[0,7,1]);
assert.equal(matchesTemplateProblem({id:'mirror',url:'https://codeforces.com/contest/547/problem/B'},{problemId:'luogu-training-CF547B',url:'https://www.luogu.com.cn/problem/CF547B'}),true);
assert.equal(matchesTemplateProblem({id:'mirror',url:'https://codeforces.com/contest/547/problem/A'},{problemId:'luogu-training-CF547B',url:'https://www.luogu.com.cn/problem/CF547B'}),false);
console.log(`PASS ${traces} algorithm traces, ten original-problem mini models, negative/boundary cases and contest alias locks`);
