import assert from 'node:assert/strict';
import {fitStickerPlacement} from '../src/lib/stickerPlacement.js';
let cases=0;
for(const [width,height] of [[240,300],[320,300],[430,500],[650,300],[950,800]]){
 for(const angle of [-180,-135,-90,-45,0,15,45,90,135,180])for(const scale of [.5,1,2]){
  for(const x of [-.2,0,.03,.5,.97,1,1.2])for(const y of [0,.04,.5,.96,1]){
   const value=fitStickerPlacement({x,y,angle,scale},{width,height});
   const size=Math.max(28,Math.min(56,width*.08))*scale,r=value.angle*Math.PI/180;
   // Check the four actual rotated corners, rather than expected clamp values.
   for(const dx of [-size/2,size/2])for(const dy of [-size/2,size/2]){
    const px=value.x*width+dx*Math.cos(r)-dy*Math.sin(r);
    const py=value.y*height+dx*Math.sin(r)+dy*Math.cos(r);
    assert(px>=7.999&&px<=width-7.999,[width,height,x,y,angle,px]);
    assert(py>=7.999&&py<=height-7.999,[width,height,x,y,angle,py]);
   }
   assert.deepEqual(fitStickerPlacement(value,{width,height}),value);
   cases++;
  }
 }
}
assert.deepEqual(fitStickerPlacement({x:.5,y:.5,angle:15},{width:430,height:500}),{x:.5,y:.5,angle:15});
console.log(`PASS ${cases} rotated sticker bounds across five content sizes, edge dragging and idempotent presentation`);
