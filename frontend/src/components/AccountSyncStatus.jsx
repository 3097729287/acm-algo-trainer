import { useEffect, useState } from 'react';

export default function AccountSyncStatus() {
  const [sync, setSync] = useState(() => window.__tbAccountSync);
  useEffect(() => {
    const update = event => setSync(event.detail);
    window.addEventListener('tb:sync-status', update);
    return () => window.removeEventListener('tb:sync-status', update);
  }, []);
  const waiting = sync?.pending || sync?.status === 'syncing';
  const label = !sync ? '本地' : sync.status === 'error' ? '待同步' : waiting ? '同步中' : '已同步';
  const title = sync?.error || (sync?.lastSyncedAt ? `最近同步：${new Date(sync.lastSyncedAt).toLocaleString('zh-CN')}` : '本机数据已保存');
  return <span className="local-indicator" title={title} aria-label={`账号数据${label}`}>{label}</span>;
}
