import CatalogName from './CatalogName.jsx';
import PagePagination from '@/components/PagePagination.jsx';
import {useRef,useState,useEffect} from 'react';
import {useFittedPageSize} from '@/lib/useFittedPageSize.js';
import {catalogPaths,catalogPathMatches,catalogEntries,normalizeCatalogPath} from '@/lib/contestCatalog.js';
export {catalogSegments} from '@/lib/contestCatalog.js';
import { ChevronLeft, ChevronRight, FileText, Folder, House } from 'lucide-react';
import './CatalogExplorer.css';

const pathOf = scope => normalizeCatalogPath(scope.path || (scope.platform ? [scope.platform] : []));
const contestKey = row => row.groupKey || `${row.platform || ''}::${row.contest}`;
const schoolSources = [{label:'Gym 726517',url:'https://codeforces.com/gym/726517'}, {label:'1024数学专场考核',url:'https://ac.nowcoder.com/acm/contest/142622'}];
const cardLevel = (row, path) => {
  return catalogPaths(row).some(parts=>path.every((part,index)=>parts[index]===part)&&(parts.length === path.length + 1 || (parts[0] === 'XCPC'
    && parts.length === path.length + 2 && ['正赛', '热身赛'].includes(parts.at(-1)))));
};
export function catalogMatches(row, scope) {
  return catalogPathMatches(row,pathOf(scope));
}
export function CatalogPath({ scope, onChange }) {
  const path = pathOf(scope);
  return <nav className="catalog-path" aria-label="题目浏览路径">
    <button type="button" data-folder-up aria-label="返回上一级文件夹" title="返回上一级 · Backspace" disabled={!path.length} onClick={()=>onChange({stage:path.length>1?'contests':'platforms',path:path.slice(0,-1)})}><ChevronLeft size={17}/></button>
    <button aria-label="全部平台" onClick={() => onChange({ stage: 'platforms', path: [] })}><House size={16}/></button>
    {path.map((part, index) => <span key={index}><ChevronRight size={13}/><button aria-current={index === path.length - 1 ? 'page' : undefined} onClick={() => onChange({ stage: index === path.length - 1 ? scope.stage : 'contests', path: path.slice(0, index + 1) })}><CatalogName>{part}</CatalogName></button></span>)}
  </nav>;
}
export default function CatalogExplorer({ rows, scope, onChange, onContest, renderContest, paginate=false,descending=true }) {
  const path = pathOf(scope), selected = rows.filter(row => catalogMatches(row, scope));
  const entries = catalogEntries(rows, path,{descending}).flatMap(entry => renderContest && entry.items.length && (entry.leaf || entry.items.every(row=>cardLevel(row,path))) ? [...new Map(entry.items.map(row=>[contestKey(row),row])).values()].map(row=>({...entry,items:[row],leaf:true,path:[...entry.path,contestKey(row)]})) : [entry]);
  const panel=useRef(null),[page,setPage]=useState(1);
  const key=JSON.stringify([path,descending]),size=useFittedPageSize(panel,key,'.catalog-folder-row, .catalog-contest-entry');
  useEffect(()=>setPage(1),[key]);
  const pages=Math.max(1,Math.ceil(entries.length/size)),current=Math.min(page,pages);
  const visible=paginate?entries.slice((current-1)*size,current*size):entries;
  return <><section ref={panel} className={`catalog-explorer${paginate?" catalog-paged":""}`} aria-label={onContest ? '比赛层级浏览' : '题库层级浏览'}>
    {!onContest && <button className="catalog-folder-row" onClick={() => onChange({ ...scope, stage: 'problems' })}><FileText size={19}/><strong>全部题目</strong><span>{selected.length}</span><ChevronRight size={16}/></button>}
    {!entries.length&&path[0]!=='校队训练'&&<p className="catalog-empty" role="status">此分类暂未收录比赛</p>}
    {path[0]==='校队训练'&&path.length===1&&schoolSources.filter(source=>!rows.some(row=>row.url?.startsWith(source.url+'/'))).map(source=><a key={source.url} className="catalog-folder-row" href={source.url} target="_blank" rel="noreferrer"><FileText size={20}/><strong><CatalogName>{source.label}</CatalogName></strong><span>等待原站公开题面 · 前往原站</span><ChevronRight size={16}/></a>)}
    {visible.map(({label:name, items, path:next, leaf}) => renderContest && items.length>0 && (leaf || items.every(row=>cardLevel(row,path))) ? <div className="catalog-contest-entry" key={JSON.stringify(next)}>{[...new Map(items.map(row=>[contestKey(row),row])).values()].map(row=><div key={contestKey(row)}>{renderContest(row)}</div>)}</div> : <button className="catalog-folder-row" key={JSON.stringify(next)} onClick={() => {
      if (leaf && onContest) onContest(items[0]);
      else onChange({ path: next, stage: leaf ? 'problems' : 'contests' });
    }}><Folder size={20}/><strong><CatalogName>{name}</CatalogName></strong><span>{onContest ? new Set(items.map(row => row.groupKey || `${row.platform}:${row.contest}`)).size : items.length}</span><ChevronRight size={16}/></button>)}
  </section>{paginate&&entries.length>0&&<PagePagination label="目录分页" count={`${entries.length} 项`} page={current} pages={pages} onPageChange={setPage} onPrevious={()=>setPage(current-1)} onNext={()=>setPage(current+1)}/>}</>;
}
