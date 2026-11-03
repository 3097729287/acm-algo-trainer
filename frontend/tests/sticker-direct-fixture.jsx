import React,{useMemo,useState} from 'react';
import {createRoot} from 'react-dom/client';
import StickerCanvas from '../src/components/StickerCanvas.jsx';
import useDuel from '../src/lib/useDuel.js';
import DuelPage from '../src/pages/DuelPage.jsx';
import '../src/styles/workspace.css';
import '../src/styles/revision.css';
const clone=value=>structuredClone(value),calls=[],pending=[],receipts=new Map();let number=0,loseCancel=true;
const inventories=Object.fromEntries(['A','B'].map(owner=>[owner,{owner,revision:1,placementPolicy:{scale:true},catalogue:[{id:'leaf',shape:'leaf',rarity:'common'},{id:'gem',shape:'gem',rarity:'common'},{id:'spark',shape:'spark',rarity:'common'}],units:[{id:owner+'-leaf',stickerId:'leaf',revision:0,placement:{x:.3,y:.4,angle:0,scale:1}},{id:owner+'-gem',stickerId:'gem',revision:0,placement:null},{id:owner+'-spark',stickerId:'spark',revision:0,placement:null}]}]));
const rooms=Object.fromEntries(['A','B'].map(owner=>[owner,{owner,status:'idle',serverNow:Date.now(),capabilities:{readyCheck:true}}]));
function client(owner){return async(path,body)=>{
 calls.push({id:++number,owner,path,body:clone(body)});
 if(path==='stickers')return clone(inventories[owner]);
 if(path==='stickers/place'){
  if(receipts.has(body.requestId))return clone(receipts.get(body.requestId));
  return new Promise((resolve,reject)=>pending.push({id:number,owner,path,body:clone(body),resolve,reject}));
 }
 if(path==='duel')return {...clone(rooms[owner]),serverNow:Date.now()};
 if(path==='duel/join'){rooms[owner]={...rooms[owner],status:'queued',ticket:body.requestId,queuedAt:Date.now(),serverNow:Date.now()};return clone(rooms[owner]);}
 if(path==='duel/cancel'){
  if(loseCancel){loseCancel=false;throw Object.assign(new Error('isolated connection unavailable'),{status:503});}
  if(rooms[owner].ticket===body.ticket)rooms[owner]={owner,status:'idle',serverNow:Date.now(),capabilities:{readyCheck:true}};
  return clone(rooms[owner]);
 }
 if(path==='duel/poll')return {...clone(rooms[owner]),serverNow:Date.now()};
 throw Error('Unexpected isolated request: '+path);
};}
function complete(id,loss=false){
 const at=pending.findIndex(value=>value.id===id),call=pending.splice(at,1)[0];if(!call)throw Error('Missing pending request');
 const inventory=inventories[call.owner],unit=inventory.units.find(value=>value.id===call.body.unitId);
 if(unit.revision!==call.body.revision){call.reject(Object.assign(Error('isolated revision conflict'),{status:409}));return;}
 const {x,y,angle,scale}=call.body;unit.placement={x,y,angle,scale};unit.revision++;inventory.revision++;
 const value=clone(inventory);receipts.set(call.body.requestId,value);
 if(loss)call.reject(Object.assign(Error('isolated lost placement reply'),{status:503}));else call.resolve(value);
}
function Fixture(){
 const [owner,setOwner]=useState('A'),api=useMemo(()=>client(owner),[owner]),duel=useDuel(api,owner);
 window.directFixture={calls,pending:()=>pending.map(({id,owner,path})=>({id,owner,path})),complete,state:()=>clone(inventories[owner]),owner:setOwner};
 return <><div className="fixture-stickers" style={{height:540,margin:24}}><StickerCanvas owner={owner} api={api}><div style={{height:420}}/></StickerCanvas></div><DuelPage duel={duel} rows={[]}/></>;
}
document.documentElement.dataset.theme='dark';createRoot(document.getElementById('root')).render(<Fixture/>);

const footer=document.createElement('footer');footer.className='app-statusbar';footer.style.cssText='position:fixed;bottom:0;left:0;right:0;z-index:20';document.body.append(footer);
