const arrays=['folder','trail','sections'];
export function trainingListLocation(value) {
 const source=value?.state;if(!source||source.curriculumVersion!==1)return null;
 const state={curriculumVersion:1,mode:source.mode==='source'?'source':'algorithm',flat:source.flat===true,descending:source.descending===true,page:Math.max(1,Math.min(100000,Number.isSafeInteger(source.page)?source.page:1))};
 if([1,2].includes(source.nowcoderLearningVersion))state.nowcoderLearningVersion=source.nowcoderLearningVersion;
 for(const key of arrays)state[key]=Array.isArray(source[key])?source[key].filter(item=>typeof item==='string'&&item.length<=240).slice(0,24):[];
 for(const key of ['query','status','sort','knowledge','platform'])if(typeof source[key]==='string')state[key]=source[key].slice(0,120);
 for(const key of ['min','max'])if(Number.isFinite(source[key]))state[key]=Math.max(0,Math.min(10000,source[key]));
 return {state,scrollTop:Math.max(0,Math.min(1000000,Number(value.scrollTop)||0))};
}
