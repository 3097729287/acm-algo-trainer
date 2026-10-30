import {useEffect,useId,useLayoutEffect,useRef,useState} from 'react';
import CatalogName from './CatalogName.jsx';
import {createPortal} from 'react-dom';
import {ArrowLeft,Check,ChevronDown,ChevronRight,FileText,Folder,FolderTree} from 'lucide-react';
import './ThemedSelect.css';
import './FolderSelect.css';

function flatten(nodes){return nodes.flatMap(node=>[...(node.value!==undefined?[node]:[]),...flatten(node.children||[])]);}
function selectedPath(nodes,value,path=[]){
 for(let index=0;index<nodes.length;index++){
  if(nodes[index].value===value)return path;
  const found=selectedPath(nodes[index].children||[],value,[...path,index]);if(found)return found;
 }
 return null;
}

export default function FolderSelect({options=[],value='',onChange,disabled=false,placeholder='请选择',label='选择项目',selectedLabel,iconOnly=false,headerActions,externalAnchor=null,openRequest=0,onClose}){
 const control=useRef(null),menu=useRef(null),search=useRef({text:'',at:0}),previousOptions=useRef(options),id=useId();
 const [open,setOpen]=useState(false),[path,setPath]=useState([]),[active,setActive]=useState(0),[position,setPosition]=useState({});
 let current=null,children=options;
 for(const index of path){current=children[index];children=current?.children||[];}
 const rows=[...(current?.value!==undefined?[{...current,children:undefined,label:`选择「${current.label}」`}]:path.length?[]:[{label:placeholder,value:''}]),...children];
 useEffect(()=>{
  const previous=previousOptions.current;previousOptions.current=options;
  setPath(currentPath=>{
   let before=previous,after=options;const next=[];
   for(const index of currentPath){
    const node=before[index];if(!node)break;
    const found=after.findIndex(item=>node.value!==undefined?item.value===node.value:item.label===node.label);
    if(found<0)break;next.push(found);before=node.children||[];after=after[found].children||[];
   }
   return next;
  });setActive(0);
 },[options]);
 function show(){if(disabled)return;setPath(selectedPath(options,value)||[]);setActive(0);setOpen(true);}
 function dismiss(){setOpen(false);onClose?.();}
 function close(){dismiss();(externalAnchor||control.current)?.focus({preventScroll:true});}
 function back(){setPath(previous=>previous.slice(0,-1));setActive(0);}
 function choose(index){const row=rows[index];if(!row||row.disabled)return;
  if(Array.isArray(row.children)){const childIndex=children.indexOf(row);setPath(previous=>[...previous,childIndex]);setActive(0);return;}
  const native=control.current;native.value=row.value;native.dispatchEvent(new Event('change',{bubbles:true}));close();
 }
 function move(direction){for(let offset=1;offset<=rows.length;offset++){const next=(active+direction*offset+rows.length)%rows.length;if(!rows[next].disabled){setActive(next);break;}}}
 useLayoutEffect(()=>{if(externalAnchor){if(openRequest)show();else setOpen(false);}},[externalAnchor,openRequest]);
 useLayoutEffect(()=>{
  if(!open)return;
  const anchor=externalAnchor||control.current;
  const layout=()=>{const rect=(externalAnchor||control.current).getBoundingClientRect(),width=Math.min(Math.max(rect.width,240),innerWidth-16),below=innerHeight-rect.bottom-12,above=rect.top-12,up=below<Math.min(300,rows.length*36+42)&&above>below,gap=externalAnchor?8:5;
   setPosition({position:'fixed',left:Math.max(8,Math.min(rect.left,innerWidth-width-8)),width,maxHeight:Math.min(380,Math.max(100,up?above:below)),...(up?{bottom:innerHeight-rect.top+gap}:{top:rect.bottom+gap})});};
  const outside=event=>{if(!(externalAnchor||control.current)?.contains(event.target)&&!menu.current?.contains(event.target))dismiss();};
  // Responsive text wrapping and late font metrics can move the trigger after
  // the window's resize event. Follow its actual box and surrounding row.
  let frame=0,alive=true;
  const schedule=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{if(alive)layout();});};
  const observer=typeof ResizeObserver==='undefined'?null:new ResizeObserver(schedule);
  if(anchor){observer?.observe(anchor);if(anchor.parentElement)observer?.observe(anchor.parentElement);}
  layout();schedule();document.fonts?.ready.then(()=>{if(alive)schedule();});
  if(externalAnchor)menu.current?.focus({preventScroll:true});document.addEventListener('pointerdown',outside,true);window.addEventListener('resize',schedule);window.addEventListener('scroll',schedule,true);
  return()=>{alive=false;cancelAnimationFrame(frame);observer?.disconnect();document.removeEventListener('pointerdown',outside,true);window.removeEventListener('resize',schedule);window.removeEventListener('scroll',schedule,true);};
 },[open,path.length,rows.length,externalAnchor]);
 useLayoutEffect(()=>{if(open)menu.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({block:'nearest'});},[open,active]);
 useEffect(()=>{if(disabled)setOpen(false);},[disabled]);
 const keyboard=event=>{
   if(event.ctrlKey||event.metaKey||event.altKey)return;
   if(event.key==='Tab'){dismiss();return;}
   if(event.key==='Escape'&&open){event.preventDefault();event.stopPropagation();close();return;}
   if(['ArrowDown','ArrowUp','ArrowRight','ArrowLeft','Home','End','Enter',' '].includes(event.key)){
    event.preventDefault();event.stopPropagation();if(!open){show();return;}
    if(event.key==='Enter'||event.key===' '||event.key==='ArrowRight'){if(event.key!=='ArrowRight'||Array.isArray(rows[active]?.children))choose(active);return;}
    if(event.key==='ArrowLeft'){if(path.length)back();return;}
    if(event.key==='Home'){setActive(0);return;}if(event.key==='End'){setActive(rows.length-1);return;}move(event.key==='ArrowDown'?1:-1);return;
   }
   if(event.key.length===1){event.preventDefault();if(!open)show();const now=Date.now();search.current={text:(now-search.current.at<700?search.current.text:'')+event.key.toLocaleLowerCase(),at:now};const found=rows.findIndex(row=>row.label.toLocaleLowerCase().startsWith(search.current.text));if(found>=0)setActive(found);}
 };
 return <><span className={`tb-select-wrap${iconOnly?' folder-icon-control':''}`} data-active={Boolean(value)} style={externalAnchor?{display:'none'}:undefined}><select ref={control} className="tb-select folder-select" title={iconOnly?`${label}${value?`：${selectedLabel||flatten(options).find(node=>node.value===value)?.label||value}`:''}`:undefined} aria-label={label} value={value} disabled={disabled} aria-expanded={open} aria-controls={open?id:undefined} aria-activedescendant={open?`${id}-${active}`:undefined}
  onChange={event=>{setOpen(false);onChange?.(event);}}
  onPointerDown={event=>{if(disabled)return;event.preventDefault();control.current.focus({preventScroll:true});if(open)setOpen(false);else show();}}
  onClick={event=>event.preventDefault()}
  onBlur={event=>{if(!menu.current?.contains(event.relatedTarget))setOpen(false);}}
  onKeyDown={keyboard}><option value="">{placeholder}</option>{value&&!flatten(options).some(node=>node.value===value)&&<option value={value}>{selectedLabel||value}</option>}{flatten(options).map((node,index)=><option key={`${node.value}:${index}`} value={node.value}>{node.selectionLabel||node.label}</option>)}</select>{iconOnly?<FolderTree className="folder-control-symbol" size={18} aria-hidden="true"/>:<ChevronDown className="tb-select-chevron" size={14} aria-hidden="true"/>}</span>
  {open&&createPortal(<div ref={menu} id={id} className="tb-select-menu folder-select-menu" role="listbox" aria-label={label} tabIndex={externalAnchor?0:undefined} aria-activedescendant={externalAnchor?`${id}-${active}`:undefined} style={position} onKeyDown={externalAnchor?keyboard:undefined} onBlur={externalAnchor?event=>{if(!menu.current?.contains(event.relatedTarget)&&!externalAnchor.contains(event.relatedTarget))dismiss();}:undefined} onPointerDown={event=>event.preventDefault()}>
   <header>{path.length?<button type="button" aria-label="返回上一级" onClick={back}><ArrowLeft size={15}/></button>:<Folder size={16}/>}<strong><CatalogName>{current?.label||placeholder}</CatalogName></strong>{headerActions&&<span className="folder-menu-actions">{headerActions}</span>}</header>
   {rows.map((row,index)=><button type="button" key={`${row.value||row.label}:${index}`} role="option" id={`${id}-${index}`} data-index={index} data-value={row.value} data-active={active===index} aria-selected={row.value!==undefined&&value===row.value} disabled={row.disabled} tabIndex={-1} onPointerMove={()=>setActive(index)} onClick={()=>choose(index)}>
    {Array.isArray(row.children)?<Folder size={16}/>:row.value?<FileText size={15}/>:null}<span><CatalogName>{row.label}</CatalogName></span>{Array.isArray(row.children)?<ChevronRight size={15}/>:value===row.value?<Check size={14}/>:null}
   </button>)}
   {!rows.length&&<p>此分类暂未收录比赛</p>}
  </div>,control.current?.closest('dialog')||document.body)}
 </>;
}
