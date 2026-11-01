import {contestYear} from './contestCatalog.js';
import {isXcpc} from './contestShelves.js';
import {compareContestNewest,contestTime} from './practiceMetadata.js';

const source=group=>group.rows?.[0]||group;
// A newly imported 2019 XCPC paper belongs with 2019, regardless of addedAt.
export function compareCompetitionNewest(a,b){
 const x=source(a),y=source(b),left=Number(contestYear(x)||0),right=Number(contestYear(y)||0);
 if(left!==right)return right-left;
 if(isXcpc(x)||isXcpc(y)){
  const time=value=>{const n=contestTime(value);return n!=null&&(!contestYear(value)||new Date(n).getUTCFullYear()===Number(contestYear(value)))?n:0;};
  return time(y)-time(x)||String(a.name||x.contest||'').localeCompare(String(b.name||y.contest||''),'zh-CN',{numeric:true});
 }
 return compareContestNewest(a,b);
}
