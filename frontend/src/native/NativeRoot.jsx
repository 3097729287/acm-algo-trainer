import { useEffect, useState } from 'react';
import App from '../app/App.jsx';
import { BackgroundPlayback } from '../components/BackgroundPlaylist.jsx';
import { request } from '../api/client.js';
import MigrationWorkbench from './MigrationWorkbench.jsx';
import './workspace-entry.css';

function LocalWorkspace() {
  const [ready, setReady] = useState(false), [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    (async () => {
      const capabilities = await request('api/capabilities');
      if (!capabilities.sandbox || capabilities.releaseReady || !capabilities.owner) throw new Error('此入口仅用于独立本地测试');
      const bootstrap = await request('account');
      if (!active) return;
      // Explicit local identity; this grants no registered account, XP,
      // rating, inventory or permission on the shared service.
      window.__tbAccountUserId = capabilities.owner;
      window.__tbAccount = { userId: capabilities.owner, nickname: '本地测试', loginId: '' };
      const saved = await request('preferences');
      const preferences = saved.preferences || {};
      const required = ['library', 'wiki', 'templates', 'lectures', 'tasks'];
      const paths = preferences.learningPaths || {};
      if (!required.every(id => paths.navigationAccess?.retained?.includes(id))) {
        const retained = [...new Set([...(paths.navigationAccess?.retained || []), ...required])];
        await request('preferences', { preferences: { ...preferences,
          learningPaths: { ...paths, navigationAccess: { version: 3, retained } } } }, bootstrap.token);
      }
      if (active) setReady(true);
    })().catch(issue => { if (active) setError(issue.message); });
    return () => { active = false; };
  }, []);
  if (error) return <main className="native-migration"><p role="alert">{error}</p><button onClick={() => { location.hash = 'native-check'; }}>返回迁移检查</button></main>;
  if (!ready) return <main className="native-migration"><p>正在读取本地测试工作区…</p></main>;
  return <><BackgroundPlayback/><App localNavigation/></>;
}

export default function NativeRoot() {
  const [hash, setHash] = useState(location.hash);
  useEffect(() => {
    const update = () => { if (['#native-check', '#native-workspace'].includes(location.hash)) setHash(location.hash); };
    window.addEventListener('hashchange', update); return () => window.removeEventListener('hashchange', update);
  }, []);
  return hash === '#native-workspace' ? <LocalWorkspace/> : <MigrationWorkbench/>;
}
