// Direct HTTPS judge transport, derived from the reviewed 002 adapter.
// The configured endpoint is immutable for this instance; no redirect or retry.
import {request} from 'node:https';
import {constants as cryptoConstants} from 'node:crypto';
import {isIP} from 'node:net';

export const TOTAL_DEADLINE_MS = 45000;
export const MAX_REQUEST_BYTES = 128 * 1024;
export const MAX_RESPONSE_BYTES = 128 * 1024;
const allowedOptions = new Set(['method', 'redirect', 'signal', 'headers', 'body']);
const fail = (code, nativeCode) => Object.assign(new Error(code), {name: 'HttpsAdapterError', safeCode: code,
  ...(typeof nativeCode === 'string' && /^[A-Z0-9_]{1,80}$/.test(nativeCode) ? {nativeCode} : {})});
const check = (ok, code) => { if (!ok) throw fail(code); };

export function validateJudgeHttpsEnvironment(env = process.env, argv = process.execArgv) {
  const overrides = /^(?:https?_proxy|all_proxy|no_proxy|node_use_env_proxy|global_agent_http_proxy|npm_config_(?:https?_proxy|proxy)|node_tls_reject_unauthorized|node_extra_ca_certs|ssl_cert_file|ssl_cert_dir|sslkeylogfile|openssl_conf|openssl_modules)$/i;
  for (const [name, value] of Object.entries(env)) if (value && overrides.test(name)) throw fail('HTTPS_ENV_OVERRIDE_FORBIDDEN');
  // Preserve ordinary container memory limits; do not admit a preload, proxy,
  // certificate or TLS override through NODE_OPTIONS.
  const remaining = String(env.NODE_OPTIONS || '').replace(/--max[-_](?:old|semi)[-_]space[-_]size(?:=|\s+)\d+/g, '').trim();
  check(!remaining, 'HTTPS_NODE_OPTIONS_FORBIDDEN');
  const forbidden = /^--(?:use-(?:system|openssl|bundled)-ca|use-env-proxy|tls-|openssl-|enable-fips|force-fips|require(?:=|$)|import(?:=|$))/;
  // Node's test/process launcher can materialize its own default cipher list.
  // Accept only that exact built-in list, never a caller-selected TLS policy.
  const defaultCiphers='--tls-cipher-list='+cryptoConstants.defaultCoreCipherList;
  check(!argv.some(arg => arg!==defaultCiphers && forbidden.test(arg)), 'HTTPS_CLI_OVERRIDE_FORBIDDEN');
}

function core(endpoint, deadlineMs) {
  validateJudgeHttpsEnvironment();
  const target = new URL(endpoint);
  check(target.protocol === 'https:' && !target.username && !target.password && !target.search && !target.hash &&
    target.pathname.endsWith('/chat/completions'), 'HTTPS_ENDPOINT_INVALID');
  const href = target.href;

  function validate(input, options) {
    validateJudgeHttpsEnvironment();
    let actual;
    try { if (typeof input === 'string' || input instanceof URL) actual = new URL(input).href; } catch {}
    check(actual === href, 'HTTPS_TARGET_CHANGED');
    check(options && typeof options === 'object' && Object.keys(options).every(name => allowedOptions.has(name)), 'HTTPS_OPTIONS_UNSUPPORTED');
    check(options.method === 'POST' && options.redirect === 'error', 'HTTPS_METHOD_OR_REDIRECT');
    check(options.signal instanceof AbortSignal, 'HTTPS_SIGNAL_REQUIRED');
    check(!options.signal.aborted, 'HTTPS_ABORTED');
    check(typeof options.body === 'string' && Buffer.byteLength(options.body) <= MAX_REQUEST_BYTES, 'HTTPS_REQUEST_SIZE');
    check(options.headers && [Object.prototype, null].includes(Object.getPrototypeOf(options.headers)), 'HTTPS_HEADERS_INVALID');
    const headers = new Map();
    for (const [name, value] of Object.entries(options.headers)) {
      const lower = name.toLowerCase();
      check(['authorization', 'content-type'].includes(lower) && !headers.has(lower) && typeof value === 'string' && !/[\r\n]/.test(value), 'HTTPS_HEADERS_INVALID');
      headers.set(lower, value);
    }
    check(headers.size === 2 && /^Bearer [^\s\x00-\x1f\x7f]{1,4096}$/.test(headers.get('authorization') || '') &&
      headers.get('content-type') === 'application/json', 'HTTPS_HEADERS_INVALID');
    return headers;
  }

  async function fetchImpl(input, options) {
    const headers = validate(input, options);
    const bytes = Buffer.from(options.body);
    return new Promise((resolve, reject) => {
      let req, response, reason, settled = false, ended = false, readerTaken = false, iterator, total = 0;
      const cleanup = () => { clearTimeout(timer); options.signal.removeEventListener('abort', cancelled); };
      const stop = error => {
        if (!reason) reason = error;
        cleanup(); response?.destroy(reason); req?.destroy(reason);
        if (!settled) { settled = true; reject(reason); }
      };
      const cancelled = () => stop(fail('HTTPS_ABORTED'));
      const timer = setTimeout(() => stop(fail('HTTPS_TOTAL_TIMEOUT')), deadlineMs);
      options.signal.addEventListener('abort', cancelled, {once: true});
      if (options.signal.aborted) { cancelled(); return; }
      try {
        req = request(target, {method: 'POST', agent: false, rejectUnauthorized: true,
          ...(isIP(target.hostname) ? {} : {servername: target.hostname}),
          headers: {Authorization: headers.get('authorization'), 'Content-Type': 'application/json',
            'Content-Length': bytes.length, 'Accept-Encoding': 'identity', Connection: 'close'}}, incoming => {
          response = incoming;
          incoming.once('end', () => { ended = true; cleanup(); });
          incoming.once('error', error => {
            if (!reason) reason = fail('HTTPS_RESPONSE_ERROR', error.code);
            cleanup();
          });
          const getReader = () => {
            check(!readerTaken, 'HTTPS_BODY_ALREADY_USED'); readerTaken = true;
            const encoding = incoming.headers['content-encoding'];
            if (encoding && String(encoding).toLowerCase() !== 'identity') { const error = fail('HTTPS_CONTENT_ENCODING'); stop(error); throw error; }
            iterator = incoming[Symbol.asyncIterator]();
            return {
              read: async () => {
                if (reason) throw reason;
                try {
                  const item = await iterator.next();
                  if (reason) throw reason;
                  if (item.done) { ended = true; cleanup(); return {done: true, value: undefined}; }
                  total += item.value.length;
                  if (total > MAX_RESPONSE_BYTES) { const error = fail('HTTPS_RESPONSE_SIZE'); stop(error); throw error; }
                  return {done: false, value: item.value};
                } catch (error) { const wrapped = reason || (error.safeCode ? error : fail('HTTPS_RESPONSE_ERROR', error.code)); stop(wrapped); throw wrapped; }
              },
              cancel: async () => { if (!ended) stop(fail('HTTPS_BODY_CANCELLED')); cleanup(); },
            };
          };
          const text = async () => {
            const reader = getReader(), chunks = [];
            for (;;) { const value = await reader.read(); if (value.done) break; chunks.push(value.value); }
            return Buffer.concat(chunks).toString('utf8');
          };
          settled = true;
          resolve({ok: incoming.statusCode >= 200 && incoming.statusCode < 300, status: incoming.statusCode,
            statusText: incoming.statusMessage, headers: {get: name => {
              const value = incoming.headers[String(name).toLowerCase()];
              return value === undefined ? null : Array.isArray(value) ? value.join(', ') : value;
            }}, body: {getReader}, text});
        });
        req.once('error', error => stop(reason || fail('HTTPS_CONNECTION', error.code)));
        req.end(bytes); // Exactly one request; never redirect or retry.
      } catch (error) { stop(error.safeCode ? error : fail('HTTPS_CONNECTION', error.code)); }
    });
  }
  fetchImpl.validate = validate; // Pure target/options/body-size check before durable outbound gate.
  return fetchImpl;
}

export function createJudgeHttpsFetch(endpoint, {deadlineMs = TOTAL_DEADLINE_MS} = {}) {
  check(Number.isInteger(deadlineMs) && deadlineMs > 0 && deadlineMs <= TOTAL_DEADLINE_MS, 'HTTPS_DEADLINE');
  return core(endpoint, deadlineMs);
}
