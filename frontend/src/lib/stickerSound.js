import DUCK from './stickerDuckAudio.js';
let context,duckBuffer,decoding;
const playing=[];
export const LEGENDARY_FEEDBACK=Object.freeze({duck:'quack',semicolon:'type',rainbow:'rainbow',envelope:'post',orbit:'orbit',gem:'gem',crown:'crown',galaxy:'galaxy',phoenix:'flame'});
function audio(){try{const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio)return null;if(!context||context.state==='closed')context=new Audio({latencyHint:'interactive'});return context;}catch{return null;}}
export function prepareStickerAudio(){
 const ctx=audio();if(!ctx||duckBuffer)return Promise.resolve();
 if(!decoding){const raw=atob(DUCK),bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));decoding=ctx.decodeAudioData(bytes.buffer).then(value=>{duckBuffer=value;}).catch(()=>{}).finally(()=>{decoding=null;});}
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
 if(!LEGENDARY_FEEDBACK[shape])return false;
 const ctx=audio();if(!ctx)return false;void ctx.resume().catch(()=>{});const now=ctx.currentTime+.008;
 if(shape==='duck'){
  // One complete call ends at 1.59 s; the next begins at 1.675 s. Preserve
  // the licensed original and soften this one call only at playback time.
  const play=()=>{
   if(!duckBuffer||ctx.state==='closed')return;
   const at=ctx.currentTime+.008,offset=1.15,duration=Math.min(.46,duckBuffer.duration-offset),rate=.9,length=duration/rate;
   if(duration<=0)return;
   const source=ctx.createBufferSource(),filter=ctx.createBiquadFilter(),gain=ctx.createGain();
   source.buffer=duckBuffer;source.playbackRate.value=rate;
   filter.type='lowpass';filter.frequency.value=2200;filter.Q.value=.55;
   gain.gain.setValueAtTime(0,at);gain.gain.linearRampToValueAtTime(.48,at+.018);gain.gain.setValueAtTime(.48,at+length-.06);gain.gain.linearRampToValueAtTime(0,at+length);
   source.connect(filter);filter.connect(gain);gain.connect(ctx.destination);source.start(at,offset,duration);keep(source,[source,filter,gain]);
  };
  if(duckBuffer)play();
  else{const clickedAt=performance.now();void prepareStickerAudio().then(()=>{if(performance.now()-clickedAt<450)play();});}
 }else if(shape==='semicolon'){for(const delay of [0,.11,.27]){breath(ctx,now+delay,.035,2400,.14);tone(ctx,220,now+delay,.055,.025,'triangle');}}
 else if(shape==='rainbow'){[523.25,587.33,659.25,698.46,783.99,880,1046.5].forEach((f,i)=>tone(ctx,f,now+i*.047,.22,.025));}
 else if(shape==='envelope'){[0,.08,.16].forEach(delay=>breath(ctx,now+delay,.12,2200,.09));tone(ctx,784,now+.15,.35,.032,'triangle',1046);}
 else if(shape==='orbit'){[392,587,784,1174].forEach((f,i)=>tone(ctx,f,now+i*.085,.32,.028,'sine',f*1.06));}
 else if(shape==='gem'){[1046.5,1568,2093].forEach((f,i)=>tone(ctx,f,now+i*.07,.45,.027));}
 else if(shape==='crown'){[261.63,392,523.25,659.25].forEach((f,i)=>tone(ctx,f,now+i*.045,.58,.025,'triangle'));}
 else if(shape==='galaxy'){[330,494,740,1109,1661].forEach((f,i)=>tone(ctx,f,now+i*.065,.42,.022,'sine',f*1.18));}
 else if(shape==='phoenix'){breath(ctx,now,.55,1000,.12);tone(ctx,330,now,.45,.035,'triangle',1100);tone(ctx,880,now+.15,.38,.025,'sine',1760);}
 return true;
}
