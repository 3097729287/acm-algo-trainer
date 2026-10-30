import {useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import ExperienceChallenge from '../src/components/ExperienceChallenge.jsx';
import useLevelUp from '../src/lib/useLevelUp.js';
import LevelUpDialog from '../src/components/LevelUpDialog.jsx';
import {availablePages} from '../src/lib/featureUnlocks.js';
import '../src/styles/workspace.css';
import '../src/styles/revision.css';

const OWNER='11111111-1111-4111-8111-111111111111',OTHER='22222222-2222-4222-8222-222222222222';
const fresh=owner=>({owner,policyVersion:1,eligible:true,promptRequired:true,seenVersion:0,choice:null,status:'offered',problemId:null,allNavigationUnlocked:false,awardedXp:0});
let fact=new URLSearchParams(location.search).has('noPolicy')?null:fresh(OWNER),revision=0,release=null;
window.__tbAccountUserId=OWNER;
const pendingChoice=new URLSearchParams(location.search).get('pending');
if(['beginner','experienced'].includes(pendingChoice))window.__tbExperienceChoicePending={owner:OWNER,choice:pendingChoice};
const value=(owner,level=1)=>({level,totalXp:level===5?500:0,currentLevelXp:0,nextLevelXp:level===5?1000:100,confirmed:true,authority:{owner,epoch:owner,revision:++revision},experienceChallenge:fact?.owner===owner?{...fact}:undefined});
window.challengeFixture={writes:[],opened:[],hold:false};
function Fixture(){
 const [owner,setOwner]=useState(OWNER),[growth,setGrowth]=useState(()=>value(OWNER)),[preferences,setPreferences]=useState({levelNoticeVersion:0,levelNoticeSeen:0,levelNoticePending:0}),[practicing,setPracticing]=useState(false),[open,setOpen]=useState(false),[mount,setMount]=useState(0);
 const level=useLevelUp({owner,growth,preferences,preferencesReady:true,setPreferences,blocked:practicing||open});
 const api=async(path,body)=>{
  if(path!=='experience-challenge')throw Error('unexpected fixture API '+path);
  if(preferences.levelNoticeVersion!==1)throw Error('Challenge preceded confirmed baseline');
  window.challengeFixture.writes.push({owner,path,body});
  const expected=owner;
  if(window.challengeFixture.hold)await new Promise(resolve=>{release=resolve;});
  const response=fresh(expected);response.seenVersion=1;response.promptRequired=false;
  if(body.action==='choose'){response.choice=body.choice;response.status=body.choice==='experienced'?'active':'beginner';response.problemId=body.choice==='experienced'?'template-drill:binary-search:1':null;}
  fact=response;
  return {challenge:response,growth:value(expected)};
 };
 Object.assign(window.challengeFixture,{
  prefs:()=>preferences,growth:()=>growth,
  remount:()=>{setGrowth(value(owner,growth.level));setMount(n=>n+1);},
  noPolicy:()=>{fact=null;setGrowth(value(owner));},
  switchOwner:()=>{window.__tbAccountUserId=OTHER;fact={...fresh(OTHER),eligible:false,promptRequired:false};setOwner(OTHER);setGrowth(value(OTHER,6));setPreferences({levelNoticeVersion:1,levelNoticeSeen:6,levelNoticePending:0});},
  release:()=>{window.challengeFixture.hold=false;release?.();},
  pass:()=>{fact={...fact,status:'passed',eligible:false,allNavigationUnlocked:true,awardedXp:500};setGrowth(value(owner,5));},
  theme:theme=>{document.documentElement.dataset.theme=theme;},
 });
 return <main><p data-owner>{owner}</p><p data-level>{growth.level}</p><p data-navigation>{availablePages(growth.level,{},growth.experienceChallenge||{}).join(',')}</p>
  <button type="button" onClick={()=>setPracticing(false)}>返回列表</button>
  <ExperienceChallenge key={owner+':'+mount} owner={owner} offer={growth.experienceChallenge} ready={preferences.levelNoticeVersion===1} blocked={Boolean(level.dialog)||practicing||open} api={api} onOpenChange={setOpen} onGrowth={setGrowth} onOpen={async id=>{window.challengeFixture.opened.push({owner,id});setPracticing(true);}}/>
  {level.dialog&&<LevelUpDialog notice={level.dialog} pages={[]} preferences={preferences} onPresented={level.markPresented} onClose={level.close} onOpen={()=>{}}/>}
 </main>;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
