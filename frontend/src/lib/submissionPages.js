// Private, in-memory metadata only; account and active-paper scope are explicit.
const sessions=new WeakMap();
export const submissionQuery=({offset=0,search='',result='',platform='',descending=true}={})=>new URLSearchParams({resultsOnly:'1',compact:'1',limit:'100',offset:String(offset),q:search,verdict:result,order:descending?'desc':'asc',...(platform?{platform}:{})}).toString();
function pages(api,scope){let session=sessions.get(api);if(!session||session.scope!==scope){session={scope,pages:new Map()};sessions.set(api,session);}return session.pages;}
export const submissionSnapshot=(api,scope,revision,key)=>pages(api,scope).get(`${revision}:${key}`)?.value;
export function loadSubmissionPage(api,scope,revision,key,{refresh=false}={}){
 const store=pages(api,scope),cacheKey=`${revision}:${key}`,old=store.get(cacheKey);
 if(old?.promise)return old.promise;
 if(old?.value&&!refresh)return Promise.resolve(old.value);
 const entry={value:old?.value};
 entry.promise=api('submissions?'+key).then(value=>{entry.value={...value,requestKey:key,scope,revision};return entry.value;}).finally(()=>{entry.promise=null;});
 store.set(cacheKey,entry);while(store.size>8)store.delete(store.keys().next().value);
 return entry.promise;
}
