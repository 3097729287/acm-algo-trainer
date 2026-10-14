// Read only the signed-in user's official personal submission page. This runs
// without a TB job, so submissions made directly on the site are also imported.
(() => {
  if (window !== window.top) return;
  const platforms = {'codeforces.com':'Codeforces','www.codeforces.com':'Codeforces','atcoder.jp':'AtCoder','ac.nowcoder.com':'牛客','www.luogu.com.cn':'洛谷','luogu.com.cn':'洛谷'};
  const platform = platforms[location.hostname];
  if (!platform) return;
  window.addEventListener('message', event => {
    const value=event.data?.tbPublicReceipt;
    if (event.source === window && event.origin === location.origin && value?.platform === platform && ['牛客','洛谷'].includes(platform) && Array.isArray(value.records) && value.records.length <= 100) {
      chrome.runtime.sendMessage({type:'receipts',...value,owner:String(value.owner)}).catch(()=>{});
    }
  });
  async function codeforces() {
    const owner=[...document.querySelectorAll('.lang-chooser a[href],#header a[href]')].map(a=>a.getAttribute('href').match(/^\/profile\/([\w.-]+)$/)?.[1]).find(Boolean);
    if (!owner) return;
    const response=await fetch('/api/user.status?handle='+encodeURIComponent(owner)+'&from=1&count=100',{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(7000)});
    if(!response.ok) return;
    const value=await response.json(), verdicts={OK:'AC',WRONG_ANSWER:'WA',TIME_LIMIT_EXCEEDED:'TLE',MEMORY_LIMIT_EXCEEDED:'MLE',RUNTIME_ERROR:'RE',COMPILATION_ERROR:'CE',OUTPUT_LIMIT_EXCEEDED:'OLE'};
    if(value.status!=='OK'||!Array.isArray(value.result))return;
    const records=value.result.filter(r=>r.author?.members?.some(m=>m.handle?.toLowerCase()===owner.toLowerCase())&&verdicts[r.verdict]&&Number.isSafeInteger(r.id)&&Number.isSafeInteger(r.creationTimeSeconds)).map(r=>({submissionId:String(r.id),url:`https://codeforces.com/${r.problem.contestId>=100000?'gym':'contest'}/${r.problem.contestId}/problem/${r.problem.index}`,verdict:verdicts[r.verdict],acceptedAt:new Date(r.creationTimeSeconds*1000).toISOString()}));
    if(records.length)await chrome.runtime.sendMessage({type:'receipts',platform,owner,records});
  }
  let busy = false;
  async function scan() {
    if (busy) return;
    if (platform === 'Codeforces') {busy=true;try {await codeforces();} catch {} finally {busy=false;}return;}
    if (platform !== 'AtCoder') return;
    const contest = location.pathname.match(/^\/contests\/([\w-]+)(?:\/|$)/)?.[1];
    if (!contest) return;
    busy = true;
    try {
      const response = await fetch(`/contests/${contest}/submissions/me`, {credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(7000)});
      if (!response.ok || new URL(response.url).pathname !== `/contests/${contest}/submissions/me`) return;
      const doc = new DOMParser().parseFromString(await response.text(), 'text/html');
      const owner = [...doc.querySelectorAll('.navbar a[href],header a[href]')].map(a => a.getAttribute('href').match(/^\/users\/([\w-]+)\/?$/)?.[1]).find(Boolean);
      if (!owner) return;
      const records = [];
      for (const row of doc.querySelectorAll('tbody tr')) {
        const links = [...row.querySelectorAll('a[href]')].map(a => new URL(a.getAttribute('href'), location.origin));
        if (!links.some(a => a.origin === location.origin && a.pathname === '/users/' + owner)) continue;
        const submissionId = links.map(a => a.origin === location.origin && a.pathname.match(/^\/contests\/[\w-]+\/submissions\/(\d+)$/)?.[1]).find(Boolean);
        const task = links.find(a => a.origin === location.origin && /^\/contests\/[\w-]+\/tasks\/[\w-]+$/.test(a.pathname));
        const verdict = [...row.querySelectorAll('.label')].map(e => e.textContent.trim()).find(v => ['AC','WA','TLE','MLE','RE','CE','OLE'].includes(v));
        const dateText = row.querySelector('time')?.textContent.trim();
        const date = dateText && /[+-]\d{4}$/.test(dateText) ? new Date(dateText) : null;
        if (submissionId && task && verdict && date && Number.isFinite(date.getTime())) records.push({submissionId,url:task.href,verdict,acceptedAt:date.toISOString()});
      }
      if (records.length) await chrome.runtime.sendMessage({type:'receipts',platform:'AtCoder',owner,records:records.slice(0,100)});
    } catch {} finally { busy = false; }
  }
  setInterval(scan, 10000);
  window.addEventListener('pageshow', scan);
  scan();
})();
