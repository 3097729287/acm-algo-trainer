// Preserve original pixels and colors. Transparent monochrome diagrams receive
// a contrasting surface; photos and already opaque figures stay unchanged.
export function imageSurface(pixels){
 let visible=0,transparent=0,dark=0,light=0;
 for(let i=0;i<pixels.length;i+=4){
  const alpha=pixels[i+3];if(alpha<245)transparent++;
  if(alpha<20)continue;visible++;
  const luminance=(.2126*pixels[i]+.7152*pixels[i+1]+.0722*pixels[i+2])/255;
  if(luminance<.43)dark++;if(luminance>.72)light++;
 }
 if(!visible||transparent<pixels.length/4*.05)return 'native';
 return dark/visible>.55?'paper':light/visible>.7?'ink':'native';
}

export async function adaptReadingImage(image){
 if(!image?.complete||!image.naturalWidth)return;
 const source=image.currentSrc||image.src;if(image.dataset.analyzedSource===source)return;
 let surface='native';
 try{
  const canvas=image.ownerDocument.createElement('canvas'),scale=Math.min(1,96/image.naturalWidth,96/image.naturalHeight);
  canvas.width=Math.max(1,Math.round(image.naturalWidth*scale));canvas.height=Math.max(1,Math.round(image.naturalHeight*scale));
  const context=canvas.getContext('2d',{willReadFrequently:true});context.drawImage(image,0,0,canvas.width,canvas.height);
  surface=imageSurface(context.getImageData(0,0,canvas.width,canvas.height).data);
 }catch{/* Cross-origin images retain their original rendering. */}
 image.dataset.analyzedSource=source;image.dataset.imageSurface=surface;
 image.style.backgroundColor=surface==='paper'?'#f7f8fa':surface==='ink'?'#171d26':'transparent';
 image.style.padding=surface==='native'?'0':'10px';image.style.borderRadius=surface==='native'?'0':'6px';
 image.style.boxSizing='border-box';
}

export function adaptDocumentImages(document){
 for(const image of document.querySelectorAll('img')){
  if(image.complete)void adaptReadingImage(image);
  else image.addEventListener('load',()=>void adaptReadingImage(image),{once:true});
 }
}
