import React from 'react';
import {createRoot} from 'react-dom/client';
import Onboarding from '../src/pages/Onboarding.jsx';
import {PAGE_GUIDES,GUIDE_LABELS} from '../src/lib/guideCatalog.js';
import {guideAction} from '../src/lib/guideActions.js';
import '../src/styles/workspace.css';
GUIDE_LABELS.fixture='实操验证';
PAGE_GUIDES.fixture=[PAGE_GUIDES.library.find(s=>s.task),PAGE_GUIDES.growth.find(s=>s.task?.signal==='scene-save'),PAGE_GUIDES.practice.find(s=>s.task?.signal==='code-formatted')];
createRoot(document.getElementById('root')).render(<><div className="app-shell" inert><p>打开学习标签页后的主窗口</p><Onboarding initialGuide="fixture" practiceId="fixture" onNavigate={()=>{}} onShown={()=>{}} onDirectory={()=>{}} onComplete={()=>{window.tourFinished=true;}}/></div><div className="page-search-controls"><input aria-label="搜索题目"/></div><button className="sticker-scene-presets" onClick={()=>{window.presetSaved=true;guideAction('scene-save');}}>确认保存场景</button><button className="cm-editor" onClick={()=>guideAction('code-formatted')}>确认格式化成功</button></>);
