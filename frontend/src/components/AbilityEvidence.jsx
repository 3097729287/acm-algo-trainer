import {useEffect,useId,useLayoutEffect,useRef,useState} from 'react';
import {createPortal} from 'react-dom';
import {Info,X} from 'lucide-react';
import './AbilityEvidence.css';

const SOURCE_NAMES={'official-cf':'Codeforces 官方','official':'平台官方','reviewed':'人工核对','estimated-cf-band':'跨平台估计','cross-platform':'跨平台估计','estimated':'估算','unknown':'待核实'};
export default function AbilityEvidence({rank,rows=[]}) {
 const [open,setOpen]=useState(false),[position,setPosition]=useState({left:12,top:12});
 const trigger=useRef(null),panel=useRef(null),id=useId();
 useLayoutEffect(()=>{
  if(!open)return;
  const place=()=>{
   const box=trigger.current?.getBoundingClientRect(),content=panel.current;
   if(!box||!content)return;
   const width=content.offsetWidth,height=content.offsetHeight;
   const left=Math.max(12,Math.min(box.right-width,innerWidth-width-12));
   const below=box.bottom+8,top=below+height<=innerHeight-12?below:Math.max(12,Math.min(box.top-height-8,innerHeight-height-12));
   setPosition(previous=>previous.left===left&&previous.top===top?previous:{left,top});
  };
  place();panel.current?.focus({preventScroll:true});
  window.addEventListener('resize',place);window.addEventListener('scroll',place,true);
  return()=>{window.removeEventListener('resize',place);window.removeEventListener('scroll',place,true);};
 },[open,rank]);
 useEffect(()=>{
  if(!open)return;
  const close=()=>{setOpen(false);trigger.current?.focus({preventScroll:true});};
  const key=event=>{if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();close();}};
  const outside=event=>{if(!panel.current?.contains(event.target)&&!trigger.current?.contains(event.target))setOpen(false);};
  window.addEventListener('keydown',key,true);document.addEventListener('pointerdown',outside);
  return()=>{window.removeEventListener('keydown',key,true);document.removeEventListener('pointerdown',outside);};
 },[open]);
 if(!rank?.model)return null;
 const names=new Map(rows.map(row=>[row.id,[row.contest,row.problem,row.title].filter(Boolean).join(' ? ')]));
 const recent=rank.recentPerformance||{},interval=rank.posteriorInterval;
 return <span className="ability-evidence"><button type="button" ref={trigger} className="icon-button" aria-label="能力分依据" title="能力分依据" aria-expanded={open} aria-controls={open?id:undefined} aria-haspopup="dialog" onClick={()=>setOpen(value=>!value)}><Info size={16}/></button>{open&&createPortal(<section ref={panel} id={id} className="ability-evidence-content" role="dialog" aria-label="能力分依据" tabIndex={-1} style={position}>
  <header><strong>能力分依据</strong><button type="button" className="icon-button" aria-label="关闭能力分依据" title="关闭 · Esc" onClick={()=>{setOpen(false);trigger.current?.focus();}}><X size={16}/></button></header>
  <p>最近 {rank.attemptedCount||0} 道不同原题，{rank.ratedEvidenceCount||0} 道有难度依据，独立完成 {rank.evidenceCount||0} 道。有效证据权重 {rank.effectiveEvidence||0}。</p>
  {interval&&<p>95% 模型区间 {interval[0]}–{interval[1]}；{rank.supportCeiling!=null?`至少五道独立成功支持到 ${rank.supportCeiling}。`:"独立成功证据尚不足五道。"}显示值取后验保守估计与已验证难度上限的较小值。</p>}
  <p>近 90 天：独立完成 {recent.independentSolved||0}/{recent.attempted||0}，首次提交通过 {recent.firstPass||0} 道，计时作答独立完成 {recent.timedSolved||0}/{recent.timedAttempted||0}。这是训练参考，未经共同人群标定。</p>
  {Object.entries(rank.topicEvidence||{}).length>0&&<p>{Object.entries(rank.topicEvidence).map(([name,value])=>`${name} ${value.independentSolved}/${value.attempted}`).join('；')}（独立完成 / 作答，同题可能关联多个专题）</p>}
  {(rank.evidence||[]).length>0&&<div className="ability-evidence-table" tabIndex={0} role="region" aria-label="作答证据表，可横向滚动"><table aria-label="能力分作答证据"><thead><tr><th>题目</th><th>难度</th><th>依据</th><th>结果</th><th>权重</th></tr></thead><tbody>{rank.evidence.map(item=><tr key={item.id}><td>{names.get(item.problemId)||item.id}</td><td>{item.difficulty}</td><td>{SOURCE_NAMES[item.difficultyKind]||item.difficultyKind||'待核实'}</td><td>{item.solved?'独立完成':'未独立完成'}</td><td>{Number(item.weight).toFixed(2)}</td></tr>)}</tbody></table></div>}
  <p>{rank.rules}</p>
 </section>,document.body)}</span>;
}
