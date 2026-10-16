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
  const response = await fetch(`${base}/${path}`, body === undefined
    ? { cache: 'no-store' }
    : { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-TB-Token': token }, body: JSON.stringify(body) });
  const text = await response.text();
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
