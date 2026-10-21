import {X} from 'lucide-react';
import BoundedNumber from './BoundedNumber.jsx';
import ThemedSelect from './ThemedSelect.jsx';
import FilterMenu from './FilterMenu.jsx';
import { CONTEST_SHELVES } from './ContestTabs.jsx';
import { CONTEST_KINDS } from '@/lib/contestShelves.js';
export default function ProblemFilters({ value, onChange, onReset, onSave, categories = [], views = [], onClear, clearDisabled, onDeleteView }) {
  const walk = nodes => nodes.flatMap(node => [node, ...walk(node.children || [])]);
  return <FilterMenu label="筛选题目" active={!!value.favoritesOnly || value.sort!=='contestDate' || value.desc || value.shelf !== 'all' || !!value.kind || !!value.category || !!value.result || value.min !== 0 || value.max !== 10000} onReset={onReset}>
    <label className="filter-field"><span>收藏</span><input type="checkbox" aria-label="收藏题目筛选" checked={!!value.favoritesOnly} onChange={event=>onChange({favoritesOnly:event.target.checked})}/></label>
    <label className="filter-field"><span>排序</span><ThemedSelect aria-label="排序方式" value={value.sort} onChange={event=>onChange({sort:event.target.value})}><option value="contestDate">比赛时间</option><option value="contest">场次</option><option value="difficulty">难度</option><option value="date">最近练习</option><option value="title">题名</option></ThemedSelect></label>
    <label className="filter-field"><span>方向</span><ThemedSelect aria-label="题目排序方向" value={value.desc?'desc':'asc'} onChange={event=>onChange({desc:event.target.value==='desc'})}><option value="asc">正序</option><option value="desc">倒序</option></ThemedSelect></label>
    <details className="filter-submenu"><summary>比赛分类</summary><div className="filter-choice-grid">{CONTEST_SHELVES.map(([id,label]) => <button key={id} type="button" aria-pressed={value.shelf===id} onClick={() => onChange({shelf:id,platform:'',contest:''})}>{label}</button>)}</div><div className="filter-choice-grid">{CONTEST_KINDS.map(([id,label]) => <button key={id} type="button" aria-pressed={value.kind===id} onClick={() => onChange({kind:value.kind===id?'':id})}>{label}</button>)}</div></details>
    <details className="filter-submenu"><summary>知识点</summary><div className="filter-knowledge-list"><button type="button" aria-pressed={!value.category} onClick={() => onChange({category:null})}>全部知识点</button>{walk(categories).map((node,i) => <button type="button" key={node.name+i} aria-pressed={value.category?.name===node.name} onClick={() => onChange({category:node})}>{node.name}</button>)}</div></details>
    <label className="filter-field"><span>难度</span><div className="inline-difficulty-range"><BoundedNumber aria-label="最低难度" min={0} max={10000} step={100} value={value.min} onChange={event => onChange({min:Number(event.target.value)})}/><span>—</span><BoundedNumber aria-label="最高难度" min={0} max={10000} step={100} value={value.max} onChange={event => onChange({max:Number(event.target.value)})}/></div></label>
    <label className="filter-field"><span>提交结果</span><ThemedSelect aria-label="提交结果筛选" value={value.result} onChange={event => onChange({result:event.target.value})}><option value="">全部结果</option><option value="accepted">AC</option><option value="pending">尚未 AC</option><option value="sample">样例通过</option>{['WA','CE','TLE','MLE','RE'].map(item => <option key={item}>{item}</option>)}</ThemedSelect></label>
    {views.length>0 && <details className="filter-submenu"><summary>已保存筛选</summary>{views.map(view => <div className="saved-filter" key={view.id}><button type="button" onClick={() => onChange(view.filters)}>{view.name}</button><button type="button" aria-label={`删除已保存筛选 ${view.name}`} onClick={()=>onDeleteView?.(view.id)}><X size={14}/></button></div>)}</details>}
    <button type="button" className="secondary" data-close-filter onClick={onSave}>保存筛选</button>{onClear&&<button type="button" className="text-button" data-close-filter aria-label="清空我的训练" disabled={clearDisabled} onClick={onClear}>清空我的训练</button>}
  </FilterMenu>;
}
