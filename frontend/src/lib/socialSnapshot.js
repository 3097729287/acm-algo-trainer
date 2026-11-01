import {trainingDay} from './trainingDate.js';

const count=value=>Number.isSafeInteger(value)&&value>=0&&value<=1e9;
const key=owner=>typeof owner==='string'&&owner.length>0&&owner.length<=160?'tb.social-counts.v1:'+encodeURIComponent(owner):null;
export function readSocialCounts(owner,storage=globalThis.localStorage,now=new Date().toISOString()){
 try{
  const name=key(owner);if(!name||!storage)return null;
  const value=JSON.parse(storage.getItem(name)||'null');
  if(value?.owner!==owner||!count(value.totalLikes)||!count(value.todayLikes)||value.todayLikes>value.totalLikes||!/^\d{4}-\d{2}-\d{2}$/.test(value.day))return null;
  return {available:false,totalLikes:value.totalLikes,todayLikes:value.day===trainingDay(now)?value.todayLikes:0,notifications:[],unreadCount:0,countsCached:true};
 }catch{return null;}
}
export function saveSocialCounts(owner,snapshot,storage=globalThis.localStorage,now=new Date().toISOString()){
 try{
  const name=key(owner);if(!name||!storage||snapshot?.available!==true||!count(snapshot.totalLikes)||!count(snapshot.todayLikes)||snapshot.todayLikes>snapshot.totalLikes)return;
  storage.setItem(name,JSON.stringify({owner,totalLikes:snapshot.totalLikes,todayLikes:snapshot.todayLikes,day:trainingDay(now)}));
 }catch{}
}
export function retainSocialCounts(previous,value){
 if(value?.available===true)return {...value,countsCached:false};
 return {...value,...(previous&&count(previous.totalLikes)?{totalLikes:previous.totalLikes,todayLikes:previous.todayLikes,countsCached:true}:{}),available:false,notifications:[],unreadCount:0};
}
