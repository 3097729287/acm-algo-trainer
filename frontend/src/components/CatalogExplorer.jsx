import {catalogSegments,catalogFolders} from '@/lib/contestCatalog.js';
export {catalogSegments} from '@/lib/contestCatalog.js';
import { compareContestNewest } from '@/lib/practiceMetadata.js';
import { ChevronRight, FileText, Folder, House } from 'lucide-react';
import './CatalogExplorer.css';

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
export default function CatalogExplorer({ rows, scope, onChange, onContest, renderContest }) {
  const path = pathOf(scope), selected = rows.filter(row => catalogMatches(row, scope)), groups = new Map();
  for (const row of selected) {
    const name = catalogSegments(row)[path.length];
    if (!name) continue;
    if (!groups.has(name)) groups.set(name, []);
    groups.get(name).push(row);
  }
  for(const name of catalogFolders(path))if(!groups.has(name))groups.set(name,[]);
  const entries = [...groups].sort(([a,left], [b,right]) => {
    if(!left.length||!right.length)return a.localeCompare(b,'zh-CN',{numeric:true});
    if (left.every(row=>catalogSegments(row).length===path.length+1)&&right.every(row=>catalogSegments(row).length===path.length+1)) return compareContestNewest({...left[0],rows:left},{...right[0],rows:right});
    if (/^20\d{2}年$/.test(a)&&/^20\d{2}年$/.test(b)) return b.localeCompare(a);
    return a.localeCompare(b, 'zh-CN', { numeric: true });
  });
  return <section className="catalog-explorer" aria-label={onContest ? '比赛层级浏览' : '题库层级浏览'}>
    {!onContest && <button className="catalog-folder-row" onClick={() => onChange({ ...scope, stage: 'problems' })}><FileText size={19}/><strong>全部题目</strong><span>{selected.length}</span><ChevronRight size={16}/></button>}
    {!entries.length&&<p className="catalog-empty" role="status">此分类暂未收录比赛</p>}
    {entries.map(([name, items]) => renderContest && items.length>0 && items.every(row=>catalogSegments(row).length===path.length+1) && new Set(items.map(row=>row.groupKey)).size===1 ? <div className="catalog-contest-entry" key={name}>{renderContest(items[0])}</div> : <button className="catalog-folder-row" key={name} onClick={() => {
      const next = [...path, name], leaf = items.length>0&&items.every(row => catalogSegments(row).length === next.length);
      if (leaf && onContest) onContest(items[0]);
      else onChange({ path: next, stage: leaf ? 'problems' : 'contests' });
    }}><Folder size={20}/><strong>{name}</strong><span>{onContest ? new Set(items.map(row => row.groupKey || `${row.platform}:${row.contest}`)).size : items.length}</span><ChevronRight size={16}/></button>)}
  </section>;
}
