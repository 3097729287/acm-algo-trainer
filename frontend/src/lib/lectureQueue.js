import {FOUNDATION_LESSONS,orderedLectures} from './learningCurriculum.js';
import {foundationLectures} from './algorithmLearning.js';

// Old servers safely expose the language route, while explicit/read lessons
// remain reachable. A current server adds only lessons of encountered problems.
export function readingQueue(snapshot,preferences={},selected,{includeAll=false}={}){
 const all=foundationLectures(Array.isArray(snapshot)?snapshot:snapshot?.lectures||[]);
 const foundation=new Set(snapshot?.learningQueue?.foundationIds||FOUNDATION_LESSONS.filter(item=>item.kind==='language').map(item=>item.id));
 const reached=new Set(snapshot?.learningQueue?.encounteredIds||[]);
 const learned=new Set(preferences.learnedLectures||[]);
 const ordered=orderedLectures(all),byId=new Map(ordered.map(item=>[item.id,item]));
 if(includeAll)return ordered;
 const mainline=ordered.filter(item=>foundation.has(item.id));
 const queued=[...reached,...ordered.filter(item=>learned.has(item.id)||item.id===selected).map(item=>item.id)];
 return [...mainline,...[...new Set(queued)].filter(id=>!foundation.has(id)&&byId.has(id)).map(id=>byId.get(id))];
}

export function nextReading(entries,id){
 const index=entries.findIndex(item=>item.id===id);
 return index<0?null:entries[index+1]||null;
}
