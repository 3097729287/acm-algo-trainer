import Tooltip from './Tooltip.jsx';

export default function SortDirection({descending=false,onChange,label='切换排序方向'}) {
 return <Tooltip text={descending?'当前倒序，点击切换正序':'当前正序，点击切换倒序'}><button type="button" className="icon-button sort-direction" aria-label={label} aria-pressed={descending} data-order={descending?'desc':'asc'} onClick={()=>onChange(!descending)}>
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><g opacity={descending ? .35 : 1}><path d="M8 19V5m-4 4 4-4 4 4"/></g><g opacity={descending ? 1 : .35}><path d="M16 5v14m-4-4 4 4 4-4"/></g></svg>
 </button></Tooltip>;
}
