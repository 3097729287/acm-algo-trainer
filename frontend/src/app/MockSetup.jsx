import PageSearch from '@/components/PageSearch.jsx';
import FilterMenu from '@/components/FilterMenu.jsx';
import {contestShelvesFor} from '@/components/ContestTabs.jsx';
import {matchesShelf} from '@/lib/contestShelves.js';
import {normalizePlatform,rowPlatform} from '@/lib/platformRegistry.js';
import BoundedNumber from '@/components/BoundedNumber.jsx';
import DifficultyRange from '@/components/DifficultyRange.jsx';
import InlineTitle from '@/components/InlineTitle.jsx';
import FolderSelect from '@/components/FolderSelect.jsx';
import {contestOptions} from '@/lib/contestCatalog.js';
import {canonicalKnowledgeName,knowledgeFilterNames} from '@/lib/knowledgeNames.js';
import SortDirection from '@/components/SortDirection.jsx';
import {defaultTrainingDuration} from '@/lib/trainingDuration.js';
import {useEffect,useMemo,useRef,useState} from 'react';
import {Clock,LoaderCircle,Play,RefreshCw,Search} from 'lucide-react';
export const TRAINING_DIFFICULTIES=[['简单',1000,1400,'easy'],['普通',1300,1700,'normal'],['困难',1600,2000,'hard'],['极难',1900,2200,'expert']];
const MODES=[['comprehensive','综合训练'],['topic','专项训练'],['replay','重现赛']];
function PaperTitle({name,onChange,disabled,count,duration}) {
 const [editing,setEditing]=useState(false),[draft,setDraft]=useState(name),finished=useRef(false),button=useRef(null);
 const open=()=>{if(disabled||editing)return;finished.current=false;setDraft(name);setEditing(true);};
 const finish=(save,focus=false)=>{if(finished.current)return;finished.current=true;if(save&&draft.trim())onChange(draft.trim());setEditing(false);if(focus)requestAnimationFrame(()=>button.current?.focus());};
 return <div className="paper-preview-title" onClick={open}>{editing?<input aria-label="模拟赛名称" autoFocus maxLength={80} value={draft} onFocus={event=>event.target.select()} onChange={event=>setDraft(event.target.value)} onBlur={()=>finish(true)} onKeyDown={event=>{if(event.key==='Enter'||event.key==='Escape'){event.preventDefault();event.stopPropagation();finish(event.key==='Enter',true);}}}/>:<button ref={button} type="button" className="paper-title-button" aria-label="重命名模拟赛" disabled={disabled} onClick={open}><strong>{name}</strong></button>}<span>{count} 题 · {duration} 分钟</span></div>;
}
export default function MockSetup({api,onStarted,onError,activeContest,onResume,categories=[],platforms=[],historyQuery='',onHistoryQuery,onPreviewChange}) {
 const [config,setConfig]=useState({mode:'comprehensive',count:4,duration:120,min:1000,max:1400,tags:[],platform:'',excludeSolved:true,reviewedOnly:false,rules:'acm',wrongPenalty:20,compilePenalty:false,contest:''});
 const [events,setEvents]=useState([]),[eventsLoading,setEventsLoading]=useState(false),[eventAttempt,setEventAttempt]=useState(0);
 const [eventDescending,setEventDescending]=useState(true);
 const [plan,setPlan]=useState(null),[busy,setBusy]=useState(false),[name,setName]=useState(''),[error,setError]=useState(''),[topic,setTopic]=useState('');
 const [modeMenu,setModeMenu]=useState(null),[menuRequest,setMenuRequest]=useState(0),modeTriggers=useRef({});
 const sequence=useRef(0),manualDurations=useRef({}),replay=config.mode==='replay';
 useEffect(()=>{onPreviewChange?.(Boolean(plan));},[plan,onPreviewChange]);
 useEffect(()=>()=>onPreviewChange?.(false),[onPreviewChange]);
 useEffect(()=>{if(!replay)return;let alive=true;setEventsLoading(true);api('contests/events').then(value=>{if(alive)setEvents(value.events||[]);}).catch(issue=>{if(alive)setError(issue.message);}).finally(()=>{if(alive)setEventsLoading(false);});return()=>{alive=false;};},[replay,api,eventAttempt]);
 const topicOptions=useMemo(()=>{const build=nodes=>nodes.map(node=>{const children=build(node.children||[]),tags=knowledgeFilterNames(node);return {label:children.length?node.name:canonicalKnowledgeName(node.name),value:node.name,tags,...(children.length?{children}:{})};});return build(categories);},[categories]);
 const topics=useMemo(()=>{const walk=nodes=>nodes.flatMap(node=>[node,...walk(node.children||[])]);return walk(topicOptions);},[topicOptions]);
 const shownEvents=useMemo(()=>{
  if(!config.platform)return events;
  if(['xcpc','XCPC','ACM','lanqiao'].includes(config.platform))return events.filter(item=>matchesShelf(item,config.platform));
  // Training selects an actual source; the folder tree still groups XCPC
  // independently of its host, matching the preview endpoint's source filter.
  const platform=normalizePlatform(config.platform);
  return events.filter(item=>rowPlatform(item)===platform);
 },[events,config.platform]);
 const eventOptions=useMemo(()=>contestOptions(shownEvents,{descending:eventDescending,shelf:config.platform}),[shownEvents,eventDescending,config.platform]);
 const change=(patch,manual=false)=>{setConfig(previous=>{
  const next={...previous,...patch};
  if(manual)manualDurations.current[next.mode]=next.duration;
  if(!Object.hasOwn(patch,'duration')&&['mode','count','min','max'].some(key=>Object.hasOwn(patch,key))){
   const event=events.find(item=>item.name===next.contest);
   next.duration=manualDurations.current[next.mode]??(next.mode==='replay'?(event?.duration||180):defaultTrainingDuration(next));
  }
  return next;
 });setPlan(null);setName('');setError('');sequence.current++;};
 const chooseMode=(mode,forceOpen=false)=>{
  if(config.mode!==mode)change({mode});
  if(mode==='comprehensive')setModeMenu(null);
  else{setModeMenu(previous=>!forceOpen&&previous===mode?null:mode);setMenuRequest(value=>value+1);}
 };
 function validation(){if(config.mode==='topic'&&!config.tags.length)return '请选择知识点';if(replay&&!config.contest)return '请选择比赛';if(![config.min,config.max,config.duration].every(value=>String(value).trim()!==''&&Number.isFinite(Number(value)))||Number(config.min)>Number(config.max))return '请检查难度范围';if(Number(config.duration)<1||Number(config.duration)>1440)return '时长应为 1–1440 分钟';return '';}
 async function generate(){if(busy||activeContest)return;const issue=validation();if(issue){setError(issue);return;}const seq=++sequence.current;setBusy(true);setError('');try {const value=await api('contests/preview',{...config,count:config.mode==='single'?1:Number(config.count),duration:Number(config.duration),min:Number(config.min),max:Number(config.max),wrongPenalty:Number(config.wrongPenalty),tags:config.mode==='topic'?config.tags:[]});if(sequence.current===seq){setPlan(value.plan);if(replay)setEventAttempt(value=>value+1);}}catch(issue){if(sequence.current===seq)setError(issue.message);}finally{setBusy(false);}}
 const paperName=name||`${MODES.find(([mode])=>mode===config.mode)[1]}${config.mode==='topic'?` · ${topic}`:replay?` · ${plan?.event?.displayName||config.contest}`:''}`;
 const range=replay?plan?.difficultyRange:config;
 const rangeText=range?.min!=null&&range?.max!=null?`${range.min}–${range.max}`:plan?'待评估':'—';
 async function start(){if(!plan||busy||activeContest)return;setBusy(true);setError('');try{const value=await api('contests/start',{previewId:plan.previewId,ids:plan.slots.map(slot=>slot.id),duration:Number(config.duration),name:paperName});onStarted(value);}catch(issue){setError(issue.message);onError?.(issue.message,'error');setBusy(false);}}
 return <div className="mock-create"><PageSearch><label className="search-box"><Search size={17}/><input aria-label="搜索模拟赛记录" value={historyQuery} onChange={event=>onHistoryQuery?.(event.target.value)}/></label><FilterMenu label="训练筛选" active={!!config.platform}>
 <section className="mock-filter-categories" aria-label="比赛分类"><span>比赛分类</span><div className="filter-choice-grid">{contestShelvesFor([...platforms,...events]).map(([id,label])=><button type="button" key={id} aria-pressed={(config.platform||'all')===id} disabled={busy} onClick={()=>change({platform:id==='all'?'':id,contest:''})}>{label}</button>)}</div></section>
 {!replay&&<div className="mock-filter-difficulty"><div className="difficulty-presets" role="radiogroup" aria-label="默认训练难度">{TRAINING_DIFFICULTIES.map(([title,low,high,tone])=><button key={title} type="button" role="radio" className={`preset-${tone}`} aria-checked={Number(config.min)===low&&Number(config.max)===high} disabled={busy} onClick={()=>change({min:low,max:high})}><i aria-hidden="true"/><span>{title}</span><small>{low}–{high}</small></button>)}</div><DifficultyRange value={config} onChange={change} disabled={busy} label="训练难度" minLabel="训练最低难度" maxLabel="训练最高难度"/></div>}
 {!replay&&<label className="filter-field"><span>题目数</span><BoundedNumber aria-label="模拟赛题目数" min={1} max={20} value={config.count} disabled={busy} onChange={event=>change({count:Number(event.target.value)})}/></label>}
 <label className="filter-field"><span>错误罚时</span><BoundedNumber aria-label="错误罚时" min={0} max={120} unit="分钟" value={config.wrongPenalty} disabled={busy} onChange={event=>change({wrongPenalty:Number(event.target.value)})}/></label>
 <label className="filter-field"><span>时长</span><BoundedNumber aria-label="模拟赛时长" min={1} max={1440} unit="分钟" value={config.duration} disabled={busy} onChange={event=>change({duration:Number(event.target.value)},true)}/></label>
 <div className="mock-filter-switches">{!replay&&<><label className="filter-field"><span>排除已通过</span><input type="checkbox" aria-label="排除已通过题目" disabled={busy} checked={config.excludeSolved} onChange={event=>change({excludeSolved:event.target.checked})}/></label><label className="filter-field"><span>本地完整评测</span><input type="checkbox" aria-label="只选本地完整评测题" disabled={busy} checked={config.reviewedOnly} onChange={event=>change({reviewedOnly:event.target.checked})}/></label></>}<label className="filter-field"><span>编译错误计罚</span><input type="checkbox" aria-label="编译错误计罚时" disabled={busy} checked={config.compilePenalty} onChange={event=>change({compilePenalty:event.target.checked})}/></label></div>
 </FilterMenu>
 </PageSearch><section className="create-main">
 {activeContest&&<div className="active-notice"><Clock size={17}/><button className="primary" aria-label="继续比赛" onClick={onResume}><Play size={17}/></button></div>}
 <div className="mock-config" data-mode={config.mode}>
 <div className="mock-mode-options" role="group" aria-label="组题方式">{MODES.map(([mode,label])=><button key={mode} ref={node=>{modeTriggers.current[mode]=node;}} type="button" aria-pressed={config.mode===mode} aria-haspopup={mode==='comprehensive'?undefined:'listbox'} aria-expanded={mode==='comprehensive'?undefined:modeMenu===mode} className={config.mode===mode?'active':''} disabled={busy} onClick={()=>chooseMode(mode)} onKeyDown={event=>{if(mode!=='comprehensive'&&['ArrowDown','ArrowUp'].includes(event.key)){event.preventDefault();chooseMode(mode,true);}}}><strong>{label}</strong></button>)}</div>
 {config.mode==='topic'&&<FolderSelect key="topic" externalAnchor={modeTriggers.current.topic} openRequest={modeMenu==='topic'?menuRequest:0} onClose={()=>setModeMenu(null)} label="专项训练知识点" placeholder="选择知识点" options={topicOptions} value={topic} disabled={busy} onChange={event=>{setTopic(event.target.value);change({tags:topics.find(item=>item.value===event.target.value)?.tags||[]});}}/>}
 {replay&&<FolderSelect key="replay" externalAnchor={modeTriggers.current.replay} openRequest={modeMenu==='replay'?menuRequest:0} onClose={()=>setModeMenu(null)} headerActions={<><SortDirection label="切换重现赛排序方向" descending={eventDescending} normalDescending onChange={setEventDescending}/>{!eventsLoading&&!events.length&&<button type="button" className="icon-button" aria-label="重新读取比赛" onClick={()=>setEventAttempt(value=>value+1)}><RefreshCw size={16}/></button>}</>} label="重现赛比赛" placeholder={eventsLoading?'正在读取比赛…':'选择比赛'} options={eventOptions} value={config.contest} selectedLabel={events.find(item=>item.name===config.contest)?.displayName||config.contest} disabled={busy} onChange={event=>{const item=events.find(item=>item.name===event.target.value);change({contest:event.target.value,...(item?{duration:item.duration}: {})});}}/>}
 <div className="create-buttons"><button type="button" className="primary" aria-label="生成试卷" onClick={generate} disabled={busy||!!activeContest}>{busy?<LoaderCircle size={17} className="spin"/>:<RefreshCw size={17}/>}</button>{plan&&<button type="button" className="primary" aria-label="开始训练" onClick={start} disabled={busy||!!activeContest}><Play size={17}/></button>}<span className="training-duration-summary"><Clock size={15}/>{replay?(plan?.slots.length??events.find(item=>item.name===config.contest)?.expectedCount??events.find(item=>item.name===config.contest)?.count??'—'):config.count} 题 · {config.duration} 分钟</span><span className="training-difficulty-summary">难度 {rangeText}</span></div>
 {error&&<div className="inline-error" role="alert">{error}</div>}
 {plan&&<div className="paper-preview" aria-label="训练试卷预览"><PaperTitle key={plan.previewId} name={paperName} onChange={setName} disabled={busy} count={plan.slots.length} duration={config.duration}/><div className="paper-slots">{plan.slots.map((slot,index)=><div className="paper-slot" key={slot.id}><strong>{String.fromCharCode(65+index)}</strong><span><InlineTitle>{slot.title}</InlineTitle></span></div>)}</div>{plan.selectionNotice&&<p className="selection-notice" role="status">{plan.selectionNotice}</p>}</div>}
 </div>
 </section></div>;
}
