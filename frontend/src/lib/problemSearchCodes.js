// Search recorded numbers and official URL identifiers without changing the
// stable problem ID used by drafts, submissions and learning records.
export const normalizeProblemCode=value=>String(value||'').normalize('NFKC').toLocaleLowerCase().replace(/[\s_:/-]+/g,'');

export function problemSearchCodes(item){
 const codes=new Set([item.problem,item.code,item.id].filter(value=>typeof value==='string'&&value.trim()).map(value=>value.trim()));
 const add=value=>{if(value){codes.add(value);codes.add(normalizeProblemCode(value));}};
 for(const address of [item.url,...(Array.isArray(item.verifiedSourceAliases)?item.verifiedSourceAliases.map(alias=>typeof alias==='string'?alias:alias?.url):[])]){
  if(typeof address!=='string')continue;
  try{
   const {hostname,pathname}=new URL(address),path=decodeURIComponent(pathname);let match;
   if(/(^|\.)luogu\.com\.cn$/.test(hostname)&&(match=path.match(/^\/problem\/([^/]+)\/?$/))){add(match[1]);if(match[1].startsWith('AT_'))add(match[1].slice(3));}
   else if(/(^|\.)codeforces\.com$/.test(hostname)&&(match=path.match(/^\/(contest|gym|problemset\/problem)\/(\d+)\/(?:problem\/)?([a-z]\d*)\/?$/i))){add(match[2]+match[3]);add((match[1]==='gym'?'GYM':'CF')+match[2]+match[3]);}
   else if(hostname==='atcoder.jp'&&(match=path.match(/^\/contests\/[^/]+\/tasks\/([^/]+)\/?$/))){add(match[1]);}
   else if(hostname==='ac.nowcoder.com'&&(match=path.match(/^\/acm\/contest\/(\d+)\/([a-z]\d*)\/?$/i))){add(match[1]+'/'+match[2]);}
  }catch{/* Invalid or non-URL sources retain their recorded number and ID. */}
 }
 for(const code of [...codes])add(code);
 return [...codes];
}
