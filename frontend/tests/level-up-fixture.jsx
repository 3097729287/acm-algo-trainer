import React,{useCallback,useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import * as Icons from 'lucide-react';
import LevelUpDialog from '../src/components/LevelUpDialog.jsx';
import useLevelUp from '../src/lib/useLevelUp.js';
import {protectGrowth,mergeLevelNotices} from '../src/lib/levelNotices.js';
import {PAGE_UNLOCKS,canOpenPage} from '../src/lib/featureUnlocks.js';
import '../src/styles/workspace.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
const read=(name,fallback)=>{try{return JSON.parse(localStorage.getItem('level-fixture:'+name)||'null')??fallback;}catch{return fallback;}};
const make=(owner,level,revision,epoch='server-first')=>({confirmed:true,authority:{owner,epoch,revision},level,currentLevelXp:70,nextLevelXp:200*level,totalXp:100*level*(level-1)+70,levelCap:100});
const pages=PAGE_UNLOCKS.map(item=>({...item,icon:Icons[{mine:'Target','training-lists':'FolderOpen',library:'Library',rankings:'ListOrdered',competitions:'Flag',mock:'Clock',paths:'FlaskConical',templates:'Code2',lectures:'BookOpen',growth:'ChartNoAxesCombined',activity:'CalendarDays',records:'History',settings:'Settings'}[item.id]]}));
function Harness(){
 const [owner,setOwner]=useState(()=>read('owner','first-account')),[growth,setGrowth]=useState(()=>read('growth',make(read('owner','first-account'),1,1))),[preferences,storePreferences]=useState(()=>read('prefs:'+read('owner','first-account'),{}));
 const [blocked,setBlocked]=useState(()=>read('blocked',false)),[other,setOther]=useState(false),[immersive,setImmersive]=useState(false),[theme,setTheme]=useState('dark'),[font,setFont]=useState(15),[collapsed,setCollapsed]=useState(false),[savedFailure,setSavedFailure]=useState(false),[page,setPage]=useState('mine');
 const retired=useRef(new Set()),latest=useRef({owner,growth,preferences});latest.current={owner,growth,preferences};
 const setPreferences=useCallback(update=>storePreferences(previous=>{const value=typeof update==='function'?update(previous):update;localStorage.setItem('level-fixture:prefs:'+latest.current.owner,JSON.stringify(value));return value;}),[]);
 const level=useLevelUp({owner,growth,preferences,preferencesReady:true,setPreferences,blocked:blocked||other||immersive});
 const usable=!blocked&&!other&&!immersive&&!document.hidden&&document.hasFocus();
 useEffect(()=>{document.documentElement.dataset.theme=theme;document.documentElement.style.fontSize=font+'px';},[theme,font]);
 useEffect(()=>{if(!usable||level.dialog||!level.feedback.length)return;const timer=setTimeout(level.clearFeedback,1400);return()=>clearTimeout(timer);},[usable,level.dialog,level.feedback]);
 window.levelFixture={
  emit:(newLevel,revision,options={})=>setGrowth(previous=>{const value=protectGrowth({growth:previous},{growth:make(options.owner||latest.current.owner,newLevel,revision,options.epoch||'server-first')},latest.current.owner,retired.current).growth;localStorage.setItem('level-fixture:growth',JSON.stringify(value));return value;}),
  block:value=>{setBlocked(value);localStorage.setItem('level-fixture:blocked',JSON.stringify(value));},other:setOther,immersive:setImmersive,
  switchOwner:(id,newLevel=11)=>{retired.current=new Set();setOwner(id);localStorage.setItem('level-fixture:owner',JSON.stringify(id));setGrowth(make(id,newLevel,1,'new-account'));localStorage.setItem('level-fixture:growth',JSON.stringify(make(id,newLevel,1,'new-account')));storePreferences(read('prefs:'+id,{}));},
  theme:setTheme,font:setFont,collapsed:setCollapsed,failSaving:setSavedFailure,
  snapshot:()=>({owner:latest.current.owner,preferences:mergeLevelNotices(latest.current.preferences),growth:latest.current.growth,dialog:level.dialog,page,feedback:level.feedback,remoteSaveFailed:savedFailure}),
 };
 return <main style={{padding:20}}><h1>等级提示隔离验证</h1><p>{owner}</p><label>练习草稿<textarea aria-label="练习草稿" defaultValue="private fixture draft"/></label><button type="button" aria-label="离开编辑器">离开编辑器</button><nav aria-label="隔离导航" data-collapsed={collapsed}>{pages.filter(item=>canOpenPage(item.id,growth.level,preferences)).map(item=><button type="button" key={item.id} aria-label={item.label} className={'nav-item '+(usable&&!level.dialog&&level.feedback.includes(item.id)?'level-new-entry':'')} onClick={()=>setPage(item.id)}>{item.label}</button>)}</nav>{other&&<section role="dialog" aria-modal="true" aria-label="其它对话框"><button type="button" onClick={()=>setOther(false)}>关闭</button></section>}{level.dialog&&<LevelUpDialog pages={pages} preferences={preferences} notice={level.dialog} onPresented={level.markPresented} onClose={level.close} onOpen={setPage}/>}</main>;
}
createRoot(document.getElementById('root')).render(<Harness/>);
