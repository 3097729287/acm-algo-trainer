import {useEffect,useRef,useState} from 'react';
import {ChevronLeft,ChevronRight,Pause,Play,RotateCcw} from 'lucide-react';
import {PLAYBACK_SPEEDS,useEditorialPlaybackSpeed} from '@/lib/editorialPlayback.js';
import EditorialMotionScene from './EditorialMotionScene.jsx';
import './ReadingMotion.css';

export default function ReadingMotion({model,renderImage}){
 const root=useRef(null),interacted=useRef(false),started=useRef(false);
 const elapsed=useRef(0),[progress,setProgress]=useState(0),[speed,setSpeed]=useEditorialPlaybackSpeed();
 const [step,setStep]=useState(0),[playing,setPlaying]=useState(false),[visible,setVisible]=useState(false),[zoomed,setZoomed]=useState(false);
 const [hidden,setHidden]=useState(()=>document.hidden),[reduced,setReduced]=useState(()=>document.documentElement.dataset.motion==='off'||matchMedia('(prefers-reduced-motion: reduce)').matches);
 useEffect(()=>{
  const media=matchMedia('(prefers-reduced-motion: reduce)'),motion=()=>setReduced(media.matches||document.documentElement.dataset.motion==='off'),visibility=()=>setHidden(document.hidden),observer=new MutationObserver(motion);
  observer.observe(document.documentElement,{attributes:true,attributeFilter:['data-motion']});media.addEventListener('change',motion);document.addEventListener('visibilitychange',visibility);
  const viewport=new IntersectionObserver(entries=>setVisible(entries.some(entry=>entry.isIntersecting&&entry.intersectionRatio>=.2)),{threshold:[0,.2]});viewport.observe(root.current);
  motion();return()=>{observer.disconnect();viewport.disconnect();media.removeEventListener('change',motion);document.removeEventListener('visibilitychange',visibility);};
 },[]);
 useEffect(()=>{if(reduced){setPlaying(false);elapsed.current=0;setProgress(0);}},[reduced]);
 useEffect(()=>{
  if(visible&&!hidden&&!reduced&&!started.current&&!interacted.current){started.current=true;setPlaying(true);}
 },[visible,hidden,reduced]);
 useEffect(()=>{
  if(!playing||hidden||reduced||!(visible||zoomed))return;
  let frame,previous=null;const duration=model.steps[step].duration;
  const tick=now=>{
   if(previous!==null)elapsed.current+=Math.min(100,now-previous)*speed;previous=now;
   if(elapsed.current>=duration){elapsed.current=0;setProgress(0);if(step>=model.steps.length-1)setPlaying(false);else setStep(step+1);return;}
   if(model.scene&&step<model.steps.length-1)setProgress(Math.max(0,Math.min(1,(elapsed.current/duration-.35)/.65)));
   frame=requestAnimationFrame(tick);
  };
  frame=requestAnimationFrame(tick);return()=>cancelAnimationFrame(frame);
 },[playing,hidden,reduced,visible,zoomed,step,model,speed]);
 const select=value=>{interacted.current=true;setPlaying(false);elapsed.current=0;setProgress(0);setStep(Math.min(model.steps.length-1,Math.max(0,Number(value))));};
 const toggle=()=>{interacted.current=true;if(reduced)return;if(!playing&&step===model.steps.length-1){elapsed.current=0;setProgress(0);setStep(0);}setPlaying(value=>!value);};
 const controls=<span className="reading-motion-controls" role="group" aria-label="演示控制">
  <button type="button" aria-label={playing?'暂停演示':step===model.steps.length-1?'重播演示':'播放演示'} title={playing?'暂停演示':step===model.steps.length-1?'重播演示':'播放演示'} disabled={reduced} onClick={toggle}>{playing?<Pause size={16}/>:<Play size={16}/>}</button>
  <button type="button" aria-label="上一步演示" title="上一步" disabled={step===0} onClick={()=>select(step-1)}><ChevronLeft size={16}/></button>
  <input type="range" aria-label="演示步骤" min="0" max={model.steps.length-1} step="1" value={step} aria-valuetext={`${step+1} / ${model.steps.length}：${model.steps[step].caption}`} onChange={event=>select(event.target.value)}/>
  <button type="button" aria-label="下一步演示" title="下一步" disabled={step===model.steps.length-1} onClick={()=>select(step+1)}><ChevronRight size={16}/></button>
  <span className="reading-motion-count">{step+1} / {model.steps.length}</span>
  <select className="reading-motion-speed" aria-label="播放速度" title="播放速度" value={speed} onChange={event=>setSpeed(event.target.value)}>{PLAYBACK_SPEEDS.map(value=><option key={value} value={value}>{value}×</option>)}</select>
  <button type="button" aria-label="演示回到开头" title="回到开头" onClick={()=>select(0)}><RotateCcw size={15}/></button>
 </span>;
 const caption=<span className="reading-motion-caption" aria-live={playing?'off':'polite'}>{model.steps[progress>0?Math.min(step+1,model.steps.length-1):step].caption}</span>;
 return <span ref={root} className="reading-motion" role="group" aria-label={model.title} data-step={step} data-progress={progress.toFixed(3)} data-speed={speed} data-mode={model.scene?'continuous':'steps'} data-playing={playing} onKeyDown={event=>{if(event.altKey||event.ctrlKey||event.metaKey||['INPUT','SELECT'].includes(event.target.tagName)||!event.target.closest('.reading-motion-controls'))return;if(event.key==='ArrowLeft'||event.key==='ArrowRight'){event.preventDefault();event.stopPropagation();select(step+(event.key==='ArrowLeft'?-1:1));}}}>
  {renderImage({source:model.steps[step].image,graphic:model.scene?<EditorialMotionScene model={model} step={step} progress={progress}/>:null,toolbar:<span className="reading-motion-expanded-controls">{controls}{caption}</span>,onZoomChange:setZoomed})}
  {controls}{caption}
 </span>;
}
