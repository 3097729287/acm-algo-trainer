import {X} from 'lucide-react';
import {useMemo} from 'react';
import FolderSelect from './FolderSelect.jsx';
import {canonicalKnowledgeName} from '@/lib/knowledgeNames.js';
import {contestFilterOptions} from '@/lib/contestCatalog.js';
import DifficultyRange from './DifficultyRange.jsx';
import ThemedSelect from './ThemedSelect.jsx';
import FilterMenu from './FilterMenu.jsx';
export default function ProblemFilters({ value, onChange, onReset, onSave, rows=[], categories = [], views = [], onClear, clearDisabled, onDeleteView }) {
  const walk = nodes => nodes.flatMap(node => [node, ...walk(node.children || [])]);
  const knowledgeOptions=useMemo(()=>{const build=nodes=>nodes.map(node=>{const children=build(node.children||[]);return {label:canonicalKnowledgeName(node.name),value:node.name,...(children.length?{children}:{})};});return build(categories);},[categories]);
  const contestOptions=useMemo(()=>contestFilterOptions(rows),[rows]);
  return <FilterMenu label="筛选题目" active={!!value.favoritesOnly || value.sort!=='contestDate' || value.shelf !== 'all' || !!value.kind || !!value.catalogPath?.length || !!value.category || !!value.result || value.min !== 0 || value.max !== 10000} onReset={onReset}>
    <label className="filter-field"><span>收藏</span><input type="checkbox" aria-label="收藏题目筛选" checked={!!value.favoritesOnly} onChange={event=>onChange({favoritesOnly:event.target.checked})}/></label>
    <label className="filter-field"><span>排序</span><ThemedSelect aria-label="排序方式" value={value.sort} onChange={event=>onChange({sort:event.target.value})}><option value="contestDate">比赛时间</option><option value="contest">场次</option><option value="difficulty">难度</option><option value="date">最近练习</option><option value="title">题名</option></ThemedSelect></label>
    <label className="filter-field"><span>比赛分类</span><FolderSelect label="筛选比赛分类" placeholder="全部比赛" options={contestOptions} value={value.catalogPath?.length?JSON.stringify(value.catalogPath):''} onChange={event=>onChange({catalogPath:event.target.value?JSON.parse(event.target.value):[],shelf:'all',kind:'',platform:'',contest:''})}/></label>
    <label className="filter-field"><span>知识点</span><FolderSelect label="筛选知识点" placeholder="全部知识点" options={knowledgeOptions} value={value.category?.name||''} onChange={event=>onChange({category:walk(categories).find(node=>node.name===event.target.value)||null})}/></label>
    <div className="filter-field difficulty-filter"><span>难度</span><DifficultyRange value={value} onChange={onChange}/></div>
    <label className="filter-field"><span>提交结果</span><ThemedSelect aria-label="提交结果筛选" value={value.result} onChange={event => onChange({result:event.target.value})}><option value="">全部结果</option><option value="accepted">AC</option><option value="pending">尚未 AC</option><option value="sample">样例通过</option>{['WA','CE','TLE','MLE','RE'].map(item => <option key={item}>{item}</option>)}</ThemedSelect></label>
    {views.length>0 && <details className="filter-submenu"><summary>已保存筛选</summary>{views.map(view => <div className="saved-filter" key={view.id}><button type="button" onClick={() => onChange(view.filters)}>{view.name}</button><button type="button" aria-label={`删除已保存筛选 ${view.name}`} onClick={()=>onDeleteView?.(view.id)}><X size={14}/></button></div>)}</details>}
    <button type="button" className="secondary" data-close-filter onClick={onSave}>保存筛选</button>{onClear&&<button type="button" className="text-button" data-close-filter aria-label="清空我的训练" disabled={clearDisabled} onClick={onClear}>清空我的训练</button>}
  </FilterMenu>;
}
