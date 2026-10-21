import { useEffect, useRef, useState } from 'react';
import { ImagePlus, Pause, Play, Trash2 } from 'lucide-react';
import BoundedNumber from './BoundedNumber.jsx';
import Tooltip from './Tooltip.jsx';

function database() { return new Promise((resolve,reject) => { const request=indexedDB.open('tb-backgrounds',1); request.onupgradeneeded=()=>request.result.createObjectStore('images',{keyPath:'id',autoIncrement:true}); request.onsuccess=()=>resolve(request.result); request.onerror=()=>reject(request.error); }); }
async function access(mode, action) {
  const db=await database();
  try { return await new Promise((resolve,reject) => { const transaction=db.transaction('images',mode), request=action(transaction.objectStore('images')); let value; request.onsuccess=()=>{value=request.result;}; transaction.oncomplete=()=>resolve(value); transaction.onerror=()=>reject(transaction.error); transaction.onabort=()=>reject(transaction.error); }); } finally { db.close(); }
}
const settings = () => { try { return JSON.parse(localStorage.getItem('tb.background.playlist') || '{}'); } catch { return {}; } };
const changed = () => window.dispatchEvent(new Event('tb:backgrounds-change'));
export async function addBackgroundFiles(files) {
  const count=await access('readonly',store=>store.count());
  if(count+files.length>20)throw new Error('播放列表最多 20 张图片');
  for(const file of files)if(!['image/png','image/jpeg','image/webp','image/gif'].includes(file.type)||file.size>12*1024*1024)throw new Error('请选择 12 MB 以内的 PNG、JPEG、WebP 或 GIF');
  if(files.length)await access('readwrite',store=>{let request;for(const file of files)request=store.add({name:file.name,blob:file});return request;});
  changed();
}
export async function clearBackgrounds() {await access('readwrite',store=>store.clear());localStorage.removeItem('tb.appearance.background');changed();}
export function BackgroundPlayback() {
  useEffect(() => {
    let urls=[],timer,alive=true,version=0;
    const refresh=async()=>{
      const request=++version; clearInterval(timer);
      let items=[]; try { items=await access('readonly',store=>store.getAll()); } catch { /* Legacy background remains available. */ }
      if (!alive || request!==version) return;
      urls.forEach(URL.revokeObjectURL); urls=items.map(item=>URL.createObjectURL(item.blob));
      const legacy=localStorage.getItem('tb.appearance.background'), playlist=settings();
      let index=0;
      const paint=()=>{const url=urls[index] || legacy; if(url)document.documentElement.style.setProperty('--workspace-image',`url("${url}")`);else document.documentElement.style.removeProperty('--workspace-image');};
      paint();
      if(urls.length>1 && playlist.playing!==false) timer=setInterval(()=>{index=(index+1)%urls.length;paint();},Math.max(5,Math.min(3600,Number(playlist.seconds)||30))*1000);
    };
    refresh(); window.addEventListener('tb:backgrounds-change',refresh);
    return()=>{alive=false;version++;clearInterval(timer);urls.forEach(URL.revokeObjectURL);window.removeEventListener('tb:backgrounds-change',refresh);};
  },[]);
  return null;
}
export default function BackgroundPlaylist({ setPrefs, onError }) {
  const [items,setItems]=useState([]),[config,setConfig]=useState(settings),[busy,setBusy]=useState(false), input=useRef(null);
  useEffect(()=>{
    let alive=true,urls=[],generation=0;
    const refresh=async()=>{const current=++generation;try{const rows=await access('readonly',store=>store.getAll());if(!alive||current!==generation)return;urls.forEach(URL.revokeObjectURL);urls=rows.map(row=>URL.createObjectURL(row.blob));setItems(rows.map((row,index)=>({...row,url:urls[index]})));}catch(error){if(alive)onError?.(error.message);}};
    refresh();window.addEventListener('tb:backgrounds-change',refresh);
    return()=>{alive=false;generation++;urls.forEach(URL.revokeObjectURL);window.removeEventListener('tb:backgrounds-change',refresh);};
  },[busy]);
  const update=patch=>{const next={...config,...patch};setConfig(next);localStorage.setItem('tb.background.playlist',JSON.stringify(next));changed();};
  async function add(event) {
    const files=[...event.target.files];if(!files.length)return;setBusy(true);
    try {
      await addBackgroundFiles(files);
      setPrefs(previous=>({...previous,backdrop:'custom'}));changed();
    }catch(error){onError?.(error.message);}finally{setBusy(false);event.target.value='';}
  }
  async function remove(id) {setBusy(true);try{await access('readwrite',store=>store.delete(id));changed();}catch(error){onError?.(error.message);}finally{setBusy(false);}}
  return <div className="background-playlist"><div className="playlist-toolbar"><Tooltip text="支持 GIF、动态 WebP / PNG；原始动画保存在本机，按添加顺序轮播。"><button type="button" className="secondary" disabled={busy} aria-label="添加背景图片或动图" onClick={()=>input.current.click()}><ImagePlus size={16}/>添加背景</button></Tooltip><input ref={input} hidden type="file" multiple accept="image/png,image/jpeg,image/webp,image/gif" onChange={add}/><Tooltip text={config.playing===false?'开始轮播':'暂停轮播'}><button type="button" className="icon-button" aria-label="切换背景轮播" aria-pressed={config.playing!==false} onClick={()=>update({playing:config.playing===false})}>{config.playing===false?<Play size={16}/>:<Pause size={16}/>}</button></Tooltip><BoundedNumber aria-label="背景轮播间隔秒" min={5} max={3600} value={config.seconds||30} unit="秒" onChange={event=>update({seconds:Number(event.target.value)})}/></div><div className="playlist-images">{items.map((item,index)=><div key={item.id}><img src={item.url} alt={item.name}/><span>{index+1}</span><button type="button" className="icon-button" aria-label={`移除背景 ${item.name}`} disabled={busy} onClick={()=>remove(item.id)}><Trash2 size={14}/></button></div>)}</div></div>;
}
