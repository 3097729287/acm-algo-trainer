import {deflateSync} from 'node:zlib';
const crcTable=Array.from({length:256},(_,n)=>{for(let i=0;i<8;i++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
function chunk(type,data){const text=Buffer.from(type),payload=Buffer.concat([text,data]);let crc=0xffffffff;for(const byte of payload)crc=crcTable[(crc^byte)&255]^(crc>>>8);const size=Buffer.alloc(4),sum=Buffer.alloc(4);size.writeUInt32BE(data.length);sum.writeUInt32BE((crc^0xffffffff)>>>0);return Buffer.concat([size,payload,sum]);}
export function originalAvatarPng(width=512,height=512){
 const header=Buffer.alloc(13);header.writeUInt32BE(width);header.writeUInt32BE(height,4);header[8]=8;header[9]=2;
 const raw=Buffer.alloc(height*(width*3+1));let state=349907;
 for(let y=0;y<height;y++)for(let x=1;x<=width*3;x++){state^=state<<13;state^=state>>>17;state^=state<<5;raw[y*(width*3+1)+x]=state&255;}
 return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',header),chunk('IDAT',deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]);
}
