import { ArrowDown, ArrowUp, Layers, RotateCcw } from 'lucide-react';
import Tooltip from '../components/Tooltip.jsx';

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

export default function NavigationSettings({ pages, prefs, setPrefs, orderOnly=false }) {
  const ordered = orderedPages(pages, prefs);
  const move = (id, direction) => {
    const next = ordered.map(page => page.id), index = next.indexOf(id), target = index + direction;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    setPrefs(previous => ({ ...previous, navOrder: next }));
  };
  const rename = (field, id, value) => setPrefs(previous => ({ ...previous, [field]: { ...previous[field], [id]: value } }));
  return <section className={`settings-navigation ${orderOnly?'navigation-order-only':'navigation-labels-only'}`}>
    <div className="settings-page-description"><h2><Layers size={18} />{orderOnly?'自定义顺序':'导航与页面组合'}</h2><Tooltip text="相同分组名会合并为一个导航入口。下方“自定义顺序”可调整入口顺序。"/></div>
    <div className="navigation-settings-content">
    <div className="progress-section-heading"><span/><Tooltip text="恢复默认导航"><button className="icon-button" aria-label="恢复默认导航" onClick={() => setPrefs(previous => ({ ...previous, ...(orderOnly?{navOrder:[]}:{navLabels:{},navGroups:{}}) }))}><RotateCcw size={14} /></button></Tooltip></div>
    <div className="navigation-editor" aria-label="自定义导航栏">
      <div className="navigation-editor-heading"><span>页面名称</span>{!orderOnly&&<span>页面组合（可选）</span>}{orderOnly&&<span>顺序</span>}</div>
      {ordered.map((page, index) => <div className="navigation-editor-row" key={page.id}>
        <label><page.icon size={16} />{orderOnly?<span>{page.label}</span>:<input aria-label={`导航名称 ${page.id}`} value={prefs.navLabels?.[page.id] ?? pages.find(item => item.id === page.id).label} maxLength={18} onChange={event => rename('navLabels', page.id, event.target.value)} />}</label>
        {!orderOnly&&<input aria-label={`页面组合 ${page.id}`} value={prefs.navGroups?.[page.id] || ''} maxLength={18} placeholder="分组名称" onChange={event => rename('navGroups', page.id, event.target.value)} />}
        {orderOnly&&<span className="navigation-reorder"><Tooltip text={`上移 ${page.label}`}><button aria-label={`上移 ${page.label}`} disabled={index === 0} onClick={() => move(page.id, -1)}><ArrowUp size={16} /></button></Tooltip><Tooltip text={`下移 ${page.label}`}><button aria-label={`下移 ${page.label}`} disabled={index === ordered.length - 1} onClick={() => move(page.id, 1)}><ArrowDown size={16} /></button></Tooltip></span>}
      </div>)}
    </div>
    </div>
  </section>;
}
