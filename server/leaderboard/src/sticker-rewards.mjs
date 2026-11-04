import {readFileSync} from 'node:fs';
import {createHash,randomInt,randomUUID} from 'node:crypto';
import {AccountError} from './accounts.mjs';

export const REWARDS=JSON.parse(readFileSync(new URL('./sticker-rewards.json',import.meta.url),'utf8'));
const fail=(code,message)=>{throw new AccountError(code,message);};
export function levelBox(level){
 if(!Number.isSafeInteger(level)||level<1||level>100)fail(400,'宝箱等级无效');
 const rarity=level<=20?REWARDS.levelBoxes.raritiesThrough20[level-1]:REWARDS.levelBoxes.after20[(level-21)%2];
 return {...packBox('level:'+level,rarity,{kind:'level',level}),level};
}
export function packBox(id,rarity,source){
 if(!Object.hasOwn(REWARDS.cardPacks,rarity))fail(400,'卡包品质无效');
 return {id,rarity,...structuredClone(REWARDS.cardPacks[rarity]),source,policyVersion:REWARDS.version,openedAt:null};
}
export function normalizeBox(box){
 if(box.openedAt||box.policyVersion===REWARDS.version)return box;
 const policy=Number.isSafeInteger(box.level)?levelBox(box.level):packBox(box.id,box.rarity,box.source);
 return {...policy,grantedAt:box.grantedAt};
}
export function dailyPackRarity(owner,day,taskId){
 const roll=createHash('sha256').update(owner+'\0'+day+'\0'+taskId+'\0pack-v1').digest().readUInt32BE(0)%10000;
 return rollRarity(REWARDS.dailyPacks.probabilities,roll);
}
export function rollRarity(probabilities,roll=randomInt(Object.values(probabilities).reduce((a,b)=>a+b,0))){
 const total=Object.values(probabilities).reduce((a,b)=>a+b,0);
 if(!Number.isSafeInteger(roll)||roll<0||roll>=total)throw new Error('Invalid random sample');
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
     for(let level=1;level<=value.level;level++){const old=state.boxes['level:'+level];if(!old||!old.openedAt&&old.policyVersion!==REWARDS.version){const box=levelBox(level);box.grantedAt=old?.grantedAt??now;state.boxes[box.id]=box;state.revision++;}}
    }else if(kind==='achievement'){
     const stickerId=Object.hasOwn(REWARDS.achievements,value.achievementId)?REWARDS.achievements[value.achievementId]:null;if(!stickerId)fail(400,'没有对应的成就贴纸');
     if(!state.achievementGrants[value.achievementId]){
      if(state.units.length>=20000)fail(409,'贴纸库存已满');
      const unit={id:randomUUID(),stickerId,placement:null,revision:0,source:{kind:'achievement',id:value.achievementId}};
      state.units.push(unit);state.achievementGrants[value.achievementId]={unitId:unit.id,stickerId,grantedAt:now};state.revision++;
     }
    }else if(kind==='open-box'||kind==='open-packs'){
     let boxes;
     if(kind==='open-box'){
      const box=Object.hasOwn(state.boxes,value.boxId)?state.boxes[value.boxId]:null;
      if(!box)fail(404,'没有找到这个卡包');
      if(box.openedAt)opening=box;else boxes=[normalizeBox(box)];
     }else{
      if(!Object.hasOwn(REWARDS.cardPacks,value.rarity)||![1,5].includes(value.count))fail(400,'抽卡数量或品质无效');
      boxes=Object.values(state.boxes).filter(box=>!box.openedAt).map(normalizeBox)
       .filter(box=>box.rarity===value.rarity).sort((a,b)=>(a.grantedAt||0)-(b.grantedAt||0)||a.id.localeCompare(b.id)).slice(0,value.count);
      if(boxes.length!==value.count)fail(409,'该品质的卡包数量不足');
     }
     if(boxes){
      if(state.units.length+boxes.reduce((sum,box)=>sum+box.quantity,0)>20000)fail(409,'贴纸库存空间不足，卡包已保留');
      for(const box of boxes){
       const drops=[];
       for(let i=0;i<box.quantity;i++){
        let weights=box.probabilities;
        if(i===0&&box.guarantee){
         const tiers=['common','rare','epic','legendary'],floor=tiers.indexOf(box.guarantee);
         weights=Object.fromEntries(tiers.map((tier,index)=>[tier,index<floor?0:box.probabilities[tier]]));
        }
        const rarity=rollRarity(weights),pool=this.catalogue.filter(item=>item.rarity===rarity&&!item.id.startsWith('achievement-'));
        const sticker=pool[randomInt(pool.length)],unit={id:randomUUID(),stickerId:sticker.id,placement:null,revision:0,source:{kind:box.source?.kind==='daily'?'daily-pack':'level-box',id:box.id}};
        state.units.push(unit);drops.push({id:unit.id,stickerId:unit.stickerId,rarity,packId:box.id});
       }
       box.openedAt=now;box.drops=drops;state.boxes[box.id]=box;state.revision++;
      }
      opening=kind==='open-box'?boxes[0]:{rarity:value.rarity,packs:boxes,drops:boxes.flatMap(box=>box.drops)};
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
