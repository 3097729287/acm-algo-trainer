import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {SQLiteStore} from './sqlite-store.mjs';
import {rankingQuery} from '../src/ranking-rules.mjs';
import {firstOfficialEventsCTE,REVIEWED_QUESTION_PAIRS} from '../src/question-identities.mjs';

const hash=value=>createHash('sha256').update(value).digest('hex');
const day='2026-11-09',at=day+'T01:00:00.000Z';
test('large public ranking fixture uses both primary-key parts and preserves first-AC/exclusion facts',async()=>{
 const store=new SQLiteStore();
 try{
  await store.createAccount({userId:'public-fixture-owner',loginId:'public_fixture',nickname:'Public fixture',
   passwordHash:'not-a-login-credential',retiredHash:hash('fixture'),timestamp:at});
  const db=store.database,put=db.prepare('INSERT INTO official_ac_events VALUES(?,?,?,?,?,?,?)');
  const exclude=db.prepare('INSERT INTO ranking_exclusions VALUES(?,?,?)');
  db.exec('BEGIN');
  for(let i=0;i<12000;i++){
   const key=hash('public-ordinary-task-'+i);
   put.run('public-fixture-owner',key,hash('public-event-'+i),at,day,1200,at);
   if(i<5000)exclude.run('public-fixture-owner',key,at);
  }
  const [left,right]=REVIEWED_QUESTION_PAIRS[0].aliases.map(hash);
  put.run('public-fixture-owner',left,hash('earlier-mirror'),'2026-11-06T01:00:00.000Z','2026-11-06',1200,at);
  put.run('public-fixture-owner',right,hash('later-mirror'),at,day,1400,at);
  db.exec('COMMIT');
  const before=db.prepare('SELECT COUNT(*) AS n FROM official_ac_events').get().n;
  assert.equal((await store.rankings('public-fixture-owner',null,day)).own.count,7001);
  assert.equal((await store.rankings('public-fixture-owner',{start:day,end:'2026-11-10'},day)).own.count,7000,
   'a later mirror remains excluded by the actual first acceptance before date filtering');
  exclude.run('public-fixture-owner',right,at);
  assert.equal((await store.rankings('public-fixture-owner',null,day)).own.count,7000,
   'an exclusion on the later physical mirror also hides the canonical first record');
  assert.equal(db.prepare('SELECT COUNT(*) AS n FROM official_ac_events').get().n,before);
  const {sql,values}=rankingQuery(null,day);
  const plan=db.prepare('EXPLAIN QUERY PLAN '+sql+' SELECT * FROM ranked').all(...values);
  const probes=plan.filter(row=>/SEARCH (?:earlier|x)\b/.test(row.detail));
  assert(probes.length>=3,'first-AC peer and original/peer exclusions must each use a keyed probe');
  for(const row of probes)assert.match(row.detail,/user_id=\? AND problem_key=\?/,
   'ordinary events must not scan all exclusions or events owned by the account');
 }finally{await store.close();}
});

test('equal accepted times retain the actual row selected by received time and then physical hash',async()=>{
 const store=new SQLiteStore();
 try{
  await store.createAccount({userId:'tie-fixture-owner',loginId:'tie_fixture',nickname:'Tie fixture',
   passwordHash:'not-a-login-credential',retiredHash:hash('tie-fixture'),timestamp:at});
  const keys=REVIEWED_QUESTION_PAIRS[0].aliases.map(hash).sort();
  const put=store.database.prepare('INSERT INTO official_ac_events VALUES(?,?,?,?,?,?,?)');
  for(const [index,key]of keys.entries())put.run('tie-fixture-owner',key,hash('tie-'+index),at,day,1100+index,at);
  const read=()=>store.database.prepare('WITH '+firstOfficialEventsCTE()+' SELECT * FROM first_official_ac').all();
  assert.equal(read().length,1);assert.equal(read()[0].problem_key,keys[0]);assert.equal(read()[0].difficulty,1100);
  store.database.prepare('UPDATE official_ac_events SET received_at=? WHERE problem_key=?').run('2026-11-09T00:00:00.000Z',keys[1]);
  assert.equal(read()[0].problem_key,keys[1]);assert.equal(read()[0].difficulty,1101);
 }finally{await store.close();}
});
