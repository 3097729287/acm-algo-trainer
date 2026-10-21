import { forwardRef, useEffect, useRef, useState } from 'react';
import './SettingsControls.css';

const BoundedNumber=forwardRef(function BoundedNumber({value,onChange,onBlur,min=0,max=10000,step=1,unit='',className='',...props},ref){
  const [draft,setDraft]=useState(String(value ?? '')),focused=useRef(false);
  useEffect(()=>{if(!focused.current)setDraft(String(value ?? ''));},[value]);
  const emit=(event,next)=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(event.currentTarget,String(next));onChange?.({...event,target:event.currentTarget,currentTarget:event.currentTarget});};
  function commit(event){
    focused.current=false;
    if(draft===''&&!props.required){setDraft('');emit(event,'');onBlur?.(event);return;}
    const number=Number(draft),bounded=Math.max(Number(min),Math.min(Number(max),Number.isFinite(number)?number:Number(value)||Number(min)));
    const next=Number(step)%1===0?Math.round(bounded):bounded;
    setDraft(String(next));emit(event,next);onBlur?.(event);
  }
  return <span className={`bounded-number ${className}`}><input {...props} ref={ref} type="number" min={min} max={max} step={step} value={draft} onFocus={()=>{focused.current=true;}} onChange={event=>{const text=event.target.value;setDraft(text);if(text===''&&!props.required){onChange?.(event);return;}const next=Number(text);if(text!==''&&Number.isFinite(next)&&next>=Number(min)&&next<=Number(max))onChange?.(event);}} onBlur={commit} onKeyDown={event=>{props.onKeyDown?.(event);if(event.key==='Enter'){event.preventDefault();commit(event);event.currentTarget.blur();}if(event.key==='Escape'){setDraft(String(value ?? ''));event.currentTarget.blur();}}}/>{unit&&<span aria-hidden="true">{unit}</span>}</span>;
});
export default BoundedNumber;
