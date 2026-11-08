import assert from 'node:assert/strict';
import {rankingResponse,rankingHasSnapshot} from '../src/lib/rankingConnection.js';
const scope={owner:'owner-a',period:'daily',today:'2026-11-08'};
const ready={configured:true,status:'ready',hasSnapshot:true,period:'daily',date:'2026-11-08',endpoint:'https://service.example',entries:[{userId:'owner-a',count:7}],self:{userId:'owner-a'}};
const cached={owner:scope.owner,date:scope.today,value:ready};
const unavailable={...ready,status:'unconfigured',hasSnapshot:false,entries:[],self:null};
let tests=0;
const check=(run)=>{run();tests++;};
check(()=>{const value=rankingResponse(null,unavailable,scope);assert.equal(value.status,'offline');assert.equal(value.connectionPending,true);assert.equal(rankingHasSnapshot(value),false);});
check(()=>{const value=rankingResponse(cached,unavailable,scope);assert.equal(value.entries[0].count,7);assert.equal(value.stale,true);assert.equal(value.hasSnapshot,true);assert.equal(value.self.userId,'owner-a');});
for(const [cache,incoming,current] of [
 [{...cached,owner:'other-owner'},unavailable,scope],
 [cached,{...unavailable,period:'weekly'},{...scope,period:'weekly'}],
 [{...cached,date:'2026-11-07'},unavailable,scope],
 [cached,{...unavailable,date:'2026-11-09'},scope],
 [cached,{...unavailable,endpoint:'https://other.example'},scope],
 [cached,{...unavailable,configured:false},scope],
 [cached,{...unavailable,requiresAdminLogin:true},scope],
])check(()=>assert.deepEqual(rankingResponse(cache,incoming,current).entries,[]));
check(()=>{const value=rankingResponse(cached,{...ready,entries:[]},scope);assert.deepEqual(value.entries,[]);assert.equal(value.stale,undefined);assert.equal(rankingHasSnapshot(value),true);});
check(()=>{const value=rankingResponse({...cached,value:{...ready,entries:[]}},unavailable,scope);assert.equal(rankingHasSnapshot(value),false);});
check(()=>{const degraded=rankingResponse(cached,unavailable,scope);const value=rankingResponse({...cached,value:degraded},{...ready,entries:[{userId:'owner-a',count:8}]},scope);assert.equal(value.entries[0].count,8);assert.equal(value.stale,undefined);assert.equal(value.connectionPending,undefined);});
console.log(JSON.stringify({ok:true,checks:tests,ownerPeriodDateAndEndpointIsolation:true,verifiedEmptyPreserved:true,recoveryClearsStaleState:true}));
