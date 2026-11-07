import {useEffect,useRef,useState} from 'react';
import MeteorsBackground from './MeteorsBackground.jsx';
import {MotionScene} from '@/lib/motionBackgrounds.js';
import './WorkspaceBackground.css';

export function MotionBackground({id,motion=true,lightning=false}){
 const host=useRef(null),engine=useRef(null);
 useEffect(()=>{if(!host.current)return;const scene=new MotionScene(host.current,{id,paused:!motion,lightning});engine.current=scene;return()=>{scene.destroy();engine.current=null;};},[]);
 useEffect(()=>{if(engine.current?.id!==id)engine.current?.setScene(id);},[id]);
 useEffect(()=>engine.current?.setLightning(lightning),[lightning]);
 useEffect(()=>{const query=matchMedia('(prefers-reduced-motion: reduce)'),apply=()=>engine.current?.setPaused(!motion||query.matches||document.documentElement.dataset.motion==='off'),observer=new MutationObserver(apply);apply();query.addEventListener('change',apply);observer.observe(document.documentElement,{attributes:true,attributeFilter:['data-motion']});return()=>{query.removeEventListener('change',apply);observer.disconnect();};},[motion]);
 return <div ref={host} className="motion-background" aria-hidden="true"/>;
}
function CustomBackground({motion}){
 const currentURL=()=>document.documentElement.style.getPropertyValue('--workspace-image').match(/^url\(["']?(.*?)["']?\)$/)?.[1]||'';
 const [url,setURL]=useState(currentURL),[paused,setPaused]=useState(!motion),picture=useRef(null),still=useRef(null),frozen=useRef(null);
 useEffect(()=>{const paint=event=>setURL(event.detail?.url||'');window.addEventListener('tb:background-painted',paint);setURL(currentURL());return()=>window.removeEventListener('tb:background-painted',paint);},[]);
 useEffect(()=>{const media=matchMedia('(prefers-reduced-motion: reduce)'),update=()=>setPaused(!motion||media.matches||document.hidden);update();media.addEventListener('change',update);document.addEventListener('visibilitychange',update);return()=>{media.removeEventListener('change',update);document.removeEventListener('visibilitychange',update);};},[motion]);
 useEffect(()=>{
  const image=picture.current,canvas=still.current;frozen.current=null;
  const draw=(capture=false)=>{if(!image?.naturalWidth||!canvas)return;if(capture){const copy=document.createElement('canvas');const scale=Math.min(1,1920/image.naturalWidth,1200/image.naturalHeight);copy.width=Math.max(1,Math.round(image.naturalWidth*scale));copy.height=Math.max(1,Math.round(image.naturalHeight*scale));copy.getContext('2d').drawImage(image,0,0,copy.width,copy.height);frozen.current=copy;}const frame=frozen.current;if(!frame)return;canvas.width=innerWidth;canvas.height=innerHeight;const scale=Math.max(canvas.width/frame.width,canvas.height/frame.height),w=frame.width*scale,h=frame.height*scale;canvas.getContext('2d').drawImage(frame,(canvas.width-w)/2,(canvas.height-h)/2,w,h);};
  const loaded=()=>{if(paused)draw(true);};if(paused)draw(true);image?.addEventListener('load',loaded);const resize=()=>{if(paused)draw();};window.addEventListener('resize',resize);return()=>{image?.removeEventListener('load',loaded);window.removeEventListener('resize',resize);};
 },[url,paused]);
 return <div className="workspace-background-image" data-paused={paused}><img ref={picture} src={url||undefined} alt="" hidden={paused}/><canvas ref={still} hidden={!paused}/></div>;
}
export default function WorkspaceBackground({value,motion=true}){
 useEffect(()=>{document.documentElement.dataset.workspaceBackground=value.kind==='none'?'off':'on';return()=>{delete document.documentElement.dataset.workspaceBackground;};},[value.kind]);
 if(value.kind==='none')return null;
 return <div className="workspace-background-layer" data-background-source={value.source} data-background-id={value.id} aria-hidden="true">{value.kind==='image'?<CustomBackground motion={motion}/>:value.id==='meteors'?<MeteorsBackground/>:<MotionBackground key={value.id} id={value.id} motion={motion} lightning={value.lightning}/>}</div>;
}
