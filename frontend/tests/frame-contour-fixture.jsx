import React from 'react';
import {createRoot} from 'react-dom/client';
import AvatarFrame from '../src/components/AvatarFrame.jsx';
document.body.style.cssText='margin:0;background:#243e50';
const style=document.createElement('style');style.textContent='.avatar-rank-frame{display:block;width:100%;height:100%}';document.head.append(style);
createRoot(document.getElementById('root')).render(<div style={{width:1024,height:1024}}><AvatarFrame index={8}/></div>);
