import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {startMySQLFixture} from './mysql-fixture.mjs';
import {ThoughtDuels} from '../src/thought-duels.mjs';
import {preservedData,assertPreserved} from '../scripts/audit-preserved-data.mjs';

test('MySQL thought budget migration preserves old tables and reserves atomically across connections',{
 skip:!process.env.TB_MYSQL_TEST_PORT&&'requires an explicitly isolated MySQL test server'
},async()=>{
 const fixture=await startMySQLFixture();let other;
 try{
  const migrate=async name=>{const source=await readFile(new URL('../mysql/'+name,import.meta.url),'utf8');for(const sql of source.split(';').map(s=>s.trim()).filter(Boolean))await fixture.STORE.pool.query(sql);};
  await migrate('017_thought_duels.sql');const before=await preservedData(fixture.STORE.pool);
  await migrate('021_thought_judge_budget.sql');const created=await preservedData(fixture.STORE.pool);assertPreserved(before,created);assert.equal(created.tables.pk_judge_usage.rows,0);
  const now=Date.parse('2026-11-09T00:00:00Z');fixture.STORE.pk.configure({dailyCallLimit:1});other=new ThoughtDuels(fixture.STORE.pk.db,'mysql',{dailyCallLimit:1});
  const reservations=await Promise.all([fixture.STORE.pk.transaction(db=>fixture.STORE.pk.reserveCall(db,now)),other.transaction(db=>other.reserveCall(db,now))]);assert.equal(reservations.filter(r=>r.reserved).length,1);
  const populated=await preservedData(fixture.STORE.pool);await migrate('021_thought_judge_budget.sql');assertPreserved(populated,await preservedData(fixture.STORE.pool));
 }finally{await other?.close();await fixture.close();}
});
