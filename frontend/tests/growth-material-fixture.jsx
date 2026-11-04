import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {GrowthPage} from '../src/pages/ProgressPanels.jsx';
import RankingsPage from '../src/pages/CommunityPanel.jsx';
import AvatarFrame from '../src/components/AvatarFrame.jsx';
import MedalEmblem from '../src/components/MedalEmblem.jsx';
import {StickerArt} from '../src/components/StickerArt.jsx';
import ARTWORK from '../src/lib/stickerArtwork.js';
import PersonalStatistics from '../src/pages/PersonalStatistics.jsx';
import DuelPage from '../src/pages/DuelPage.jsx';
import DuelBannerFrame from '../src/components/DuelBannerFrame.jsx';
import ProfileBadge from '../src/components/ProfileBadge.jsx';
import {TIER_NAMES,RANK_THRESHOLDS} from '../src/lib/rankTiers.js';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';
import '../src/styles/followups-1434.css';

const owner='00000000-0000-4000-8000-000000000010';
const equippedTitles=[{id:'ac-2000',name:'双千传奇',category:'ac',target:2000},{id:'streak-730',name:'星火不息',category:'streak',target:730},{id:'difficulty-2300',name:'最高成绩',category:'difficulty',target:2300}];
const stickerState={owner,revision:1,catalogue:[{id:'gold-fox',rarity:'legendary',shape:'fox'}],units:[],boxes:{}};
let goals=[{id:'goal-one',title:'CF 1600',kind:'cf',deadline:'2027-05-01',currentRating:1000,targetRating:1600,dailyMinutes:60,totalProblems:100},{id:'goal-two',title:'基础练习',kind:'custom',deadline:'2027-06-01',currentRating:800,targetRating:1200,dailyMinutes:30,totalProblems:50}];
const summary={totalSolved:1112,submissions:2048,activeDays:333,streak:23,completedContests:101,longestStreak:230};
let authenticated=false;
const calls=[];
const api=async(path,body)=>{
 calls.push({path,method:body?'POST':'GET'});
 if(path==='stickers')return stickerState;
 if(path==='goals')return structuredClone({goals});
 if(path==='goals/save'){const item={...body,id:body.id||'goal-new'};goals=[...goals.filter(goal=>goal.id!==item.id),item];return structuredClone({goals});}
 if(path==='goals/archive'){goals=goals.filter(goal=>goal.id!==body.id);return structuredClone({goals});}
 if(path==='usage')return {totalSeconds:3600,maxDailySeconds:1800};
 if(path==='admin/session'){if(body){if(body.password!=='fixture-password')throw Error('fixture auth denied');authenticated=true;}return {authenticated,configured:true,loginId:'admin'};}
 if(path==='leaderboard/sync')return {queued:false};
 if(path.startsWith('leaderboard?'))return authenticated?{period:new URLSearchParams(path.split('?')[1]).get('period'),date:'2026-11-02',configured:true,status:'ready',hasSnapshot:true,isAdmin:true,self:null,socialAvailable:false,entries:[{userId:'00000000-0000-4000-8000-000000000011',nickname:'其他训练者',rank:1,count:12,publicProgress:{level:12,rankScore:1400}}]}:{period:'daily',configured:true,status:'unconfigured',isAdmin:false,requiresAdminLogin:true,self:null,entries:[],notice:'使用 admin 账号登录管理员控制'};
 throw Error('Unexpected fixture request '+path);
};
function Fixture(){
 const [tier,setTier]=useState(1),[panel,setPanel]=useState('growth'),[overview,setOverview]=useState({goals});
 window.growthCheck={setTier,setPanel,calls,goals:()=>goals,empty:()=>{goals=[];setOverview({goals});},theme:value=>document.documentElement.dataset.theme=value};
 if(panel==='duel')return <DuelPage titles={equippedTitles} thought={{state:{owner,enabled:false,status:'idle',rating:1000},clock:{current:null},reload:()=>{}}} account={{nickname:'训练者'}} growth={{level:14,ranked:{tier:TIER_NAMES[tier],abilityScore:RANK_THRESHOLDS[tier],qualified:true}}} duel={{state:{status:'idle'},clock:{current:null},act:()=>{},reload:()=>{}}} rows={[]}/>;
 if(panel==='banners')return <div className="banner-gallery">{TIER_NAMES.map((name,index)=><div className="banner-example" key={name}><div className="duel-lobby-identity"><DuelBannerFrame rank={{tier:name}}/><ProfileBadge compact={false} growth={{level:14,ranked:{tier:name}}} nickname={name} showXp={false}/><div className="duel-lobby-rank"><MedalEmblem index={index} size={96}/></div></div></div>)}</div>;
 if(panel==='art')return <div className="material-gallery">{Array.from({length:9},(_,tier)=><div className="rank-material-pair" data-tier={tier} key={tier}><div style={{position:'relative',width:150,height:150}}><AvatarFrame index={tier}/></div><MedalEmblem index={tier} size={150}/></div>)}</div>;
 if(panel==='stickers')return <div className="cartoon-gallery">{Object.keys(ARTWORK).map(shape=><StickerArt key={shape} item={{shape,rarity:'legendary'}} size={128}/>)}</div>;
 if(panel==='statistics')return <PersonalStatistics api={api} insights={{summary}} account={{createdAt:'2026-10-01T12:00:00Z'}}/>;
 if(panel==='rankings')return <RankingsPage api={api} ownGrowth={{authority:{owner}}}/>;
 return <GrowthPage api={api} account={{userId:owner,nickname:'训练者'}} profile={{userId:owner,nickname:'训练者'}} goalOverview={overview} onGoalsChanged={async()=>setOverview(await api('goals'))} insights={{growth:{level:100,currentLevelXp:0,nextLevelXp:0,ranked:{tier:'王者',abilityScore:2000,qualified:true}},equippedTitles:[{id:'ac-2000',name:'双千传奇',category:'ac',target:2000},{id:'streak-730',name:'星火不息',category:'streak',target:730},{id:'difficulty-2300',name:'最高成绩',category:'difficulty',target:2300}],knowledge:[],summary}}/>;
}
document.documentElement.dataset.theme='dark';
window.__tbAdmin=true;window.__tbAccountUserId=owner;
const style=document.createElement('style');style.textContent='.banner-gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;padding:30px;background:var(--panel-base)}.banner-example{display:flex;justify-content:center}.banner-example .duel-lobby-identity{width:300px;min-height:460px;padding:66px 30px 52px;--duel-portrait:152px;gap:24px}html,body,#root{height:100%;margin:0}#root{padding:18px;box-sizing:border-box}.material-gallery{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;padding:26px;background:var(--panel-base)}.rank-material-pair{display:flex;justify-content:center;align-items:center;gap:12px;min-height:200px}.rank-material-pair .avatar-rank-frame{inset:0;width:100%;height:100%}.cartoon-gallery{display:grid;grid-template-columns:repeat(9,128px);justify-content:center;gap:18px;padding:24px;background:var(--panel-base)}';document.head.append(style);
createRoot(document.getElementById('root')).render(<Fixture/>);

const footer=document.createElement('footer');footer.className='app-statusbar';footer.style.cssText='position:fixed;bottom:0;left:0;right:0;z-index:20';document.body.append(footer);
