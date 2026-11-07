import React,{useEffect,useState} from 'react';
import WorkspaceBackground from '../src/components/WorkspaceBackground.jsx';
import BackgroundPicker from '../src/components/BackgroundPicker.jsx';
import useBackgroundInventory from '../src/lib/useBackgroundInventory.js';
import {chooseRewardBackground,workspaceBackground} from '../src/lib/workspaceBackground.js';

export default function BackgroundHarness({api,owner,children}){
 const [prefs,setPrefs]=useState(()=>{try{return JSON.parse(localStorage.getItem('background-harness.'+owner))||{backdrop:'none',learningPaths:{}};}catch{return {backdrop:'none',learningPaths:{}};}}),[open,setOpen]=useState(false),model=useBackgroundInventory(api,owner,true);
 useEffect(()=>{localStorage.setItem('background-harness.'+owner,JSON.stringify(prefs));},[prefs,owner]);
 useEffect(()=>{const choose=event=>{if(event.detail?.owner===owner)setPrefs(previous=>chooseRewardBackground(previous,event.detail.id));};window.addEventListener('tb:workspace-background-select',choose);return()=>window.removeEventListener('tb:workspace-background-select',choose);},[owner]);
 useEffect(()=>{if(prefs.learningPaths?.workspaceBackground||!model.inventory)return;const placed=model.inventory.units.find(unit=>unit.placement&&model.inventory.catalogue.find(item=>item.id===unit.stickerId)?.kind==='background');if(placed)setPrefs(previous=>chooseRewardBackground(previous,placed.stickerId));},[model.inventory,prefs]);
 return <div className="app-shell" style={{display:'block',isolation:'isolate',minHeight:'100vh'}}><WorkspaceBackground value={workspaceBackground(prefs,model.inventory,owner)}/><button type="button" onClick={()=>setOpen(true)}>背景选择</button>{children}{open&&<BackgroundPicker owner={owner} prefs={prefs} setPrefs={setPrefs} model={model} onClose={()=>setOpen(false)}/>}</div>;
}
