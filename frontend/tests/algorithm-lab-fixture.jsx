import React, { useCallback, useState } from 'react';
import { createRoot } from 'react-dom/client';
import LearningPathsPage from '../src/pages/LearningPathsPage.jsx';
import '../src/styles/workspace.css';
import '../src/styles/refinements.css';
import '../src/styles/polish.css';
import '../src/styles/unified.css';
import '../src/styles/revision.css';

const key = 'tb.algorithm-lab.preview.v1';
window.algorithmLabFixture = { trained: [] };
const api = async route => { if (route === 'lectures') return { lectures: [] }; throw Error(`Unexpected preview API: ${route}`); };
const rows = [{ id: '入门赛 50::F', title: '神奇的背包', difficulty: 1150, tags: ['背包 DP'], url: 'https://www.luogu.com.cn/problem/P17162' }];
document.documentElement.dataset.theme = 'dark';
document.documentElement.dataset.accent = 'teal';
document.documentElement.dataset.motion = 'on';
document.documentElement.style.setProperty('--panel-opacity', '100%');
function Preview() {
  const [prefs, setState] = useState(() => { try { return JSON.parse(localStorage.getItem(key)) || { learningPaths: { knapsack: { idea: true } }, favorites: ['retained'] }; } catch { return {}; } });
  const [notice, setNotice] = useState(''), [light, setLight] = useState(false);
  const setPrefs = useCallback(update => setState(previous => { const next = typeof update === 'function' ? update(previous) : update; localStorage.setItem(key, JSON.stringify(next)); return next; }), []);
  window.algorithmLabFixture.prefs = prefs;
  return <div className="lab-preview-shell"><header className="lab-preview-header"><b>TB <span>算法实验室 · 开发预览</span></b><div><span>进度仅保存在此预览</span><button type="button" onClick={() => { document.documentElement.dataset.theme = light ? 'dark' : 'light'; setLight(value => !value); }}>切换深浅主题</button></div></header>{notice && <div className="lab-preview-notice" role="status">{notice}<a href="https://www.luogu.com.cn/problem/P17162" target="_blank" rel="noreferrer">查看原题</a><button type="button" onClick={() => setNotice('')}>收起</button></div>}<main><LearningPathsPage rows={rows} api={api} prefs={prefs} setPrefs={setPrefs} onTrain={id => { window.algorithmLabFixture.trained.push(id); setNotice('这是独立课程预览。完整 C++ 工作台已接入开发源码，待软件打包后使用；现在也可以打开原题练习。'); }}/></main><style>{`.lab-preview-shell{height:100dvh;display:flex;flex-direction:column}.lab-preview-header{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;padding:13px 24px;border-bottom:1px solid var(--line);background:var(--panel);font-size:13px}.lab-preview-header b{color:var(--accent);font-size:18px}.lab-preview-header b span{color:var(--text);font-size:12px;font-weight:400;margin-left:12px}.lab-preview-header>div{display:flex;align-items:center;gap:16px}.lab-preview-header>div>span{color:var(--muted);font-size:11px}.lab-preview-header button,.lab-preview-notice button{color:var(--accent);border:1px solid var(--line);background:transparent;border-radius:6px;padding:6px 10px;font-size:11px}.lab-preview-shell>main{display:flex;min-height:0;flex:1;padding:16px 22px}.lab-preview-notice{padding:12px 25px;font-size:12px;color:var(--muted);border-bottom:1px solid var(--line);line-height:1.8}.lab-preview-notice a,.lab-preview-notice button{margin-left:14px;color:var(--accent)}@media(max-width:560px){.lab-preview-header{padding:10px 14px}.lab-preview-header>div>span{display:none}.lab-preview-shell>main{padding:10px 8px}}`}</style></div>;
}
createRoot(document.getElementById('root')).render(<Preview/>);
