import {useEffect} from 'react';
import './readingZoom.css';

const headers='.wb-top-toolbar,.wb-compact-toolbar,.lectures-detail-bar,.lecture-directory-toolbar,.wiki-reader-toolbar,.template-heading,.lab-course-header,.solution-reader-header,.study-single-controls,.study-task-previous,.study-task-next';
const bodySelectors='.tb-workbench>.wb-body,.study-pane .lecture-markdown,.study-pane .lecture-prerequisites,.study-pane .template-body,.study-pane .template-fields,.study-pane .template-notes,.study-pane .template-contest-variations,.study-pane .template-example,.study-pane .lab-lesson,.study-pane .reader-content,.lecture-reading-full .lecture-markdown,.lecture-reading-full .lecture-prerequisites,.reader-full .reader-content';
const toolbarSelectors='.tb-workbench>.wb-top-toolbar,.tb-workbench>.wb-compact-toolbar,.study-pane .lectures-detail-bar,.study-pane .lecture-directory-toolbar,.study-pane .wiki-reader-toolbar,.study-pane .template-heading,.study-pane .lab-course-header,.study-pane .solution-reader-header,.study-single-controls,.study-task-previous,.study-task-next,.lecture-reading-full .lectures-detail-bar,.lecture-reading-full .lecture-directory-toolbar,.reader-full .solution-reader-header';
const clamp=value=>Math.max(.6,Math.min(1.8,Math.round(value*100)/100));
let users=0,dispose;

export function installReadingZoom(doc=document){
  const frames=new Map(),touched=new Map(),cache=new Map(),painted=new Set();let frame=0,toast,toastTimer,removeTimer;
  const showZoom=(node,zone,percentage)=>{
    const win=doc.defaultView,root=node.closest?.('.study-pane,.reader-full,.lecture-reading-full')||node.closest?.('.tb-workbench');
    const group=node.closest?.('.study-group-header');
    const toolbar=zone==='bookmarks'?group:root?.querySelector('.wb-editor-header,.wiki-reader-toolbar,.lectures-detail-bar,.template-heading,.lab-course-header,.solution-reader-header');
    const shown=toolbar&&win.getComputedStyle(toolbar).visibility!=='hidden'&&toolbar.getBoundingClientRect().height>0;
    const bounds=(shown?toolbar:root||group||node).getBoundingClientRect();
    if(!toast){toast=doc.createElement('output');toast.className='reading-zoom-toast';toast.setAttribute('role','status');toast.setAttribute('aria-label','缩放比例');doc.body.append(toast);}
    clearTimeout(toastTimer);clearTimeout(removeTimer);toast.classList.remove('is-fading');
    toast.textContent=percentage+'%';toast.dataset.zone=zone;
    toast.classList.toggle('is-inline',Boolean(shown));
    if(shown){
      const actions=toolbar.querySelector('.wb-editor-actions')||[...toolbar.children].find((child,index)=>index>0&&child.matches('a,button')&&!child.matches('.wiki-origin-back,.wb-back-button'));
      toolbar.insertBefore(toast,actions||null);
      let zoom=1;for(let parent=toolbar;parent;parent=parent.parentElement)zoom*=parseFloat(win.getComputedStyle(parent).zoom)||1;
      toast.style.zoom=String(1/zoom);toast.style.left='';toast.style.top='';
    }else{
      doc.body.append(toast);toast.style.zoom='';
      toast.style.left=Math.max(64,Math.min(win.innerWidth-12,bounds.right-12))+'px';toast.style.top=Math.max(4,bounds.top+6)+'px';
    }
    toastTimer=setTimeout(()=>{toast?.classList.add('is-fading');removeTimer=setTimeout(()=>{toast?.remove();toast=null;},160);},1100);
  };
  const owner=()=>doc.defaultView.__tbAccountUserId||'local';
  const values=()=>{const id=owner();if(!cache.has(id)){let value={};try{value=JSON.parse(doc.defaultView.localStorage.getItem('tb.readingZoom.v1.'+id))||{};}catch{}cache.set(id,value);}return cache.get(id);};
  const scope=node=>{
    const workbench=node.closest?.('.tb-workbench');if(workbench)return 'problem:'+workbench.dataset.problemId;
    const pane=node.closest?.('.study-pane');if(pane)return pane.dataset.studyKey;
    const group=node.closest?.('.study-group-header');if(group){const selected=group.querySelector('[role=tab][aria-selected=true]');return doc.getElementById(selected?.getAttribute('aria-controls'))?.dataset.studyKey;}
    const lecture=node.closest?.('.lecture-reading-full');if(lecture)return 'lecture:'+lecture.closest('.lectures-page')?.dataset.lectureId;
    if(node.closest?.('.reader-full'))return 'solution:'+node.closest('.reader-full').dataset.problemId;
    return null;
  };
  const key=(node,zone)=>{const id=scope(node);return id?id+':'+zone:null;};
  const level=k=>{const value=values()[k];return typeof value==='number'&&Number.isFinite(value)?clamp(value):1;};
  const paint=(node,k)=>{if(!node||!k)return;painted.add(node);if(!touched.has(node))touched.set(node,node.style.zoom);const next=String(level(k));if(node.style.zoom!==next)node.style.zoom=next;node.dataset.readingZoom=next;};
  const apply=()=>{
    frame=0;painted.clear();
    for(const node of doc.querySelectorAll(bodySelectors))paint(node,key(node,'content'));
    for(const node of doc.querySelectorAll(toolbarSelectors))paint(node,key(node,'toolbar'));
    for(const node of doc.querySelectorAll('.study-group-header'))paint(node,key(node,'bookmarks'));
    for(const iframe of doc.querySelectorAll('.study-pane .wiki-reader')){
      if(!frames.has(iframe)){
        let inner;const loaded=()=>{if(inner)inner.removeEventListener('wheel',wheel,true);try{inner=iframe.contentDocument;}catch{}if(inner){inner.addEventListener('wheel',wheel,{capture:true,passive:false});paint(inner.body,key(iframe,'content'));}};
        const wheel=event=>adjust(event,iframe,'content');iframe.addEventListener('load',loaded);frames.set(iframe,()=>{iframe.removeEventListener('load',loaded);inner?.removeEventListener('wheel',wheel,true);});loaded();
      }else{try{if(iframe.contentDocument?.body)paint(iframe.contentDocument.body,key(iframe,'content'));}catch{}}
    }
    for(const [iframe,remove]of frames)if(!iframe.isConnected){remove();frames.delete(iframe);}
    for(const[node,initial]of touched)if(!painted.has(node)){if(node.isConnected){node.style.zoom=initial;delete node.dataset.readingZoom;}touched.delete(node);}
  };
  const schedule=()=>{if(!frame)frame=doc.defaultView.requestAnimationFrame(apply);};
  function adjust(event,node,zone){
    if(!event.ctrlKey||event.altKey||event.metaKey||!event.deltaY||event.defaultPrevented)return;
    const k=key(node,zone);if(!k)return;
    event.preventDefault();event.stopImmediatePropagation();
    const value=values();value[k]=clamp(level(k)+(event.deltaY<0?.1:-.1));
    try{doc.defaultView.localStorage.setItem('tb.readingZoom.v1.'+owner(),JSON.stringify(value));}catch{}
    apply();
    showZoom(node,zone,Math.round(value[k]*100));
  }
  const wheel=event=>{const node=event.target?.nodeType===1?event.target:event.target?.parentElement;if(!node||doc.querySelector('dialog[open],[aria-modal=true]:not(.reader-full)'))return;const zone=node.closest('.study-group-header')?'bookmarks':node.closest(headers)?'toolbar':'content';adjust(event,node,zone);};
  const observer=new MutationObserver(schedule);observer.observe(doc.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['class','data-problem-id','data-study-key','data-lecture-id','aria-selected','hidden']});
  doc.addEventListener('wheel',wheel,{capture:true,passive:false});apply();
  return()=>{observer.disconnect();clearTimeout(toastTimer);clearTimeout(removeTimer);toast?.remove();doc.defaultView.cancelAnimationFrame(frame);doc.removeEventListener('wheel',wheel,true);for(const remove of frames.values())remove();for(const[node,zoom]of touched)if(node.isConnected){node.style.zoom=zoom;delete node.dataset.readingZoom;}};
}

export default function useReadingZoom(){useEffect(()=>{if(users++===0)dispose=installReadingZoom();return()=>{if(--users===0){dispose?.();dispose=null;}};},[]);}
