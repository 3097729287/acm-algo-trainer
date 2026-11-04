import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import RankingsPage from '../src/pages/CommunityPanel.jsx';
import DuelPage from '../src/pages/DuelPage.jsx';
import StickerCanvas from '../src/components/StickerCanvas.jsx';
import ProfileBadge from '../src/components/ProfileBadge.jsx';
import {TIER_NAMES,RANK_THRESHOLDS} from '../src/lib/rankTiers.js';
import {trainingDay} from '../src/lib/trainingDate.js';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';
import '../src/styles/followups-160.css';
const owner='10000000-0000-4000-8000-000000000001',date=trainingDay();
let panel='rankings',inventory={owner,revision:1,catalogue:window.reviewCatalogue||[],capabilities:{scenes:true},placementPolicy:{scale:true},units:(window.reviewCatalogue||[]).filter(item=>item.kind!=='background'&&['epic','legendary'].includes(item.rarity)).map((item,index)=>({id:'u-'+item.id,stickerId:item.id,revision:1,placement:{x:.08+index%6*.167,y:.11+Math.floor(index/6)*.18,angle:0,scale:1.4}}))};
const avatar='data:image/svg+xml;base64,'+btoa('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="#6b8e95"/><circle cx="50" cy="48" r="25" fill="#e4c9b3"/></svg>');
const growth={level:14,currentLevelXp:45,nextLevelXp:100,ranked:{tier:'青铜',qualified:true,abilityScore:1050}};
const entries=['xxxg','将去未还','Zane','Rei'].map((nickname,index)=>({userId:index?owner.slice(0,-1)+(index+1):owner,nickname,rank:index+1,count:[98,45,13,5][index],likes:{total:[10,6,6,5][index],likedToday:index===0},publicProgress:{level:14-index,rankTier:index===1?'铂金':'青铜',rankScore:index===1?1480:1030},online:index===0,activity:'查看排行榜中'}));
async function api(path,body){
 if(path==='stickers')return structuredClone(inventory);
 if(path==='stickers/place'){const unit=inventory.units.find(item=>item.id===body.unitId);unit.placement={x:body.x,y:body.y,angle:body.angle,scale:body.scale};unit.revision++;inventory.revision++;return structuredClone(inventory);}
 if(path.startsWith('leaderboard?'))return {configured:true,status:'ready',hasSnapshot:true,period:new URLSearchParams(path.split('?')[1]).get('period'),date,self:entries[0],entries,socialAvailable:true};
 if(path==='leaderboard/sync')return {};
 if(path.startsWith('duel/board?'))return {owner,mode:new URLSearchParams(path.split('?')[1]).get('mode'),date,entries:entries.map(item=>({...item,rating:1000+item.count})),records:[{id:'finished-fixture',finishedAt:Date.now()-360000,winner:owner,players:entries.slice(0,2).map((item,index)=>({...item,change:index?-14:16}))}],next:null};
 if(path.startsWith('presence/'))return {members:[]};
 if(path.startsWith('avatars/'))return {};
 throw new Error('Unexpected isolated request '+path);
}
const thought={api,state:{owner,status:'idle',enabled:false,rating:1000},clock:{current:null},reload:()=>{},act:()=>{}},duel={state:{owner,status:'idle',rating:1000},clock:{current:null},reload:()=>{},act:()=>{}};
function Fixture(){const [view,setView]=useState('rankings'),[account,setAccount]=useState(owner);panel=view;window.uiReview={show:setView,inventory:()=>inventory,overlap:()=>{inventory={...inventory,revision:inventory.revision+1,units:inventory.units.map((unit,index)=>({...unit,placement:{...unit.placement,x:index<2?.5:.05+(index%6)*.16,y:index<2?.5:.08+Math.floor(index/6)*.18}}))};window.dispatchEvent(new CustomEvent('tb:sticker-rewards',{detail:{inventory}}));},switchOwner:()=>{inventory={...inventory,owner:'other-account',units:[]};setAccount('other-account');}};return <main className="fixture-root">{view==='rankings'?<RankingsPage api={api} ownGrowth={growth}/>:view==='duel'?<DuelPage api={api} duel={duel} thought={thought} account={{userId:owner,nickname:'xxxg'}} rows={[]} growth={growth}/>:view==='frames'?<div className="frames-preview">{TIER_NAMES.map((name,index)=><div key={name}><ProfileBadge nickname={name} compact={false} showXp={false} growth={{...growth,ranked:{tier:name,qualified:true,abilityScore:RANK_THRESHOLDS[index]}}}/></div>)}</div>:<section className="growth-account-hero sticker-fixture"><StickerCanvas api={api} owner={account}><div style={{height:700,pointerEvents:'none'}}/></StickerCanvas></section>}</main>;}
document.documentElement.dataset.theme='dark';document.body.style.margin=0;
const style=document.createElement('style');style.textContent='html,body,#root{height:100%;margin:0}.fixture-root{height:100dvh;display:flex;flex-direction:column;padding:22px 28px 60px;box-sizing:border-box;background:var(--panel-base);color:var(--text)}.sticker-fixture{width:100%;flex:1;min-height:700px}.frames-preview{display:grid;grid-template-columns:repeat(3,1fr);gap:70px;justify-items:center;padding:50px}.frames-preview .profile-badge{flex-direction:column;gap:45px;border:0;background:none}.frames-preview .profile-avatar-button{width:145px;height:145px}.frames-preview .profile-avatar-face{width:68%;height:68%}.frames-preview .profile-nickname{font-size:20px}';document.head.append(style);
createRoot(document.getElementById('root')).render(<Fixture/>);
const footer=document.createElement('footer');footer.className='app-statusbar';footer.style.cssText='position:fixed;bottom:0;left:0;right:0;z-index:20';document.body.append(footer);
