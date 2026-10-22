import React, { useCallback, useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import KnapsackCourse from '../src/pages/algorithm-lab/KnapsackCourse.jsx';
import './labShell.css';

export const STORAGE_KEY = 'tb.knapsack.standalone.v1';

function readPreferences() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || localStorage.getItem('tb.algorithm-lab.preview.v1') || '{}');
    return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  } catch { return {}; }
}

export default function KnapsackApp() {
  const [prefs, setState] = useState(readPreferences), [storageFailed, setStorageFailed] = useState(false);
  const setPrefs = useCallback(update => setState(previous => typeof update === 'function' ? update(previous) : update), []);
  const light = prefs.standaloneTheme === 'light';
  useEffect(() => {
    document.documentElement.dataset.theme = light ? 'light' : 'dark';
  }, [light]);
  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs)); setStorageFailed(false); }
    catch { setStorageFailed(true); }
  }, [prefs]);
  return <div className="lab-standalone-shell">
    {storageFailed && <p className="lab-storage-notice" role="status">浏览器禁止保存，关闭页面后本次进度会丢失。</p>}
    <KnapsackCourse prefs={prefs} setPrefs={setPrefs} headerActions={<button type="button" className="lab-theme-toggle" aria-label={light ? '切换深色主题' : '切换浅色主题'} title={light ? '切换深色主题' : '切换浅色主题'} onClick={() => setPrefs(previous => ({ ...previous, standaloneTheme: light ? 'dark' : 'light' }))}>{light ? <Moon size={18}/> : <Sun size={18}/>}</button>}/>
  </div>;
}
