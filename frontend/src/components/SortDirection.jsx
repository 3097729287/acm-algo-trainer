import Tooltip from './Tooltip.jsx';

export default function SortDirection({descending=false,normalDescending=false,onChange,label='切换排序方向'}) {
 const reversed=descending!==normalDescending;
 return <Tooltip text={reversed?'当前倒序，点击切换正序':'当前正序，点击切换倒序'}><button type="button" className="icon-button sort-direction" aria-label={label} aria-pressed={reversed} data-order={descending?'desc':'asc'} data-direction={reversed?'reverse':'normal'} onClick={()=>onChange(!descending)}>
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><g opacity={reversed ? .35 : 1}><path d="M8 19V5m-4 4 4-4 4 4"/></g><g opacity={reversed ? 1 : .35}><path d="M16 5v14m-4-4 4 4 4-4"/></g></svg>
 </button></Tooltip>;
}
