// HTTP contract shared by the browser build and the desktop webview.
const pendingReads = new Map();
let generation = 0;

export function request(path, body, token) {
  if (body !== undefined) {
    generation++;
    return load(path, body, token);
  }
  // Share concurrent reads (including StrictMode's initial effects), while
  // every completed request and every write still permits a fresh response.
  const key = `${generation}:${window.__tbAccountUserId || ''}:${token || ''}:${path}`;
  if (pendingReads.has(key)) return pendingReads.get(key);
  const pending = load(path, body, token).finally(() => {
    if (pendingReads.get(key) === pending) pendingReads.delete(key);
  });
  pendingReads.set(key, pending);
  return pending;
}

async function load(path, body, token) {
  const base = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
  const accountRequest = /^account(?:[/?]|$)/.test(path);
  const controller = accountRequest ? new AbortController() : null;
  // Backend account barriers and authentication/state initialization have
  // separate finite budgets. Leave room for their structured error response;
  // this guard handles a broken local connection, never retries a password POST.
  const milliseconds = body === undefined ? 12000 : path === 'account/register' ? 15000 : path === 'account/login' ? 45000 : 60000;
  const timeout = controller ? setTimeout(() => controller.abort(), milliseconds) : null;
  let response, text;
  try {
    response = await fetch(`${base}/${path}`, body === undefined
      ? { cache: 'no-store', ...(controller ? { signal: controller.signal } : {}) }
      : { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-TB-Token': token }, body: JSON.stringify(body), ...(controller ? { signal: controller.signal } : {}) });
    text = await response.text();
  } catch (issue) {
    if (controller?.signal.aborted) {
      const error = new Error(path === 'account/register'
        ? '尚未收到注册结果，请先尝试用该登录号登录；本机学习记录已保留'
        : '账号连接暂未完成，本机学习记录已保留，请重新连接');
      error.uncertain = body !== undefined;
      throw error;
    }
    throw issue;
  } finally { if (timeout) clearTimeout(timeout); }
  let result;
  try { result = JSON.parse(text); }
  catch { throw new Error('ToBe 服务没有返回有效数据，请检查服务连接'); }
  if (!response.ok) {
    const error = new Error(result.error || '操作未完成，请重试');
    error.status = response.status;
    if (response.status === 401 && !['account/login', 'account/register'].includes(path)) window.dispatchEvent(new Event('tb:account-change'));
    throw error;
  }
  return result;
}
