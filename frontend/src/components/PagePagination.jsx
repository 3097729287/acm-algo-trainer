import {ChevronLeft,ChevronRight} from 'lucide-react';
import {useEffect,useState} from 'react';
import './PagePagination.css';

export default function PagePagination({label,count,page,pages,onPrevious,onNext,onPageChange,previousLabel='上一页',nextLabel='下一页',previousDisabled=false,nextDisabled=false}) {
 const [draft,setDraft]=useState(String(page));
 useEffect(()=>setDraft(String(page)),[page,pages]);
 const editable=typeof onPageChange==='function'&&Number.isFinite(pages)&&pages>=1;
 const jump=event=>{
  if(event.isComposing||event.nativeEvent?.isComposing)return;
  if(event.key==='Escape'){event.preventDefault();event.stopPropagation();setDraft(String(page));return;}
  if(event.key!=='Enter')return;
  event.preventDefault();event.stopPropagation();
  if(!draft){setDraft(String(page));return;}
  const target=Math.max(1,Math.min(pages,Number(draft)));
  setDraft(String(target));if(target!==page)onPageChange(target);
 };
 return <nav className="library-pagination page-pagination" data-pagination aria-label={label}>
  <span className="pagination-total" role="status">{count}</span>
  <div className="pagination-actions">
   <button type="button" aria-label={previousLabel} disabled={previousDisabled||page<=1} onClick={onPrevious}><ChevronLeft size={15} aria-hidden="true"/><span>上一页</span></button>
   <span className="pagination-position">第 {editable?<input className="pagination-page-input" aria-label="跳转页码" title="输入页码，按回车跳转" type="text" inputMode="numeric" pattern="[0-9]*" maxLength={10} value={draft} disabled={pages===1} style={{width:`${Math.max(2,String(pages).length)}ch`}} onFocus={event=>event.target.select()} onChange={event=>{if(/^\d*$/.test(event.target.value))setDraft(event.target.value);}} onBlur={()=>setDraft(String(page))} onKeyDown={jump}/>:page}{pages!=null?` / ${pages}`:''} 页</span>
   <button type="button" aria-label={nextLabel} disabled={nextDisabled||(pages!=null&&page>=pages)} onClick={onNext}><span>下一页</span><ChevronRight size={15} aria-hidden="true"/></button>
  </div>
 </nav>;
}
