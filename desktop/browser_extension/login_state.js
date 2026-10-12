// Preparation hints only. Original-site submission still verifies the account.
function tbCookieLoginState(platform, cookies) {
  const live = cookies.filter(cookie => cookie.value && (!cookie.expirationDate || cookie.expirationDate > Date.now() / 1000));
  if (!live.length) return 'logged_out';
  if (platform === '牛客' && live.some(cookie => cookie.name === 't')) return 'logged_in';
  if (platform === '洛谷') {
    const user = live.find(cookie => cookie.name === '_uid');
    if (user?.value === '0') return 'logged_out';
    if (/^[1-9]\d*$/.test(user?.value || '') && live.some(cookie => cookie.name === '__client_id')) return 'logged_in';
  }
  return 'unknown';
}
function tbPageLoginState(platform, html) {
  if (/just a moment|checking your browser|cf-chl-|安全验证/i.test(html.slice(0, 10000))) return 'unknown';
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
  if (platform === 'Codeforces' && /id=["']header["'][\s\S]{0,12000}?href=["']\/profile\//i.test(html)) return 'logged_in';
  return 'unknown';
}
