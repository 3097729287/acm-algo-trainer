import {createContext,useContext,useMemo} from 'react';
import BoundedNumber from './BoundedNumber.jsx';
import './DifficultyRange.css';

const bounded = (value, min, max) => Math.max(min, Math.min(max, Number(value) || 0));
const DifficultyBounds=createContext({min:0,max:4000});
export function DifficultyBoundsProvider({rows=[],children}) {
  const bounds=useMemo(()=>({min:0,max:Math.max(1,...rows.map(row=>Number(row.difficulty)).filter(value=>Number.isFinite(value)&&value>0))}),[rows]);
  return <DifficultyBounds.Provider value={rows.length?bounds:{min:0,max:4000}}>{children}</DifficultyBounds.Provider>;
}
export function useDifficultyBounds(){return useContext(DifficultyBounds);}

export default function DifficultyRange({ value, onChange, min = 0, max: maximum, step = 10, disabled = false, label = '难度范围', minLabel = '最低难度', maxLabel = '最高难度' }) {
  const bounds=useDifficultyBounds(),max=Math.max(min+1,Number(maximum??bounds.max)||4000);
  const low = bounded(value.min, min, max), high = Math.max(low, bounded(value.max, min, max));
  const percent = number => (number - min) / (max - min);
  const change = (key, next) => onChange(key === 'min' ? { min: Math.min(bounded(next, min, max), high) } : { max: Math.max(bounded(next, min, max), low) });
  const slide=(key,value)=>{const numeric=bounded(value,min,max);change(key,numeric>=max-step/2?max:min+Math.round((numeric-min)/step)*step);};
  const keys=(key,value,event)=>{
    if(event.ctrlKey||event.metaKey)return;
    const increment=event.altKey?1:event.shiftKey?step*5:step;
    const next={ArrowLeft:value-increment,ArrowDown:value-increment,ArrowRight:value+increment,ArrowUp:value+increment,Home:min,End:max,PageDown:value-step*10,PageUp:value+step*10}[event.key];
    if(next!==undefined){event.preventDefault();change(key,next);}
  };
  // We apply drag snapping ourselves; native snapping would discard Alt+1
  // adjustments and make a non-multiple library maximum unreachable.
  const nativeStep='any';
  return <div className="difficulty-range" role="group" aria-label={label} data-disabled={disabled}>
    <div className="difficulty-range-track" style={{ '--range-low': percent(low), '--range-high': percent(high) }}>
      <span className="difficulty-range-rail" aria-hidden="true"/><span className="difficulty-range-fill" aria-hidden="true"/>
      <input type="range" min={min} max={max} step={nativeStep} value={low} disabled={disabled} aria-label={`${minLabel}滑块`} onChange={event => slide('min', event.target.value)} onKeyDown={event=>keys('min',low,event)} style={{ zIndex: low === high ? 3 : 1 }}/>
      <input type="range" min={min} max={max} step={nativeStep} value={high} disabled={disabled} aria-label={`${maxLabel}滑块`} onChange={event => slide('max', event.target.value)} onKeyDown={event=>keys('max',high,event)}/>
    </div>
    <div className="difficulty-range-values"><BoundedNumber aria-label={minLabel} min={min} max={high} step={1} value={low} disabled={disabled} required onChange={event => change('min', event.target.value)}/><span aria-hidden="true">~</span><BoundedNumber aria-label={maxLabel} min={low} max={max} step={1} value={high} disabled={disabled} required onChange={event => change('max', event.target.value)}/></div>
  </div>;
}

export function DifficultySlider({ value, onChange, min = 0, max = 4000, step = 50, label, disabled = false }) {
  return <span className="difficulty-single"><input type="range" min={min} max={max} step={step} value={bounded(value, min, max)} aria-label={`${label}滑块`} disabled={disabled} onChange={onChange}/><BoundedNumber aria-label={label} min={min} max={max} value={value} disabled={disabled} required onChange={onChange}/></span>;
}
