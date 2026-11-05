import {useEffect,useState} from 'react';
import {Check,Image,Layers,RefreshCw} from 'lucide-react';
import {BoardDialog} from './TaskBoardControls.jsx';
import BackgroundPlaylist from './BackgroundPlaylist.jsx';
import {MOTION_SCENES,MotionScene} from '@/lib/motionBackgrounds.js';
import {chooseRewardBackground,ownedBackgrounds} from '@/lib/workspaceBackground.js';
import './BackgroundPicker.css';
let queue=Promise.resolve();const thumbnails=new Map();
function thumbnail(id,alive){
 if(thumbnails.has(id))return Promise.resolve(thumbnails.get(id));
 const task=queue.then(async()=>{if(!alive())return null;if(thumbnails.has(id))return thumbnails.get(id);await new Promise(requestAnimationFrame);if(!alive())return null;const host=document.createElement('div');host.style.cssText='position:fixed;inset:auto;left:-1000px;top:0;width:384px;height:216px;visibility:hidden';document.body.append(host);const scene=new MotionScene(host,{id,paused:true});try{scene.time=6;const url=scene.snapshot();thumbnails.set(id,url);return url;}finally{scene.destroy();host.remove();}});queue=task.catch(()=>{});return task;
}
function BackgroundChoice({item,selected,onChoose}){
 const [preview,setPreview]=useState(null),scene=MOTION_SCENES.find(scene=>scene.id===item.theme);
 useEffect(()=>{let alive=true;void thumbnail(item.theme,()=>alive).then(value=>{if(alive)setPreview(value)}).catch(()=>{});return()=>{alive=false};},[item.theme]);
 return <button type="button" className="background-choice" aria-label={'使用背景 '+item.title} aria-pressed={selected} onClick={onChoose}><span className="background-choice-art" style={{background:`linear-gradient(135deg,${scene?.colors?.[0]||'#071321'},${scene?.colors?.[1]||'#20495e'})`}}>{preview&&<img src={preview} alt=""/>}{selected&&<Check size={18}/>}</span><span><b>{item.title}</b><small>{scene?.name||item.title}</small><em>{item.unlimited?'∞':item.count}</em></span></button>;
}
export default function BackgroundPicker({owner,prefs,setPrefs,model,onClose}){
 const [customError,setCustomError]=useState(''),[tab,setTab]=useState(prefs.backdrop==='custom'&&prefs.learningPaths?.workspaceBackground?.kind!=='reward'?'images':'rewards'),items=ownedBackgrounds(model.inventory,owner);
 return <BoardDialog title="背景选择" className="background-picker" onClose={onClose}><nav className="background-picker-tabs" aria-label="背景分类"><button type="button" aria-pressed={tab==='rewards'} onClick={()=>setTab('rewards')}><Layers size={16}/>奖励背景</button><button type="button" aria-pressed={tab==='images'} onClick={()=>setTab('images')}><Image size={16}/>我的背景</button><button type="button" className="task-icon" aria-label="刷新背景库存" disabled={model.loading} onClick={()=>void model.refresh()}><RefreshCw size={16}/></button></nav>{tab==='rewards'?<><div className="background-choice-grid">{items.map(item=><BackgroundChoice key={item.id} item={item} selected={prefs.learningPaths?.workspaceBackground?.kind==='reward'&&prefs.learningPaths.workspaceBackground.id===item.id} onChoose={()=>{setPrefs(previous=>chooseRewardBackground(previous,item.id));onClose();}}/>)}</div>{!items.length&&<p className="task-muted">{model.loading?'正在读取背景…':model.error||'完成默认时长的重现赛，至少 AC 2 题且用时达到一半，可获得一张背景。'}</p>}</>:<><BackgroundPlaylist setPrefs={setPrefs} onError={setCustomError} onSelected={onClose}/>{customError&&<p className="connection-error" role="alert">{customError}</p>}</>}</BoardDialog>;
}
