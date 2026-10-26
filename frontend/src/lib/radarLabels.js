// Place labels beside their own vertices. Pack only crowded neighbours, keeping
// the same circular order and leaving room for the top and bottom labels.
function wrapLabel(text,width=112) {
 const lines=[];let line='',size=0;
 for(const char of text){const next=/[\u0000-\u00ff]/.test(char)?8:14;
  if(size+next>width&&line){lines.push(line);line='';size=0;}
  line+=char;size+=next;
 }
 if(line)lines.push(line);return lines;
}
export function radarLabels(names) {
 const labels=names.map((name,i)=>{
  const angle=-Math.PI/2+i*2*Math.PI/names.length,dx=Math.cos(angle),dy=Math.sin(angle);
  const lines=wrapLabel(name),side=Math.abs(dx)<.05?0:Math.sign(dx);
  return {name,lines,side,axis:[340+dx*163,245+dy*163],x:340+dx*183+side*8,y:245+dy*189,height:lines.length*18};
 });
 for(const side of [-1,1]){
  const ordered=labels.filter(label=>label.side===side).sort((a,b)=>a.y-b.y);
  let bottom=26;
  for(const label of ordered){label.y=Math.max(label.y,bottom+label.height/2);bottom=label.y+label.height/2+6;}
  let top=474;
  for(const label of ordered.reverse()){label.y=Math.min(label.y,top-label.height/2);top=label.y-label.height/2-6;}
 }
 // Centred pole labels may be wider than the space between nearby vertices.
 for(const pole of labels.filter(label=>label.side===0)){
  const width=Math.max(...pole.lines.map(line=>[...line].reduce((sum,char)=>sum+(/[\u0000-\u00ff]/.test(char)?8:14),0)));
  for(const label of labels.filter(label=>label.side!==0)){
   if(Math.abs(label.y-pole.y)<(label.height+pole.height)/2+6){
    label.x=label.side>0?Math.max(label.x,pole.x+width/2+8):Math.min(label.x,pole.x-width/2-8);
   }
  }
 }
 return labels;
}
