// Use stored contest provenance, or the contest identity in a problem URL.
// A problem number or a displayed contest title cannot identify its contest.
export function contestOriginalUrl(rows=[]){
 for(const row of rows){
  for(const source of [row.contestUrl,row.collectionSource,row.url]){
   try{
    const url=new URL(source);if(!['https:','http:'].includes(url.protocol)||url.username||url.password)continue;
    const host=url.hostname.toLowerCase().replace(/^www\./,''),path=url.pathname;
    let match;
    if(/^(?:m[12]\.)?codeforces\.com$/.test(host)){
     match=path.match(/^\/(contest|gym)\/(\d+)(?:\/|$)/);if(match)return `https://codeforces.com/${match[1]}/${match[2]}`;
     match=path.match(/^\/problemset\/problem\/(\d+)\//);if(match)return `https://codeforces.com/contest/${match[1]}`;
    }
    if(host==='atcoder.jp'&&(match=path.match(/^\/contests\/([a-z0-9_-]+)(?:\/|$)/i)))return `https://atcoder.jp/contests/${match[1]}`;
    if(host==='ac.nowcoder.com'&&(match=path.match(/^\/acm\/contest\/(\d+)(?:\/|$)/)))return `https://ac.nowcoder.com/acm/contest/${match[1]}`;
    if(host==='luogu.com.cn'){
     match=path.match(/^\/contest\/(\d+)(?:\/|$)/);if(match)return `https://www.luogu.com.cn/contest/${match[1]}`;
     if(/^\d+$/.test(String(row.contestId||'')))return `https://www.luogu.com.cn/contest/${row.contestId}`;
    }
    if(host==='qoj.ac'){
     match=path.match(/^\/contest\/(\d+)(?:\/|$)/);if(match)return `https://qoj.ac/contest/${match[1]}`;
     if(/^\d+$/.test(String(row.contestId||'')))return `https://qoj.ac/contest/${row.contestId}`;
    }
    if(source===row.contestUrl)return url.href;
   }catch{/* Missing provenance leaves the shortcut unavailable. */}
  }
 }
 return null;
}
