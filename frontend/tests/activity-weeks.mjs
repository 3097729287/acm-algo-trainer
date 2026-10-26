import assert from 'node:assert/strict';
import {activityWeek,activityWeekTotal,activityDetailPages,activityTone} from '../src/lib/activityDate.js';
assert.deepEqual(activityWeek('2026-10-26'),{start:'2026-10-26',end:'2026-11-01',year:2026,number:43});
assert.equal(activityWeek('2026-01-05').number,1);
assert.equal(activityWeek('2026-01-04').year,2025);
assert.equal(activityWeek('2024-01-01').number,1);
assert.equal(activityWeek('2024-02-29').number,9);
assert.equal(activityWeek('bad'),null);
const week=activityWeek('2026-10-31'),activity=new Map([['2026-10-26',{officialAccepted:5}],['2026-10-31',{officialAccepted:30}],['2026-11-01',{officialAccepted:7}]]);
assert.equal(activityWeekTotal(week,activity,'2026-10-31'),35);
assert.equal(activityWeekTotal(week,activity,'2026-11-01'),42);
assert.deepEqual(activityTone(35,35),{band:1,shade:5});
assert.deepEqual(activityTone(36,35),{band:2,shade:1});
const days=['2026-10-26','2026-10-25','2026-10-24','2026-10-23','2026-10-22','2026-10-21','2026-10-20','2026-10-19'];
for(const capacity of [2,3,5,8,20]){
 const pages=activityDetailPages(days,capacity);
 assert.deepEqual(pages.flat().filter(x=>x.type==='day').map(x=>x.day),days);
 for(const page of pages){assert(page.length<=capacity);assert.equal(page[0].type,'week');assert.equal(page.at(-1).type,'day');}
}
console.log('PASS: week boundaries, partial weeks, cross-month totals, pagination');
