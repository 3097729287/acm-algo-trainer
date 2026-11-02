// A short original two-note cue. No external sound asset or network request.
// Audio is unlocked by the user's join gesture, and never blocks a match.
export function createDuelSound(){
 let context=null,closed=false;
 const unlock=async()=>{
  try{
   if(closed)return false;
   const Audio=window.AudioContext||window.webkitAudioContext;
   if(!Audio)return false;
   context??=new Audio();
   if(context.state==='suspended')await context.resume();
   return !closed&&context.state==='running';
  }catch{return false;}
 };
 return {
  unlock,
  async play(isCurrent=()=>true){
   if(!await unlock()||!isCurrent())return false;
   const now=context.currentTime;
   for(const [offset,frequency] of [[0,587.33],[.18,880]]){
    const oscillator=context.createOscillator(),volume=context.createGain(),at=now+offset;
    oscillator.type='sine';oscillator.frequency.value=frequency;
    volume.gain.setValueAtTime(0,at);volume.gain.linearRampToValueAtTime(.12,at+.012);volume.gain.exponentialRampToValueAtTime(.001,at+.32);
    oscillator.connect(volume);volume.connect(context.destination);oscillator.start(at);oscillator.stop(at+.34);
    oscillator.onended=()=>{oscillator.disconnect();volume.disconnect();};
   }
   return true;
  },
  close(){closed=true;if(context&&context.state!=='closed')void context.close().catch(()=>{});},
 };
}
