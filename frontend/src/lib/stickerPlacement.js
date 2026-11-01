// Stored coordinates stay normalized to the content region. Resizing only
// constrains their presentation; it never writes or consumes an inventory unit.
export function fitStickerPlacement(position,bounds={}){
 const finite=(value,fallback)=>Number.isFinite(value)?value:fallback;
 const angle=((finite(position.angle,0)+180)%360+360)%360-180;
 const {width=0,height=0}=bounds;
 const size=Math.max(44,Math.min(88,width*.13));
 const radians=angle*Math.PI/180;
 const half=size*(Math.abs(Math.cos(radians))+Math.abs(Math.sin(radians)))/2+8;
 const marginX=width>0?Math.min(.5,half/width):0;
 const marginY=height>0?Math.min(.5,half/height):0;
 const constrain=(value,margin)=>Math.max(margin,Math.min(1-margin,finite(value,.5)));
 return {...position,x:constrain(position.x,marginX),y:constrain(position.y,marginY),angle};
}
