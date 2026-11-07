// The approved toy-duck clip is a small embedded PCM WAV. Reading it directly
// avoids a decoder round trip on the first gesture; the source file stays intact.
export function duckPcmBuffer(context,bytes){
 const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
 const tag=offset=>String.fromCharCode(...bytes.subarray(offset,offset+4));
 if(bytes.length<44||tag(0)!=='RIFF'||tag(8)!=='WAVE')return null;
 let channels=0,sampleRate=0,data=0,length=0;
 for(let offset=12;offset+8<=bytes.length;){
  const size=view.getUint32(offset+4,true),start=offset+8;
  if(start+size>bytes.length)return null;
  if(tag(offset)==='fmt '){
   if(size<16||view.getUint16(start,true)!==1||view.getUint16(start+14,true)!==16)return null;
   channels=view.getUint16(start+2,true);sampleRate=view.getUint32(start+4,true);
  }else if(tag(offset)==='data'){data=start;length=size;}
  offset=start+size+(size%2);
 }
 if(!channels||!sampleRate||!length||length%(channels*2))return null;
 const frames=length/(channels*2),sample=(frame,channel)=>view.getInt16(data+(frame*channels+channel)*2,true)/32768;
 let peak=0;
 for(let frame=0;frame<frames;frame++)for(let channel=0;channel<channels;channel++)peak=Math.max(peak,Math.abs(sample(frame,channel)));
 const window=Math.max(1,Math.round(sampleRate*.002)),threshold=Math.max(.001,peak*.01);
 let first=0;
 for(let from=0;from<frames;from+=window){
  const to=Math.min(frames,from+window);let squares=0;
  for(let frame=from;frame<to;frame++)for(let channel=0;channel<channels;channel++)squares+=sample(frame,channel)**2;
  if(Math.sqrt(squares/((to-from)*channels))>threshold){first=Math.max(0,from-window);break;}
 }
 const buffer=context.createBuffer(channels,frames-first,sampleRate);
 for(let channel=0;channel<channels;channel++){
  const output=buffer.getChannelData(channel);
  for(let frame=first;frame<frames;frame++)output[frame-first]=sample(frame,channel);
 }
 return buffer;
}
