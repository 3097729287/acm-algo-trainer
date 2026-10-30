import assert from 'node:assert/strict';
import {createCalendarCatalogReader} from '../src/lib/calendarCatalogRefresh.js';

const pending=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};};
function fixture(){let owner='A';const calls=[],applied=[];const reader=createCalendarCatalogReader({api:path=>{const value=pending();calls.push({path,...value});return value.promise;},apply:(data,account)=>applied.push({data,account}),currentOwner:()=>owner});return {reader,calls,applied,owner:value=>{owner=value;}};}
{
 const f=fixture(),a=f.reader.refresh('A'),b=f.reader.refresh('A');
 assert.notEqual(f.calls[0].path,f.calls[1].path,'a new import read cannot share a pre-import pending response');
 f.calls[1].resolve({rows:['new B']});assert.equal(await b,true);
 f.calls[0].resolve({rows:['old A']});assert.equal(await a,true);
 assert.deepEqual(f.applied,[{data:{rows:['new B']},account:'A'}],'late A cannot overwrite B rows');
}
{
 const f=fixture(),a=f.reader.refresh('A');f.owner('B');f.calls[0].resolve({rows:['private A']});
 assert.equal(await a,false);assert.deepEqual(f.applied,[]);
 assert.equal(await f.reader.refresh('A'),false);assert.equal(f.calls.length,1);
}
{
 const f=fixture(),a=f.reader.refresh('A');f.reader.invalidate();f.calls[0].resolve({rows:['unmounted']});
 assert.equal(await a,false);assert.deepEqual(f.applied,[]);
 const b=f.reader.refresh('A');f.calls[1].resolve({rows:['remounted']});assert.equal(await b,true);
}
{
 const f=fixture();let current=true;const a=f.reader.refresh('A',{isCurrent:()=>current});current=false;
 f.calls[0].resolve({rows:['closed intent']});assert.equal(await a,false);assert.deepEqual(f.applied,[]);
}
{
 const f=fixture(),a=f.reader.refresh('A'),b=f.reader.refresh('A');f.calls[0].reject(new Error('old failure'));
 f.calls[1].resolve({rows:['new success']});assert.equal(await b,true);assert.equal(await a,true);
 assert.deepEqual(f.applied,[{data:{rows:['new success']},account:'A'}]);
}
console.log('Calendar catalog: fresh reads, B over late A, account switch, unmount, cancelled intent and obsolete errors passed.');
