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
  const timeout = controller ? setTimeout(() => controller.abort(), body === undefined ? 12000 : 60000) : null;
  let response, text;
  try {
    response = await fetch(`${base}/${path}`, body === undefined
      ? { cache: 'no-store', ...(controller ? { signal: controller.signal } : {}) }
      : { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-TB-Token': token }, body: JSON.stringify(body), ...(controller ? { signal: controller.signal } : {}) });
    text = await response.text();
  } catch (issue) {
    if (controller?.signal.aborted) throw new Error('登录服务响应超时，本机学习记录已保留，请重试连接');
    throw issue;
  } finally { if (timeout) clearTimeout(timeout); }
  let result;
  try { result = JSON.parse(text); }
  catch { throw new Error('TB 服务没有返回有效数据，请检查服务连接'); }
  if (!response.ok) {
    const error = new Error(result.error || '操作未完成，请重试');
    error.status = response.status;
    if (response.status === 401 && !['account/login', 'account/register'].includes(path)) window.dispatchEvent(new Event('tb:account-change'));
    throw error;
  }
  return result;
}
