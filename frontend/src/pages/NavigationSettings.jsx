import { Layers,RotateCcw } from 'lucide-react';
import {ESSENTIAL_PAGES,PAGE_LEVELS,hiddenPages} from '@/lib/navigationVisibility.js';
import {NAVIGATION_ORDER} from '@/lib/navigationDefaults.js';
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
 const hidden=hiddenPages(prefs.hiddenNavPages);
 const toggle=id=>setPrefs(previous=>({...previous,hiddenNavPages:hiddenPages(previous.hiddenNavPages).includes(id)?hiddenPages(previous.hiddenNavPages).filter(value=>value!==id):hiddenPages([...hiddenPages(previous.hiddenNavPages),id])}));
 return <section className="settings-navigation" aria-label="板块显示"><header className="progress-section-heading"><h2><Layers size={19}/>板块显示</h2><button type="button" className="icon-button" aria-label="重置板块顺序" title="重置板块顺序" onClick={()=>setPrefs(previous=>({...previous,navOrder:[...NAVIGATION_ORDER]}))}><RotateCcw size={17}/></button></header><div className="navigation-visibility-grid">{orderedPages(pages,prefs).map(page=>{
  const essential=ESSENTIAL_PAGES.includes(page.id),visible=!hidden.includes(page.id),locked=Number.isFinite(level)&&level<PAGE_LEVELS[page.id];
  return <label className="navigation-visibility-item" data-hidden={!visible} key={page.id}><page.icon size={19} aria-hidden="true"/><span>{page.label}</span><input className="toggle" type="checkbox" aria-label={`显示 ${page.label}`} title={essential?'此板块始终保留':locked?`Lv.${PAGE_LEVELS[page.id]} 解锁`:undefined} checked={visible} disabled={essential} onChange={()=>toggle(page.id)}/></label>;
 })}</div></section>;
}
