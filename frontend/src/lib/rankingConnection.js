// A failed refresh is not a new, verified empty leaderboard.
export function rankingResponse(cached,incoming,{owner,period,today}){
 const value={...incoming};
 if(value.configured&&value.status==='unconfigured'){
  value.status='offline';value.connectionPending=true;
  value.error=value.error||'正在恢复账号连接，后台会自动重试。';
 }
 const previous=cached?.owner===owner&&cached.date===today?cached.value:null;
 const verified=previous&&Array.isArray(previous.entries)&&previous.entries.length>0&&(previous.hasSnapshot===true||previous.hasSnapshot!==false&&previous.status==='ready');
 const sameScope=previous?.period===period&&value.period===period&&previous.date===value.date&&(!previous.endpoint||!value.endpoint||previous.endpoint===value.endpoint);
 if(value.configured&&!value.requiresAdminLogin&&value.hasSnapshot===false&&verified&&sameScope){
  return {...previous,...value,entries:previous.entries,self:previous.self,socialAvailable:previous.socialAvailable,
   isAdmin:value.isAdmin===true,hasSnapshot:true,stale:true};
 }
 return value;
}

export function rankingHasSnapshot(value){
 return Boolean(value&&(value.hasSnapshot===true||value.hasSnapshot!==false&&value.status==='ready'));
}
