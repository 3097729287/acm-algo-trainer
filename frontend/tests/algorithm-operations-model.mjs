import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {parseXorInput,subsetXors,xorBasis,xorQuery,xorContains,xorKth} from '../src/pages/algorithm-lab/linearBasisModel.js';
import {operationTrace} from '../src/pages/algorithm-lab/operationModels.js';
import {foundationLectures,lectureDestination,ALGORITHM_TOPICS} from '../src/lib/algorithmLearning.js';

let seed=20261030,checks=0;const rng=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;};
const equal=(a,b)=>{assert.deepEqual(a,b);checks++;};
for(const text of ['', '-1','1.5','1e3','0xff','18446744073709551616','1 '.repeat(11)])assert.throws(()=>parseXorInput(text));
equal(parseXorInput('0, 18446744073709551615，2'),[0n,(1n<<64n)-1n,2n]);
for(let t=0;t<600;t++){
 const values=Array.from({length:1+rng(10)},()=>BigInt(rng(256))),results=subsetXors(values),{p,rank}=xorBasis(values);
 equal(results.length,2**rank);equal(xorQuery(p).answer,results.at(-1));
 const start=BigInt(rng(256)),candidates=results.map(x=>x^start).sort((a,b)=>a<b?-1:a>b?1:0);
 equal(xorQuery(p,start).answer,candidates.at(-1));equal(xorQuery(p,start,true).answer,candidates[0]);
 for(let x=0n;x<256n;x++){equal(xorContains(p,x),results.includes(x));}
 for(let k=0;k<results.length;k++)equal(xorKth(p,k),results[k]);equal(xorKth(p,results.length),null);
 for(const frame of xorBasis(values).frames)for(let i=0;i<64;i++)if(frame.basis[i])equal(frame.basis[i]>>BigInt(i),1n);
}
const full=xorBasis(Array.from({length:64},(_,i)=>1n<<BigInt(i)));equal(full.rank,64);equal(xorKth(full.p,(1n<<64n)-1n),(1n<<64n)-1n);
for(let t=0;t<150;t++){
 const n=1+rng(8),values=Array.from({length:n},()=>rng(11)-5),operations=[],naive=[...values];
 for(let q=0;q<30;q++)if(rng(2)){const i=rng(n),d=rng(15)-7;operations.push(['add',i,d]);naive[i]+=d;}else{let l=rng(n+1),r=rng(n+1);if(l>r)[l,r]=[r,l];operations.push(['sum',l,r]);}
 const frames=operationTrace('fenwick',values,operations);equal(frames.at(-1).a,naive);
 let a=[...values];for(let i=0;i<operations.length;i++){const [op,l,r]=operations[i];if(op==='add')a[l]+=r;else equal(frames[i+1].log.at(-1),`range_sum(${l},${r}) = ${a.slice(l,r).reduce((x,y)=>x+y,0)}`);}
 const rangeOps=operations.map(([op,x,y])=>op==='add'?['addRange',x,n,y]:[op,x,y]);a=[...values];const rangeFrames=operationTrace('segment-tree',values,rangeOps);
 for(let i=0;i<rangeOps.length;i++){const [op,l,r,d]=rangeOps[i];if(op==='addRange')for(let j=l;j<r;j++)a[j]+=d;else equal(rangeFrames[i+1].log.at(-1),`range_sum(${l},${r}) = ${a.slice(l,r).reduce((x,y)=>x+y,0)}`);equal(rangeFrames[i+1].tree[1].sum,a.reduce((x,y)=>x+y,0));}
 const edgeCount=2+rng(8),edges=Array.from({length:edgeCount},()=>[rng(n+1),rng(n+1),rng(5)]);edges.push([0,n,0]);
 const flow=operationTrace('dinic',edges,[['flow',0,n]]).at(-1).flow;let cut=Infinity;
 for(let mask=0;mask<(1<<(n+1));mask++)if(mask&1&&!(mask&(1<<n)))cut=Math.min(cut,edges.reduce((s,[u,v,c])=>s+((mask&(1<<u))&&!(mask&(1<<v))?c:0),0));
 equal(flow,cut);
}
for(let t=0;t<100;t++){
 const n=1+rng(10),values=Array.from({length:n},()=>rng(n)),ops=Array.from({length:20},()=>['jump',rng(n),rng(1000)]),frames=operationTrace('binary-lifting',values,ops);
 ops.forEach(([,v,k],i)=>{for(let j=0;j<k;j++)v=values[v];equal(frames[i+1].target,v);});
 const words=['','a','ab','abc','b','ba'],ops2=Array.from({length:40},()=>[['insert','erase','count','prefix'][rng(4)],words[rng(words.length)]]),trie=operationTrace('trie',[],ops2);let all=[];
 ops2.forEach(([op,word],i)=>{if(op==='insert')all.push(word);else if(op==='erase'){const at=all.indexOf(word);if(at>=0)all.splice(at,1);}else equal(trie[i+1].log.at(-1),`${op==='count'?'count':'prefix_count'}("${word}") = ${all.filter(x=>op==='count'?x===word:x.startsWith(word)).length}`);equal(trie[i+1].words,all);});
 const dsuOps=Array.from({length:30},()=>['unite',rng(n),rng(n)]),dsu=operationTrace('dsu',Array(n).fill(0),dsuOps);let groups=Array.from({length:n},(_,i)=>i);
 dsuOps.forEach(([,u,v],i)=>{const from=groups[v],to=groups[u];groups=groups.map(g=>g===from?to:g);equal(dsu[i+1].components,new Set(groups).size);});
}
const lectures=JSON.parse(await readFile('../data/library/lectures.json','utf8')).map(row=>row.content),kept=foundationLectures(lectures);
equal(kept.length,lectures.length-15);equal(kept.some(x=>x.id==='lecture:foundation-vector'),true);
const originalTemplates=JSON.parse(await readFile('../data/algorithm-template-preservation.json','utf8')).templates;
const templates=JSON.parse(await readFile('../backend/resources/code-templates.json','utf8')).templates;
for(const old of originalTemplates){const next=templates.find(x=>x.id===old.id);for(const [key,digest] of Object.entries(old.fields)){const text=typeof next[key]==='string'?next[key]:JSON.stringify(next[key]);equal(createHash('sha256').update(text).digest('hex'),digest);}}
for(const topic of ALGORITHM_TOPICS)for(const section of topic.sections){equal(lectureDestination(section.id).id,topic.id);const old=lectures.find(l=>l.id===section.id);equal(section.markdown,old.markdown);equal(section.images,old.images||{});}
await mkdir('../.backups/algorithm-learning-20261030',{recursive:true});await writeFile('../.backups/algorithm-learning-20261030/model-report.json',JSON.stringify({ok:true,checks,randomXorCases:600,randomOperationCases:150,lectures:lectures.length,moved:15,preservedTemplates:originalTemplates.length},null,2));
console.log(`Algorithm operations: ${checks} independent checks passed`);
