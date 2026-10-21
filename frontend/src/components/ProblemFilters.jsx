import BoundedNumber from '@/components/BoundedNumber.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import { BookmarkPlus } from 'lucide-react';

export default function ProblemFilters({ value, onChange, onReset, onSave }) {
  return <div className="inline-problem-filters" role="group" aria-label="题目筛选条件">
    <div className="inline-difficulty-range">
      <BoundedNumber aria-label="最低难度" placeholder="最低难度" type="number" min={0} max={10000} step={100} value={value.min} onChange={event => onChange({ min: event.target.value })} />
      <span aria-hidden="true">–</span>
      <BoundedNumber aria-label="最高难度" placeholder="最高难度" type="number" min={0} max={10000} step={100} value={value.max} onChange={event => onChange({ max: event.target.value })} />
    </div>
    <ThemedSelect aria-label="提交结果筛选" value={value.result} onChange={event => onChange({ result: event.target.value })}>
      <option value="">全部结果</option><option value="accepted">AC</option><option value="pending">尚未 AC</option><option value="sample">样例通过</option>
      {['WA', 'CE', 'TLE', 'MLE', 'RE'].map(item => <option key={item} value={item}>{item}</option>)}
    </ThemedSelect>
    <button className="text-button" onClick={onReset}>重置</button>
    <button className="secondary save-filter" onClick={onSave}><BookmarkPlus size={14} />保存筛选</button>
  </div>;
}
