import assert from 'node:assert/strict';
import {parseActivityDate,fitActivityGrid,activitySegmentSize} from '../src/lib/activityDate.js';
for(const input of ['2026:04:13','2026 4 13','26 04 13','26-04-13','2026/4/13','26.4.13','2026年4月13日','20260413','260413'])assert.equal(parseActivityDate(input),'2026-04-13');
for(const input of ['','2026-02-30','2026-02-29','2026-13-1','2026-0-1','2026-4-0','2026-4','2026-4-13-other','2026.5'])assert.equal(parseActivityDate(input),null);
assert.equal(parseActivityDate('24-2-29'),'2024-02-29');
assert.equal(parseActivityDate('00-2-29'),'2000-02-29');
for(const [width,height] of [[1800,330],[1250,260],[600,180],[300,140]])for(const count of [28,29,30,31]){
 const {columns,size}=fitActivityGrid(width,height,count);
 assert.ok(size>0&&columns*size+7*(columns-1)<=width);
 assert.ok(Math.ceil(count/columns)*size+7*(Math.ceil(count/columns)-1)<=height);
}
assert.equal(activitySegmentSize(7),5);
assert.equal(activitySegmentSize(25),5);
assert.equal(activitySegmentSize(26),10);
assert.ok(activitySegmentSize(1007)*5>=1007);
console.log('ACTIVITY OK: strict date formats, leap days, square layout and uncapped shared progress scale');
