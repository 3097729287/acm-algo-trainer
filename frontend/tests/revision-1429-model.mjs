import assert from 'node:assert/strict';
import {radarTopicGroups} from '../src/lib/radarTopicGroups.js';
import {catalogSegments,catalogPathMatches,contestOptions} from '../src/lib/contestCatalog.js';
import {completeContest} from '../src/lib/completeContest.js';
import {consolidateSmallCurriculum} from '../src/lib/trainingCurriculum.js';
import {submissionQuery,submissionSnapshot,loadSubmissionPage} from '../src/lib/submissionPages.js';

const groups=radarTopicGroups([['empty',1600],['one',1000],['two',2000],['regular',1400]],new Map([['one',new Set(['a'])],['two',new Set(['a','b'])],['regular',new Set(['a','b','c'])]]));
assert.equal(groups.length,2);assert(groups.some(node=>node.name==='regular'));
const misc=groups.find(node=>node.name==='杂项');assert.deepEqual(misc.members,['one','two']);assert.equal(misc.difficulty,null);
assert(!groups.some(node=>node.name==='empty'));
const regional={contest:'ICPC 2026 西安区域赛',series:'XCPC'};
const provincial={contest:'CCPC 2026 黑龙江省赛',contestFullName:'CCPC2026黑龙江省大学生程序设计竞赛',xcpcKind:'省赛',series:'XCPC'};
assert.deepEqual(catalogSegments(regional).slice(0,2),['XCPC','ICPC 区域赛']);
assert(catalogPathMatches(regional,['ACM','ICPC']));
assert(!catalogPathMatches(provincial,['XCPC','CCPC 区域赛']));
assert(catalogPathMatches(provincial,['XCPC','省赛']));
assert.deepEqual(contestOptions([]),[]);
assert(!completeContest([{contestProblemCount:8,catalogContentReady:true}]));
assert(!completeContest([{catalogContentReady:true},{catalogContentReady:true}]));
assert(completeContest([{contestProblemCount:2,catalogContentReady:true},{catalogContentReady:true}]));
assert(!completeContest([{contestProblemCount:2,catalogContentReady:true},{catalogContentReady:false}]));
const lists=[{id:'curriculum:small',title:'计算几何',topicPath:['09 高阶拓展'],problems:[{problemId:'geo'}]},
 {id:'curriculum:all',title:'综合训练',topicPath:['09 高阶拓展'],problems:[{problemId:'a'},{problemId:'b'},{problemId:'c'}]},
 {id:'custom:small',title:'My own',topicPath:['09 高阶拓展'],problems:[{problemId:'private'}]}];
const compact=consolidateSmallCurriculum(lists);assert.equal(compact.length,2);assert.equal(compact.find(list=>list.id==='curriculum:all').problems.length,4);assert.equal(compact.find(list=>list.id==='custom:small').problems.length,1);assert.equal(lists[1].problems.length,3);
let calls=0;const api=async()=>{calls++;return {submissions:[{id:'r',codePending:true}],total:1};};const key=submissionQuery();
assert(key.includes('compact=1'));assert.equal(submissionSnapshot(api,'user-a',1,key),undefined);
await loadSubmissionPage(api,'user-a',1,key);await loadSubmissionPage(api,'user-a',1,key);assert.equal(calls,1);
assert.equal(submissionSnapshot(api,'user-a',1,key).submissions[0].id,'r');assert.equal(submissionSnapshot(api,'user-b',1,key),undefined);
assert.equal(submissionSnapshot(api,'user-b:active',1,key),undefined);
console.log('Revision 1.4.29 models: grouping, exclusive XCPC paths, complete papers, public-only list merge, isolated metadata cache passed.');
