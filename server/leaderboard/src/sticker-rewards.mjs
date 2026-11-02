import {readFileSync} from 'node:fs';
import {randomInt,randomUUID} from 'node:crypto';
import {AccountError} from './accounts.mjs';

export const REWARDS=JSON.parse(readFileSync(new URL('./sticker-rewards.json',import.meta.url),'utf8'));
const fail=(code,message)=>{throw new AccountError(code,message);};
export function levelBox(level){
 if(!Number.isSafeInteger(level)||level<5||level>100)fail(400,'宝箱等级无效');
 const t=1-Math.exp(-(level-5)/REWARDS.levelBoxes.curveScale);
 const common=Math.round((58-38*t)*100),epic=Math.round((9+23*t)*100),legendary=Math.round((8+24*t)*100);
 const probabilities={common,rare:10000-common-epic-legendary,epic,legendary};
 const quantity=REWARDS.levelBoxes.quantitySteps.filter(([start])=>level>=start).at(-1)[1];
 return {id:'level:'+level,level,quantity,probabilities,policyVersion:REWARDS.version,openedAt:null};
}
export function rollRarity(probabilities,roll=randomInt(10000)){
 if(!Number.isSafeInteger(roll)||roll<0||roll>=10000)throw new Error('Invalid random sample');
 let cursor=roll;for(const kind of ['common','rare','epic','legendary']){cursor-=probabilities[kind];if(cursor<0)return kind;}
 throw new Error('Invalid rarity weights');
}

// These methods share Gameplay's transaction/session/operation ledger. Neither
// client retries nor an older learning snapshot can recreate a claimed box.
export class StickerRewards {
 async rewardWrite(owner,auth,kind,value,now){
  return this.db.transaction(async db=>{
   await this.session(db,owner,auth,now);const state=await this.account(db,owner);
   state.boxes??={};state.achievementGrants??={};
   return this.once(db,owner,'stickers/'+kind,value,async()=>{
    let opening=null;
    if(kind==='levels'){
     if(!Number.isSafeInteger(value.level)||value.level<1||value.level>100)fail(400,'等级无效');
     const [rows]=await db.execute('SELECT payload FROM account_public_progress WHERE user_id=?',[owner]);
     const confirmed=rows.length?JSON.parse(rows[0].payload).level:1;
     if(value.level>confirmed)fail(409,'等级正在同步，请稍后刷新宝箱');
     for(let level=5;level<=value.level;level++){const old=state.boxes['level:'+level];if(!old||!old.openedAt&&old.policyVersion!==REWARDS.version){const box=levelBox(level);box.grantedAt=old?.grantedAt??now;state.boxes[box.id]=box;state.revision++;}}
    }else if(kind==='achievement'){
     const stickerId=Object.hasOwn(REWARDS.achievements,value.achievementId)?REWARDS.achievements[value.achievementId]:null;if(!stickerId)fail(400,'没有对应的成就贴纸');
     if(!state.achievementGrants[value.achievementId]){
      if(state.units.length>=20000)fail(409,'贴纸库存已满');
      const unit={id:randomUUID(),stickerId,placement:null,revision:0,source:{kind:'achievement',id:value.achievementId}};
      state.units.push(unit);state.achievementGrants[value.achievementId]={unitId:unit.id,stickerId,grantedAt:now};state.revision++;
     }
    }else if(kind==='open-box'){
     const box=Object.hasOwn(state.boxes,value.boxId)?state.boxes[value.boxId]:null;if(!box)fail(404,'没有找到这个宝箱');
     if(box.openedAt){opening=box;}
     else{
      if(box.policyVersion!==REWARDS.version){const grantedAt=box.grantedAt;Object.assign(box,levelBox(box.level),{grantedAt});}
      if(state.units.length+box.quantity>20000)fail(409,'贴纸库存空间不足，宝箱已保留');
      const drops=[];
      for(let i=0;i<box.quantity;i++){
       const rarity=rollRarity(box.probabilities),pool=this.catalogue.filter(item=>item.rarity===rarity&&!item.id.startsWith('achievement-'));
       const sticker=pool[randomInt(pool.length)],unit={id:randomUUID(),stickerId:sticker.id,placement:null,revision:0,source:{kind:'level-box',id:box.id}};
       state.units.push(unit);drops.push({id:unit.id,stickerId:unit.stickerId,rarity});
      }
      box.openedAt=now;box.drops=drops;state.revision++;opening=box;
     }
    }else fail(404,'没有找到这项奖励');
    await this.saveAccount(db,owner,state);
    return {owner,revision:state.revision,requestId:value.requestId,...(opening?{opening}:{})};
   });
  });
 }
 async transferGift(db,actor,recipient,gift,now){
  if(!gift||Object.keys(gift).sort().join(',')!=='revision,unitId'||!Number.isSafeInteger(gift.revision)||gift.revision<0)fail(400,'赠送贴纸无效');
  const sender=await this.account(db,actor),receiver=await this.account(db,recipient);
  const at=sender.units.findIndex(unit=>unit.id===gift.unitId);if(at<0)fail(404,'这张贴纸已不在库存中');
  const unit=sender.units[at];if(unit.revision!==gift.revision)fail(409,'贴纸已更新，请重新选择');
  if(unit.placement)fail(409,'请先将已放置的贴纸回收到库存');
  if(receiver.units.length>=20000)fail(409,'对方贴纸库存已满，贴纸仍在你的库存中');
  const sticker=this.catalogue.find(item=>item.id===unit.stickerId);if(!sticker)fail(409,'贴纸资料暂不可用');
  sender.units.splice(at,1);receiver.units.push({...unit,revision:unit.revision+1,receivedFrom:actor,receivedAt:now});sender.revision++;receiver.revision++;
  await this.saveAccount(db,actor,sender);await this.saveAccount(db,recipient,receiver);
  return {unitId:unit.id,stickerId:unit.stickerId,title:sticker.title||sticker.shape,rarity:sticker.rarity,shape:sticker.shape};
 }
}
