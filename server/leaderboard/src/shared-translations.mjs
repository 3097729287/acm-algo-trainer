import {createHash} from 'node:crypto';
import {AccountError} from './accounts.mjs';
const hash=value=>createHash('sha256').update(value).digest('hex');
const fail=()=>{throw new AccountError(400,'共享译文字段无效');};

export function translationIdentity(value){
 if(!value||typeof value.url!=='string'||value.url.length>2048||!/^https:\/\//.test(value.url)||!/^[a-f0-9]{64}$/.test(value.sourceHash||'')||value.format!=='complete-prose-v4'||value.language!=='zh-CN')fail();
 let url;try{url=new URL(value.url);}catch{fail();}
 if(url.username||url.password||url.port||url.hash)fail();
 const rules={'codeforces.com':/^\/(?:contest|gym)\/\d+\/problem\/[A-Za-z]\d?\/?$/,'atcoder.jp':/^\/contests\/[A-Za-z0-9_-]+\/tasks\/[A-Za-z0-9_-]+\/?$/,'www.luogu.com.cn':/^\/problem\/[A-Za-z0-9_]+\/?$/,'ac.nowcoder.com':/^\/acm\/(?:contest\/\d+\/[A-Za-z0-9_]+|problem\/\d+)\/?$/};
 if(url.hostname==='www.codeforces.com')url.hostname='codeforces.com';
 url.pathname=url.pathname.replace(/^\/problemset\/problem\/(\d+)\/([A-Za-z]\d?)$/,'/contest/$1/problem/$2');
 if(!rules[url.hostname]?.test(url.pathname))fail();url.search='';
 const result={url:url.href,sourceHash:value.sourceHash,format:value.format,language:value.language};
 return {...result,key:hash(JSON.stringify(result))};
}

export function translationSubmission(value){
 const identity=translationIdentity(value);
 if(typeof value.original!=='string'||!value.original.trim()||value.original.length>24000||typeof value.markdown!=='string'||!value.markdown.trim()||value.markdown.length>48000||!/[\u3400-\u9fff]/u.test(value.markdown)||/<(?:script|iframe|object)\b|javascript\s*:/i.test(value.markdown))fail();
 if(hash(value.format+'\n'+value.original)!==identity.sourceHash)fail();
 const protectedSpans=value.original.match(/```[\s\S]*?```|`[^`\n]+`|\$\$[\s\S]*?\$\$|(?<![\\$])\$(?!\$)[^\n]*?(?<!\\)\$|https?:\/\/[^\s<>\)]+/g)||[];
 for(const span of new Set(protectedSpans))if(!value.markdown.includes(span))fail();
 return {...identity,markdown:value.markdown};
}

export class SharedTranslations {
 constructor(database,dialect='mysql'){this.database=database;this.dialect=dialect;this.checkedAt=0;this.enabled=false;}
 async available(){
  if(Date.now()-this.checkedAt<10000)return this.enabled;
  try{await this.database.execute('SELECT translation_key FROM shared_statement_translations LIMIT 0');this.enabled=true;}
  catch(error){if(!['ER_NO_SUCH_TABLE','ER_BAD_FIELD_ERROR'].includes(error.code)&&!/no such (?:table|column)/i.test(error.message||''))throw error;this.enabled=false;}
  this.checkedAt=Date.now();return this.enabled;
 }
 async get(value){
  const identity=translationIdentity(value);if(!await this.available())throw new AccountError(503,'共享译文正在准备');
  const [rows]=await this.database.execute('SELECT source_url,source_hash,source_format,target_language,markdown,created_at FROM shared_statement_translations WHERE translation_key=?',[identity.key]);
  const row=rows[0];
  return row?{available:true,translation:{url:row.source_url,sourceHash:row.source_hash,format:row.source_format,language:row.target_language,markdown:row.markdown,createdAt:row.created_at}}:{available:true,translation:null};
 }
 async publish(value,owner,timestamp){
  const item=translationSubmission(value);if(!await this.available())throw new AccountError(503,'共享译文正在准备');
  const insert=this.dialect==='mysql'?'INSERT IGNORE':'INSERT OR IGNORE';
  await this.database.execute(`${insert} INTO shared_statement_translations VALUES(?,?,?,?,?,?,?,?)`,[item.key,item.url,item.sourceHash,item.format,item.language,item.markdown,owner,timestamp]);
  return {saved:true,sourceHash:item.sourceHash};
 }
}
