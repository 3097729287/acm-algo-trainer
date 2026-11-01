import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {AchievementPanel,DailyTasks,GrowthPage} from '../src/pages/ProgressPanels.jsx';
import AdminDominancePreview,{useAdminDominancePreview} from '../src/components/AdminDominancePreview.jsx';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
import '../src/styles/interaction.css';
import '../src/styles/followups-1434.css';
const rewards=[
 {id:'first',name:'星光代码',description:'北京时间 20–次日 2 点完成一次正式提交',unlocked:true,unlockedAt:'2026-11-01T00:00:00Z',rewardClaimed:false,rewardXp:20},
 {id:'second',name:'周末开卷',description:'周末完成一次正式提交',unlocked:true,unlockedAt:'2026-11-01T00:00:00Z',rewardClaimed:false,rewardXp:30},
 {id:'third',name:'键盘接力',description:'同一天正式提交 10 次',unlocked:true,unlockedAt:'2026-11-01T00:00:00Z',rewardClaimed:true,rewardXp:40},
 {id:'next',name:'再战老友',description:'两次间隔复习均先错误提交后 AC',unlocked:false,target:2,progress:1,rewardXp:30},
];
const tasks=[
 {id:'hard',lane:'fixed',title:'攻坚挑战'}, {id:'ac',lane:'ac',title:'AC'},
 {id:'time',lane:'learning',title:'使用时长'}, {id:'night',lane:'fixed',title:'晚间一题'},
 {id:'review',lane:'review-random',title:'复习'},{id:'base',lane:'fixed',title:'基础巩固'},
].map((task,index)=>({...task,description:'完成练习',target:1,progress:index===0?1:0,completed:index===0,xp:20}));
function Fixture(){
 const[panel,setPanel]=useState('rewards'),[owner,setOwner]=useState('A'),[items,setItems]=useState(rewards),[claims,setClaims]=useState(0);
 const[days,onDays]=useAdminDominancePreview(owner);
 window.followups={setPanel,setOwner,claims,days,theme:value=>document.documentElement.dataset.theme=value};
 if(panel==='growth')return <GrowthPage profile={{nickname:'测试学习者'}} insights={{growth:{level:13,currentLevelXp:10,nextLevelXp:3000,ranked:{tier:'青铜',badge:'tier-1',abilityScore:800}},equippedTitles:[{id:'difficulty-1500',name:'进阶第一步',category:'difficulty',target:1500}],knowledge:[],summary:{totalSolved:108,submissions:195,activeDays:33,streak:23,completedContests:1,longestStreak:23}}}/>;
 if(panel==='admin')return <AdminDominancePreview owner={owner} days={days} actualDays={{daily:2,weekly:3,total:8}} onChange={onDays}/>;
 return <section className="modal" style={{position:'static',width:'100%',maxWidth:1000,margin:'auto',padding:20,background:'var(--panel-base)'}}>{panel==='daily'?<DailyTasks dailyTasks={{date:'2026-11-01',tasks}} onClaim={async()=>{}}/>:<AchievementPanel achievements={items} onClaim={async id=>{setClaims(value=>value+1);await new Promise(resolve=>setTimeout(resolve,80));setItems(previous=>previous.map(item=>item.id===id?{...item,rewardClaimed:true}:item));}}/>}</section>;
}
document.documentElement.dataset.theme='dark';
createRoot(document.getElementById('root')).render(<Fixture/>);
