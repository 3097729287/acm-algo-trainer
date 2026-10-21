import { ChevronRight, FileText, Folder, House } from 'lucide-react';
import './CatalogExplorer.css';

export function catalogSegments(row) {
  const name = row.contest || row.name || '其他题目';
  const fullName = `${name} ${row.contestFullName || ''}`;
  const xcpc = !/蓝桥/.test(fullName) && (row.series === 'XCPC' || /ICPC|CCPC|XCPC|区域赛|邀请赛|省赛|网络.*赛/i.test(fullName));
  if (xcpc) {
    const type = /网络|预选|online|qualification/i.test(fullName) ? '网络预选赛'
      : /省赛|省(?:第[一二三四五六七八九十\d]+届)?(?:ICPC|CCPC|大学生|程序)/i.test(fullName) ? '省赛'
      : /邀请|invitational/i.test(fullName) ? '邀请赛'
      : /总决赛|world finals/i.test(fullName) ? '总决赛'
      : /分区赛|subregional/i.test(fullName) ? '分区赛'
      : /CCPC/i.test(fullName) ? 'CCPC'
      : /ICPC/i.test(fullName) ? 'ICPC' : '其他赛事';
    const year = fullName.match(/20\d{2}/)?.[0] || String(row.contestDate || row.startedAt || '').match(/^20\d{2}/)?.[0];
    const warmup = /热身|warm.?up/i.test(fullName);
    const event = name.replace(/[（(]\s*(?:热身赛?|正式赛|正赛|warm.?up)\s*[）)]/gi, '').trim();
    return ['XCPC', 'ACM', type, year ? `${year}年` : '年份待核实', event, warmup ? '热身赛' : '正赛'];
  }
  const series = row.series && row.series !== row.platform ? row.series
    : name.match(/练习赛|小白月赛|周赛|月赛|挑战赛|入门赛|基础赛|教育赛|ABC|ARC|Div\.?\s*[1-4](?:\s*\+\s*Div\.?\s*[1-4])?/i)?.[0] || '其他比赛';
  return [row.platform || '其他平台', series, name];
}

const pathOf = scope => scope.path || (scope.platform ? [scope.platform] : []);
export function catalogMatches(row, scope) {
  const path = pathOf(scope), parts = catalogSegments(row);
  return path.every((part, index) => parts[index] === part);
}
export function CatalogPath({ scope, onChange }) {
  const path = pathOf(scope);
  return <nav className="catalog-path" aria-label="题目浏览路径">
    <button aria-label="全部平台" onClick={() => onChange({ stage: 'platforms', path: [] })}><House size={16}/></button>
    {path.map((part, index) => <span key={index}><ChevronRight size={13}/><button aria-current={index === path.length - 1 ? 'page' : undefined} onClick={() => onChange({ stage: index === path.length - 1 ? scope.stage : 'contests', path: path.slice(0, index + 1) })}>{part}</button></span>)}
  </nav>;
}
export default function CatalogExplorer({ rows, scope, onChange, onContest }) {
  const path = pathOf(scope), selected = rows.filter(row => catalogMatches(row, scope)), groups = new Map();
  for (const row of selected) {
    const name = catalogSegments(row)[path.length];
    if (!name) continue;
    if (!groups.has(name)) groups.set(name, []);
    groups.get(name).push(row);
  }
  const entries = [...groups].sort(([a], [b]) => a.localeCompare(b, 'zh-CN', { numeric: true }));
  return <section className="catalog-explorer" aria-label={onContest ? '比赛层级浏览' : '题库层级浏览'}>
    {!onContest && <button className="catalog-folder-row" onClick={() => onChange({ ...scope, stage: 'problems' })}><FileText size={19}/><strong>全部题目</strong><span>{selected.length}</span><ChevronRight size={16}/></button>}
    {entries.map(([name, items]) => <button className="catalog-folder-row" key={name} onClick={() => {
      const next = [...path, name], leaf = items.every(row => catalogSegments(row).length === next.length);
      if (leaf && onContest) onContest(items[0]);
      else onChange({ path: next, stage: leaf ? 'problems' : 'contests' });
    }}><Folder size={20}/><strong>{name}</strong><span>{onContest ? new Set(items.map(row => row.groupKey || `${row.platform}:${row.contest}`)).size : items.length}</span><ChevronRight size={16}/></button>)}
  </section>;
}
