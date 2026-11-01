function originalKey(value){
 try{
  const url=new URL(value),cf=url.pathname.match(/^\/(?:problemset\/problem|contest)\/(\d+)\/(?:problem\/)?([a-z]\d*)\/?$/i);
  if(/(^|\.)codeforces\.com$/i.test(url.hostname)&&cf)return 'cf:'+cf[1]+':'+cf[2].toUpperCase();
  const luogu=url.pathname.match(/^\/problem\/(CF\d+[a-z]\d*|[a-z]+\d+)\/?$/i);
  if(/(^|\.)luogu\.com\.cn$/i.test(url.hostname)&&luogu){
   const mirror=luogu[1].match(/^CF(\d+)([a-z]\d*)$/i);
   return mirror?'cf:'+mirror[1]+':'+mirror[2].toUpperCase():'luogu:'+luogu[1].toUpperCase();
  }
  return url.origin+url.pathname.replace(/\/$/,'');
 }catch{return null;}
}
export function matchesTemplateProblem(row,task){
 if(!row||!task)return false;
 if([row.id,...(row.aliasIds||[])].includes(task.problemId))return true;
 const key=originalKey(row.url);return !!key&&key===originalKey(task.url);
}
