import assert from 'node:assert/strict';
import {contestOptions} from '../src/lib/contestCatalog.js';

const partial={name:'CCPC 2026 长春区域赛',platform:'QOJ',series:'XCPC',count:13,expectedCount:13,complete:false,availableCount:12,missingProblems:['I']};
const empty={...partial,name:'CCPC 2026 隔离目录校验',availableCount:0};
const complete={name:'ABC 478',platform:'AtCoder',series:'ABC',count:7,complete:true};
const events=[partial,empty,complete],before=JSON.stringify(events);
const leaves=nodes=>nodes.flatMap(node=>node.children?leaves(node.children):[node]);
const options=leaves(contestOptions(events));
for(const event of events){
 const option=options.find(option=>option.value===event.name);
 assert(option,'Every original event remains selectable for a real server preview');
 assert.notEqual(option.disabled,true,'Incomplete collection is not a reason to disable the whole contest');
 assert.equal(option.event,event,'Selection retains the original event and stable identity');
}
const option=options.find(option=>option.value===partial.name);
assert.match(option.selectionLabel,/13 题.*题面待核验/);
assert.equal(JSON.stringify(events),before,'Opening the menu must not change completeness, missing slots or reward evidence');
console.log('PASS partial replay selection, empty-preview boundary, original roster warning and immutable event metadata');
