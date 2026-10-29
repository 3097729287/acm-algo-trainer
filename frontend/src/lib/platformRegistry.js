// Display/source identity is separate from the explicitly implemented adapters.
// A new row platform can be browsed without claiming support for its submit form.
export const PLATFORM_REGISTRY=Object.freeze([
 {id:'Codeforces',badge:'CF',aliases:['codeforces','cf'],hosts:['codeforces.com','www.codeforces.com'],publicAccount:'codeforces',nativeSubmit:true},
 {id:'AtCoder',badge:'At',aliases:['atcoder','ac'],hosts:['atcoder.jp'],publicAccount:'atcoder',nativeSubmit:true},
 {id:'牛客',badge:'牛',aliases:['nowcoder'],hosts:['nowcoder.com','www.nowcoder.com','ac.nowcoder.com'],publicAccount:'nowcoder',nativeSubmit:true},
 {id:'洛谷',badge:'洛',aliases:['luogu'],hosts:['luogu.com.cn','www.luogu.com.cn','luogu.org','www.luogu.org'],publicAccount:'luogu',nativeSubmit:true},
 {id:'QOJ',badge:'QJ',aliases:['qoj'],hosts:['qoj.ac'],nativeSubmit:true},
]);
const known=value=>PLATFORM_REGISTRY.find(platform=>[platform.id,...platform.aliases].some(alias=>alias.toLowerCase()===String(value||'').trim().toLowerCase()));
export function normalizePlatform(value){return known(value)?.id||String(value||'').trim();}
export function platformInfo(value){const id=normalizePlatform(value);return known(id)||{id,badge:Array.from(id||'·').slice(0,2).join(''),nativeSubmit:false};}
export function platformFromUrl(value){
 try{const url=new URL(value);if(!['https:','http:'].includes(url.protocol)||url.username||url.password)return '';return PLATFORM_REGISTRY.find(platform=>platform.hosts.includes(url.hostname.toLowerCase()))?.id||'';}catch{return '';}
}
export const rowPlatform=row=>normalizePlatform(row?.platform)||platformFromUrl(row?.url);
export function platformNames(rows=[],selected=''){
 const names=new Set(rows.map(row=>typeof row==='string'?normalizePlatform(row):rowPlatform(row)).filter(Boolean));
 if(selected)names.add(normalizePlatform(selected));
 const order=new Map(PLATFORM_REGISTRY.map((platform,index)=>[platform.id,index]));
 return [...names].sort((a,b)=>(order.get(a)??99)-(order.get(b)??99)||a.localeCompare(b,'zh-CN',{numeric:true}));
}
