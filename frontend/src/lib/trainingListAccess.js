import {CURRICULUM_STAGES} from './trainingCurriculum.js';
export const STAGE_LEVELS=[1,2,3,4,4,4,5,5,6];
export const curriculumLevel=stage=>STAGE_LEVELS[CURRICULUM_STAGES.indexOf(stage)]||6;
export function accessibleTrainingList(list,level=6){
 if(level>=6||list.custom||list.virtual)return true;
 const stage=list.topicPath?.find(part=>CURRICULUM_STAGES.includes(part));
 return stage?level>=curriculumLevel(stage):level>=3;
}
