(() => {
  const platform = ({ 'codeforces.com': 'Codeforces', 'www.codeforces.com': 'Codeforces', 'atcoder.jp': 'AtCoder', 'ac.nowcoder.com': '牛客', 'www.nowcoder.com':'牛客', 'nowcoder.com':'牛客', 'www.luogu.com.cn': '洛谷', 'luogu.com.cn': '洛谷', 'login.luogu.com.cn':'洛谷', 'qoj.ac':'QOJ' })[location.hostname];
  const context = { platform, originalUrl: location.href, sessionId: 'not-assigned', code: '', attempted: false, nativeFormOnly:true };
  let channel = '', submitted = '';
  const acknowledgments = new Map();
  const controls=new Map();
  const identity=()=>{try{const value=tbConnectedIdentity(),url=new URL(value.url);return {platform:value.platform,state:value.state,owner:value.owner||'',url:url.origin+url.pathname}}catch{return {platform,state:'unknown',url:location.origin+location.pathname}}};
  const report = (value,inspection=false) => {
    if (!channel)return;
    value={...value,ownerProof:identity()};
    for (const key of ['attempted', 'baseline', 'baselineKnown', 'baselineOwner', 'submissionId']) if (key in value) context[key] = value[key];
    if (value.status === 'submitted' && value.attempted) {
      return new Promise((resolve, reject) => {
        const requestId = crypto.randomUUID();
        const timer = setTimeout(() => { acknowledgments.delete(requestId); reject(new Error('TB 未确认连接，尚未点击原站提交按钮。')); }, 10000);
        acknowledgments.set(requestId, ok => { clearTimeout(timer); acknowledgments.delete(requestId); ok ? resolve() : reject(new Error('TB 连接已失效，尚未点击原站提交按钮。')); });
        window.postMessage({ tbBrowserResult: channel, value, requestId, inspection }, location.origin);
      });
    }
    window.postMessage({ tbBrowserResult: channel, value, inspection }, location.origin);
  };
  // Observe before the site can cache fetch/XHR. Context is filled later, without
  // replacing the observer or losing closures retained by the site's editor.
  tbOfficialPage(context, 'observe', report);
  window.addEventListener('message', event => {
    const packet = event.data;
    if(event.source===window&&event.origin===location.origin&&packet?.tbIdentityRequest){window.postMessage({tbIdentityResponse:packet.tbIdentityRequest,value:identity()},location.origin);return;}
    if (event.source === window && event.origin === location.origin && channel && packet?.tbBrowserAck === channel) {
      acknowledgments.get(packet.requestId)?.(packet.ok === true);
      return;
    }
    if (event.source !== window || event.origin !== location.origin || !packet?.tbBrowserCommand || !packet.context || packet.context.platform !== platform) return;
    if (channel && channel !== packet.tbBrowserCommand) return;
    channel = packet.tbBrowserCommand;
    if (context.sessionId !== packet.context.sessionId && context.sessionId !== 'not-assigned') {
      // A reused page keeps its original fetch observers, but an old receipt
      // must never be reported as the new job's result.
      submitted = '';
      for (const state of [window.__tbNowcoder, window.__tbLuogu]) if (state) {
        state.armed = false; state.pending = null; state.receipt = null;
      }
      delete window.__tbSubmissionWork;
    }
    Object.assign(context, packet.context);
    if(packet.action==='control'){
      const key=context.sessionId+':'+context.controlCommand;
      if(!controls.has(key)){
        const request=context.control;let value;
        if(request.kind==='identity')value={identity:identity(),url:location.origin+location.pathname,ready:document.readyState};
        else if(request.kind==='read')value=tbConnectedRead(identity());
        else if(request.kind==='virtual'){
          const current=identity(),expected=context.expectedOwner;
          const same=current.state==='logged_in'&&expected&&current.owner?.toLowerCase()===expected.toLowerCase();
          value=request.context?.action==='start'&&!same?{state:'login',identity:current}:{...tbVirtualContest(request.context),identity:current};
        }
        else return;
        controls.set(key,value);
      }
      report({sessionId:context.sessionId,controlCommand:context.controlCommand,value:controls.get(key)});return;
    }
    for (const state of [window.__tbNowcoder, window.__tbLuogu]) if (state) state.sessionId = context.sessionId;
    if (packet.action === 'submit') {
      const key = context.sessionId + ':' + packet.command;
      if (submitted === key) return;
      submitted = key;
    }
    try {
      const result = tbOfficialPage(context, packet.action, report);
      if (result?.status && packet.action !== 'submit') report({ tbOfficial: true, sessionId: context.sessionId, ...result },true);
    } catch {
      report({ sessionId: context.sessionId, status: 'error', message: '原站页面尚未就绪，请检查浏览器中的提交页面。' });
    }
  });
})();
