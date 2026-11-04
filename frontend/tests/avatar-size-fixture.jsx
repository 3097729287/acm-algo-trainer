import React from 'react';
import {createRoot} from 'react-dom/client';
import ProfileBadge from '../src/components/ProfileBadge.jsx';
import '../src/styles/workspace.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';
const canvas=document.createElement('canvas');canvas.width=64;canvas.height=64;const c=canvas.getContext('2d');c.fillStyle='#619caa';c.fillRect(0,0,64,64);const avatar=canvas.toDataURL();
createRoot(document.getElementById('root')).render(<>{Array.from({length:9},(_,index)=><header key={index} className="topbar" style={{height:90,minHeight:90,display:'flex',justifyContent:'flex-end',paddingRight:20,position:'relative'}}><div className="topbar-actions"><span>AC : 122</span><ProfileBadge avatar={avatar} nickname={'用户 '+index} growth={{level:14,currentLevelXp:100,nextLevelXp:200,ranked:{qualified:true,badge:'tier-'+index}}}/></div></header>)}</>);
