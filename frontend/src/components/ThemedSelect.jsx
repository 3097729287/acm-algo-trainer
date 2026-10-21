import { forwardRef, useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Check, ChevronDown } from 'lucide-react';
import './ThemedSelect.css';

// Retain the native form control, labels, validation and change events. Only the
// popup is rendered here, so Windows cannot paint it in an unrelated palette.
const ThemedSelect=forwardRef(function ThemedSelect({children,onChange,onKeyDown,onPointerDown,onClick,className='',style,...props},forwardedRef) {
  const native=useRef(null),menu=useRef(null),search=useRef({text:'',at:0}),id=useId();
  const [open,setOpen]=useState(false),[active,setActive]=useState(-1),[items,setItems]=useState([]),[position,setPosition]=useState({});
  const attach=useCallback(node=>{native.current=node;if(typeof forwardedRef==='function')forwardedRef(node);else if(forwardedRef)forwardedRef.current=node;},[forwardedRef]);
  function options(){return Array.from(native.current?.options || []).map((option,index)=>({index,value:option.value,text:option.text,disabled:option.disabled || Boolean(option.parentElement?.disabled),group:option.parentElement?.tagName==='OPTGROUP'?option.parentElement.label:''}));}
  function show(){if(props.disabled)return;const values=options();setItems(values);setActive(native.current.selectedIndex);setOpen(true);}
  function choose(index){const option=items[index];if(!option || option.disabled)return;const select=native.current;select.value=option.value;select.dispatchEvent(new Event('change',{bubbles:true}));setOpen(false);select.focus({preventScroll:true});}
  function move(direction){let index=active;for(let count=0;count<items.length;count++){index=(index+direction+items.length)%items.length;if(!items[index].disabled){setActive(index);break;}}}
  useLayoutEffect(()=>{
    if(!open)return;
    const layout=()=>{const rect=native.current.getBoundingClientRect();const width=Math.min(Math.max(rect.width,160),innerWidth-16);const below=innerHeight-rect.bottom-12,above=rect.top-12;const height=Math.min(288,Math.max(80,Math.max(below,above)));const upwards=below<Math.min(240,items.length*36)&&above>below;
      setPosition({position:'fixed',left:Math.max(8,Math.min(rect.left,innerWidth-width-8)),width,maxHeight:height,...(upwards?{bottom:innerHeight-rect.top+5}:{top:rect.bottom+5})});};
    layout();const outside=event=>{if(!native.current?.contains(event.target)&&!menu.current?.contains(event.target))setOpen(false);};
    document.addEventListener('pointerdown',outside,true);window.addEventListener('resize',layout);window.addEventListener('scroll',layout,true);
    return()=>{document.removeEventListener('pointerdown',outside,true);window.removeEventListener('resize',layout);window.removeEventListener('scroll',layout,true);};
  },[open,items.length]);
  useLayoutEffect(()=>{if(open)menu.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({block:'nearest'});},[open,active]);
  useEffect(()=>{if(props.disabled)setOpen(false);},[props.disabled]);
  return <><span className="tb-select-wrap"><select {...props} ref={attach} className={`tb-select ${className}`} style={style} aria-expanded={open} aria-controls={open?id:undefined} aria-activedescendant={open&&active>=0?`${id}-${active}`:undefined}
    onPointerDown={event=>{onPointerDown?.(event);if(event.defaultPrevented || props.disabled)return;event.preventDefault();native.current.focus({preventScroll:true});if(open)setOpen(false);else show();}}
    onClick={event=>{event.preventDefault();onClick?.(event);}}
    onChange={event=>{setOpen(false);onChange?.(event);}}
    onBlur={event=>{props.onBlur?.(event);if(!menu.current?.contains(event.relatedTarget))setOpen(false);}}
    onKeyDown={event=>{
      onKeyDown?.(event);if(event.defaultPrevented || event.ctrlKey || event.metaKey)return;
      if(event.key==='Tab'){setOpen(false);return;}
      if(event.key==='Escape' && open){event.preventDefault();event.stopPropagation();setOpen(false);return;}
      if(['ArrowDown','ArrowUp','Home','End','Enter',' '].includes(event.key)){
        event.preventDefault();event.stopPropagation();
        if(!open){show();return;}
        if(event.key==='Enter'||event.key===' '){choose(active);return;}
        if(event.key==='Home'){setActive(items.findIndex(item=>!item.disabled));return;}
        if(event.key==='End'){setActive(items.findLastIndex(item=>!item.disabled));return;}
        move(event.key==='ArrowDown'?1:-1);return;
      }
      if(event.key.length===1&&!event.altKey){
        event.preventDefault();const values=open?items:options();if(!open)show();const now=Date.now();search.current={text:(now-search.current.at<700?search.current.text:'')+event.key.toLocaleLowerCase(),at:now};
        const found=values.findIndex(item=>!item.disabled&&item.text.toLocaleLowerCase().startsWith(search.current.text));if(found>=0)setActive(found);
      }
    }}>{children}</select><ChevronDown className="tb-select-chevron" size={14} aria-hidden="true"/></span>
    {open&&createPortal(<div ref={menu} id={id} className="tb-select-menu" role="listbox" aria-label={props['aria-label'] || native.current?.labels?.[0]?.textContent || '选项'} style={position} onPointerDown={event=>event.preventDefault()}>{items.map((item,index)=><div key={`${item.value}:${index}`}>
      {item.group&&item.group!==items[index-1]?.group&&<div className="tb-select-group">{item.group}</div>}
      <button type="button" role="option" id={`${id}-${index}`} data-index={index} aria-selected={native.current.value===item.value} aria-disabled={item.disabled} data-active={active===index} disabled={item.disabled} tabIndex={-1} onPointerMove={()=>setActive(index)} onClick={()=>choose(index)}><span>{item.text}</span>{native.current.value===item.value&&<Check size={14} aria-hidden="true"/>}</button>
    </div>)}</div>,native.current?.closest('dialog') || document.body)}
  </>;
});
export default ThemedSelect;
