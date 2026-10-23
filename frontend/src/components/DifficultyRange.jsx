import BoundedNumber from './BoundedNumber.jsx';
import './DifficultyRange.css';

const bounded = (value, min, max) => Math.max(min, Math.min(max, Number(value) || 0));

export default function DifficultyRange({ value, onChange, min = 0, max = 10000, step = 100, disabled = false, label = '难度范围', minLabel = '最低难度', maxLabel = '最高难度' }) {
  const low = bounded(value.min, min, max), high = Math.max(low, bounded(value.max, min, max));
  const percent = number => `${(number - min) / (max - min) * 100}%`;
  const change = (key, next) => onChange(key === 'min' ? { min: Math.min(bounded(next, min, max), high) } : { max: Math.max(bounded(next, min, max), low) });
  return <div className="difficulty-range" role="group" aria-label={label} data-disabled={disabled}>
    <div className="difficulty-range-track" style={{ '--range-low': percent(low), '--range-high': percent(high) }}>
      <span className="difficulty-range-rail" aria-hidden="true"/><span className="difficulty-range-fill" aria-hidden="true"/>
      <input type="range" min={min} max={max} step={step} value={low} disabled={disabled} aria-label={`${minLabel}滑块`} onChange={event => change('min', event.target.value)} style={{ zIndex: low === max ? 3 : 1 }}/>
      <input type="range" min={min} max={max} step={step} value={high} disabled={disabled} aria-label={`${maxLabel}滑块`} onChange={event => change('max', event.target.value)}/>
    </div>
    <div className="difficulty-range-values"><BoundedNumber aria-label={minLabel} min={min} max={high} step={1} value={low} disabled={disabled} required onChange={event => change('min', event.target.value)}/><span aria-hidden="true">~</span><BoundedNumber aria-label={maxLabel} min={low} max={max} step={1} value={high} disabled={disabled} required onChange={event => change('max', event.target.value)}/></div>
  </div>;
}

export function DifficultySlider({ value, onChange, min = 0, max = 4000, step = 50, label, disabled = false }) {
  return <span className="difficulty-single"><input type="range" min={min} max={max} step={step} value={bounded(value, min, max)} aria-label={`${label}滑块`} disabled={disabled} onChange={onChange}/><BoundedNumber aria-label={label} min={min} max={max} value={value} disabled={disabled} required onChange={onChange}/></span>;
}
