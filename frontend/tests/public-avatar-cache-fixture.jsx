import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {flushSync} from 'react-dom';
import usePublicAvatar from '../src/lib/usePublicAvatar.js';
import RankingsPage from '../src/pages/CommunityPanel.jsx';
const OWNER='11111111-1111-4111-8111-111111111111',TARGET='22222222-2222-4222-8222-222222222222';
window.__tbAccountUserId=OWNER;window.__tbAccount={userId:OWNER,nickname:'Original self'};
const assets={};
for(const [name,color] of [['a','#3355aa'],['b','#55aa33']]) {
 const canvas=document.createElement('canvas');canvas.width=4;canvas.height=4;
 const ctx=canvas.getContext('2d');ctx.fillStyle=color;ctx.fillRect(0,0,4,4);
 const data=canvas.toDataURL('image/png');
 const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(data)))].map(v=>v.toString(16).padStart(2,'0')).join('');
 assets[name]={avatarData:data,avatarHash:hash};
}
let fail=new URLSearchParams(location.search).has('fail'),responseAsset=null,failures=0,boardDelay=0;
window.boardCalls=[];
window.avatarCalls=[];window.firstAvatarRenders=[];
const api=async path=>{
 if(path.startsWith('leaderboard/avatar?')) {
  const hash=new URLSearchParams(path.split('?')[1]).get('hash');window.avatarCalls.push(hash);
  await new Promise(resolve=>setTimeout(resolve,100));
  if(fail||failures-->0)throw new Error('Isolated network failure');
  if(responseAsset)return assets[responseAsset];
  const asset=Object.values(assets).find(item=>item.avatarHash===hash);
  return asset||{avatarData:'',avatarHash:null};
 }
 if(path.startsWith('leaderboard?')){const period=new URLSearchParams(path.split('?')[1]).get('period');window.boardCalls.push(period);await new Promise(resolve=>setTimeout(resolve,boardDelay));return {configured:true,hasSnapshot:true,status:'ready',date:new Date().toISOString().slice(0,10),period,entries:[{userId:OWNER,nickname:'Old board nickname',rank:1,count:3,publicProgress:{level:1}},{userId:TARGET,nickname:'Other person',avatarHash:assets.a.avatarHash,rank:2,count:2,publicProgress:{level:1}}],self:{userId:OWNER},socialAvailable:false};}
 throw new Error('Unexpected isolated API '+path);
};
function Probe({id,hash}) {
 const image=usePublicAvatar(api,id,hash);
 const [first]=useState(()=>{window.firstAvatarRenders.push(Boolean(image));return true;});
 return image?<img src={image} alt="Cached public avatar" data-first={first}/>:<span data-empty="true"/>;
}
function Fixture(){
 const [config,setConfig]=useState({show:true,asset:'a',id:TARGET,board:false,revision:0,own:assets.a.avatarData});
 window.publicAvatarFixture={assets,OWNER,TARGET,server(change){if('asset' in change)responseAsset=change.asset;if('failures' in change)failures=change.failures;if('delay' in change)boardDelay=change.delay;},configure(change){flushSync(()=>setConfig(old=>({...old,...change,revision:old.revision+1})));},fail(value){fail=value;},rename(name){window.__tbAccount.nickname=name;flushSync(()=>setConfig(old=>({...old,revision:old.revision+1})));}};
 return config.board?<RankingsPage api={api} socialState={{snapshot:{activity:[]}}} avatarData={config.own} ownGrowth={{level:1}}/>:config.show?<div key={config.id}><Probe id={config.id} hash={assets[config.asset]?.avatarHash||null}/><Probe id={config.id} hash={assets[config.asset]?.avatarHash||null}/></div>:null;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
