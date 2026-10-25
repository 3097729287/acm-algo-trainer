import PageSearch from '@/components/PageSearch.jsx';
import FilterMenu from '@/components/FilterMenu.jsx';
import {CONTEST_SHELVES} from '@/components/ContestTabs.jsx';
import {matchesShelf} from '@/lib/contestShelves.js';
import BoundedNumber from '@/components/BoundedNumber.jsx';
import DifficultyRange from '@/components/DifficultyRange.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import FolderSelect from '@/components/FolderSelect.jsx';
import {contestOptions} from '@/lib/contestCatalog.js';
import {canonicalKnowledgeName,knowledgeFilterNames} from '@/lib/knowledgeNames.js';
import SortDirection from '@/components/SortDirection.jsx';
import {defaultTrainingDuration} from '@/lib/trainingDuration.js';
import {useEffect,useMemo,useRef,useState} from 'react';
import {Clock,LoaderCircle,Play,RefreshCw,Search} from 'lucide-react';
export const TRAINING_DIFFICULTIES=[['简单',1000,1400,'easy'],['普通',1300,1700,'normal'],['困难',1600,2000,'hard'],['极难',1900,2200,'expert']];
const MODES=[['comprehensive','综合训练'],['topic','专项训练'],['replay','重现赛']];
export default function MockSetup({api,onStarted,onError,activeContest,onResume,categories=[],historyQuery='',onHistoryQuery}) {
 const [config,setConfig]=useState({mode:'comprehensive',count:4,duration:120,min:1000,max:1400,tags:[],platform:'',excludeSolved:true,reviewedOnly:false,rules:'acm',wrongPenalty:20,compilePenalty:false,contest:''});
 const [events,setEvents]=useState([]),[eventsLoading,setEventsLoading]=useState(false),[eventAttempt,setEventAttempt]=useState(0);
 const [eventDescending,setEventDescending]=useState(true);
 const [plan,setPlan]=useState(null),[busy,setBusy]=useState(false),[name,setName]=useState(''),[error,setError]=useState(''),[topic,setTopic]=useState('');
 const sequence=useRef(0),manualDurations=useRef({}),replay=config.mode==='replay';
 useEffect(()=>{if(!replay)return;let alive=true;setEventsLoading(true);api('contests/events').then(value=>{if(alive)setEvents(value.events||[]);}).catch(issue=>{if(alive)setError(issue.message);}).finally(()=>{if(alive)setEventsLoading(false);});return()=>{alive=false;};},[replay,api,eventAttempt]);
 const topicOptions=useMemo(()=>{const build=nodes=>nodes.map(node=>{const children=build(node.children||[]),tags=knowledgeFilterNames(node);return {label:children.length?node.name:canonicalKnowledgeName(node.name),value:node.name,tags,...(children.length?{children}:{})};});return build(categories);},[categories]);
 const topics=useMemo(()=>{const walk=nodes=>nodes.flatMap(node=>[node,...walk(node.children||[])]);return walk(topicOptions);},[topicOptions]);
 const shownEvents=useMemo(()=>events.filter(item=>!config.platform||matchesShelf(item,config.platform)),[events,config.platform]);
 const eventOptions=useMemo(()=>contestOptions(shownEvents,{descending:eventDescending,shelf:config.platform}),[shownEvents,eventDescending,config.platform]);
 const change=(patch,manual=false)=>{setConfig(previous=>{
  const next={...previous,...patch};
  if(manual)manualDurations.current[next.mode]=next.duration;
  if(!Object.hasOwn(patch,'duration')&&['mode','count','min','max'].some(key=>Object.hasOwn(patch,key))){
   const event=events.find(item=>item.name===next.contest);
   next.duration=manualDurations.current[next.mode]??(next.mode==='replay'?(event?.duration||180):defaultTrainingDuration(next));
  }
  return next;
 });setPlan(null);setError('');sequence.current++;};
 function validation(){if(config.mode==='topic'&&!config.tags.length)return '请选择知识点';if(replay&&!config.contest)return '请选择比赛';if(![config.min,config.max,config.duration].every(value=>String(value).trim()!==''&&Number.isFinite(Number(value)))||Number(config.min)>Number(config.max))return '请检查难度范围';if(Number(config.duration)<1||Number(config.duration)>1440)return '时长应为 1–1440 分钟';return '';}
 async function generate(){if(busy||activeContest)return;const issue=validation();if(issue){setError(issue);return;}const seq=++sequence.current;setBusy(true);setError('');try {const value=await api('contests/preview',{...config,count:config.mode==='single'?1:Number(config.count),duration:Number(config.duration),min:Number(config.min),max:Number(config.max),wrongPenalty:Number(config.wrongPenalty),tags:config.mode==='topic'?config.tags:[]});if(sequence.current===seq)setPlan(value.plan);}catch(issue){if(sequence.current===seq)setError(issue.message);}finally{setBusy(false);}}
 async function start(){if(!plan||busy||activeContest)return;setBusy(true);setError('');try{const value=await api('contests/start',{previewId:plan.previewId,ids:plan.slots.map(slot=>slot.id),duration:Number(config.duration),name:name.trim()||plan.name});onStarted(value);}catch(issue){setError(issue.message);onError?.(issue.message,'error');setBusy(false);}}
 return <div className="mock-create"><PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索模拟赛记录" value={historyQuery} onChange={event=>onHistoryQuery?.(event.target.value)}/></label>{replay&&<SortDirection label="切换重现赛排序方向" descending={eventDescending} normalDescending onChange={setEventDescending}/>}<FilterMenu label="训练筛选" active={!!config.platform}>
 <details className="filter-submenu"><summary>比赛分类</summary><div className="filter-choice-grid">{CONTEST_SHELVES.map(([id,label])=><button type="button" key={id} aria-pressed={(config.platform||'all')===id} disabled={busy} onClick={()=>change({platform:id==='all'?'':id})}>{label}</button>)}</div></details>
 {!replay&&<><label className="filter-field"><span>题目数</span><BoundedNumber aria-label="模拟赛题目数" min={1} max={20} value={config.mode==='single'?1:config.count} disabled={busy||config.mode==='single'} onChange={event=>change({count:Number(event.target.value)})}/></label><label className="filter-field"><span>排除已通过</span><input type="checkbox" aria-label="排除已通过题目" disabled={busy} checked={config.excludeSolved} onChange={event=>change({excludeSolved:event.target.checked})}/></label><label className="filter-field"><span>本地完整评测</span><input type="checkbox" aria-label="只选本地完整评测题" disabled={busy} checked={config.reviewedOnly} onChange={event=>change({reviewedOnly:event.target.checked})}/></label></>}
 <label className="filter-field"><span>赛制</span><ThemedSelect aria-label="模拟赛赛制" value={config.rules} disabled={busy} onChange={event=>change({rules:event.target.value})}><option value="acm">ACM</option><option value="xcpc">XCPC</option></ThemedSelect></label><label className="filter-field"><span>错误罚时</span><BoundedNumber aria-label="错误罚时" min={0} max={120} unit="分钟" value={config.wrongPenalty} disabled={busy} onChange={event=>change({wrongPenalty:Number(event.target.value)})}/></label><label className="filter-field"><span>编译错误计罚</span><input type="checkbox" aria-label="编译错误计罚时" disabled={busy} checked={config.compilePenalty} onChange={event=>change({compilePenalty:event.target.checked})}/></label>
 <label className="filter-field"><span>时长</span><BoundedNumber aria-label="模拟赛时长" min={1} max={1440} unit="分钟" value={config.duration} disabled={busy} onChange={event=>change({duration:Number(event.target.value)},true)}/></label><label className="filter-field"><span>名称</span><input aria-label="试卷名称" value={name} disabled={busy} onChange={event=>setName(event.target.value)} maxLength={80}/></label>
 </FilterMenu></PageSearch><section className="create-main">
 {activeContest&&<div className="active-notice"><Clock size={17}/><button className="primary" onClick={onResume}>继续比赛</button></div>}
 <div className="mock-config" data-mode={config.mode}>
 <div className="mock-mode-options" role="group" aria-label="组题方式">{MODES.map(([mode,label])=><button key={mode} type="button" aria-pressed={config.mode===mode} className={config.mode===mode?'active':''} disabled={busy} onClick={()=>change({mode})}><strong>{label}</strong></button>)}</div>
 {!replay&&<div className="difficulty-presets" role="radiogroup" aria-label="默认训练难度">{TRAINING_DIFFICULTIES.map(([title,low,high,tone])=><button key={title} type="button" role="radio" className={`preset-${tone}`} aria-checked={Number(config.min)===low&&Number(config.max)===high} disabled={busy} onClick={()=>change({min:low,max:high})}><i aria-hidden="true"/><span>{title}</span><small>{low}–{high}</small></button>)}</div>}
 <div className="mock-difficulty-row">{!replay&&<><span>难度</span><DifficultyRange value={config} onChange={change} disabled={busy} label="训练难度" minLabel="训练最低难度" maxLabel="训练最高难度"/></>}</div>
 <div className="training-specific-fields">
 {config.mode==='topic'&&<FolderSelect label="专项训练知识点" placeholder="选择知识点" options={topicOptions} value={topic} disabled={busy} onChange={event=>{setTopic(event.target.value);change({tags:topics.find(item=>item.value===event.target.value)?.tags||[]});}}/>}
 {replay&&<><FolderSelect label="重现赛比赛" placeholder={eventsLoading?'正在读取比赛…':'选择比赛'} options={eventOptions} value={config.contest} selectedLabel={events.find(item=>item.name===config.contest)?.displayName||config.contest} disabled={busy||eventsLoading} onChange={event=>{const item=events.find(item=>item.name===event.target.value);change({contest:event.target.value,...(item?{duration:item.duration,rules:item.rules}: {})});}}/>{!eventsLoading&&!events.length&&<button type="button" className="icon-button" aria-label="重新读取比赛" onClick={()=>setEventAttempt(value=>value+1)}><RefreshCw size={16}/></button>}</>}
 </div>
 <div className="create-buttons"><button type="button" className="primary" onClick={generate} disabled={busy||!!activeContest}>{busy?<LoaderCircle size={17} className="spin"/>:<RefreshCw size={17}/>}生成试卷</button>{plan&&<button type="button" className="primary" onClick={start} disabled={busy||!!activeContest}><Play size={17}/>开始训练</button>}<span className="training-duration-summary"><Clock size={15}/>{replay?(events.find(item=>item.name===config.contest)?.count??'—'):config.mode==='single'?1:config.count} 题 · {config.duration} 分钟</span></div>
 </div>
 {error&&<div className="inline-error" role="alert">{error}</div>}
 {plan&&<div className="paper-preview" aria-label="训练试卷预览"><div className="paper-preview-title"><strong>{MODES.find(([mode])=>mode===config.mode)[1]}{config.mode==='topic'?` · ${topic}`:replay?` · ${plan.event?.displayName||config.contest}`:''}</strong><span>{plan.slots.length} 题 · {config.duration} 分钟</span></div><div className="paper-slots">{plan.slots.map((slot,index)=><div className="paper-slot" key={slot.id}><strong>{slot.letter||String.fromCharCode(65+index)}</strong><span>{slot.judgeScope==='local'?'本地评测':'官方样例'}</span></div>)}</div>{plan.selectionNotice&&<p className="selection-notice" role="status">{plan.selectionNotice}</p>}</div>}
 </section></div>;
}
