import React from 'react';
import { createRoot } from 'react-dom/client';
import AccountSyncStatus from '../src/components/AccountSyncStatus.jsx';

const states = {
  error: { status: 'error', pending: true, error: '本地模拟：同步失败，请稍后重试' },
  ready: { status: 'ready', pending: false, lastSyncedAt: '2026-10-15T08:30:00.000Z' },
  pending: { status: 'ready', pending: true },
};
window.__tbAccountSync = states[new URLSearchParams(location.search).get('state')];
window.accountSyncStatusFixture = {
  update(sync) {
    window.__tbAccountSync = sync;
    window.dispatchEvent(new CustomEvent('tb:sync-status', { detail: sync }));
  },
};
createRoot(document.getElementById('root')).render(
  <main style={{ fontFamily: 'sans-serif', margin: 40, lineHeight: 2 }}>
    <h1>账号同步状态本地回归</h1>
    <p>账户数据状态：<AccountSyncStatus /></p>
  </main>,
);
