import assert from 'node:assert/strict';
import {rangeFenwick} from '../src/pages/algorithm-lab/fenwickRangeModel.js';
import {currentActivity} from '../src/lib/usePresence.js';
let seed=17;const random=n=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)%n);
for(let n=1;n<=12;n++){
 const values=Array.from({length:n},()=>random(21)-10),naive=[...values],operations=[];
 for(let step=0;step<80;step++){
  let l=random(n+1),r=random(n+1);if(l>r)[l,r]=[r,l];const delta=random(31)-15;operations.push([l,r,delta]);for(let i=l;i<r;i++)naive[i]+=delta;
  for(let k=0;k<=n;k++){const result=rangeFenwick(values,operations,k);assert.equal(result.sum,naive.slice(0,k).reduce((s,x)=>s+x,0));assert.deepEqual(result.a,naive);}
 }
}
assert.throws(()=>rangeFenwick([1],[[0,2,1]]));assert.throws(()=>rangeFenwick([1],[],2));
assert.equal(currentActivity({page:'library',studyKind:'lab'}),'lab');
assert.equal(currentActivity({studyKind:'wiki',contest:{status:'active',config:{mode:'replay'}}}),'replay');
assert.equal(currentActivity({studyKind:'wiki',contest:{status:'running',config:{strategy:'replay'}}}),'replay');
assert.equal(currentActivity({contest:{status:'running',config:{strategy:'mixed'}}}),'contest');
assert.equal(currentActivity({studyKind:'lecture'}),'lecture');assert.equal(currentActivity({practice:'A'}),'problem');
console.log('PASS independent brute-force range updates/prefixes, negative and empty ranges, and activity priority');
