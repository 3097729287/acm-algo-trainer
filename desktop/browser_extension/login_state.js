// Preparation hints only. Original-site submission still verifies the account.
function tbCookieLoginState(platform, cookies) {
  const live = cookies.filter(cookie => cookie.value && (!cookie.expirationDate || cookie.expirationDate > Date.now() / 1000));
  // The live CF/AtCoder browser session is authoritative; a cookie export
  // can be empty without proving that the original page is logged out.
  if (!live.length) return ['Codeforces','AtCoder'].includes(platform) ? 'unknown' : 'logged_out';
  if (platform === 'AtCoder') {
    const session = live.find(cookie => cookie.name === 'REVEL_SESSION');
    if (session) {
      try {
        // Revel signs a URL-encoded, NUL-delimited map. The session cookie also
        // exists for guests; only its explicit user claim is a login hint.
        const value = decodeURIComponent(session.value.replace(/\+/g, ' '));
        if (/\x00UserScreenName:[A-Za-z0-9_]+\x00/.test(value)) return 'logged_in';
        if (/\x00(?:csrf_token|_TS):[^\x00]*\x00/.test(value)) return 'logged_out';
      } catch { /* Unknown encodings still require the original site's check. */ }
    }
  }
  if (platform === '牛客' && live.some(cookie => cookie.name === 't')) return 'logged_in';
  if (platform === '洛谷') {
    const user = live.find(cookie => cookie.name === '_uid');
    if (user?.value === '0') return 'logged_out';
    if (/^[1-9]\d*$/.test(user?.value || '') && live.some(cookie => cookie.name === '__client_id')) return 'logged_in';
  }
  return 'unknown';
}

function tbFirstPartyCookie(platform, cookie) {
  const root = {Codeforces:'codeforces.com',AtCoder:'atcoder.jp','牛客':'nowcoder.com','洛谷':'luogu.com.cn',QOJ:'qoj.ac'}[platform];
  const domain = cookie.domain?.replace(/^\./, '').toLowerCase();
  if (!root || !(domain === root || domain?.endsWith('.' + root))) return false;
  if (!cookie.partitionKey) return true;
  try {
    const site = new URL(cookie.partitionKey.topLevelSite);
    return site.protocol === 'https:' && !site.username && !site.password && !site.port
      && (site.hostname === root || site.hostname.endsWith('.' + root))
      && cookie.partitionKey.hasCrossSiteAncestor !== true;
  } catch { return false; }
}
function tbPageLoginState(platform, html) {
  if (/just a moment|checking your browser|cf-chl-|安全验证/i.test(html.slice(0, 10000))) return 'unknown';
  if (platform === 'QOJ') {
    const start=/<(nav|div|header)\b[^>]*\bclass\s*=\s*["'][^"']*\bnavbar\b[^"']*["'][^>]*>/i.exec(html);
    if (!start) return 'unknown';
    const tags=new RegExp('<\\/?'+start[1]+'\\b[^>]*>','gi');tags.lastIndex=start.index;
    let depth=0,end=html.length,tag;while((tag=tags.exec(html))){depth+=/^<\//.test(tag[0])?-1:1;if(!depth){end=tags.lastIndex;break;}}
    const nav=html.slice(start.index,end),paths=[...nav.matchAll(/<a\b[^>]*\bhref\s*=\s*["']([^"']*)["']/gi)].map(link=>{try{const u=new URL(link[1],'https://qoj.ac');return u.origin==='https://qoj.ac'&&!u.username&&!u.password?u.pathname:'';}catch{return '';}});
    if(paths.includes('/logout')&&paths.some(path=>/^\/user\/profile\/[A-Za-z0-9_-]{1,64}\/?$/.test(path)))return 'logged_in';
    return paths.includes('/login')?'logged_out':'unknown';
  }
  if (platform === 'Codeforces') {
    const start = /<(div|header)\b[^>]*\bid\s*=\s*["']header["'][^>]*>/i.exec(html);
    if (!start) return 'unknown';
    const tags = new RegExp('<\\/?' + start[1] + '\\b[^>]*>', 'gi');
    tags.lastIndex = start.index;
    let depth = 0, end = html.length, tag;
    while ((tag = tags.exec(html))) {
      depth += /^<\//.test(tag[0]) ? -1 : 1;
      if (!depth) { end = tags.lastIndex; break; }
    }
    const header = html.slice(start.index, end);
    // Ignore article/sidebar/login-dialog links outside the account header.
    if (/\bhref\s*=\s*["'](?:https:\/\/(?:www\.)?codeforces\.com)?\/(?:profile\/|logout(?:["'?/#]|$))/i.test(header)) return 'logged_in';
    if (/\bhref\s*=\s*["']\/(?:login|enter)(?:["'?/#]|$)/i.test(header)) return 'logged_out';
    return 'unknown';
  }
  if (platform === '洛谷') {
    const raw = html.match(/<script\b[^>]*\bid=["']lentille-context["'][^>]*>([\s\S]*?)<\/script>/i)?.[1];
    if (raw) {
      try { const data = JSON.parse(raw); if ('user' in data) return Number(data.user?.uid) > 0 ? 'logged_in' : 'logged_out'; } catch {}
    }
    if (/currentUser\s*:\s*null|"currentUser"\s*:\s*null/.test(html)) return 'logged_out';
  }
  if (platform === '牛客') {
    if (/(?:"ownerId"|ownerId)\s*:\s*["']?[1-9]\d*/.test(html)) return 'logged_in';
    return 'unknown';
  }
  if (/\bhref\s*=\s*["']\/(?:logout|signout)(?:["'?/#]|$)|\baction\s*=\s*["']\/logout/i.test(html)) return 'logged_in';
  if (platform === 'AtCoder') {
    const owner = html.match(/\buserScreenName\s*=\s*["']([^"']*)["']/);
    if (owner) return owner[1] ? 'logged_in' : 'logged_out';
  }
  if (/\bhref\s*=\s*["']\/(?:login|enter)(?:["'?/#]|$)/i.test(html)) return 'logged_out';
  return 'unknown';
}
