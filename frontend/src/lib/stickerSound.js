import DUCK_CALLS from './stickerDuckCalls.js';
import {STICKER_FEEDBACK} from './stickerFeedbackCatalog.js';
let context,duckBuffers=[],decoding;
const playing=[];

export const STICKER_ANIMATIONS=Object.freeze(Object.fromEntries(Object.entries(STICKER_FEEDBACK).filter(([,value])=>value.motion).map(([shape,value])=>[shape,value.motion])));
export const LEGENDARY_FEEDBACK=STICKER_ANIMATIONS;
export function stopStickerSounds(){for(const source of [...playing])try{source.stop();}catch{}playing.length=0;}
function audio(){try{const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio)return null;if(!context||context.state==='closed')context=new Audio({latencyHint:'interactive'});return context;}catch{return null;}}
export function prepareStickerAudio(){
 const ctx=audio();if(!ctx||duckBuffers.length===DUCK_CALLS.length)return Promise.resolve();
 if(!decoding){decoding=Promise.all(DUCK_CALLS.map(call=>{const raw=atob(call),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));return ctx.decodeAudioData(bytes.buffer);})).then(values=>{duckBuffers=values;}).catch(()=>{}).finally(()=>{decoding=null;});}
 return decoding;
}
function keep(source,nodes){
 playing.push(source);while(playing.length>20){try{playing.shift().stop();}catch{}}
 source.onended=()=>{const at=playing.indexOf(source);if(at>=0)playing.splice(at,1);for(const node of nodes)try{node.disconnect();}catch{}};
}
function tone(ctx,frequency,at,duration=.3,volume=.035,type='sine',end=frequency){
 const source=ctx.createOscillator(),gain=ctx.createGain();source.type=type;source.frequency.setValueAtTime(frequency,at);source.frequency.exponentialRampToValueAtTime(Math.max(30,end),at+duration);
 gain.gain.setValueAtTime(.0001,at);gain.gain.exponentialRampToValueAtTime(volume,at+.014);gain.gain.exponentialRampToValueAtTime(.0001,at+duration);source.connect(gain);gain.connect(ctx.destination);source.start(at);source.stop(at+duration+.02);keep(source,[source,gain]);
}
function breath(ctx,at,duration,frequency,volume){
 const length=Math.ceil(ctx.sampleRate*duration),buffer=ctx.createBuffer(1,length,ctx.sampleRate),values=buffer.getChannelData(0);for(let i=0;i<length;i++)values[i]=(Math.random()*2-1)*Math.sin(Math.PI*i/length);
 const source=ctx.createBufferSource(),filter=ctx.createBiquadFilter(),gain=ctx.createGain();source.buffer=buffer;filter.type='bandpass';filter.frequency.setValueAtTime(frequency,at);filter.Q.value=3;gain.gain.value=volume;source.connect(filter);filter.connect(gain);gain.connect(ctx.destination);source.start(at);keep(source,[source,filter,gain]);
}
export function playStickerSound(shape){
 if(!STICKER_FEEDBACK[shape])return false;
 const ctx=audio();if(!ctx)return false;void ctx.resume().catch(()=>{});const now=ctx.currentTime+.008;
 if(shape==='duck'){
  // Randomly choose one of the two calls from the user's toy-duck clip.
  const play=()=>{
   if(!duckBuffers.length||ctx.state==='closed')return;
   const buffer=duckBuffers[Math.floor(Math.random()*duckBuffers.length)],at=ctx.currentTime+.008,length=buffer.duration;
   const source=ctx.createBufferSource(),gain=ctx.createGain();source.buffer=buffer;
   gain.gain.setValueAtTime(0,at);gain.gain.linearRampToValueAtTime(.65,at+.008);gain.gain.setValueAtTime(.65,at+length-.025);gain.gain.linearRampToValueAtTime(0,at+length);
   source.connect(gain);gain.connect(ctx.destination);source.start(at);keep(source,[source,gain]);
  };
  if(duckBuffers.length)play();
  else{const clickedAt=performance.now();void prepareStickerAudio().then(()=>{if(performance.now()-clickedAt<450)play();});}
 }else if(shape==='semicolon'){for(const delay of [0,.11,.27]){breath(ctx,now+delay,.035,2400,.14);tone(ctx,220,now+delay,.055,.025,'triangle');}}
 else if(shape==='rainbow'){[523.25,587.33,659.25,698.46,783.99,880,1046.5].forEach((f,i)=>tone(ctx,f,now+i*.047,.22,.025));}
 else if(shape==='envelope'){[0,.08,.16].forEach(delay=>breath(ctx,now+delay,.12,2200,.09));tone(ctx,784,now+.15,.35,.032,'triangle',1046);}
 else if(shape==='orbit'){[392,587,784,1174].forEach((f,i)=>tone(ctx,f,now+i*.085,.32,.028,'sine',f*1.06));}
 else if(shape==='gem'){[1046.5,1568,2093].forEach((f,i)=>tone(ctx,f,now+i*.07,.45,.027));}
 else if(shape==='crown'){[261.63,392,523.25,659.25].forEach((f,i)=>tone(ctx,f,now+i*.045,.58,.025,'triangle'));}
 else if(shape==='galaxy'){[330,494,740,1109,1661].forEach((f,i)=>tone(ctx,f,now+i*.065,.42,.022,'sine',f*1.18));}
 else if(shape==='phoenix'){breath(ctx,now,.55,1000,.12);tone(ctx,330,now,.45,.035,'triangle',1100);tone(ctx,880,now+.15,.38,.025,'sine',1760);}
 else if(shape==='moon'){[659.25,987.77,1318.51].forEach((f,i)=>tone(ctx,f,now+i*.18,.55,.023));}
 else if(shape==='planet'){[196,293.66,392].forEach((f,i)=>tone(ctx,f,now+i*.12,.58,.025,'sine',f*1.12));}
 else if(shape==='crystal'){[1396.91,2093,2793.83].forEach((f,i)=>tone(ctx,f,now+i*.055,.43,.02));}
 else if(shape==='butterfly'){[0,.11,.23,.38].forEach((delay,i)=>breath(ctx,now+delay,.09,1800+i*220,.047));tone(ctx,1174.66,now+.35,.2,.013);}
 else if(shape==='rocket'){breath(ctx,now,.65,650,.11);tone(ctx,90,now,.68,.03,'triangle',1200);}
 else if(shape==='whale'){tone(ctx,155,now,.75,.04,'sine',340);tone(ctx,290,now+.3,.6,.018,'sine',130);}
 else if(shape==='cottage'){tone(ctx,180,now,.23,.025,'triangle',270);breath(ctx,now,.19,650,.045);[659,880].forEach((f,i)=>tone(ctx,f,now+.18+i*.17,.4,.023));}
 else if(shape==='sofa'){tone(ctx,120,now,.18,.05,'sine',65);breath(ctx,now,.12,320,.055);tone(ctx,165,now+.14,.2,.024,'sine',95);}
 else if(shape==='bookshelf'){[0,.15,.33].forEach(delay=>breath(ctx,now+delay,.15,2100,.06));}
 else if(shape==='boat'){[0,.3].forEach(delay=>{breath(ctx,now+delay,.24,620,.07);tone(ctx,520,now+delay+.07,.14,.016,'sine',200);});}
 else if(shape==='mountain'){breath(ctx,now,.7,420,.075);[0,.22,.44].forEach((delay,i)=>tone(ctx,293.66,now+delay,.42,.028/(i+1),'sine',261.63));}
 else if(shape==='answer42'){[523.25,659.25,783.99,1046.5].forEach((f,i)=>tone(ctx,f,now+i*.065,.11,.022,'triangle'));[783.99,1046.5].forEach((f,i)=>tone(ctx,f,now+.39+i*.09,.21,.024,'triangle'));}
 else if(shape==='heart'){[0,.27].forEach(delay=>{tone(ctx,68,now+delay,.17,.07,'sine',42);tone(ctx,90,now+delay+.09,.13,.035,'sine',55);});}
 else if(shape==='key'){[1864.66,2489].forEach((f,i)=>tone(ctx,f,now+i*.065,.18,.019));breath(ctx,now+.2,.04,1500,.1);tone(ctx,392,now+.23,.2,.027,'triangle',523.25);}
 else if(shape==='owl'){[0,.34].forEach(delay=>{tone(ctx,450,now+delay,.27,.038,'sine',330);tone(ctx,900,now+delay,.23,.008,'sine',660);});}
 else if(shape==='dragon'){breath(ctx,now,.46,310,.11);tone(ctx,85,now,.5,.042,'triangle',190);tone(ctx,170,now+.18,.28,.024,'sine',95);}
 else if(shape==='telescope'){[0,.09].forEach(delay=>breath(ctx,now+delay,.035,1900,.075));[1046.5,1568,2093].forEach((f,i)=>tone(ctx,f,now+.22+i*.1,.36,.023));}
 else if(shape==='tower'){[523.25,783.99,1046.5,1318.51].forEach((f,i)=>tone(ctx,f,now+i*.16,.65,.024));}
 else if(shape==='bridge'){[0,.15,.3].forEach(delay=>{breath(ctx,now+delay,.06,550,.06);tone(ctx,160,now+delay,.08,.027,'triangle',100);});breath(ctx,now+.42,.3,720,.045);}
 else if(shape==='yearbadge'){[523.25,659.25,783.99,1046.5].forEach((f,i)=>tone(ctx,f,now+i*.18,.4,.028,'sine',f*1.02));}
 return true;
}
