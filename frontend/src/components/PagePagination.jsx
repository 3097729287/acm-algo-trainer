import {ChevronLeft,ChevronRight} from 'lucide-react';
import './PagePagination.css';

export default function PagePagination({label,count,page,pages,onPrevious,onNext,previousLabel='上一页',nextLabel='下一页',previousDisabled=false,nextDisabled=false}) {
 return <nav className="library-pagination page-pagination" data-pagination aria-label={label}>
  <span className="pagination-total" role="status">{count}</span>
  <div className="pagination-actions">
   <button type="button" aria-label={previousLabel} disabled={previousDisabled||page<=1} onClick={onPrevious}><ChevronLeft size={15} aria-hidden="true"/><span>上一页</span></button>
   <span className="pagination-position">第 {page}{pages!=null?` / ${pages}`:''} 页</span>
   <button type="button" aria-label={nextLabel} disabled={nextDisabled||(pages!=null&&page>=pages)} onClick={onNext}><span>下一页</span><ChevronRight size={15} aria-hidden="true"/></button>
  </div>
 </nav>;
}
