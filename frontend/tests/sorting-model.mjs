import assert from 'node:assert/strict';
import {parseSortInput,sortingTrace,SORT_NAMES} from '../src/pages/algorithm-lab/sortingModel.js';
assert.deepEqual(parseSortInput('10, 2，0'),[10,2,0]);
for(const text of ['', '-1 2','1.5 2','1000','0 '.repeat(13)])assert.throws(()=>parseSortInput(text));
let seed=51;
const rng=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};
const fixtures=[[0],[5,5,5],[3,1,3,2,0],[1,2,3,4],[9,8,7,6,5],[999,10,1,0,999],...Array.from({length:100},()=>Array.from({length:1+rng()%12},()=>rng()%30))];
for(const values of fixtures)for(const algorithm of Object.keys(SORT_NAMES)){
 const frames=sortingTrace(values,algorithm),final=frames.at(-1);
 assert.deepEqual(final.items.map(x=>x.value),values.toSorted((a,b)=>a-b),algorithm);
 assert.deepEqual(final.items.map(x=>x.id).sort((a,b)=>a-b),values.map((_,i)=>i));
 if(['bubble','insertion','merge','counting','radix','bucket'].includes(algorithm))for(let i=1;i<final.items.length;i++)if(final.items[i].value===final.items[i-1].value)assert.ok(final.items[i].id>final.items[i-1].id,algorithm);
 if(algorithm==='merge')assert.equal(final.inversions,values.reduce((sum,x,i)=>sum+values.slice(i+1).filter(y=>x>y).length,0));
 assert.ok(frames.length<600);
}
assert.deepEqual(sortingTrace([8,2,6,4],'randomQuick',34),sortingTrace([8,2,6,4],'randomQuick',34));
assert.ok(sortingTrace([1,2,3,4,5,6],'bubble').at(-1).comparisons<10);
console.log(`sorting: ${fixtures.length*Object.keys(SORT_NAMES).length} traces checked`);
