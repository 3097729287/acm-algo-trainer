import { ArrowDown, ArrowUp, Layers, RotateCcw } from 'lucide-react';

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

export default function NavigationSettings({ pages, prefs, setPrefs }) {
  const ordered = orderedPages(pages, prefs);
  const move = (id, direction) => {
    const next = ordered.map(page => page.id), index = next.indexOf(id), target = index + direction;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    setPrefs(previous => ({ ...previous, navOrder: next }));
  };
  const rename = (field, id, value) => setPrefs(previous => ({ ...previous, [field]: { ...previous[field], [id]: value } }));
  return <details className="settings-navigation">
    <summary><Layers size={18} /><strong>导航与页面组合</strong><span>名称 · 分组 · 顺序</span></summary>
    <div className="navigation-settings-content">
    <div className="progress-section-heading"><p className="progress-small">相同分组名会合并为一个导航入口。</p><button className="text-button" onClick={() => setPrefs(previous => ({ ...previous, navOrder: [], navLabels: {}, navGroups: {} }))}><RotateCcw size={14} />恢复默认</button></div>
    <div className="navigation-editor" aria-label="自定义导航栏">
      <div className="navigation-editor-heading"><span>页面名称</span><span>页面组合（可选）</span><span>顺序</span></div>
      {ordered.map((page, index) => <div className="navigation-editor-row" key={page.id}>
        <label><page.icon size={16} /><input aria-label={`导航名称 ${page.id}`} value={prefs.navLabels?.[page.id] ?? pages.find(item => item.id === page.id).label} maxLength={18} onChange={event => rename('navLabels', page.id, event.target.value)} /></label>
        <input aria-label={`页面组合 ${page.id}`} value={prefs.navGroups?.[page.id] || ''} maxLength={18} placeholder="例如：学习记录" onChange={event => rename('navGroups', page.id, event.target.value)} />
        <span className="navigation-reorder"><button aria-label={`上移 ${page.label}`} disabled={index === 0} onClick={() => move(page.id, -1)}><ArrowUp size={16} /></button><button aria-label={`下移 ${page.label}`} disabled={index === ordered.length - 1} onClick={() => move(page.id, 1)}><ArrowDown size={16} /></button></span>
      </div>)}
    </div>
    </div>
  </details>;
}
