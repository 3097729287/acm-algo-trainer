import assert from 'node:assert/strict';
import {parseActivityDate,fitActivityGrid,activitySegmentSize,activityMonths,yearDays,activityYearCells,activityTone,monthCells,fitActivityMonths} from '../src/lib/activityDate.js';
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
assert.equal(activityMonths('2026-02').length,12);
for(const year of [2024,2026]){
 const days=yearDays(year);assert.equal(days[0],`${year}-01-01`);assert.equal(days.at(-1),`${year}-12-31`);assert.equal(days.length,year===2024?366:365);
 for(const rows of [5,6,7,8,9,10,12]){const cells=activityYearCells(days,rows);assert.equal(cells.length%rows,0);assert.deepEqual(cells.filter(Boolean),days);assert.equal(cells[0],days[0]);assert.deepEqual(cells.slice(0,days.length),days);assert(cells.slice(days.length).every(day=>day===null));}
}
for(let band=1;band<=5;band++)for(let shade=1;shade<=5;shade++)assert.deepEqual(activityTone((band-1)*5+shade,5),{band,shade});
assert.deepEqual(activityTone(0),{band:0,shade:0});
assert.equal(monthCells('2024-02').filter(Boolean).length,29);
assert.equal(monthCells('2026-10')[3],'2026-10-01','Monday-first calendar alignment');
assert.equal(monthCells('2026-10').length,42);
for(const [width,height] of [[1800,330],[1000,260],[600,250],[300,270]]){
 const {columns,size}=fitActivityMonths(width,height),rows=4/columns;
 assert.ok(size<=48&&size>0);
 assert.ok(columns*(size*7+30)+16*(columns-1)<=width);
 assert.ok(rows*(size*6+25+26)+16*(rows-1)<=height);
}
console.log('ACTIVITY OK: strict date formats, leap days, square layout and uncapped shared progress scale');
