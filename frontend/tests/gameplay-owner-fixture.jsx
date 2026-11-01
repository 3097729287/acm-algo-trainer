import {createRoot} from 'react-dom/client';
import {useMemo,useState} from 'react';
import useDuel from '../src/lib/useDuel.js';
import DuelPage from '../src/pages/DuelPage.jsx';
import StickerCanvas from '../src/components/StickerCanvas.jsx';
import '../src/styles/workspace.css';
import '../src/styles/revision.css';

const states=Object.fromEntries(['A','B'].map(owner=>[owner,{owner,revision:0,catalogue:[{id:'common-leaf',rarity:'common',shape:'leaf'}],units:[{id:owner+'-unit',stickerId:'common-leaf',revision:0,placement:null}],grants:{}}]));
const rooms=Object.fromEntries(['A','B'].map(owner=>[owner,{owner,status:'idle',serverNow:Date.now()}]));
const pending=[];const reads=new Set();let number=0;
function api(owner){return async(path,body)=>{
 const current=structuredClone(path.startsWith('stickers')?states[owner]:rooms[owner]);
 if(body===undefined&&!reads.delete(owner+':'+path))return current;
 if(path==='duel/poll')return {...current,serverNow:Date.now()};
 return new Promise((resolve,reject)=>pending.push({id:++number,owner,path,body,current,resolve,reject}));
};}
window.gameplayRaces={pending:()=>pending.map(({id,owner,path})=>({id,owner,path})),deferRead:(owner,path)=>reads.add(owner+':'+path),
 finish:id=>{const index=pending.findIndex(p=>p.id===id);const call=pending.splice(index,1)[0];if(!call)throw Error('Missing deferred call');
  if(call.path==='duel/join'){rooms[call.owner]={owner:call.owner,status:'queued',ticket:call.owner+'-ticket',serverNow:Date.now()};call.resolve(structuredClone(rooms[call.owner]));}
  else if(call.path==='stickers/place'){const state=states[call.owner],unit=state.units[0];state.revision++;unit.revision++;unit.placement={x:call.body.x,y:call.body.y,angle:call.body.angle};call.resolve(structuredClone(state));}
  else call.resolve(call.current);
 }};
function Fixture(){
 const [owner,setOwner]=useState('A'),request=useMemo(()=>api(owner),[owner]),duel=useDuel(request,owner);
 return <><header><button onClick={()=>setOwner('A')}>账号 A</button><button onClick={()=>setOwner('B')}>账号 B</button><output aria-label="当前账号">{owner}</output></header><div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:20,height:450}}><DuelPage duel={duel} rows={[]}/><StickerCanvas api={request} owner={owner}><div style={{height:400}}/></StickerCanvas></div></>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
