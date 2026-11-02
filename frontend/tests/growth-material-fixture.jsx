import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {GrowthPage} from '../src/pages/ProgressPanels.jsx';
import RankingsPage from '../src/pages/CommunityPanel.jsx';
import AvatarFrame from '../src/components/AvatarFrame.jsx';
import MedalEmblem from '../src/components/MedalEmblem.jsx';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';
import '../src/styles/followups-1434.css';

const owner='00000000-0000-4000-8000-000000000010';
const stickerState={owner,revision:1,catalogue:[{id:'gold-fox',rarity:'legendary',shape:'fox'}],units:[],boxes:{}};
let authenticated=false;
const calls=[];
const api=async(path,body)=>{
 calls.push({path,method:body?'POST':'GET'});
 if(path==='stickers')return stickerState;
 if(path==='goals')return {goals:[]};
 if(path==='admin/session'){if(body){if(body.password!=='fixture-password')throw Error('fixture auth denied');authenticated=true;}return {authenticated,configured:true,loginId:'admin'};}
 if(path==='leaderboard/sync')return {queued:false};
 if(path.startsWith('leaderboard?'))return authenticated?{period:new URLSearchParams(path.split('?')[1]).get('period'),date:'2026-11-02',configured:true,status:'ready',hasSnapshot:true,isAdmin:true,self:null,socialAvailable:false,entries:[{userId:'00000000-0000-4000-8000-000000000011',nickname:'其他训练者',rank:1,count:12,publicProgress:{level:12,rankScore:1400}}]}:{period:'daily',configured:true,status:'unconfigured',isAdmin:false,requiresAdminLogin:true,self:null,entries:[],notice:'使用 admin 账号登录管理员控制'};
 throw Error('Unexpected fixture request '+path);
};
function Fixture(){
 const [panel,setPanel]=useState('growth');
 window.growthCheck={setPanel,calls,theme:value=>document.documentElement.dataset.theme=value};
 if(panel==='art')return <div className="material-gallery">{[32,56,180].map(size=><div key={size} style={{display:'flex',alignItems:'center',gap:50}}><div style={{position:'relative',width:size,height:size}}><AvatarFrame index={8}/></div><MedalEmblem index={8} size={size}/><MedalEmblem variant="difficulty" index={9} size={size} label="最高成绩"/></div>)}</div>;
 if(panel==='rankings')return <RankingsPage api={api} ownGrowth={{authority:{owner}}}/>;
 return <GrowthPage api={api} account={{userId:owner,nickname:'训练者'}} profile={{userId:owner,nickname:'训练者'}} goalOverview={{goals:[]}} insights={{growth:{level:100,currentLevelXp:0,nextLevelXp:0,ranked:{tier:'王者',abilityScore:2000,qualified:true}},equippedTitles:[{id:'ac-2000',name:'题海旅人',category:'ac',target:2000},{id:'streak-730',name:'星火不息',category:'streak',target:730},{id:'difficulty-2300',name:'最高成绩',category:'difficulty',target:2300}],knowledge:[],summary:{totalSolved:1112,submissions:2048,activeDays:333,streak:23,completedContests:101,longestStreak:230}}}/>;
}
document.documentElement.dataset.theme='dark';
window.__tbAdmin=true;window.__tbAccountUserId=owner;
const style=document.createElement('style');style.textContent='html,body,#root{height:100%;margin:0}#root{padding:18px;box-sizing:border-box}.material-gallery{display:flex;flex-direction:column;align-items:center;gap:36px;padding:32px;background:var(--panel-base)}';document.head.append(style);
createRoot(document.getElementById('root')).render(<Fixture/>);
