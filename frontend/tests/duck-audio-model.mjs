import assert from 'node:assert/strict';
import DUCK_CALLS from '../src/lib/stickerDuckCalls.js';
import {duckPcmBuffer} from '../src/lib/stickerDuckClip.js';

const bytes=Buffer.from(DUCK_CALLS[0],'base64'),sampleRate=bytes.readUInt32LE(24),frames=bytes.readUInt32LE(40)/2;
const context={createBuffer(channels,length,sampleRate){const data=Array.from({length:channels},()=>new Float32Array(length));return {numberOfChannels:channels,length,sampleRate,duration:length/sampleRate,getChannelData:channel=>data[channel]};}};
const buffer=duckPcmBuffer(context,bytes),samples=buffer.getChannelData(0),removed=frames-buffer.length;
assert.equal(buffer.sampleRate,sampleRate);assert.equal(buffer.numberOfChannels,1);
assert(removed/sampleRate>.12&&removed/sampleRate<.15,'Remove the silent lead-in of the approved recording');
assert(samples.slice(0,sampleRate*.005).some(value=>Math.abs(value)>.003),'Audible onset falls within five milliseconds');
for(let index=0;index<samples.length;index++)assert.equal(samples[index],bytes.readInt16LE(44+(index+removed)*2)/32768,'Retain the original waveform and pitch');
assert.equal(duckPcmBuffer(context,new Uint8Array(0)),null);
assert.equal(duckPcmBuffer(context,new Uint8Array(44)),null);
console.log(JSON.stringify({ok:true,originalSeconds:frames/sampleRate,trimmedLeadInMs:removed/sampleRate*1000,playSeconds:buffer.duration,originalWaveformRetained:true}));
