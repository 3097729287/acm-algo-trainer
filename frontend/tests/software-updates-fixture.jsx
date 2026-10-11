import React from 'react';
import { createRoot } from 'react-dom/client';
import { SoftwareUpdatePanel, SoftwareUpdateNotice, useSoftwareUpdates } from '../src/pages/SoftwareUpdates.jsx';

let state = { currentVersion: '0.9.3', latestVersion: '0.10.0', status: 'available', canInstall: true, autoCheck: true, notes: '官方 AC 与软件更新\n<script>unsafe()</script>', releaseUrl: 'https://github.com/3097729287/acm-algo-trainer/releases/tag/v0.10.0' };
window.updaterCalls = [];
window.saveAllowed = false;
window.addEventListener('tb-before-update', event => event.detail.waitUntil(new Promise(resolve => setTimeout(() => { window.draftSaved = window.saveAllowed; resolve(window.saveAllowed); }, 200))));
async function api(path, body) {
  if (body) {
    window.updaterCalls.push({ path, draftSaved: Boolean(window.draftSaved) });
    if (path.endsWith('/download')) state = { ...state, status: 'ready' };
    if (path.endsWith('/install')) state = { ...state, status: 'installing' };
    if (path.endsWith('/settings')) state = { ...state, ...body };
  }
  return { ...state };
}
function Fixture() {
  const update = useSoftwareUpdates(api, true);
  return <><SoftwareUpdatePanel update={update} /><SoftwareUpdateNotice update={update} onDetails={() => { window.detailsClicked = true; }} /></>;
}
createRoot(document.getElementById('root')).render(<Fixture />);
