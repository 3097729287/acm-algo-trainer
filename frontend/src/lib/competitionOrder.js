import {contestYear} from './contestCatalog.js';
import {isXcpc} from './contestShelves.js';
import {compareContestNewest,contestTime,contestAddedTime} from './practiceMetadata.js';

const source=group=>group.rows?.[0]||group;
function position(group){
 const row=source(group),added=!isXcpc(row)?contestAddedTime(group):null;
 if(added!=null)return [new Date(added).getUTCFullYear(),added];
 const time=contestTime(row),year=Number(contestYear(row)||(time!=null?new Date(time).getUTCFullYear():0));
 return [year,time!=null&&new Date(time).getUTCFullYear()===year?time:0];
}
// Keep verified addition chronology for normal contests; an old XCPC paper
// belongs to its actual event year. One key also keeps mixed lists transitive.
export function compareCompetitionNewest(a,b){
 const left=position(a),right=position(b);
 return right[0]-left[0]||right[1]-left[1]||compareContestNewest(a,b);
}
