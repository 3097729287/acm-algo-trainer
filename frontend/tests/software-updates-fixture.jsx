import React from 'react';
import { createRoot } from 'react-dom/client';
import { SoftwareUpdatePanel, SoftwareUpdateNotice, useSoftwareUpdates } from '../src/pages/SoftwareUpdates.jsx';
import AccountGate from '../src/accounts/AccountGate.jsx';

let state = { currentVersion: '0.9.3', latestVersion: '0.10.0', status: 'available', canInstall: true, autoCheck: true, notes: '官方 AC 与软件更新\n<script>unsafe()</script>', releaseUrl: 'https://github.com/3097729287/acm-algo-trainer/releases/tag/v0.10.0' };
const automatic = location.search.includes('automatic');
if (automatic) state = { ...state, automatic: true, startupCheckRequired: true, status: 'ready' };
window.updaterCalls = [];
window.saveAllowed = false;
window.guardBlocked = automatic;
window.addEventListener('tb-before-update', event => event.detail.waitUntil(new Promise(resolve => setTimeout(() => { window.draftSaved = window.saveAllowed; resolve(window.saveAllowed); }, 200))));
async function api(path, body) {
  if (body) {
    window.updaterCalls.push({ path, draftSaved: Boolean(window.draftSaved) });
    if (path.endsWith('/download')) state = { ...state, status: 'ready' };
    if (path.endsWith('/install')) {
      if (window.guardBlocked) throw new Error('请等待当前官方提交取得结果后再安装更新');
      state = { ...state, status: 'installing' };
    }
    if (path.endsWith('/settings')) state = { ...state, ...body };
  }
  return { ...state };
}
function Fixture() {
  const update = useSoftwareUpdates(api, true);
  return <><SoftwareUpdatePanel update={update} /><SoftwareUpdateNotice update={update} onDetails={() => { window.detailsClicked = true; }} /></>;
}
if (location.search.includes('login')) {
  window.fetch = async (url, options) => {
    const path = String(url).split('/api/')[1];
    const result = path === 'account' ? { token: 'fixture-only', authenticated: false } : await api(path, options?.body ? JSON.parse(options.body) : undefined);
    return { ok: true, text: async () => JSON.stringify(result) };
  };
  createRoot(document.getElementById('root')).render(<AccountGate><p>Authenticated content</p></AccountGate>);
} else createRoot(document.getElementById('root')).render(<Fixture />);
