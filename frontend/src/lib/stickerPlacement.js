// Stored coordinates stay normalized to the content region. Resizing only
// constrains their presentation; it never writes or consumes an inventory unit.
export const STICKER_SCALE={min:.5,max:2};
export function scalePolicy(item={}){return {min:item.minScale??STICKER_SCALE.min,max:item.maxScale??STICKER_SCALE.max,base:item.baseScale??1};}
export function stickerSize(bounds={},scale=1,item={}){const p=scalePolicy(item);return Math.max(28,Math.min(56,(bounds.width||0)*.08))*p.base*Math.max(p.min,Math.min(p.max,Number.isFinite(scale)?scale:1));}
export function fitStickerPlacement(position,bounds={},item={}){
 const finite=(value,fallback)=>Number.isFinite(value)?value:fallback;
 const angle=((finite(position.angle,0)+180)%360+360)%360-180;
 const {width=0,height=0}=bounds;
 const policy=scalePolicy(item),scale=Math.max(policy.min,Math.min(policy.max,finite(position.scale,1))),size=stickerSize(bounds,scale,item);
 const radians=angle*Math.PI/180;
 const half=size*(Math.abs(Math.cos(radians))+Math.abs(Math.sin(radians)))/2+8;
 const marginX=width>0?Math.min(.5,half/width):0;
 const marginY=height>0?Math.min(.5,half/height):0;
 const constrain=(value,margin)=>Math.max(margin,Math.min(1-margin,finite(value,.5)));
 return {...position,x:constrain(position.x,marginX),y:constrain(position.y,marginY),angle,...(position.scale!==undefined?{scale}:{})};
}
