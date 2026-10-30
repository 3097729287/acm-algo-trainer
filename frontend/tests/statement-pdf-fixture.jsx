import React from 'react';
import {createRoot} from 'react-dom/client';
import Workbench from '../src/app/Workbench.jsx';
const style=document.createElement('style');
style.textContent=':root{--panel:white;--panel-2:#f5f5f5;--text:#222;--line:#ddd;--muted:#666;--accent:#198}*{box-sizing:border-box}body{margin:0}#root{height:100dvh}';
document.head.append(style);
const api=async(path,body)=>path==='draft'?{savedAt:new Date().toISOString()}:path.startsWith('problem?')?window.pdfFixtureData:Promise.reject(new Error('Unexpected fixture API: '+path));
createRoot(document.getElementById('root')).render(<Workbench problemId="pdf-fixture" contest={null} api={api}/>);
