import { ArrowDown, ArrowUp, Eye, EyeOff, Layers, LockKeyhole, RotateCcw } from 'lucide-react';
import Tooltip from '../components/Tooltip.jsx';
import {ESSENTIAL_PAGES,PAGE_LEVELS,hiddenPages} from '@/lib/navigationVisibility.js';
import './NavigationSettings.css';

export function orderedPages(pages, preferences) {
  const order = Array.isArray(preferences.navOrder) ? preferences.navOrder : [];
  const groups={...(preferences.navGroups||{})};
  if (groups.mine?.trim() === '训练与待办') delete groups.mine;
  // Activity has its own entry; retire the previously forced growth group.
  for (const id of ['growth','activity','goals']) delete groups[id];
  return [...pages].sort((left, right) => {
    const a = order.indexOf(left.id), b = order.indexOf(right.id);
    return (a < 0 ? 100 + pages.indexOf(left) : a) - (b < 0 ? 100 + pages.indexOf(right) : b);
  }).map(page => ({ ...page, label: preferences.navLabels?.[page.id]?.trim() || page.label, group: groups[page.id]?.trim() || '' }));
}

export default function NavigationSettings({pages,prefs,setPrefs,level}) {
 const ordered=orderedPages(pages,prefs);
 const rename=(field,id,value)=>setPrefs(previous=>({...previous,[field]:{...previous[field],[id]:value}}));
 function move(id,direction){const next=ordered.map(page=>page.id),index=next.indexOf(id),target=index+direction;if(target<0||target>=next.length)return;[next[index],next[target]]=[next[target],next[index]];setPrefs(previous=>({...previous,navOrder:next}));}
 const hidden=hiddenPages(prefs.hiddenNavPages);
 const toggle=id=>setPrefs(previous=>({...previous,hiddenNavPages:hiddenPages(previous.hiddenNavPages).includes(id)?hiddenPages(previous.hiddenNavPages).filter(value=>value!==id):hiddenPages([...hiddenPages(previous.hiddenNavPages),id])}));
 const controls=(page,index)=>{const essential=ESSENTIAL_PAGES.includes(page.id),locked=Number.isFinite(level)&&level<PAGE_LEVELS[page.id],visible=!hidden.includes(page.id);return <span className="navigation-reorder"><button type="button" aria-label={`${visible?'隐藏':'显示'} ${page.label}`} title={essential?'此板块始终保留':locked?`Lv.${PAGE_LEVELS[page.id]} 解锁`:visible?'隐藏板块':'显示板块'} aria-pressed={!visible} disabled={essential} onClick={()=>toggle(page.id)}>{essential?<LockKeyhole size={17}/>:visible?<Eye size={17}/>:<EyeOff size={17}/>}</button><button type="button" aria-label={`上移 ${page.label}`} disabled={index===0} onClick={()=>move(page.id,-1)}><ArrowUp size={17}/></button><button type="button" aria-label={`下移 ${page.label}`} disabled={index===ordered.length-1} onClick={()=>move(page.id,1)}><ArrowDown size={17}/></button></span>;};
 return <section className="settings-navigation"><header className="progress-section-heading"><h2><Layers size={19}/>导航与页面组合</h2><Tooltip text="相同分组名会合并导航入口。箭头调整顺序。眼睛按钮控制显示；等级达到后解锁对应板块。"><button type="button" className="icon-button" aria-label="恢复默认导航" onClick={()=>setPrefs(previous=>({...previous,navOrder:[],navLabels:{},navGroups:{},hiddenNavPages:[]}))}><RotateCcw size={16}/></button></Tooltip></header>
 <div className="navigation-editor" aria-label="自定义导航栏"><div className="navigation-editor-heading"><span>页面名称</span><span>页面组合</span><span>顺序</span></div>{ordered.map((page,index)=><div className="navigation-editor-row" key={page.id}><label><page.icon size={18}/><input aria-label={`导航名称 ${page.id}`} value={prefs.navLabels?.[page.id]??pages.find(item=>item.id===page.id).label} maxLength={18} onChange={event=>rename('navLabels',page.id,event.target.value)}/></label><input aria-label={`页面组合 ${page.id}`} value={prefs.navGroups?.[page.id]||''} maxLength={18} onChange={event=>rename('navGroups',page.id,event.target.value)}/>{controls(page,index)}</div>)}</div></section>;
}
