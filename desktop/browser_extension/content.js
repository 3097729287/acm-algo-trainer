(() => {
  let busy = false, stopped = false;
  const channel = crypto.randomUUID();
  const run = answer => {
    if (answer?.stop) { stopped = true; return; }
    if (answer?.context) window.postMessage({ tbBrowserCommand: channel, ...answer }, location.origin);
  };
  async function tick() {
    if (busy || stopped || document.readyState === 'loading') return;
    busy = true;
    try { run(await chrome.runtime.sendMessage({ type: 'tick' })); } catch {} finally { busy = false; }
  }
  window.addEventListener('message', event => {
    if (event.source !== window || event.origin !== location.origin || event.data?.tbBrowserResult !== channel) return;
    const requestId = event.data.requestId;
    chrome.runtime.sendMessage({ type: 'event', value: event.data.value }).then(answer => {
      if (requestId) window.postMessage({ tbBrowserAck: channel, requestId, ok: answer?.ack === true }, location.origin);
      run(answer);
      if (event.data.value?.status === 'ready') tick();
    }).catch(() => {
      if (requestId) window.postMessage({ tbBrowserAck: channel, requestId, ok: false }, location.origin);
    });
  });
  chrome.runtime.onMessage.addListener((message, sender, reply) => {
    if (message.type === 'wake') { stopped = false; tick(); }
    if (message.type === 'submission-page') {
      // Reuse only an idle AtCoder form for this exact task. Never disclose a
      // verification token or replace code that the user wrote in the browser.
      let available = false;
      try {
        const target = new URL(message.url);
        const task = document.querySelector('select[name="data.TaskScreenName"]');
        const editors = [...document.querySelectorAll('textarea')].filter(e => /source|code|editor/i.test(e.name + ' ' + e.id));
        const rendered = [...document.querySelectorAll('.ace_text-layer,.CodeMirror-code,.monaco-editor .view-lines,.cm-content')];
        available = location.hostname === 'atcoder.jp' && target.origin === location.origin && target.pathname === location.pathname
          && document.readyState !== 'loading' && task?.value === target.searchParams.get('taskScreenName')
          && editors.length > 0 && editors.every(e => !e.value.trim()) && rendered.every(e => !e.textContent.trim());
      } catch {}
      reply({available});
    }
    if (message.type === 'login-state') {
      const platform = ({'codeforces.com':'Codeforces','www.codeforces.com':'Codeforces','atcoder.jp':'AtCoder','ac.nowcoder.com':'牛客','www.luogu.com.cn':'洛谷','luogu.com.cn':'洛谷'})[location.hostname];
      if (platform !== message.platform) { reply({state:'unknown'}); return; }
      // Check a fresh same-origin page: an old sign-in/header DOM can remain
      // open after logging in or out elsewhere. No navigation or form action.
      const path = platform === '牛客' ? '/acm/home' : '/';
      fetch(path,{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(5000)})
        .then(async response=>{
          if (!response.ok || Number(response.headers.get('content-length')) > 1048576) return {state:'unknown'};
          const html = await response.text();
          return {state:html.length <= 1048576 ? tbPageLoginState(platform,html) : 'unknown',fresh:true};
        }).then(reply,()=>reply({state:'unknown'}));
      return true;
    }
  });
  document.addEventListener('DOMContentLoaded', tick, { once: true });
  setInterval(tick, 1000);
})();
