import React,{useCallback,useState} from 'react';
import {createRoot} from 'react-dom/client';
import StickerCanvas from '../src/components/StickerCanvas.jsx';
import {SocialNotifications} from '../src/components/Social.jsx';
import {AchievementPanel,DailyTasks} from '../src/pages/ProgressPanels.jsx';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/unified.css';
const owner='11111111-1111-4111-8111-111111111111',other='22222222-2222-4222-8222-222222222222';
window.__tbAccountUserId=owner;document.documentElement.dataset.theme='dark';
const data=window.rewardFixtureData,stamp=new Date().toISOString(),key='sticker-reward-fixture';
let saved;try{saved=JSON.parse(localStorage.getItem(key));}catch{}
const remote=saved||{owner,revision:0,catalogue:data.catalogue,boxPolicy:{firstLevel:5},packPolicy:data.packPolicy,boxes:Object.fromEntries(data.boxes.map(box=>[box.id,box])),units:[{id:'33333333-3333-4333-8333-333333333333',stickerId:'common-spark',revision:0,placement:null},{id:'55555555-5555-4555-8555-555555555555',stickerId:'achievement-duck',revision:0,placement:null}],replies:[],operations:{}};
const calls=[],save=()=>localStorage.setItem(key,JSON.stringify(remote));let loseBoxResponse=true;
const clone=value=>structuredClone(value);
async function api(path,body){
 calls.push({path,body:clone(body)});
 if(path==='stickers')return clone(remote);
 if(path==='stickers/open-packs'){
  if(remote.operations[body.requestId])return clone(remote.operations[body.requestId]);
  const selected=Object.values(remote.boxes).filter(box=>!box.openedAt&&box.rarity===body.rarity).slice(0,body.count);
  if(selected.length!==body.count)throw new Error('卡包数量不足');
  for(const box of selected){box.openedAt=Date.now();box.drops=Array.from({length:box.quantity},(_,index)=>{
   const rarity=index===0?(box.guarantee||'common'):['rare','common'][index%2];
   const sticker=remote.catalogue.find(item=>item.rarity===rarity&&!item.id.startsWith('achievement-'));
   const unit={id:crypto.randomUUID(),stickerId:sticker.id,revision:0,placement:null};remote.units.push(unit);return {...unit,rarity};
  });remote.revision++;}
  const result={...clone(remote),opening:{rarity:body.rarity,packs:clone(selected),drops:clone(selected.flatMap(box=>box.drops))}};
  remote.operations[body.requestId]=result;save();
  if(loseBoxResponse){loseBoxResponse=false;throw new Error('测试：开包回执暂未收到，请重试');}return clone(result);
 }
 if(path==='social/comments'){
  if(remote.operations[body.requestId])return clone(remote.operations[body.requestId]);
  if(body.targetId!==other)throw new Error('Wrong recipient');
  let gift=null;if(body.gift){const at=remote.units.findIndex(unit=>unit.id===body.gift.unitId&&unit.revision===body.gift.revision);if(at<0)throw new Error('库存已变化');const [unit]=remote.units.splice(at,1);gift={...remote.catalogue.find(item=>item.id===unit.stickerId),unitId:unit.id};remote.revision++;}
  const result={id:body.requestId,text:body.text,createdAt:stamp,...(gift?{gift}:{})};remote.replies.push(result);remote.operations[body.requestId]=result;save();return clone(result);
 }
 throw new Error('Unexpected reward fixture call '+path);
}
function Fixture(){
 const snapshot=()=>({available:true,totalLikes:0,todayLikes:0,notifications:[{id:'44444444-4444-4444-8444-444444444444',actor:{userId:other,nickname:'训练者乙'},kind:'comment',text:'送你一点好运',createdAt:stamp,read:true,myReplies:clone(remote.replies)}],unreadCount:0});
 const [social,setSocial]=useState(snapshot),refresh=useCallback(()=>{setSocial(snapshot());return Promise.resolve();},[]);
 const achievements=[{id:'fixed',name:'榜首切磋',description:'给今日排行榜第一名留言“就这?”',target:1,progress:0,unlocked:false,rewardXp:0,rewardSticker:remote.catalogue.find(item=>item.id==='achievement-duck')},{id:'xp',name:'五湖四海',description:'给五位训练者赠送贴纸',target:5,progress:2,unlocked:false,rewardXp:35}];
 const tasks=[{id:'routine-xp',lane:'ac',title:'AC',description:'AC 2 道不同题目',target:2,progress:1,xp:30,stickerRarity:'rare'},{id:'challenge-xp',lane:'fixed',title:'攻坚挑战',description:'首次 AC 一道新题',target:1,progress:0,xp:100,stickerRarity:'legendary'},...['common','rare','epic','legendary'].map(rarity=>({id:rarity,lane:'fixed',title:rarity+' 贴纸任务',description:'完成后领取贴纸',target:1,progress:0,xp:0,stickerRarity:rarity,rewardPack:{rarity}}))];
 window.rewardFixture={calls,state:()=>clone(remote)};
 return <div style={{padding:20}}><div style={{height:330,position:'relative'}}><StickerCanvas owner={owner} api={api}><div style={{padding:40}}>成长</div></StickerCanvas></div><AchievementPanel achievements={achievements}/><DailyTasks dailyTasks={{date:'2026-11-02',tasks}}/><SocialNotifications social={{owner,snapshot:social,refresh}} api={api}/></div>;
}
createRoot(document.getElementById('root')).render(<React.StrictMode><Fixture/></React.StrictMode>);

const footer=document.createElement('footer');footer.className='app-statusbar';footer.style.cssText='position:fixed;bottom:0;left:0;right:0;z-index:20';document.body.append(footer);
