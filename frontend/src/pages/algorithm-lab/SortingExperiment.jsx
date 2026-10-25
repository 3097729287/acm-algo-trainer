import {useMemo,useState} from 'react';
import {ArrowLeft,ArrowRight,RotateCcw} from 'lucide-react';
import {Feedback} from './LabParts.jsx';
import {parseSortInput,sortingTrace,SORT_NAMES} from './sortingModel.js';
import './sortingLab.css';

export default function SortingExperiment({algorithms=['bubble','insertion','selection'],initial=[5,2,5,1,4,2]}){
 const [text,setText]=useState(initial.join(' ')),[values,setValues]=useState(initial),[algorithm,setAlgorithm]=useState(algorithms[0]),[seed,setSeed]=useState(7),[index,setIndex]=useState(0),[error,setError]=useState(''),[answer,setAnswer]=useState(''),[checked,setChecked]=useState(false);
 const frames=useMemo(()=>sortingTrace(values,algorithm,seed),[values,algorithm,seed]),position=Math.min(index,frames.length-1),frame=frames[position],next=frames[position+1];
 const reset=()=>{setIndex(0);setAnswer('');setChecked(false);};
 const move=to=>{setIndex(to);setAnswer('');setChecked(false);};
 const correct=answer.trim().split(/[\s,，]+/).join(' ')===next?.items.map(x=>x.value).join(' ');
 return <section className="lab-panel sorting-experiment" aria-label="排序实验"><form className="sorting-input" onSubmit={e=>{e.preventDefault();try{setValues(parseSortInput(text));setError('');reset();}catch(e){setError(e.message);}}}><label>实验数组<input aria-label="排序实验数组" value={text} maxLength={60} onChange={e=>setText(e.target.value)}/></label><button className="lab-button">应用</button></form>{error&&<p role="alert">{error}</p>}
 <div className="sorting-tools"><label>算法<select aria-label="排序算法" value={algorithm} onChange={e=>{setAlgorithm(e.target.value);reset();}}>{algorithms.map(id=><option key={id} value={id}>{SORT_NAMES[id]}</option>)}</select></label>{algorithm==='randomQuick'&&<button className="lab-button lab-button-quiet" onClick={()=>{setSeed(seed+1);reset();}}>换一组随机基准</button>}<button className="lab-icon-button" aria-label="重置排序实验" onClick={reset}><RotateCcw size={16}/></button><span>比较 {frame.comparisons}{algorithm==='merge'?` · 逆序对 ${frame.inversions}`:''}</span></div>
 <div className="sorting-array" aria-label="当前数组">{frame.items.map((item,i)=><div key={i} data-active={frame.active.includes(i)} data-in-range={!frame.range||i>=frame.range[0]&&i<frame.range[1]}><b>{item.value}</b><small>#{item.id+1}</small><span>{i}</span></div>)}</div>
 {frame.buffer&&<div className="sorting-buffer"><span>输出缓冲</span>{frame.buffer.map((x,i)=><b key={i}>{x?.value??'·'}</b>)}</div>}
 {frame.buckets&&<div className="sorting-buckets">{frame.buckets.map(bucket=><div key={bucket.key}><b>{bucket.key}</b><span>{bucket.values.join(' → ')||'—'}</span></div>)}</div>}
 <p className="sorting-explanation" aria-live="polite">{frame.note}</p>
 <nav aria-label="实验步骤" className="sorting-tools"><button className="lab-button lab-button-quiet" disabled={!position} onClick={()=>move(position-1)}><ArrowLeft size={15}/>上一步</button><span>{position+1} / {frames.length}</span><button className="lab-button" disabled={!next} onClick={()=>move(position+1)}>下一步<ArrowRight size={15}/></button><button className="lab-button lab-button-quiet" disabled={!next} onClick={()=>move(frames.length-1)}>查看结果</button></nav>
 {next&&<form className="sorting-prediction" onSubmit={e=>{e.preventDefault();setChecked(true);}}><label>预测下一步的数组<input aria-label="预测下一步数组" value={answer} onChange={e=>{setAnswer(e.target.value);setChecked(false);}}/></label><button className="lab-button lab-button-quiet" disabled={!answer.trim()}>核对</button>{checked&&<Feedback good={correct}>{correct?'正确，继续检查这一步维持了什么顺序。':'还不一致。下一步可能只比较或分桶，原数组不一定会变化；按当前规则再推一遍。'}</Feedback>}</form>}
 </section>;
}
