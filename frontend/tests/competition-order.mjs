import assert from 'node:assert/strict';
import {compareCompetitionNewest as compare} from '../src/lib/competitionOrder.js';
const group=(name,row)=>({name,rows:[{contest:name,...row}]});
const oldXcpc=group('ICPC 2019 南昌区域赛',{series:'XCPC',eventYear:2019,contestDate:'2019-11-03',addedAt:'2026-11-02'});
const midXcpc=group('ICPC 2025 区域赛',{series:'XCPC',eventYear:2025,contestDate:'2025-11-01'});
const newCf=group('Div.3 1131',{platform:'Codeforces',series:'Div.3',contestDate:'2026-10-31',addedAt:'2026-11-01'});
const oldCfAdded=group('Div.3 old',{platform:'Codeforces',series:'Div.3',contestDate:'2018-01-01',addedAt:'2026-11-02'});
const unrecorded=group('ABC new',{platform:'AtCoder',series:'ABC',contestDate:'2026-11-03'});
const unknown=group('Unknown XCPC',{series:'XCPC'});
const datedYear=group('ICPC 2023 only year',{series:'XCPC',eventYear:2023,contestDate:'2026-11-02',addedAt:'2026-11-02'});
const values=[oldXcpc,midXcpc,newCf,oldCfAdded,unrecorded,unknown,datedYear];
assert(compare(oldXcpc,newCf)>0);assert(compare(oldCfAdded,newCf)<0);assert(compare(datedYear,midXcpc)>0);
assert.deepEqual([...values].sort(compare).map(x=>x.name),['ABC new','Div.3 old','Div.3 1131','ICPC 2025 区域赛','ICPC 2023 only year','ICPC 2019 南昌区域赛','Unknown XCPC']);
for(const a of values)for(const b of values)for(const c of values){
 assert.equal(Math.sign(compare(a,b))+Math.sign(compare(b,a)),0);
 if(compare(a,b)<=0&&compare(b,c)<=0)assert(compare(a,c)<=0,'Mixed-list ordering is transitive');
}
console.log('PASS XCPC actual-year placement, verified normal addition chronology, unknown dates and 343 mixed-order triples');
