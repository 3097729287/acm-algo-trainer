// One versioned boundary; product pages keep using request(path, body, token).
// Native failures never fall back to a local HTTP server or replay a write.
export const IPC_VERSION = 1;

export function isNativeRuntime(scope = globalThis.window) {
  return Boolean(scope?.__TAURI_INTERNALS__ || scope?.__TAURI__);
}

export function nativeRequest(path, body, token, owner, id = globalThis.crypto.randomUUID()) {
  if (typeof path !== 'string' || path.includes('#')) throw new Error('接口路径无效');
  const marker = path.indexOf('?');
  const route = marker < 0 ? path : path.slice(0, marker);
  if (!/^[a-z0-9-]+(?:\/[a-z0-9-]+)*$/.test(route)) throw new Error('接口路径无效');
  const query = Object.create(null);
  for (const [key, value] of new URLSearchParams(marker < 0 ? '' : path.slice(marker + 1))) {
    (query[key] ||= []).push(value);
  }
  if (body !== undefined && (body === null || typeof body !== 'object' || Array.isArray(body))) {
    throw new Error('请求必须是 JSON 对象');
  }
  return { version: IPC_VERSION, id, method: body === undefined ? 'GET' : 'POST', path: route, query,
    ...(body === undefined ? {} : { body }), ...(token ? { token } : {}), ...(owner ? { owner } : {}) };
}

export function apiError(value) {
  const error = new Error(typeof value?.message === 'string' ? value.message : '本次操作未完成，请重试');
  if (Number.isInteger(value?.status)) error.status = value.status;
  if (typeof value?.code === 'string') error.code = value.code;
  error.retryable = value?.retryable === true;
  error.uncertain = value?.uncertain === true;
  return error;
}

export async function invokeRequest(path, body, token, scope = globalThis.window) {
  const owner = scope.__tbAccountUserId || '';
  const request = nativeRequest(path, body, token, owner);
  const invoke = scope.__TAURI__?.core?.invoke;
  if (typeof invoke !== 'function') throw apiError({ code: 'IPC_UNAVAILABLE', message: '原生接口尚未连接' });
  let response;
  try { response = await invoke('api_request', { request }); }
  catch (issue) { throw apiError(issue); }
  if ((scope.__tbAccountUserId || '') !== owner) {
    throw apiError({ status: 409, code: 'ACCOUNT_CHANGED', message: '账号已切换，请重新读取' });
  }
  if (!response || response.version !== IPC_VERSION || response.id !== request.id || typeof response.ok !== 'boolean') {
    throw apiError({ code: 'IPC_PROTOCOL', message: '原生接口返回的数据格式无效' });
  }
  if (!response.ok) {
    const error = apiError(response.error);
    if (error.status === 401 && !['account/login', 'account/register'].includes(request.path)) {
      scope.dispatchEvent(new Event('tb:account-change'));
    }
    throw error;
  }
  if (!Object.hasOwn(response, 'data')) throw apiError({ code: 'IPC_PROTOCOL', message: '原生接口返回的数据格式无效' });
  return response.data;
}
