import {createHash} from 'node:crypto';
import {AccountError} from './accounts.mjs';
export function validateAvatar(value) {
 const fail=()=>{throw new AccountError(400,'头像须为不超过 48 KB 的 PNG、JPEG 或 WebP 图片');};
 if(value==='')return {data:'',hash:null};
 if(typeof value!=='string'||value.length>48*1024)fail();
 const match=/^data:image\/(png|jpeg|webp);base64,([A-Za-z0-9+/]+={0,2})$/.exec(value);
 if(!match)fail();
 const bytes=Buffer.from(match[2],'base64');
 if(bytes.toString('base64')!==match[2])fail();
 const valid=match[1]==='png'?bytes.length>=24&&bytes.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))&&bytes.toString('ascii',12,16)==='IHDR':match[1]==='jpeg'?bytes.length>=4&&bytes[0]===255&&bytes[1]===216&&bytes[2]===255&&bytes.at(-2)===255&&bytes.at(-1)===217:bytes.length>=16&&bytes.toString('ascii',0,4)==='RIFF'&&bytes.toString('ascii',8,12)==='WEBP'&&bytes.readUInt32LE(4)===bytes.length-8;
 if(!valid)fail();
 return {data:value,hash:createHash('sha256').update(value).digest('hex')};
}
