(() => {
  let busy = false, stopped = false, timer, idle = true;
  const channel = crypto.randomUUID();
  const run = answer => {
    if (answer?.stop) { stopped = true; clearTimeout(timer); return; }
    if (answer?.idle === true) idle = true;
    if (answer?.context) { idle = false; window.postMessage({ tbBrowserCommand: channel, ...answer }, location.origin); }
  };
  async function tick() {
    if (busy || stopped) return;
    busy = true;
    clearTimeout(timer);
    try { run(await chrome.runtime.sendMessage({ type: 'tick' })); } catch {} finally {
      busy = false;
      if (!stopped) timer = setTimeout(tick, idle ? 30000 : 1000);
    }
  }
  window.addEventListener('message', event => {
    if (event.source !== window || event.origin !== location.origin || event.data?.tbBrowserResult !== channel) return;
    const requestId = event.data.requestId;
    chrome.runtime.sendMessage({ type: 'event', value: event.data.value, inspection:event.data.inspection===true }).then(answer => {
      if (requestId) window.postMessage({ tbBrowserAck: channel, requestId, ok: answer?.ack === true }, location.origin);
      run(answer);
      if (event.data.value?.status === 'ready') tick();
    }).catch(() => {
      if (requestId) window.postMessage({ tbBrowserAck: channel, requestId, ok: false }, location.origin);
    });
  });
  chrome.runtime.onMessage.addListener((message, sender, reply) => {
    if(message.type==='identity'){
      const nonce=crypto.randomUUID();let done=false;
      const receive=event=>{if(event.source!==window||event.origin!==location.origin||event.data?.tbIdentityResponse!==nonce)return;done=true;window.removeEventListener('message',receive);reply(event.data.value)};
      window.addEventListener('message',receive);window.postMessage({tbIdentityRequest:nonce},location.origin);
      setTimeout(()=>{if(!done){window.removeEventListener('message',receive);reply({state:'unknown'})}},1200);return true;
    }
    if (message.type === 'wake') { stopped = false; idle = false; clearTimeout(timer); tick(); }
  });
  document.addEventListener('DOMContentLoaded', tick, { once: true });
  // Unbound tabs need no one-second IPC/storage polling. A newly assigned or
  // reused job is explicitly woken by the worker and remains responsive.
  if (document.readyState !== 'loading') tick();
})();
