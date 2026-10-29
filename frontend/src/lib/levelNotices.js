export const LEVEL_NOTICE_VERSION=1;
const valid=value=>Number.isSafeInteger(value)&&value>=0&&value<=100;
export function mergeLevelNotices(...values){
 const current=values.filter(value=>value?.levelNoticeVersion===LEVEL_NOTICE_VERSION);
 const seen=Math.max(0,...current.map(value=>valid(value.levelNoticeSeen)?value.levelNoticeSeen:0));
 const pending=Math.max(0,...current.map(value=>valid(value.levelNoticePending)?value.levelNoticePending:0));
 return {levelNoticeVersion:current.length?LEVEL_NOTICE_VERSION:0,levelNoticeSeen:seen,levelNoticePending:pending>seen?pending:0};
}
export function confirmedGrowth(value,owner){const a=value?.authority;return value?.confirmed===true&&valid(value.level)&&value.level>=1&&a?.owner===owner&&typeof a.epoch==='string'&&a.epoch.length>0&&Number.isSafeInteger(a.revision)&&a.revision>=0;}
export function acceptGrowth(previous,value,owner){
 if(!confirmedGrowth(value,owner))return null;const a=value.authority;
 if(previous?.owner===owner){if(previous.retired?.includes(a.epoch))return null;if(previous.epoch===a.epoch&&a.revision<=previous.revision)return null;}
 return {owner,epoch:a.epoch,revision:a.revision,level:value.level,retired:previous?.owner===owner?[...new Set([...(previous.retired||[]),...(previous.epoch!==a.epoch?[previous.epoch]:[])])]:[]};
}
export function observeLevel(preferences,level){
 const previous=mergeLevelNotices(preferences);if(!valid(level)||level<1)return previous;
 if(previous.levelNoticeVersion!==LEVEL_NOTICE_VERSION)return {levelNoticeVersion:LEVEL_NOTICE_VERSION,levelNoticeSeen:level,levelNoticePending:0};
 const pending=Math.max(previous.levelNoticePending,level>previous.levelNoticeSeen?level:0);
 return {...previous,levelNoticePending:pending>previous.levelNoticeSeen?pending:0};
}
export function acknowledgeLevel(preferences,presented){const previous=mergeLevelNotices(preferences),seen=valid(presented)?Math.max(previous.levelNoticeSeen,presented):previous.levelNoticeSeen;return {...previous,levelNoticeSeen:seen,levelNoticePending:previous.levelNoticePending>seen?previous.levelNoticePending:0};}
export function protectGrowth(previous,value,owner,retired=new Set()){
 if(!owner)return value;
 if(!confirmedGrowth(value?.growth,owner))return {...value,growth:confirmedGrowth(previous?.growth,owner)?previous.growth:null};
 const current=previous?.growth,next=value.growth;
 if(retired.has(next.authority.epoch))return {...value,growth:current};
 if(confirmedGrowth(current,owner)){
  if(current.authority.epoch===next.authority.epoch&&current.authority.revision>next.authority.revision)return {...value,growth:current};
  if(current.authority.epoch!==next.authority.epoch)retired.add(current.authority.epoch);
 }
 return value;
}
