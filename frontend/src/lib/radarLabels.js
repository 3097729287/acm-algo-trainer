// Keep text outside the chart and separate adjacent labels vertically. All
// domains use the same layout, including dense mathematics/string subtopics.
function wrapLabel(text,width=132) {
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
  return {name,lines,side,axis:[340+dx*163,245+dy*163],x:side===0?340:side<0?152:528,y:side===0?(dy<0?40:452):245+dy*183,height:lines.length*18};
 });
 for(const side of [-1,1]){
  const ordered=labels.filter(label=>label.side===side).sort((a,b)=>a.y-b.y);
  let bottom=12;
  for(const label of ordered){label.y=Math.max(label.y,bottom+label.height/2);bottom=label.y+label.height/2+6;}
  let top=488;
  for(const label of ordered.reverse()){label.y=Math.min(label.y,top-label.height/2);top=label.y-label.height/2-6;}
 }
 return labels;
}
