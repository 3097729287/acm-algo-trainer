import assert from 'node:assert/strict';
import test from 'node:test';
import {SQLiteStore} from './sqlite-store.mjs';
import {dominanceFromDays} from '../src/ranking-dominance.mjs';

test('dominance keeps earned days, breaks gaps and ignores future dates',()=>{
 assert.deepEqual(dominanceFromDays(['2026-10-01','2026-10-02','2026-10-04','2026-10-05','2026-10-05','2026-10-07'],'2026-10-06'),{days:2,totalDays:4,longestDays:2});
 assert.equal(dominanceFromDays(['2026-10-01'],'2026-10-06').days,0);
});

test('daily observations cover all three boards, are idempotent and exclude late imported history',async()=>{
 const store=new SQLiteStore(),db=store.database,stamp='2026-10-01T02:00:00.000Z';
 try {
  for(const id of ['a','b']){
   db.prepare('INSERT INTO users VALUES(?,?,?,?,?)').run(id,id,'fixture',stamp,stamp);
   db.prepare('INSERT INTO accounts(user_id,login_id,password_hash,created_at,updated_at) VALUES(?,?,?,?,?)').run(id,id,'fixture',stamp,stamp);
  }
  await store.settleRewards(Date.parse(stamp));
  function ac(id,key,day,received=day+'T12:00:00.000Z'){
   db.prepare('INSERT INTO official_ac_events VALUES(?,?,?,?,?,?,?)').run(id,key,key,day+'T12:00:00.000Z',day,1500,received);
  }
  for(let day=1;day<=3;day++){
   const date=`2026-10-0${day}`;ac('a','a'+day,date);
   await store.settleRewards(Date.parse(`2026-10-0${day+1}T00:00:00+08:00`));
  }
  for(const period of ['daily','weekly','total'])assert.equal((await store.dominance.summary(['a'],period,'2026-10-04')).get('a').days,3);
  const count=db.prepare('SELECT COUNT(*) AS n FROM ranking_leader_days').get().n;
  await store.settleRewards(Date.parse('2026-10-04T00:00:00+08:00'));
  assert.equal(db.prepare('SELECT COUNT(*) AS n FROM ranking_leader_days').get().n,count);
  for(let index=0;index<5;index++)ac('b','b'+index,'2026-10-02','2026-10-04T12:00:00.000Z');
  await store.settleRewards(Date.parse('2026-10-05T00:00:00+08:00'));
  assert.equal((await store.dominance.summary(['b'],'total','2026-10-05')).get('b').days,1);
  assert.equal(db.prepare("SELECT user_id FROM ranking_leader_days WHERE period='total' AND ranking_day='2026-10-02'").get().user_id,'a');
 } finally {await store.close();}
});
