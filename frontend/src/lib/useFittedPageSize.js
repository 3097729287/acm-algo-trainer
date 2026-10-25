import {useLayoutEffect,useState} from 'react';

export function useFittedPageSize(ref,resetKey='',selector='') {
  const [size,setSize]=useState(1);
  useLayoutEffect(()=>{
    const panel=ref.current;if(!panel)return;
    let frame;
    const measure=()=>{
      cancelAnimationFrame(frame);
      frame=requestAnimationFrame(()=>{
        const row=selector?panel.querySelector(selector):panel.firstElementChild;if(!row)return;
        const style=getComputedStyle(panel),gap=parseFloat(style.rowGap)||0;
        const height=panel.clientHeight-(parseFloat(style.paddingTop)||0)-(parseFloat(style.paddingBottom)||0);
        const offset=Math.max(0,row.getBoundingClientRect().top-panel.getBoundingClientRect().top+panel.scrollTop-(parseFloat(style.paddingTop)||0));
        const rowHeight=selector?Math.max(...[...panel.querySelectorAll(selector)].map(item=>item.offsetHeight)):row.offsetHeight;
        if(rowHeight>0)setSize(Math.max(1,Math.floor((height-offset+gap)/(rowHeight+gap))));
      });
    };
    const observer=new ResizeObserver(measure);observer.observe(panel);
    const first=selector?panel.querySelector(selector):panel.firstElementChild;if(first)observer.observe(first);
    const mutation=new MutationObserver(measure);mutation.observe(panel,{childList:true,subtree:true});
    measure();return()=>{observer.disconnect();mutation.disconnect();cancelAnimationFrame(frame);};
  },[ref,resetKey,selector]);
  return size;
}
