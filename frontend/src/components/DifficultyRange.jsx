import {createContext,useContext,useMemo,useRef} from 'react';
import BoundedNumber from './BoundedNumber.jsx';
import {difficultyDragValue,MIN_PIXELS_PER_STEP} from '@/lib/difficultyDrag.js';
import './DifficultyRange.css';

const bounded = (value, min, max) => Math.max(min, Math.min(max, Number(value) || 0));
const DifficultyBounds=createContext({min:0,max:4000});
export function DifficultyBoundsProvider({rows=[],children}) {
  const bounds=useMemo(()=>({min:0,max:Math.max(1,...rows.map(row=>Number(row.difficulty)).filter(value=>Number.isFinite(value)&&value>0))}),[rows]);
  return <DifficultyBounds.Provider value={rows.length?bounds:{min:0,max:4000}}>{children}</DifficultyBounds.Provider>;
}
export function useDifficultyBounds(){return useContext(DifficultyBounds);}

export default function DifficultyRange({ value, onChange, min = 0, max: maximum, step = 100, disabled = false, label = '难度范围', minLabel = '最低难度', maxLabel = '最高难度' }) {
  const drag=useRef(null);
  const bounds=useDifficultyBounds(),max=Math.max(min+1,Number(maximum??bounds.max)||4000);
  const low = bounded(value.min, min, max), high = Math.max(low, bounded(value.max, min, max));
  const percent = number => (number - min) / (max - min);
  const change = (key, next) => onChange(key === 'min' ? { min: Math.min(bounded(next, min, max), high) } : { max: Math.max(bounded(next, min, max), low) });
  const slide=(key,value)=>{const numeric=bounded(value,min,max);change(key,numeric>=max-step/2?max:min+Math.round((numeric-min)/step)*step);};
  const keys=(key,value,event)=>{
    if(event.ctrlKey||event.metaKey)return;
    const increment=event.altKey?10:event.shiftKey?step*5:step;
    const next={ArrowLeft:value-increment,ArrowDown:value-increment,ArrowRight:value+increment,ArrowUp:value+increment,Home:min,End:max,PageDown:value-step*10,PageUp:value+step*10}[event.key];
    if(next!==undefined){event.preventDefault();change(key,next);}
  };
  const startDrag=(key,event)=>{
    if(disabled||event.button!==0)return;
    event.preventDefault();event.currentTarget.focus({preventScroll:true});
    const width=event.currentTarget.getBoundingClientRect().width;
    drag.current={key,x:event.clientX,low,high,overlap:low===high,pixelsPerStep:Math.max(MIN_PIXELS_PER_STEP,(width-12)*step/(max-min)),pointerId:event.pointerId};
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const moveDrag=event=>{
    const current=drag.current;if(!current||current.pointerId!==event.pointerId)return;
    event.preventDefault();const distance=event.clientX-current.x;
    const key=current.overlap?(distance<0?'min':'max'):current.key;
    change(key,difficultyDragValue(key==='min'?current.low:current.high,distance,{min,max,step,pixelsPerStep:current.pixelsPerStep}));
  };
  const endDrag=event=>{if(drag.current?.pointerId===event.pointerId){drag.current=null;if(event.currentTarget.hasPointerCapture(event.pointerId))event.currentTarget.releasePointerCapture(event.pointerId);}};
  const pointerProps={onPointerMove:moveDrag,onPointerUp:endDrag,onPointerCancel:endDrag,onLostPointerCapture:()=>{drag.current=null;}};
  // Keep native range semantics for keyboard and assistive technology. Pointer
  // movement is relative, so pressing a thumb never jumps to an absolute value.
  const nativeStep='any';
  return <div className="difficulty-range" role="group" aria-label={label} data-disabled={disabled}>
    <div className="difficulty-range-track" style={{ '--range-low': percent(low), '--range-high': percent(high) }}>
      <span className="difficulty-range-rail" aria-hidden="true"/><span className="difficulty-range-fill" aria-hidden="true"/>
      <input type="range" min={min} max={max} step={nativeStep} value={low} disabled={disabled} aria-label={`${minLabel}滑块`} onChange={event => {if(!drag.current)slide('min', event.target.value);}} onKeyDown={event=>keys('min',low,event)} onPointerDown={event=>startDrag('min',event)} {...pointerProps} style={{ zIndex: low === high ? 3 : 1 }}/>
      <input type="range" min={min} max={max} step={nativeStep} value={high} disabled={disabled} aria-label={`${maxLabel}滑块`} onChange={event => {if(!drag.current)slide('max', event.target.value);}} onKeyDown={event=>keys('max',high,event)} onPointerDown={event=>startDrag('max',event)} {...pointerProps}/>
    </div>
    <div className="difficulty-range-values"><BoundedNumber aria-label={minLabel} min={min} max={high} step={1} value={low} disabled={disabled} required onChange={event => change('min', event.target.value)}/><span aria-hidden="true">~</span><BoundedNumber aria-label={maxLabel} min={low} max={max} step={1} value={high} disabled={disabled} required onChange={event => change('max', event.target.value)}/></div>
  </div>;
}

export function DifficultySlider({ value, onChange, min = 0, max = 4000, step = 50, label, disabled = false }) {
  return <span className="difficulty-single"><input type="range" min={min} max={max} step={step} value={bounded(value, min, max)} aria-label={`${label}滑块`} disabled={disabled} onChange={onChange}/><BoundedNumber aria-label={label} min={min} max={max} value={value} disabled={disabled} required onChange={onChange}/></span>;
}
