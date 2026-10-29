// Observe the original site's requests without replacing submit or judge behavior.
// Contest protocol: public terminal 2.0.114; global problem identity/native
// form parameters also checked against public terminal 2.0.118 (2026-10-29).
function installNowcoderReceipts(ctx, report) {
  if (ctx.platform !== '牛客' || location.hostname !== 'ac.nowcoder.com') return null;
  if (window.__tbNowcoder?.sessionId === ctx.sessionId) return window.__tbNowcoder;
  const state = { sessionId: ctx.sessionId, armed: false, pending: null, receipt: null, early: [] };
  state.confirmedIds = new Set();
  window.__tbNowcoder = state;
  const notify = value => {
    if (value.status === 'finished' && state.pending) value = {...value, owner:state.pending.owner, url:ctx.originalUrl, acceptedAt:state.pending.acceptedAt};
    state.receipt = value;
    if (report) report(value);
    else chrome.webview.postMessage(JSON.stringify({ tbOfficial: true, sessionId: ctx.sessionId, ...value }));
  };
  const textCode = value => String(value || '').replace(/\r\n/g, '\n').trim();
  const fields = body => {
    if (!body) return {};
    if (typeof body === 'string') {
      try { return JSON.parse(body); } catch { return Object.fromEntries(new URLSearchParams(body)); }
    }
    try { return Object.fromEntries(body.entries()); } catch { return {}; }
  };
  const parseUrl = value => { try { return new URL(value, location.href); } catch { return null; } };
  // The current terminal sends judging requests to the production editor API.
  // These are the two verified production origins, not arbitrary subdomains.
  const allowed = url => url && ['https://ac.nowcoder.com', 'https://victorinox.nowcoder.com'].includes(url.origin);
  const submitPaths = new Set(['/submit_cd', '/nccommon/submit_cd', '/api/service/judge/submit']);
  const statusPaths = new Set(['/status', '/nccommon/status', '/api/service/judge/submit-status']);
  const id = value => /^\d+$/.test(String(value ?? '')) && BigInt(value) > 0n ? String(value) : null;
  state.isGlobalTarget = () => /^\/acm\/problem\/[1-9]\d{0,19}$/.test(parseUrl(ctx.originalUrl)?.pathname || '');
  const pageIdentity = () => {
    const original = parseUrl(ctx.originalUrl), info = window.pageInfo;
    if (!original || original.origin !== 'https://ac.nowcoder.com' || location.origin !== original.origin || location.pathname !== original.pathname || !info || !id(info.questionId)) return null;
    const global = original.pathname.match(/^\/acm\/problem\/([1-9]\d{0,19})$/);
    if (global) {
      // The global NC number is NOT the internal questionId and is not a
      // contestId. Bind both actual IDs from this exact page, never infer one.
      if (id(info.problemId) !== global[1] || id(info.doneQuestionId) !== global[1] || info.contestId != null && String(info.contestId) !== '' || String(info.codeJudgeType) !== '0' || String(info.tagId) !== '4' || String(info.subTagId) !== '0') return null;
      return {kind:'global', problemId:global[1], questionId:id(info.questionId), originalUrl:original.href};
    }
    const contest = original.pathname.match(/^\/acm\/contest\/(\d+)\/[A-Za-z]\d?$/);
    return contest && String(info.contestId) === contest[1] ? {kind:'contest',questionId:id(info.questionId),originalUrl:original.href} : null;
  };
  state.pageMatches = () => !!pageIdentity();
  state.loggedOut = () => state.isGlobalTarget() && (window.isLogin === false || !id(window.globalInfo?.ownerId));
  const requestInfo = (url, method, body) => {
    const target = parseUrl(url), params = { ...Object.fromEntries(target?.searchParams || []), ...fields(body) };
    if (!allowed(target)) return null;
    if (statusPaths.has(target.pathname)) return { kind: 'status', target, params: { ...Object.fromEntries(target.searchParams), ...params } };
    const passive = ctx.sessionId === 'unbound';
    if ((!state.armed && !passive) || method.toUpperCase() !== 'POST' || !submitPaths.has(target.pathname)) return null;
    const identity = pageIdentity(), info = window.pageInfo;
    if (!identity) return null;
    if (String(params.questionId) !== identity.questionId || (!passive && !ctx.manual && textCode(params.content) !== textCode(ctx.code))) return null;
    if (target.pathname === '/api/service/judge/submit' && String(params.submitType) !== '1') return null;
    if (params.selfType != null || params.selfInputData != null || params.input != null || params.isSelfTest) return null;
    const owner = id(window.globalInfo?.ownerId);
    if (identity.kind === 'global') {
      if (!owner || window.isLogin === false || id(info.teamId) && id(info.teamId) !== owner || state.pending && !passive) return null;
      if (!textCode(params.content) || !/^\d+$/.test(String(params.language ?? '')) || String(params.tagId) !== String(info.tagId)) return null;
      if (params.problemId != null && id(params.problemId) !== identity.problemId) return null;
      if (target.pathname === '/api/service/judge/submit') {
        if (target.origin !== 'https://victorinox.nowcoder.com' || String(params.userId) !== owner || String(params.appId) !== '6') return null;
      } else if (target.origin !== location.origin || id(params.doneQuestionId) !== identity.problemId || String(params.subTagId) !== String(info.subTagId)) return null;
    }
    const submitOwner = id(info.teamId) || owner;
    if (params.userId != null && (!submitOwner || String(params.userId) !== submitOwner)) return null;
    return { kind: 'submit', target, params, owner, identity };
  };
  // Evaluate a status payload against the confirmed pending submission.
  const evaluateStatus = (pending, params, data) => {
    if (!pending || id(params.submissionId ?? params.id) !== pending.submissionId || !data || typeof data !== 'object') return null;
    if (params.submitType != null && String(params.submitType) !== '1') return null;
    if (data.submissionId != null && id(data.submissionId) !== pending.submissionId || data.id != null && id(data.id) !== pending.submissionId) return null;
    for (const key of ['userId', 'appId', 'tagId']) {
      if (pending[key] != null && String(params[key]) !== String(pending[key])) return null;
      if (pending[key] != null && data[key] != null && String(data[key]) !== String(pending[key])) return null;
    }
    if (pending.identity?.kind === 'global') {
      const current = pageIdentity();
      if (!current || current.kind !== 'global' || current.problemId !== pending.identity.problemId || current.questionId !== pending.identity.questionId || current.originalUrl !== pending.identity.originalUrl || state.loggedOut() || id(window.globalInfo?.ownerId) !== pending.owner) return null;
      if (pending.subTagId != null && String(params.subTagId) !== String(pending.subTagId)) return null;
      if (params.selfType != null || params.selfInputData != null || params.input != null || ['1','true'].includes(String(data.isSelfTest))) return null;
      for (const key of ['questionId','problemId','doneQuestionId']) {
        const expected = key === 'questionId' ? pending.identity.questionId : pending.identity.problemId;
        if (params[key] != null && id(params[key]) !== expected || data[key] != null && id(data[key]) !== expected) return null;
      }
      if (data.userId != null && id(data.userId) !== pending.owner || data.ownerId != null && id(data.ownerId) !== pending.owner) return null;
      if (data.subTagId != null && String(data.subTagId) !== String(pending.subTagId)) return null;
    }
    if (pending.owner && window.globalInfo?.ownerId != null && String(window.globalInfo.ownerId) !== pending.owner) return null;
    if (data.error || data.isSelfTest === true || data.isSelfTest === 1 || !Number.isInteger(data.status)) return null;
    if (data.status >= 0 && data.status <= 2) return null;
    const descriptions = { '编译错误': 'CE', '答案错误': 'WA', '运行超时': 'TLE', '超时': 'TLE', '内存超限': 'MLE', '运行错误': 'RE', '输出超限': 'OLE' };
    const failure = descriptions[String(data.desc || '').trim()] || normal(data.desc);
    return data.status === 5 ? 'AC' : failure && failure !== 'AC' && failure !== 'JUDGING' ? failure : null;
  };
  const observe = (request, value) => {
    if (!request || !value || typeof value !== 'object') return;
    if (request.kind === 'submit' && request.identity?.kind === 'global' && value.code === 999) {
      state.armed = false;
      notify({status:'needs_login',attempted:false,message:'牛客登录已失效，请在浏览器登录后重试。'});
      return;
    }
    if (request.kind === 'submit' && Number.isInteger(value.code) && (value.code !== 0 || value.error)) {
      state.armed = false;
      const verification = value.code === 1125 || /captcha|验证码|验证/.test(String(value.errorType || '') + ' ' + String(value.msg || ''));
      notify({ status: verification ? 'needs_verification' : 'error', attempted: false,
        message: verification ? '牛客要求验证，请打开原站完成验证后再提交。' : '牛客未受理代码：' + String(value.msg || '请打开原站检查提交要求。').slice(0,160) });
      return;
    }
    if (value.code !== 0 || value.error) return;
    // Legacy /nccommon endpoints return submissionId/status at the top level.
    // Both envelopes are used by the site's own current codeSubmit module.
    const data = value.data ?? value;
    if (request.kind === 'submit') {
      const submissionId = id(typeof data === 'object' ? data?.submissionId ?? data?.id : data);
      if (!submissionId) return;
      if (request.identity?.kind === 'global') {
        const current = pageIdentity(), previous = [...(ctx.baseline || []), ...state.confirmedIds];
        if (!current || current.kind !== 'global' || current.problemId !== request.identity.problemId || current.questionId !== request.identity.questionId || state.loggedOut() || id(window.globalInfo?.ownerId) !== request.owner) return;
        if (previous.some(value => id(value) && BigInt(value) >= BigInt(submissionId))) return;
        state.confirmedIds.add(submissionId);
      }
      state.pending = { submissionId, owner: request.owner, identity:request.identity, acceptedAt:new Date().toISOString(), origin: request.target.origin, userId: request.params.userId, appId: request.params.appId, tagId: request.params.tagId, subTagId:request.params.subTagId };
      if (request.identity?.kind === 'global') state.armed = false;
      // Keep the site's short-lived judge token in this page only. It is never
      // sent to TB, persisted, logged, or used to submit a second request.
      const modern = request.target.pathname === '/api/service/judge/submit';
      const query = modern ? { id: submissionId, submitType: 1 } : { submissionId };
      for (const key of ['userId', 'appId', 'tagId', 'subTagId', 'token']) {
        if (request.params[key] != null) query[key] = request.params[key];
      }
      const statusPath = modern ? '/api/service/judge/submit-status' : request.target.pathname.startsWith('/nccommon/') ? '/nccommon/status' : '/status';
      state.statusUrl = new URL(statusPath + '?' + new URLSearchParams(query), request.target.origin).href;
      state.attempted = true;
      // 受理时刻随 judging 消息一起发出：宿主据此持久化 pending，并用它（而非
      // 收到回执的时间）记 submitted_at。不额外多发消息，保持既有消息条数契约。
      notify({ status: 'judging', submissionId, attempted:true, ...(ctx.manual ? {submittedCode:String(request.params.content || '')} : {}), acceptedAt: state.pending.acceptedAt, message: '牛客已接收本次提交 #' + submissionId + '，正在评测。' });
      // Replay any status payload that arrived before we knew the submission ID.
      const early = state.early; state.early = [];
      for (const item of early) {
        if (item.origin !== state.pending.origin || id(item.params.submissionId ?? item.params.id) !== submissionId) continue;
        const verdict = evaluateStatus(state.pending, item.params, item.data);
        if (verdict) { notify({ status: 'finished', submissionId, verdict, message: '牛客确认本次提交 #' + submissionId + '：' + verdict }); break; }
      }
      return;
    }
    // Status response. If the pending submission is not known yet, buffer it so a
    // late-arriving submit response can still promote a real terminal verdict
    // instead of the client hanging in "judging" forever.
    if (!state.pending) {
      if (id(request.params.submissionId ?? request.params.id)) {
        state.early.push({ origin: request.target.origin, params: request.params, data });
        if (state.early.length > 10) state.early.shift();
      }
      return;
    }
    if (request.target.origin !== state.pending.origin) return;
    const verdict = evaluateStatus(state.pending, request.params, data);
    if (verdict) notify({ status: 'finished', submissionId: state.pending.submissionId, verdict, message: '牛客确认本次提交 #' + state.pending.submissionId + '：' + verdict });
  };
  const originalFetch = window.fetch;
  // Global problems always use the site's real submit control. In particular,
  // do not synthesize a contestId or bypass the native CSRF/captcha handling.
  state.hasLegacyApi = () => !state.isGlobalTarget() && window.pageInfo?.isNewJudgeEditor === false && String(window.pageInfo?.codeJudgeType) === '0';
  state.submitLegacy = async (compiler, checkpoint) => {
    const info = window.pageInfo, original = parseUrl(ctx.originalUrl);
    if (!state.hasLegacyApi() || location.pathname !== original?.pathname || String(info.contestId) !== original.pathname.split('/')[3] || !id(info.questionId)) throw new Error('牛客题目信息尚未就绪');
    if (!id(window.globalInfo?.ownerId)) return notify({status:'needs_login', attempted:false, message:'请先在浏览器登录牛客，再回 TB 提交。'});
    // Language 2 is the C++ compiler in the verified production legacy config.
    // Select/validate its displayed compiler first, while sending code directly.
    const body = {questionId:info.questionId, tagId:info.tagId, subTagId:info.subTagId,
      doneQuestionId:info.doneQuestionId, content:ctx.code, language:'2', languageName:compiler.label};
    const token = document.cookie.split(';').map(p=>p.trim()).find(p=>p.startsWith('csrf_token='))?.slice(11);
    const target = new URL('/nccommon/submit_cd', location.origin);
    if (token) target.searchParams.set('token', decodeURIComponent(token));
    state.armed = true; state.pending = null; state.receipt = null;
    await checkpoint({status:'submitted', attempted:true, compiler:compiler.label, message:'正在调用牛客提交接口，等待原站受理。'});
    const request = requestInfo(target.href, 'POST', new URLSearchParams(body));
    if (!request) throw new Error('牛客提交参数与本题不匹配');
    try {
      const response = await originalFetch.call(window, target.href, {method:'POST', credentials:'same-origin',
        headers:{'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8','X-Requested-With':'XMLHttpRequest'},
        body:new URLSearchParams(body), signal:AbortSignal.timeout(30000)});
      const value = await response.json();
      if (value.code === 999) return notify({status:'needs_login',attempted:false,message:'牛客登录已失效，请在浏览器登录后重试。'});
      observe(request, value);
      if (!state.receipt) notify({status:'unconfirmed',message:'牛客暂未返回可识别的受理编号，请核对原站提交记录。'});
    } catch {
      notify({status:'unconfirmed',message:'牛客提交请求的响应中断，请先核对原站记录，避免重复提交。'});
    }
  };
  // Called by the desktop watcher, so receipt collection does not depend on
  // timers or visibility of the site's background console.
  state.poll = async () => {
    if (!state.statusUrl || state.polling || state.receipt?.status === 'finished' || typeof originalFetch !== 'function') return;
    state.polling = true;
    try {
      const result = await originalFetch.call(window, state.statusUrl, { credentials: 'include', cache: 'no-store', signal: AbortSignal.timeout(15000) });
      const target = parseUrl(result.url || state.statusUrl);
      if (result.ok && allowed(target) && target.origin === state.pending?.origin && (!state.isGlobalTarget() || target.pathname === parseUrl(state.statusUrl)?.pathname)) {
        observe(requestInfo(state.statusUrl, 'GET'), await result.json());
      }
    } catch {} finally { state.polling = false; }
  };
  if (typeof originalFetch === 'function') {
    window.fetch = function(resource, options) {
      const url = typeof resource === 'string' || resource instanceof URL ? String(resource) : resource.url;
      const method = options?.method || resource?.method || 'GET';
      const info = options?.body != null ? Promise.resolve(requestInfo(url, method, options.body)) :
        typeof resource?.clone === 'function' && method.toUpperCase() === 'POST' ? resource.clone().text().then(body => requestInfo(url, method, body)).catch(() => null) : Promise.resolve(requestInfo(url, method));
      const response = originalFetch.apply(this, arguments);
      response.then(result => {
        if (result.ok && allowed(parseUrl(result.url || url))) {
          const copy = result.clone();
          info.then(request => {
            if (request && (!state.isGlobalTarget() || parseUrl(result.url || url)?.origin === request.target.origin && parseUrl(result.url || url)?.pathname === request.target.pathname)) copy.json().then(value => observe(request, value)).catch(() => {});
          });
        }
      }).catch(() => {});
      return response;
    };
  }
  if (window.XMLHttpRequest) {
    const proto = window.XMLHttpRequest.prototype, open = proto.open, send = proto.send;
    proto.open = function(method, url) { this.__tbRequest = { method, url }; return open.apply(this, arguments); };
    proto.send = function(body) {
      const meta = this.__tbRequest, request = meta && requestInfo(meta.url, meta.method, body);
      if (request) this.addEventListener('load', () => {
        if (this.status < 200 || this.status >= 300 || !allowed(parseUrl(this.responseURL || meta.url))) return;
        if (state.isGlobalTarget() && (parseUrl(this.responseURL || meta.url)?.origin !== request.target.origin || parseUrl(this.responseURL || meta.url)?.pathname !== request.target.pathname)) return;
        try { observe(request, this.responseType === 'json' ? this.response : JSON.parse(this.responseText)); } catch {}
      }, { once: true });
      return send.apply(this, arguments);
    };
  }
  return state;
}
