import assert from 'node:assert/strict';
import test from 'node:test';
import {randomUUID} from 'node:crypto';

export function rankingDominanceSuite(startFixture){
 test('settled daily, weekly and all-time leadership survives repeat settlement and rejects retroactive imported wins',async()=>{
  const fixture=await startFixture({now:Date.parse('2026-10-01T02:00:00Z')});
  const {STORE}=fixture,db=STORE.dominance.database,owners=[randomUUID(),randomUUID()],stamp='2026-10-01T02:00:00.000Z';
  try {
   for(const [index,id] of owners.entries()){
    await db.execute('INSERT INTO users VALUES(?,?,?,?,?)',[id,'leader'+index,'fixture',stamp,stamp]);
    await db.execute('INSERT INTO accounts(user_id,login_id,password_hash,created_at,updated_at) VALUES(?,?,?,?,?)',[id,'leader_'+id.replaceAll('-','').slice(0,20),'fixture',stamp,stamp]);
   }
   await STORE.settleRewards(Date.parse(stamp));
   async function ac(owner,key,day,received=day+'T12:00:00.000Z'){
    await db.execute('INSERT INTO official_ac_events VALUES(?,?,?,?,?,?,?)',[owner,key,key,day+'T12:00:00.000Z',day,1500,received]);
   }
   for(let day=1;day<=3;day++){
    await ac(owners[0],'first-'+day,`2026-10-0${day}`);
    await STORE.settleRewards(Date.parse(`2026-10-0${day+1}T00:00:00+08:00`));
   }
   for(const period of ['daily','weekly','total'])assert.equal((await STORE.dominance.summary([owners[0]],period,'2026-10-04')).get(owners[0]).days,3);
   const count=async()=>Number((await db.execute('SELECT COUNT(*) AS n FROM ranking_leader_days'))[0][0].n);
   const initial=await count();await STORE.settleRewards(Date.parse('2026-10-04T00:00:00+08:00'));assert.equal(await count(),initial);
   for(let i=0;i<5;i++)await ac(owners[1],'late-'+i,'2026-10-02','2026-10-04T12:00:00.000Z');
   await STORE.settleRewards(Date.parse('2026-10-05T00:00:00+08:00'));
   assert.equal((await STORE.dominance.summary([owners[1]],'total','2026-10-05')).get(owners[1]).days,1);
   const [rows]=await db.execute("SELECT user_id FROM ranking_leader_days WHERE period='total' AND ranking_day='2026-10-02'");
   assert.equal(rows[0].user_id,owners[0]);
  } finally {await fixture.close();}
 });
}
