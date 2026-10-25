import {useEffect} from 'react';
const visible=node=>node.getClientRects().length>0&&!node.closest('[inert],[hidden],[aria-hidden=true]');
export default function useNavigationKeys() {
  useEffect(()=>{
    const key=event=>{
      if(event.defaultPrevented||event.isComposing||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;
      if(event.target.closest?.('input,textarea,select,[contenteditable]:not([contenteditable=false]),.cm-editor,[role=slider],[role=grid],[role=tree],video'))return;
      if(document.querySelector('dialog[open],[aria-modal=true],[data-popconfirm],.tb-select-menu,.filter-popover'))return;
      if(event.key==='Backspace') {
        const up=[...document.querySelectorAll('[data-folder-up]')].find(visible);
        if(up){event.preventDefault();if(!up.disabled)up.click();}
        return;
      }
      const direction=['ArrowLeft','a','A'].includes(event.key)?'上一页':['ArrowRight','d','D'].includes(event.key)?'下一页':null;
      if(!direction)return;
      const containers=[...document.querySelectorAll('.library-pagination,.competition-pagination,.submission-page-controls,.activity-pagination,[data-pagination]')].filter(visible);
      if(containers.length!==1)return;
      const button=[...containers[0].querySelectorAll('button')].find(node=>(node.getAttribute('aria-label')||node.textContent).includes(direction));
      if(button){event.preventDefault();if(!button.disabled)button.click();}
    };
    window.addEventListener('keydown',key);
    return()=>window.removeEventListener('keydown',key);
  },[]);
}
