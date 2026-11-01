import test from 'node:test';
import assert from 'node:assert/strict';
import {bounds,settlementStart,REWARD_POLICY} from '../src/ranking-rules.mjs';

test('Shanghai Sunday 24:00 is Monday 00:00, including exact boundaries',()=>{
 assert.equal(REWARD_POLICY.weekStartsOn,'Monday');
 for(const [stamp,start] of [
  ['2026-10-31T16:00:00Z','2026-10-26'],
  ['2026-11-01T15:59:59.999Z','2026-10-26'],
  ['2026-11-01T16:00:00Z','2026-11-02'],
  ['2026-11-08T15:59:59.999Z','2026-11-02'],
  ['2026-11-08T16:00:00Z','2026-11-09']]){
  assert.equal(bounds('weekly',Date.parse(stamp)).start,start,stamp);
 }
 assert.equal(bounds('daily',Date.parse('2026-11-01T16:00:00Z')).start,'2026-11-02');
 assert.equal(settlementStart('weekly','2026-11-01'),'2026-11-02');
 assert.equal(settlementStart('weekly','2026-11-02'),'2026-11-02');
 assert.equal(settlementStart('daily','2026-11-01'),'2026-11-01');
});
