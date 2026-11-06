import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {MotionScene,MOTION_SCENES} from '../src/lib/motionBackgrounds.js';
import BackgroundPicker from '../src/components/BackgroundPicker.jsx';
import VisualStyleSettings from '../src/components/VisualStyleSettings.jsx';
import WorkspaceBackground from '../src/components/WorkspaceBackground.jsx';
import {BACKGROUND_CARDS} from '../src/lib/stickerCatalogue.js';
import {workspaceBackground} from '../src/lib/workspaceBackground.js';
import RocketSticker from '../src/components/RocketSticker.jsx';
import {StickerArt} from '../src/components/StickerArt.jsx';
import StickerReaction from '../src/components/StickerReaction.jsx';
import '../src/styles/workspace.css';
import '../src/styles/surfaces.css';
import '../src/components/WorkspaceBackground.css';
import '../src/components/MeteorsBackground.css';
window.MotionScene=MotionScene;window.scenes=MOTION_SCENES;
const owner='fixture',inventory={owner,revision:1,unlimited:true,catalogue:BACKGROUND_CARDS,units:BACKGROUND_CARDS.map(item=>({id:item.id,stickerId:item.id,placement:null}))};
function Fixture(){const [prefs,setPrefs]=useState({backdrop:'none',learningPaths:{},panelStyle:'outlined'}),[level,setLevel]=useState(9),[open,setOpen]=useState(false),[reaction,setReaction]=useState(null);window.setLevel=setLevel;window.prefs=prefs;return <div className="app-shell" style={{minHeight:'100vh',display:'block'}}><WorkspaceBackground value={workspaceBackground(prefs,inventory,owner,{level})}/><button onClick={()=>setOpen(true)}>背景选择</button><VisualStyleSettings prefs={prefs} setPrefs={setPrefs}/>{open&&<BackgroundPicker owner={owner} prefs={prefs} setPrefs={setPrefs} access={{level}} model={{inventory,refresh:async()=>{}}} onClose={()=>setOpen(false)}/>}<div className="sticker-surface" style={{position:'relative',width:900,height:700,margin:30}}><button className="placed-sticker" style={{position:'absolute',left:450,top:72,width:140,height:140,transform:'translate(-50%,-50%) rotate(90deg)',padding:0,border:0,background:'none'}} onClick={()=>setReaction({id:performance.now(),shape:'rocket'})} aria-label="火箭"><RocketSticker reaction={reaction} point={{x:.5,y:72/700,angle:90,scale:2.5}} bounds={{width:900,height:700}} size={140}><StickerArt item={{shape:'rocket'}} size="100%"/>{reaction&&<StickerReaction reaction={reaction}/>}</RocketSticker></button></div></div>}
document.documentElement.dataset.theme='dark';document.documentElement.dataset.motion='on';createRoot(document.getElementById('root')).render(<Fixture/>);
