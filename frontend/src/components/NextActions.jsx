import {useEffect,useState} from 'react';
import {ArrowRight,BookOpen,Code2,FlaskConical,FolderOpen,History,Target} from 'lucide-react';
import {nextActions} from '@/lib/nextActions.js';
import './NextActions.css';
const icons={review:History,list:FolderOpen,problem:Target,course:FlaskConical,template:Code2,'template-problem':Code2,stretch:Target,contest:BookOpen};
const labels={review:'间隔复习',list:'基础题单',problem:'基础练习',course:'算法实验室',template:'模板','template-problem':'模板练习',stretch:'进阶挑战',contest:'继续比赛'};
export default function NextActions({rows,training,insights,prefs,api,availablePages,activeContest,onNavigate,onTrain}) {
 const [metadata,setMetadata]=useState({lists:[],templates:[]}),[revision,setRevision]=useState(0);
 useEffect(()=>{const refresh=()=>setRevision(value=>value+1);window.addEventListener('tb:training-lists-changed',refresh);return()=>window.removeEventListener('tb:training-lists-changed',refresh);},[]);
 const scope=availablePages.join(',');
 useEffect(()=>{let alive=true;const requests=[['training-lists','lists'],['templates','templates']].filter(([page])=>availablePages.includes(page));Promise.allSettled(requests.map(async([page,key])=>[key,(await api(page))[key]||[]])).then(results=>{if(alive)setMetadata(Object.fromEntries([['lists',[]],['templates',[]],...results.filter(item=>item.status==='fulfilled').map(item=>item.value)]));});return()=>{alive=false;};},[api,scope,revision]);
 const items=nextActions({rows,training,insights:insights||{},prefs,...metadata,availablePages,activeContest});
 return <section className="next-actions" aria-label="下一步推荐做的事"><h2>下一步推荐做的事</h2><div className="next-actions-grid">{items.map(item=>{const Icon=icons[item.kind];return <article key={item.kind} data-recommendation={item.kind}><div><small><Icon size={15}/>{labels[item.kind]}</small><strong>{item.title}</strong><p>{item.reason}</p></div><button type="button" className="icon-button" aria-label={`开始${labels[item.kind]} ${item.title}`} title={item.reason} onClick={()=>['problem','stretch','review','template-problem'].includes(item.kind)?onTrain(item.id):onNavigate(item)}><ArrowRight size={18}/></button></article>;})}</div></section>;
}
