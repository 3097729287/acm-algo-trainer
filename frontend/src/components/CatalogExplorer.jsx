import {catalogSegments,catalogEntries} from '@/lib/contestCatalog.js';
export {catalogSegments} from '@/lib/contestCatalog.js';
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
  const path = pathOf(scope), selected = rows.filter(row => catalogMatches(row, scope));
  const entries = catalogEntries(rows, path);
  return <section className="catalog-explorer" aria-label={onContest ? '比赛层级浏览' : '题库层级浏览'}>
    {!onContest && <button className="catalog-folder-row" onClick={() => onChange({ ...scope, stage: 'problems' })}><FileText size={19}/><strong>全部题目</strong><span>{selected.length}</span><ChevronRight size={16}/></button>}
    {!entries.length&&<p className="catalog-empty" role="status">此分类暂未收录比赛</p>}
    {entries.map(({label:name, items, path:next, leaf}) => renderContest && leaf && new Set(items.map(row=>row.groupKey||`${row.platform}:${row.contest}`)).size===1 ? <div className="catalog-contest-entry" key={JSON.stringify(next)}>{renderContest(items[0])}</div> : <button className="catalog-folder-row" key={JSON.stringify(next)} onClick={() => {
      if (leaf && onContest) onContest(items[0]);
      else onChange({ path: next, stage: leaf ? 'problems' : 'contests' });
    }}><Folder size={20}/><strong>{name}</strong><span>{onContest ? new Set(items.map(row => row.groupKey || `${row.platform}:${row.contest}`)).size : items.length}</span><ChevronRight size={16}/></button>)}
  </section>;
}
