import assert from 'node:assert/strict';
import {contestAddedTime,compareContestAddedNewest} from '../src/lib/practiceMetadata.js';

const school={name:'Old event added today',rows:[{addedAt:'2026-11-01T07:00:00Z',contestDate:'2019-01-01'}]};
const recent={name:'New event added yesterday',rows:[{addedAt:'2026-10-31T00:00:00Z',contestDate:'2026-11-02'}]};
const unrecorded={name:'Legacy event',rows:[{contestDate:'2026-11-03'}]};
assert.deepEqual([recent,unrecorded,school].sort(compareContestAddedNewest),[school,recent,unrecorded]);
assert.equal(contestAddedTime({...school,rows:[...school.rows,{addedAt:'2026-11-02T00:00:00Z'}]}),contestAddedTime(school),'Later statement imports do not move an existing contest');
assert.equal(contestAddedTime({rows:[{addedAt:'not a date',catalogAddedAt:'2026-11-01T15:00:00+08:00'}]}),contestAddedTime(school));
assert.deepEqual([school,recent].sort((a,b)=>-compareContestAddedNewest(a,b)),[recent,school]);
console.log('PASS addition time takes precedence over event date/name, partial refresh preserves first addition, reverse sort and timezone');
