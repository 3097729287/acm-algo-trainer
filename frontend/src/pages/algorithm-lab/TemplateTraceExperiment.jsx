import {useMemo,useState} from 'react';
import {ArrowLeft,ArrowRight,Check,RotateCcw} from 'lucide-react';
import TEMPLATES from '../../../../backend/resources/code-templates.json';
import {TEMPLATE_CURRICULUM} from '@/lib/templateCurriculum.js';
import {binaryBoundaryTrace,windowExtremaTrace,parseTraceValues,bruteTraceResult} from './templateTraceModels.js';
import {Feedback} from './LabParts.jsx';
import './templateTrace.css';

export default function TemplateTraceExperiment({kind,draft={},update}){
 const binary=kind==='binary-search',lesson=TEMPLATE_CURRICULUM[kind];
 const text=draft.values??(binary?'1 3 3 3 7':'3 1 1 5 -2 4'),parameter=Number(draft.parameter??3),mode=draft.variant||(binary?'lower':'minimum');
 const [checked,setChecked]=useState(false);
 const parsed=useMemo(()=>parseTraceValues(text),[text]);
 const trace=useMemo(()=>parsed.error?{error:parsed.error,frames:[]}:binary?binaryBoundaryTrace(parsed.values,parameter,mode==='upper'):windowExtremaTrace(parsed.values,parameter,mode),[kind,text,parameter,mode]);
 const index=Math.max(0,Math.min(trace.frames.length-1,Number(draft.frame)||0)),frame=trace.frames[index];
 const change=delta=>{setChecked(false);update({...draft,...delta,frame:delta.frame??0});};
 const variants=binary?[['lower','第一个 ≥'],['upper','第一个 >']]:[['minimum','最小值'],['maximum','最大值'],['earliest','最早最小值下标']];
 let code=binary?lesson.variants.find(v=>v.id==='lower-upper').code:mode==='minimum'?TEMPLATES.templates.find(t=>t.id==='builtin:window-extrema').code:lesson.variants.find(v=>v.id===(mode==='maximum'?'maximum':'earliest-index')).code;
 if(binary){const functionName=mode==='upper'?'upper_position':'lower_position';code=code.slice(code.indexOf('int '+functionName));if(mode==='lower')code=code.slice(0,code.indexOf('\nint upper_position'));}
 const anchors=binary?{initialize:'int left',compare:'int middle',left:'else left',right:'right=middle',return:'return left'}:{initialize:'deque<int>',iterate:'for(int right',expire:'pending.front()<=',dominate:'pending.back()',insert:'pending.push_back',output:'result.push_back',return:'return result'};
 const lines=code.trim().split('\n'),compact=value=>value.replace(/\s+/g,'');
 const activeLine=frame?lines.findIndex(line=>compact(line).includes(compact(anchors[frame.action]))):-1;
 const expected=frame&&!trace.error?bruteTraceResult(kind,parsed.values,parameter,mode):null;
 const same=JSON.stringify(expected)===JSON.stringify(trace.result);
 return <section className="lab-panel template-trace" aria-label={binary?'二分边界实验':'单调队列实验'}>
  <div className="template-trace-inputs"><label>数组<input aria-label="实验数组" value={text} onChange={e=>change({values:e.target.value})}/></label><label>{binary?'目标':'宽度'}<input aria-label={binary?'实验目标':'窗口宽度'} type="number" min={binary?undefined:1} max={binary?undefined:16} value={draft.parameter??3} onChange={e=>change({parameter:e.target.value})}/></label></div>
  <div className="seq-tabs" aria-label="实验变种">{variants.map(([id,title])=><button type="button" key={id} aria-pressed={id===mode} onClick={()=>change({variant:id})}>{title}</button>)}</div>
  {trace.error?<Feedback>{trace.error}</Feedback>:<>
   <div className="template-trace-strip" aria-label="当前数组状态">{parsed.values.map((value,i)=><div key={i} data-active={binary?i>=frame.left&&i<frame.right:i>=frame.left&&i<=frame.right} data-middle={binary&&i===frame.middle} data-candidate={!binary&&frame.queue.includes(i)}><small>{i}</small><strong>{value}</strong></div>)}{binary&&<div className="trace-sentinel" data-boundary={frame.left===parsed.values.length}><small>{parsed.values.length}</small><strong>∅</strong></div>}</div>
   {binary?<p className="seq-equation">left={frame.left}，right={frame.right}，mid={frame.middle??'—'}</p>:<><p className="seq-equation">right={frame.right}；候选 {frame.queue.map(i=>`${i}:${parsed.values[i]}`).join(' → ')||'∅'}</p><output aria-label="窗口输出">{frame.result.join(' ')||'∅'}</output></>}
   <p role="status" className="template-trace-reason">{frame.explanation}</p>
   <div className="template-trace-controls"><button type="button" className="lab-icon-button" aria-label="上一步" disabled={!index} onClick={()=>change({frame:index-1})}><ArrowLeft size={17}/></button><span>{index+1} / {trace.frames.length}</span><button type="button" className="lab-icon-button" aria-label="下一步" disabled={index>=trace.frames.length-1} onClick={()=>change({frame:index+1})}><ArrowRight size={17}/></button><button type="button" className="lab-icon-button" aria-label="重置推演" onClick={()=>change({frame:0})}><RotateCcw size={17}/></button><button type="button" className="lab-icon-button" aria-label="核对完整结果" onClick={()=>setChecked(true)}><Check size={17}/></button></div>
   {checked&&<Feedback good={same}>{same?`完整结果 ${JSON.stringify(trace.result)} 与独立逐项枚举一致。`:`结果不一致：逐项枚举为 ${JSON.stringify(expected)}。`}</Feedback>}
   <pre className="template-trace-code" tabIndex={0} aria-label="对应的讲解代码">{lines.map((line,i)=><span key={i} data-current={i===activeLine}><small>{i+1}</small><code>{line||' '}</code></span>)}</pre>
   <p className="lab-caption">逐步执行的是与上方 C++ 对应的课堂模型；完整程序另经 C++17 编译和样例、小数据对照。课堂核对不产生正式通过记录。</p>
  </>}
 </section>;
}
