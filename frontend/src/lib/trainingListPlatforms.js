import {buildTrainingCurriculum,CURRICULUM_STAGES} from './trainingCurriculum.js';
import {normalizePlatform,platformFromUrl} from './platformRegistry.js';
import {organizeNowcoderTrainingLists} from './nowcoderTrainingLists.js';
import {buildNowcoderCurriculum,nowcoderUnitId} from './nowcoderCurriculum.js';

// A collection's source is its own provenance, not its title or its problems'
// platforms. Luogu collections legitimately contain mirrored contest tasks.
export function trainingListPlatform(list) {
 if(!list||list.custom||list.virtual)return null;
 for(const raw of [list.url,list.sourceUrl,list.source?.url]){
  if(typeof raw!=='string'||!raw)continue;
  try{
   const url=new URL(raw);if(!['https:','http:'].includes(url.protocol))continue;
   const platform=platformFromUrl(url.href);if(platform)return platform;
  }catch{/* Unknown provenance stays separate. */}
 }
 const explicit=list.sourcePlatform||list.platform||list.source?.platform;
 return normalizePlatform(explicit)||null;
}

export function platformTrainingLists(lists,rows,mode='algorithm') {
 if(mode==='source')return organizeNowcoderTrainingLists(lists);
 const luogu=lists.filter(list=>trainingListPlatform(list)==='洛谷');
 const other=organizeNowcoderTrainingLists(lists.filter(list=>trainingListPlatform(list)!=='洛谷'));
 const nowcoder=buildNowcoderCurriculum(other.filter(list=>trainingListPlatform(list)==='牛客'),rows);
 const curriculum=buildTrainingCurriculum(luogu,rows).map(list=>({...list,topicPath:['洛谷',...list.topicPath]}));
 return [...curriculum,...other.filter(list=>trainingListPlatform(list)!=='牛客').map(list=>{
  const platform=trainingListPlatform(list);
  return {...list,topicPath:platform==='牛客'?['牛客']:platform?[platform,...(list.topicPath||[]).filter(part=>part!==platform)]:['其他来源',...(list.topicPath||[])],
   sourceLabel:platform?(list.sourceLabel||platform):String(list.sourceLabel||'').replace(/^洛谷\s+.*$/,'')};
 }),...nowcoder];
}

// Existing new-user and remembered stage paths predate the platform root.
// Their original curriculum IDs and the user's personal folders stay intact.
export function platformListState(state) {
 if(state?.nowcoderLearningVersion!==2){
  const previous=state?.nowcoderLearningVersion;state={...state,nowcoderLearningVersion:2};
  if(state.mode==='algorithm'&&state.folder?.[0]==='牛客'){
   const old=state.trail?.find(id=>id.startsWith('nowcoder-curriculum:')&&!id.startsWith('nowcoder-curriculum:unit:'));
   let path=state.folder.slice(1);
   if(old)try{path=decodeURIComponent(old.slice(old.lastIndexOf(':')+1)).split('/');}catch{/* Fall back to the saved folder. */}
   if(path.length>=2)state={...state,folder:['牛客',path[0]],trail:[nowcoderUnitId(path.slice(0,2))],sections:[],flat:false,page:1};
   else if(previous!==1)state={...state,folder:['牛客'],trail:[],sections:[],flat:false,page:1};
  }
 }
 if(state?.mode==='algorithm'&&CURRICULUM_STAGES.includes(state.folder?.[0]))return {...state,folder:['洛谷',...state.folder]};
 return state;
}
