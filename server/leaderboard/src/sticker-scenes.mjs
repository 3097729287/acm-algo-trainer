import {randomInt,randomUUID} from 'node:crypto';
import {AccountError} from './accounts.mjs';
import {REWARDS} from './sticker-rewards.mjs';
import {resolveScene} from './scene-presets.mjs';
export {resolveScene,giftSceneWarnings} from './scene-presets.mjs';

const fail=(status,message)=>{throw new AccountError(status,message);};
const scalar=(v,lo,hi)=>typeof v==='number'&&Number.isFinite(v)&&v>=lo&&v<=hi;
const own=(object,key)=>Object.hasOwn(object,key);
export const backgroundCards=()=>REWARDS.backgroundThemes.map(theme=>({id:`background-${theme.id}`,shape:`background-${theme.id}`,theme:theme.id,kind:'background',title:theme.title}));
export const shapePolicy=item=>item?.kind==='background'?{baseScale:1,minScale:1,maxScale:1}:REWARDS.shapePolicy[item?.shape]||{baseScale:1,minScale:.5,maxScale:2};
export function outfit(value={}){
 if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(key=>!own(REWARDS.wardrobe,key)))fail(400,'服装选项无效');
 const result={};for(const [key,choices] of Object.entries(REWARDS.wardrobe)){const selected=value[key]??choices[0];if(!choices.includes(selected))fail(400,'服装选项无效');result[key]=selected;}return result;
}
export function placement(value,item){
 if(item.kind==='background')return {x:.5,y:.5,angle:0,scale:1};
 const policy=shapePolicy(item);
 if(!scalar(value.x,0,1)||!scalar(value.y,0,1)||!scalar(value.angle,-180,180)||value.scale!==undefined&&!scalar(value.scale,policy.minScale,policy.maxScale))fail(400,'贴纸位置或大小无效');
 return {x:value.x,y:value.y,angle:value.angle,scale:value.scale??1};
}
export function replayEvidence(value,now){
 const e=value.evidence;
 if(!e||Object.keys(e).some(key=>!['version','contestKey','replayId','duration','originalDuration','startedAt','finishedAt','difficulty','total','accepted'].includes(key))||e.version!==1||!/^replay:[a-f0-9]{64}$/.test(e.contestKey||'')||!/^contest-[a-f0-9]{32}$/.test(e.replayId||''))fail(400,'重现赛奖励凭据无效');
 if(!Number.isSafeInteger(e.duration)||e.duration<1||e.duration>1440||e.duration!==e.originalDuration||!Number.isSafeInteger(e.total)||e.total<2||e.total>100||!scalar(e.difficulty,0,10000))fail(400,'重现赛条件无效');
 if(!Number.isSafeInteger(e.startedAt)||!Number.isSafeInteger(e.finishedAt)||e.finishedAt>now+30000||e.startedAt>e.finishedAt||e.finishedAt-e.startedAt<e.duration*30000||e.finishedAt-e.startedAt>e.duration*60000+2000)fail(400,'重现赛用时不符合奖励条件');
 if(!Array.isArray(e.accepted)||e.accepted.length<2||e.accepted.length>e.total||new Set(e.accepted.map(a=>a.problemKey)).size!==e.accepted.length||e.accepted.some(a=>!a||!/^p:[a-f0-9]{64}$/.test(a.problemKey||'')||typeof a.submissionId!=='string'||a.submissionId.length>160||!Number.isSafeInteger(a.submittedAt)||a.submittedAt<e.startedAt||a.submittedAt>e.finishedAt||a.scope!=='official'||a.verdict!=='AC'))fail(400,'需要至少两道不同赛题的原站 AC');
 return e;
}

export async function sceneWrite(game,owner,auth,kind,value,now){
 return game.db.transaction(async db=>{
  await game.session(db,owner,auth,now);const state=await game.account(db,owner);
  return game.once(db,owner,'stickers/'+kind,value,async()=>{
   let result={};
   if(kind==='replay-background'){
    const evidence=replayEvidence(value,now);state.replayBackgroundGrants??={};state.backgroundRewards??={};
    let receipt=state.replayBackgroundGrants[evidence.contestKey];
    if(receipt?.rewardId)receipt=state.backgroundRewards[receipt.rewardId];
    if(!receipt){
     receipt={id:randomUUID(),contestKey:evidence.contestKey,grantedAt:now,accepted:evidence.accepted.length,difficulty:evidence.difficulty,openedAt:null};
     state.backgroundRewards[receipt.id]=receipt;state.replayBackgroundGrants[evidence.contestKey]={rewardId:receipt.id};state.revision++;
    }result.backgroundReward=receipt;
   }else if(kind==='open-background'){
    const reward=state.backgroundRewards?.[value.rewardId];if(!reward)fail(404,'没有找到这份背景奖励');
    if(!reward.openedAt){
     if(state.units.length>=20000)fail(409,'贴纸库存已满，背景奖励仍保持未拆');
     const owned=new Set([...(state.discoveredStickers||[]),...state.units.map(unit=>unit.stickerId)]),pool=game.catalogue.filter(item=>item.kind==='background'),novel=pool.filter(item=>!owned.has(item.id)),choices=novel.length?novel:pool;
     const card=choices[randomInt(choices.length)],unit={id:randomUUID(),stickerId:card.id,revision:0,placement:null,source:{kind:'replay-background',id:reward.contestKey}};
     state.units.push(unit);state.discoveredStickers=[...new Set([...owned,card.id])];state.revision++;
     reward.openedAt=now;reward.opening={id:reward.id,kind:'background',drops:[{id:unit.id,stickerId:card.id}]};
    }result.opening=reward.opening;
   }else{
    if(value.inventoryRevision!==state.revision)fail(409,'场景已在其他窗口更新，请刷新后重试');
    state.scenePresets??=[];
    if(kind==='scene-save'){
     if(typeof value.name!=='string'||!value.name.trim()||value.name.trim().length>32)fail(400,'预设名称须为 1–32 个字');
     const old=state.scenePresets.find(p=>p.id===value.presetId);
     if(value.presetId&&!old)fail(404,'没有找到这个预设');
     if(!old&&state.scenePresets.length>=20)fail(409,'最多保存 20 个场景预设');
     const preset={id:old?.id||randomUUID(),name:value.name.trim(),updatedAt:now,items:state.units.filter(u=>u.placement).map(u=>({unitId:u.id,stickerId:u.stickerId,placement:{...u.placement},...(u.appearance?{appearance:{...u.appearance}}:{})}))};
     if(preset.items.length>200)fail(409,'一个预设最多放置 200 张贴纸');
     if(old)state.scenePresets[state.scenePresets.indexOf(old)]=preset;else state.scenePresets.push(preset);
     state.activePresetId=preset.id;
     result.presetId=preset.id;
    }else if(kind==='scene-delete'){
     if(!state.scenePresets.some(p=>p.id===value.presetId))fail(404,'没有找到这个预设');
     state.scenePresets=state.scenePresets.filter(p=>p.id!==value.presetId);if(state.activePresetId===value.presetId)state.activePresetId=null;
    }else if(kind==='scene-apply'){
     const preset=state.scenePresets.find(p=>p.id===value.presetId);if(!preset)fail(404,'没有找到这个预设');
     const {matched,missing}=resolveScene(preset,state.units),points=new Map(matched.map(({unit,entry})=>[unit.id,entry]));
     let background=false;
     for(const unit of state.units){
      const entry=points.get(unit.id),item=game.catalogue.find(item=>item.id===unit.stickerId);let point=null;
      if(entry&&item){point=placement(entry.placement,item);if(item.kind==='background'){if(background)point=null;else background=true;}}
      const appearance=entry&&item?.shape.startsWith('person')?outfit(entry.appearance):unit.appearance;
      if(JSON.stringify(point)!==JSON.stringify(unit.placement)||JSON.stringify(appearance)!==JSON.stringify(unit.appearance)){unit.placement=point;if(appearance)unit.appearance=appearance;unit.revision++;}
     }
     state.activePresetId=preset.id;result.scene={presetId:preset.id,missing};
    }else fail(404,'没有找到这个场景操作');
    state.revision++;
   }
   await game.saveAccount(db,owner,state);return {owner,revision:state.revision,requestId:value.requestId,...result};
  });
 });
}
