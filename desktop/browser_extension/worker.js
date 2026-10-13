// Capabilities stay in the extension's session storage, never in an OJ page.
importScripts('login_state.js');
const loginStates = {}, loginChecks = new Map(), loginGenerations = {}, loginCookies = {}, loginRescans = new Set();
const loginDirty = new Set();
let lastLoginRefresh = 0;
async function updateLoginState(platform, cookies) {
  loginCookies[platform] = cookies;
  const generation = loginGenerations[platform] = (loginGenerations[platform] || 0) + 1;
  loginStates[platform] = tbCookieLoginState(platform, cookies);
  if (loginChecks.has(platform)) { loginRescans.add(platform); return; }
  const urls = {Codeforces:'https://codeforces.com/',AtCoder:'https://atcoder.jp/','牛客':'https://ac.nowcoder.com/acm/home','洛谷':'https://www.luogu.com.cn/'};
  const check = (async () => {
    try {
      const patterns = {Codeforces:['https://codeforces.com/*','https://www.codeforces.com/*'],AtCoder:['https://atcoder.jp/*'],'牛客':['https://ac.nowcoder.com/*'],'洛谷':['https://www.luogu.com.cn/*','https://luogu.com.cn/*']};
      const tabs = await chrome.tabs.query({url:patterns[platform]});
      const hints = await Promise.all(tabs.filter(tab=>!tab.incognito).slice(0,8).map(async tab=>{
        try { return await Promise.race([chrome.tabs.sendMessage(tab.id,{type:'login-state',platform}),new Promise(resolve=>setTimeout(()=>resolve({state:'unknown'}),750))]); }
        catch { return {state:'unknown'}; }
      }));
      if (generation !== loginGenerations[platform]) return;
      if (hints.some(value=>value?.state==='logged_in')) {loginStates[platform]='logged_in';return;}
      if (hints.some(value=>value?.state==='logged_out') && loginStates[platform]!=='logged_in') {loginStates[platform]='logged_out';return;}
      const response = await fetch(urls[platform], {credentials:'include',cache:'no-store',signal:AbortSignal.timeout(5000)});
      if (!response.ok || Number(response.headers.get('content-length')) > 1048576) return;
      const html = await response.text();
      if (html.length > 1048576 || generation !== loginGenerations[platform]) return;
      const state = tbPageLoginState(platform, html);
      // A cross-origin negative may be caused by the browser's SameSite cookie
      // policy. Only an original-page hint or empty cookies proves logout.
      if (state === 'logged_in') loginStates[platform] = state;
    } catch { /* A blocked or unavailable site is not evidence of logout. */ }
    finally {
      loginChecks.delete(platform);
      if (loginRescans.delete(platform)) updateLoginState(platform, loginCookies[platform]);
    }
  })();
  loginChecks.set(platform, check);
}
const hosts = new Set(['codeforces.com', 'www.codeforces.com', 'atcoder.jp', 'ac.nowcoder.com', 'www.nowcoder.com', 'nowcoder.com', 'www.luogu.com.cn', 'luogu.com.cn', 'login.luogu.com.cn']);
const queues = new Map();
const connections = new Map();
let queueBusy = false;
async function backgroundRequest(base, path, body, key = '') {
  const response = await fetch(base + '/api/browser/' + path, {
    method: 'POST', headers: { 'Content-Type': 'application/json', 'X-TB-Browser': key, 'X-TB-Browser-Client': chrome.runtime.id },
    body: JSON.stringify(body), signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) { connections.delete(base); throw new Error('TB 后台连接不可用'); }
  return response.json();
}
async function pollQueues() {
  if (queueBusy) return;
  queueBusy = true;
  try {
    const settings = await chrome.storage.local.get(['bases', 'clientId']);
    const clientId = settings.clientId || crypto.randomUUID();
    if (!settings.clientId) await chrome.storage.local.set({ clientId });
    const bases = settings.bases || ['http://127.0.0.1:18765'];
    for (const base of bases) {
      try {
        const local = new URL(base);
        if (local.protocol !== 'http:' || local.hostname !== '127.0.0.1' || local.origin !== base) continue;
        if (!connections.has(base)) connections.set(base, (await backgroundRequest(base, 'register', { clientId, protocol: 3, extensionVersion:chrome.runtime.getManifest().version })).key);
        const [windows, tabs] = await Promise.all([
          chrome.windows.getAll({ windowTypes: ['normal'] }),
          chrome.tabs.query({url:['https://codeforces.com/*','https://www.codeforces.com/*','https://atcoder.jp/*','https://ac.nowcoder.com/*','https://www.luogu.com.cn/*','https://luogu.com.cn/*']}),
        ]);
        const platformHosts = {'codeforces.com':'Codeforces','www.codeforces.com':'Codeforces','atcoder.jp':'AtCoder','ac.nowcoder.com':'牛客','www.luogu.com.cn':'洛谷','luogu.com.cn':'洛谷'};
        const platforms = [...new Set(tabs.filter(tab=>!tab.incognito).map(tab=>platformHosts[new URL(tab.url).hostname]).filter(Boolean))];
        if (Date.now() - lastLoginRefresh >= 5000) { platforms.forEach(platform=>loginDirty.add(platform)); lastLoginRefresh=Date.now(); }
        const syncPlatforms = [...loginDirty];
        const answer = await backgroundRequest(base, 'queue', { clientId, hasWindow:windows.some(w=>!w.incognito), platforms, loginStates, syncPlatforms }, connections.get(base));
        syncPlatforms.forEach(platform=>loginDirty.delete(platform));
        if (answer.mode === 'silent' || answer.mode === 'hybrid') {
          const scopes = {Codeforces:['codeforces.com'],AtCoder:['atcoder.jp'],'牛客':['nowcoder.com'],'洛谷':['luogu.com.cn']};
          await Promise.all((answer.sync || []).map(async request => {
            const domains = scopes[request.platform];
            if (!domains || typeof request.nonce !== 'string') return;
            const cookies = (await Promise.all(domains.map(domain => chrome.cookies.getAll({domain})))).flat();
            updateLoginState(request.platform, cookies);
            await backgroundRequest(base, 'session', {clientId,platform:request.platform,nonce:request.nonce,cookies,userAgent:navigator.userAgent}, connections.get(base));
          }));
          if (answer.mode === 'silent') continue;
        }
        for (const item of answer.jobs || []) {
          const saved = (await chrome.storage.session.get('jobs')).jobs || {};
          if (Object.values(saved).some(j => j.sessionId === item.sessionId && j.base === base)) continue;
          // Never create/activate a browser window. Reuse an existing window in
          // the background solely as the authenticated origin for site requests.
          const regularWindows=windows.filter(w=>!w.incognito);
          if (!regularWindows.length) continue;
          const job = { ...item, base, owned: true };
          const claim = await exchange(job, { claim: true });
          if (['closed', 'finished', 'error'].includes(claim.status)) continue;
          const target = new URL(claim.url);
          if (target.protocol !== 'https:' || !hosts.has(target.hostname)) continue;
          let tab;
          if (target.hostname === 'atcoder.jp') {
            for (const candidate of tabs.filter(t=>!t.incognito&&!saved[t.id]&&new URL(t.url).origin===target.origin&&new URL(t.url).pathname===target.pathname)) {
              try {
                const probe = await Promise.race([chrome.tabs.sendMessage(candidate.id,{type:'submission-page',url:target.href}),new Promise(resolve=>setTimeout(()=>resolve({}),750))]);
                if (probe?.available) { tab=candidate;job.owned=false;break; }
              } catch { /* A stale page without the connector is not reusable. */ }
            }
          }
          const matching=tabs.find(tab=>!tab.incognito&&new URL(tab.url).hostname===target.hostname);
          if (!tab) tab = await chrome.tabs.create({ windowId: matching?.windowId||(regularWindows.find(w => w.focused) || regularWindows[0]).id, url: 'about:blank', active: false });
          job.tabId = tab.id;
          saved[tab.id] = job;
          await chrome.storage.session.set({ jobs: saved });
          if (job.owned) await chrome.tabs.update(tab.id, { url: target.href });
          else await chrome.tabs.sendMessage(tab.id, {type:'wake'}).catch(()=>{});
        }
      } catch { /* No browser window or missing TB: wait for the next heartbeat. */ }
    }
  } finally { queueBusy = false; }
}
async function exchange(job, body) {
  const response = await fetch(job.base + '/api/browser/exchange', {
    method: 'POST', headers: { 'Content-Type': 'application/json', 'X-TB-Browser': job.key, 'X-TB-Browser-Client': chrome.runtime.id },
    body: JSON.stringify({ sessionId: job.sessionId, ...body }), signal: AbortSignal.timeout(10000),
  });
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || 'TB 连接失败');
  return value;
}
async function handle(message, sender) {
  if (sender.id !== chrome.runtime.id || sender.frameId !== 0 || !sender.tab?.id) return {};
  const page = new URL(sender.url);
  if (message.type === 'pair') {
    if (page.protocol !== 'http:' || page.hostname !== '127.0.0.1' || page.pathname !== '/browser-connect.html') return {};
    const params = new URLSearchParams(page.hash.slice(1));
    if (params.get('session') !== message.sessionId || params.get('key') !== message.key || !/^official-[a-f0-9]{32}$/.test(message.sessionId) || !/^[A-Za-z0-9_-]{40,64}$/.test(message.key)) return {};
    const job = { base: page.origin, sessionId: message.sessionId, key: message.key, tabId: sender.tab.id };
    const settings = await chrome.storage.local.get('bases');
    await chrome.storage.local.set({ bases: [...new Set([page.origin, ...(settings.bases || [])])].slice(0, 4) });
    const claim = await exchange(job, { claim: true });
    if (['closed', 'finished', 'error'].includes(claim.status)) return { error: '本次连接已结束，请回 TB 重新提交。' };
    const target = new URL(claim.url);
    if (target.protocol !== 'https:' || !hosts.has(target.hostname)) throw new Error('原站地址无效');
    if (claim.mode === 'silent') {
      await chrome.tabs.update(sender.tab.id, { url: target.href, active: true });
      return { connected: true };
    }
    // A reconnect reuses its own submission tab instead of creating a second submitter.
    const saved = (await chrome.storage.session.get('jobs')).jobs || {};
    const old = Object.values(saved).find(j => j.sessionId === job.sessionId && j.base === job.base);
    let existing;
    if (old && old.tabId !== job.tabId) {
      try {
        const tab = await chrome.tabs.get(old.tabId), current = new URL(tab.url);
        if (current.protocol === 'https:' && current.hostname === target.hostname) { existing=tab;job.tabId=old.tabId;job.owned=old.owned; }
      } catch { delete saved[old.tabId]; }
    }
    saved[job.tabId] = job;
    await chrome.storage.session.set({ jobs: saved });
    // Preserve this tab's form and completed verification. Reloading it here
    // would discard precisely the state the user needs to inspect or complete.
    await chrome.tabs.update(job.tabId, { ...(existing ? {} : {url:target.href}), active: true });
    if (existing) {
      await chrome.windows.update(existing.windowId, {focused:true});
      await chrome.tabs.sendMessage(job.tabId, {type:'wake'}).catch(()=>{});
    }
    if (job.tabId !== sender.tab.id) await chrome.tabs.remove(sender.tab.id);
    return { connected: true };
  }
  if (page.protocol !== 'https:' || !hosts.has(page.hostname)) return {};
  const jobs = (await chrome.storage.session.get('jobs')).jobs || {}, job = jobs[sender.tab.id];
  if (!job) return {};
  if (message.type === 'event' && message.value?.sessionId !== job.sessionId) return {};
  if (!['tick', 'event'].includes(message.type)) return {};
  const answer = await exchange(job, { pageUrl: page.href, ...(message.type === 'event' ? { event: message.value } : {}) });
  if (answer.stop) {
    const latest = (await chrome.storage.session.get('jobs')).jobs || {};
    delete latest[sender.tab.id]; await chrome.storage.session.set({ jobs: latest });
    if (job.owned && answer.status === 'finished') await chrome.tabs.remove(sender.tab.id).catch(() => {});
  }
  return answer;
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  // Serialize commands and receipts for each tab, including async storage writes.
  const key = sender.tab?.id;
  const next = (queues.get(key) || Promise.resolve()).catch(() => {}).then(() => handle(message, sender));
  queues.set(key, next);
  next.then(respond, () => respond({ error: '与 TB 的连接中断，请回到 TB 查看状态。' })).finally(() => { if (queues.get(key) === next) queues.delete(key); });
  return true;
});
chrome.alarms.create('tb-browser-heartbeat', { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener(async alarm => {
  if (alarm.name !== 'tb-browser-heartbeat') return;
  await pollQueues();
  const jobs = (await chrome.storage.session.get('jobs')).jobs || {};
  for (const job of Object.values(jobs)) {
    try { await chrome.tabs.sendMessage(job.tabId, { type: 'wake' }); } catch { /* Desktop detects a lost tab with a bounded timeout. */ }
  }
});
chrome.runtime.onStartup.addListener(pollQueues);
chrome.runtime.onInstalled.addListener(pollQueues);
chrome.cookies.onChanged.addListener(({cookie}) => {
  const domain = cookie.domain.replace(/^\./,'').toLowerCase();
  const scopes = {Codeforces:'codeforces.com',AtCoder:'atcoder.jp','牛客':'nowcoder.com','洛谷':'luogu.com.cn'};
  for (const [platform, root] of Object.entries(scopes)) {
    if (domain === root || domain.endsWith('.'+root)) loginDirty.add(platform);
  }
  if (loginDirty.size) pollQueues();
});
// Requests keep an active desktop session responsive; the alarm revives an idle
// service worker. No cookies, account passwords or CSRF tokens leave the browser.
setInterval(pollQueues, 1000);
pollQueues();
