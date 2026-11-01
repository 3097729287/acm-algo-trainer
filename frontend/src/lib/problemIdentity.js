export function original(row){
 try{
  const url=new URL(row.url),host=url.hostname.toLowerCase().replace(/^www\./,''),path=url.pathname.replace(/\/+$/,'');
  if(!['http:','https:'].includes(url.protocol))return row.id;
  if(/^(?:m[12]\.)?codeforces\.com$/.test(host)){
   const found=path.match(/^\/(?:contest\/(\d+)\/problem|problemset\/problem\/(\d+))\/([A-Za-z0-9]+)$/);
   if(found)return `codeforces.com/contest/${found[1]||found[2]}/problem/${found[3].toUpperCase()}`;
  }
  if(host==='qoj.ac'){
   const found=path.match(/^\/(?:contest\/\d+\/)?problem\/(\d+)(?:\/statement\/(?:default|zh_cn))?$/);
   if(found)return 'qoj.ac/problem/'+found[1];
  }
  return host+(host==='atcoder.jp'?path.toLowerCase():path);
 }catch{return row.id;}
}
