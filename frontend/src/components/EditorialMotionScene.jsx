const clamp=value=>Math.max(0,Math.min(1,value));
const ease=value=>{const t=clamp(value);return t*t*(3-2*t);};
const numeric=['x','y','u','v','w','h','r','width','size','opacity'];
const defaults={opacity:1,width:2,size:19,r:23,w:65,h:46};
const mixColor=(a,b,t)=>a&&b&&/^#[\da-f]{6}$/i.test(a)&&/^#[\da-f]{6}$/i.test(b)?'#'+[1,3,5].map(i=>Math.round(parseInt(a.slice(i,i+2),16)*(1-t)+parseInt(b.slice(i,i+2),16)*t).toString(16).padStart(2,'0')).join(''):b||a;

function interpolate(a,b,progress){
 if(!a){a={...b,x:b.enter?.[0]??b.x,y:b.enter?.[1]??b.y,opacity:0};progress=clamp((progress-(b.delay??.28))/(1-(b.delay??.28)));}
 else if(!b){b={...a,x:a.exit?.[0]??a.x,y:a.exit?.[1]??a.y-30,opacity:0};progress=clamp(progress/.4);}
 const t=ease(progress),result={...b};
 for(const key of numeric){const from=a[key]??defaults[key],to=b[key]??defaults[key];if(from!==undefined&&to!==undefined)result[key]=from+(to-from)*t;}
 if((a.x!==b.x||a.y!==b.y)&&b.arc)result.y+=Math.sin(Math.PI*t)*b.arc;
 result.color=mixColor(a.color,b.color,t);result.fill=mixColor(a.fill,b.fill,t);
 result.text=t<1?a.text:b.text;
 return result;
}

function ObjectShape({item}){
 const {kind,x,y,w,h,r,color='#2365ab',fill='#eaf3ff',width=2,size=19,opacity=1}=item;
 const label=(text,alpha=1)=><text x={kind==='text'?x:x} y={kind==='text'?y:y+7} textAnchor={kind==='text'?(item.anchor||'start'):'middle'} fontSize={size} fill={color} opacity={alpha}>{text}</text>;
 return <g data-motion-object={item.id} data-kind={kind} opacity={opacity}>
  {kind==='box'&&<rect x={x-w/2} y={y-h/2} width={w} height={h} rx="7" fill={fill} stroke={color} strokeWidth={width}/>}
  {kind==='rect'&&<rect x={x} y={y} width={Math.max(0,w)} height={Math.max(0,h)} rx="3" fill={fill} stroke={color} strokeWidth={width}/>}
  {kind==='dot'&&<circle cx={x} cy={y} r={r} fill={fill} stroke={color} strokeWidth={width}/>}
  {kind==='line'&&<line x1={x} y1={y} x2={item.u} y2={item.v} stroke={color} strokeWidth={width} strokeLinecap="round"/>}
  {item.text!==undefined&&label(item.text)}
 </g>;
}

export default function EditorialMotionScene({model,step,progress}){
 const scene=model.scene,before=scene.frames[step],after=progress>0?(scene.frames[step+1]||before):before;
 const first=new Map(before.map(item=>[item.id,item])),second=new Map(after.map(item=>[item.id,item]));
 return <svg className="reading-motion-scene" xmlns="http://www.w3.org/2000/svg" width={scene.width} height={scene.height} viewBox={`0 0 ${scene.width} ${scene.height}`} role="img" aria-label={model.title}>
  <image href={scene.background} width={scene.width} height={scene.height}/>
  <g fontFamily="Microsoft YaHei, Noto Sans CJK SC, sans-serif">{[...new Set([...first.keys(),...second.keys()])].map(id=><ObjectShape key={id} item={interpolate(first.get(id),second.get(id),progress)}/>)}</g>
 </svg>;
}
