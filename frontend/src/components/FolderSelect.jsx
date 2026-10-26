import {useEffect,useId,useLayoutEffect,useRef,useState} from 'react';
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

export default function FolderSelect({options=[],value='',onChange,disabled=false,placeholder='请选择',label='选择项目',selectedLabel,iconOnly=false,headerActions}){
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
 function close(){setOpen(false);control.current?.focus({preventScroll:true});}
 function back(){setPath(previous=>previous.slice(0,-1));setActive(0);}
 function choose(index){const row=rows[index];if(!row||row.disabled)return;
  if(Array.isArray(row.children)){const childIndex=children.indexOf(row);setPath(previous=>[...previous,childIndex]);setActive(0);return;}
  const native=control.current;native.value=row.value;native.dispatchEvent(new Event('change',{bubbles:true}));close();
 }
 function move(direction){for(let offset=1;offset<=rows.length;offset++){const next=(active+direction*offset+rows.length)%rows.length;if(!rows[next].disabled){setActive(next);break;}}}
 useLayoutEffect(()=>{
  if(!open)return;
  const layout=()=>{const rect=control.current.getBoundingClientRect(),width=Math.min(Math.max(rect.width,240),innerWidth-16),below=innerHeight-rect.bottom-12,above=rect.top-12,up=below<Math.min(300,rows.length*36+42)&&above>below;
   setPosition({position:'fixed',left:Math.max(8,Math.min(rect.left,innerWidth-width-8)),width,maxHeight:Math.min(380,Math.max(100,up?above:below)),...(up?{bottom:innerHeight-rect.top+5}:{top:rect.bottom+5})});};
  const outside=event=>{if(!control.current?.contains(event.target)&&!menu.current?.contains(event.target))setOpen(false);};
  layout();document.addEventListener('pointerdown',outside,true);window.addEventListener('resize',layout);window.addEventListener('scroll',layout,true);
  return()=>{document.removeEventListener('pointerdown',outside,true);window.removeEventListener('resize',layout);window.removeEventListener('scroll',layout,true);};
 },[open,path.length,rows.length]);
 useLayoutEffect(()=>{if(open)menu.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({block:'nearest'});},[open,active]);
 useEffect(()=>{if(disabled)setOpen(false);},[disabled]);
 return <><span className={`tb-select-wrap${iconOnly?' folder-icon-control':''}`} data-active={Boolean(value)}><select ref={control} className="tb-select folder-select" title={iconOnly?`${label}${value?`：${selectedLabel||flatten(options).find(node=>node.value===value)?.label||value}`:''}`:undefined} aria-label={label} value={value} disabled={disabled} aria-expanded={open} aria-controls={open?id:undefined} aria-activedescendant={open?`${id}-${active}`:undefined}
  onChange={event=>{setOpen(false);onChange?.(event);}}
  onPointerDown={event=>{if(disabled)return;event.preventDefault();control.current.focus({preventScroll:true});if(open)setOpen(false);else show();}}
  onClick={event=>event.preventDefault()}
  onBlur={event=>{if(!menu.current?.contains(event.relatedTarget))setOpen(false);}}
  onKeyDown={event=>{
   if(event.ctrlKey||event.metaKey||event.altKey)return;
   if(event.key==='Tab'){setOpen(false);return;}
   if(event.key==='Escape'&&open){event.preventDefault();event.stopPropagation();close();return;}
   if(['ArrowDown','ArrowUp','ArrowRight','ArrowLeft','Home','End','Enter',' '].includes(event.key)){
    event.preventDefault();event.stopPropagation();if(!open){show();return;}
    if(event.key==='Enter'||event.key===' '||event.key==='ArrowRight'){if(event.key!=='ArrowRight'||Array.isArray(rows[active]?.children))choose(active);return;}
    if(event.key==='ArrowLeft'){if(path.length)back();return;}
    if(event.key==='Home'){setActive(0);return;}if(event.key==='End'){setActive(rows.length-1);return;}move(event.key==='ArrowDown'?1:-1);return;
   }
   if(event.key.length===1){event.preventDefault();if(!open)show();const now=Date.now();search.current={text:(now-search.current.at<700?search.current.text:'')+event.key.toLocaleLowerCase(),at:now};const found=rows.findIndex(row=>row.label.toLocaleLowerCase().startsWith(search.current.text));if(found>=0)setActive(found);}
  }}><option value="">{placeholder}</option>{value&&!flatten(options).some(node=>node.value===value)&&<option value={value}>{selectedLabel||value}</option>}{flatten(options).map((node,index)=><option key={`${node.value}:${index}`} value={node.value}>{node.selectionLabel||node.label}</option>)}</select>{iconOnly?<FolderTree className="folder-control-symbol" size={18} aria-hidden="true"/>:<ChevronDown className="tb-select-chevron" size={14} aria-hidden="true"/>}</span>
  {open&&createPortal(<div ref={menu} id={id} className="tb-select-menu folder-select-menu" role="listbox" aria-label={label} style={position} onPointerDown={event=>event.preventDefault()}>
   <header>{path.length?<button type="button" aria-label="返回上一级" onClick={back}><ArrowLeft size={15}/></button>:<Folder size={16}/>}<strong>{current?.label||placeholder}</strong>{headerActions&&<span className="folder-menu-actions">{headerActions}</span>}</header>
   {rows.map((row,index)=><button type="button" key={`${row.value||row.label}:${index}`} role="option" id={`${id}-${index}`} data-index={index} data-active={active===index} aria-selected={row.value!==undefined&&value===row.value} disabled={row.disabled} tabIndex={-1} onPointerMove={()=>setActive(index)} onClick={()=>choose(index)}>
    {Array.isArray(row.children)?<Folder size={16}/>:row.value?<FileText size={15}/>:null}<span>{row.label}</span>{Array.isArray(row.children)?<ChevronRight size={15}/>:value===row.value?<Check size={14}/>:null}
   </button>)}
   {!rows.length&&<p>此分类暂未收录比赛</p>}
  </div>,control.current?.closest('dialog')||document.body)}
 </>;
}
