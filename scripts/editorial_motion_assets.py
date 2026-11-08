"""Self-contained vector animations and their exact, inspectable step frames."""
import base64,json,math,re
from copy import deepcopy
from html import escape
from pathlib import Path
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY,INK

ROOT=Path(__file__).resolve().parents[1]
ORANGE='#9b630c';PALE={BLUE:'#eaf3ff',GREEN:'#e9f7ee',RED:'#fff0f0',GRAY:'#f2f4f7',ORANGE:'#fff6df'}
PREFIX='data:image/svg+xml;base64,'

class Board(Figure):
 def __init__(self,title,height=440,width=840):super().__init__(title,height,width)
 def row(self,values,y,label='',colors=None,indices=False,start=1):
  values=list(values);left=145;cell=(self.width-left-30)/max(1,len(values));colors=colors or {}
  if label:self.text(25,y+30,label,size=18)
  for i,value in enumerate(values):
   color=colors.get(i,BLUE)
   self.box(left+i*cell,y,cell-5,46,value,color,PALE.get(color,'#fff'),size=min(22,max(14,int((cell-10)/max(1,len(str(value)))))))
   if indices:self.text(left+(i+.5)*cell-2,y-10,i+start,GRAY,size=16,anchor='middle')
 def note(self,y,text,color=INK,size=20,x=32):
  # Keep actual text inside the figure; Chinese letters need a whole em.
  line='';units=0;limit=(self.width-x-28)/size
  for char in str(text):
   cost=1 if ord(char)>255 else .58
   if units+cost>limit and line:self.text(x,y,line,color,size);line='';units=0;y+=29
   line+=char;units+=cost
  if line:self.text(x,y,line,color,size)
 def label(self,x,y,text,color=INK,size=18):
  width=sum(1 if ord(char)>255 else .61 for char in str(text))*size+16
  self.parts.append(f'<rect x="{x-width/2:.1f}" y="{y-size-3:.1f}" width="{width:.1f}" height="{size+10}" rx="4" fill="#fff"/>')
  self.text(x,y,text,color,size,anchor='middle')
 def graph(self,points,edges,active=(),special=None,labels=None,directed=False):
  special=special or {};labels=labels or {}
  for edge in edges:
   a,b=edge[:2];color=special.get((a,b),GRAY);x,y=points[a];u,v=points[b];dx,dy=u-x,v-y;length=math.hypot(dx,dy)
   if not length:continue
   x+=dx/length*23;y+=dy/length*23;u-=dx/length*23;v-=dy/length*23
   self.line(x,y,u,v,color,width=4 if color!=GRAY else 2)
   if directed:
    angle=math.atan2(v-y,u-x);tip=[(u,v)]+[(u-11*math.cos(angle+t),v-11*math.sin(angle+t)) for t in [-.5,.5]]
    self.parts.append('<polygon points="'+' '.join(f'{p:.1f},{q:.1f}' for p,q in tip)+'" fill="'+color+'"/>')
   label=edge[2] if len(edge)>2 else ''
   if label!='':self.label((x+u)/2-dy/length*24,(y+v)/2+dx/length*24,label,color,size=18)
  for node,(x,y) in points.items():self.circle(x,y,labels.get(node,node),GREEN if node in active else BLUE,radius=22)
 def svg(self):return '\n'.join(self.parts+['</g></svg>'])+'\n'

class Clip:
 def __init__(self,key,pid,title,reason,after='',height=440):
  self.key,self.pid,self.title,self.reason,self.after,self.height=key,pid,title,reason,after,height
  self.steps=[];self.input=None;self.expected=None;self.scene=None
 def frame(self,caption,draw,facts=None,duration=2100):
  board=Board(self.title,self.height);draw(board)
  svg=board.svg()
  self.steps.append({'caption':caption,'image':PREFIX+base64.b64encode(svg.encode()).decode(),'duration':duration,'facts':deepcopy(facts or {})})
  return self
 def check(self,input,expected):self.input,self.expected=input,expected;return self
 def model(self):return {'version':1,'title':self.title,'steps':self.steps,**({'scene':self.scene} if self.scene else {})}
 def export(self,directory):
  assert 2<=len(self.steps)<=48,self.key
  total=sum(s['duration'] for s in self.steps);elapsed=0;times=[]
  for s in self.steps:times.append(elapsed/total);elapsed+=s['duration']
  times.append(1);body=[]
  for i,step in enumerate(self.steps):
   source=base64.b64decode(step['image'][len(PREFIX):]).decode();inside=re.fullmatch(r'<svg[^>]*>(.*)</svg>\s*',source,re.S)[1]
   inside=re.sub(r'<title[^>]*>.*?</title>','',inside,flags=re.S)
   values=['1' if j==i else '0' for j in range(len(self.steps))]+['1' if i==0 else '0']
   body.append(f'<g class="motion-state state-{i}" opacity="{1 if i==0 else 0}"><animate attributeName="opacity" values="'+ ';'.join(values)+'" keyTimes="'+';'.join(f'{t:.7f}' for t in times)+f'" dur="{total/1000:g}s" calcMode="discrete" repeatCount="indefinite"/>'+inside+'</g>')
  document=f'<svg xmlns="http://www.w3.org/2000/svg" width="840" height="{self.height}" viewBox="0 0 840 {self.height}" role="img"><title>{escape(self.title)}</title>'
  document+='<metadata id="tb-editorial-motion">'+escape(json.dumps(self.model(),ensure_ascii=False,separators=(',',':')))+'</metadata>'
  if self.scene:
   from editorial_motion_svg import animated_scene
   document+=animated_scene(self.scene,self.steps)
  else:document+='<style>@media(prefers-reduced-motion:reduce){.motion-state{opacity:0!important}.state-0{opacity:1!important}}</style>'+''.join(body)
  document+='</svg>\n'
  path=directory/(self.key+'.svg');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(document,encoding='utf8',newline='\n')
  return path
