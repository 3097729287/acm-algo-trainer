export function original(row){
 try{
  const url=new URL(row.url),host=url.hostname.toLowerCase().replace(/^www\./,''),path=url.pathname.replace(/\/+$/,'');
  if(!['http:','https:'].includes(url.protocol))return row.id;
  if(/^(?:m[12]\.)?codeforces\.com$/.test(host)){
   const found=path.match(/^\/(?:contest\/(\d+)\/problem|problemset\/problem\/(\d+))\/([A-Za-z0-9]+)$/);
   if(found)return `codeforces.com/contest/${found[1]||found[2]}/problem/${found[3].toUpperCase()}`;
   const gym=path.match(/^\/gym\/(\d+)\/problem\/([A-Za-z0-9]+)$/);if(gym)return `codeforces.com/gym/${gym[1]}/problem/${gym[2].toUpperCase()}`;
  }
  if(host==='qoj.ac'){
   const found=path.match(/^\/(?:contest\/\d+\/)?problem\/(\d+)(?:\/statement\/(?:default|zh_cn))?$/);
   if(found)return 'qoj.ac/problem/'+found[1];
  }
  const query=url.searchParams;
  if(['onlinejudge.org','uva.onlinejudge.org'].includes(host)&&path==='/index.php'&&/^\d+$/.test(query.get('problem')||''))return 'onlinejudge.org/problem/'+query.get('problem');
  if(host==='acm.hdu.edu.cn'&&path==='/showproblem.php'&&/^\d+$/.test(query.get('pid')||''))return host+'/problem/'+query.get('pid');
  if(host==='poj.org'&&path==='/problem'&&/^\d+$/.test(query.get('id')||''))return host+'/problem/'+query.get('id');
  if(host==='spoj.com'&&/^\/problems\/[A-Za-z0-9_]+$/.test(path))return host+'/problems/'+path.split('/').at(-1).toUpperCase();
  return host+(host==='atcoder.jp'?path.toLowerCase():path);
 }catch{return row.id;}
}
