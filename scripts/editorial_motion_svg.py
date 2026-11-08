"""Portable SMIL animation of stable SVG objects, with a still reduced-motion view."""
import base64
import re
from copy import deepcopy
from html import escape
from editorial_motion_scenes import object_svg


def inner(source):
    return re.fullmatch(r'<svg[^>]*>(.*)</svg>\s*',source,re.S)[1]


def animated_scene(scene,steps):
    frames=[{o['id']:o for o in frame} for frame in scene['frames']]
    ids=list(dict.fromkeys(o['id'] for frame in scene['frames'] for o in frame))
    total=sum(step['duration'] for step in steps);samples=[(0,0,False)];elapsed=0
    for i,step in enumerate(steps[:-1]):
        samples.extend([((elapsed+step['duration']*.35)/total,i,False),((elapsed+step['duration']*.675)/total,i,True),((elapsed+step['duration'])/total,i+1,False)])
        elapsed+=step['duration']
    samples.append((1,len(steps)-1,False));times=';'.join(f'{t:.8f}' for t,_,_ in samples)

    def pose(key,index):
        if key in frames[index]:return frames[index][key]
        previous=next((frames[i][key] for i in range(index-1,-1,-1) if key in frames[i]),None)
        source=previous or next(frame[key] for frame in frames[index+1:] if key in frame)
        item=deepcopy(source);item['opacity']=0
        item['x'],item['y']=source.get('exit' if previous else 'enter',[source['x'],source['y']-30] if previous else [source['x'],source['y']])
        return item

    def animate(name,values,discrete=False):
        if len(set(map(str,values)))<2:return ''
        return f'<animate attributeName="{name}" values="{escape(";".join(map(str,values)))}" keyTimes="{times}" dur="{total/1000:g}s" repeatCount="indefinite" calcMode="{"discrete" if discrete else "linear"}"/>'

    body=[]
    for key in ids:
        poses=[]
        for _,i,midpoint in samples:
            item=deepcopy(pose(key,i))
            if midpoint:
                following=pose(key,i+1)
                for k in ['x','y','u','v','w','h','r','opacity']:
                    if k in item and k in following:item[k]=(item[k]+following[k])/2
                if following.get('arc') and item['x']!=following['x']:item['y']+=following['arc']
            poses.append(item)
        first=poses[0];kind=first['kind']
        translations=[f'{p["x"]} {p["y"]}' for p in poses]
        group=f'<g transform="translate({translations[0]})" opacity="{first.get("opacity",1)}">'
        if len(set(translations))>1:group+=f'<animateTransform attributeName="transform" type="translate" values="{";".join(translations)}" keyTimes="{times}" dur="{total/1000:g}s" repeatCount="indefinite"/>'
        group+=animate('opacity',[p.get('opacity',1) for p in poses])
        color=[p.get('color','#2365ab') for p in poses];fill=[p.get('fill','#eaf3ff') for p in poses]
        if kind in {'box','rect','dot','line'}:
            attrs={'stroke':color,'stroke-width':[p.get('width',2) for p in poses]}
            if kind in {'box','rect'}:
                attrs.update(x=[-p.get('w',65)/2 if kind=='box' else 0 for p in poses],y=[-p.get('h',46)/2 if kind=='box' else 0 for p in poses],width=[p.get('w',65) for p in poses],height=[p.get('h',46) for p in poses],fill=fill,rx=[7 if kind=='box' else 3]*len(poses));tag='rect'
            elif kind=='dot':attrs.update(cx=[0]*len(poses),cy=[0]*len(poses),r=[p.get('r',23) for p in poses],fill=fill);tag='circle'
            else:attrs.update(x1=[0]*len(poses),y1=[0]*len(poses),x2=[p['u']-p['x'] for p in poses],y2=[p['v']-p['y'] for p in poses]);tag='line'
            group+='<'+tag+' '+ ' '.join(f'{k}="{values[0]}"' for k,values in attrs.items())+'>'+''.join(animate(k,v) for k,v in attrs.items())+'</'+tag+'>'
        for value in dict.fromkeys(p.get('text') for p in poses):
            if value is None:continue
            alpha=[1 if p.get('text')==value else 0 for p in poses]
            group+=f'<text x="0" y="{0 if kind=="text" else 7}" text-anchor="{first.get("anchor","start") if kind=="text" else "middle"}" font-size="{first.get("size",19)}" fill="{color[0]}" opacity="{alpha[0]}">'+escape(value)+animate('fill',color)+animate('opacity',alpha,True)+'</text>'
        body.append(group+'</g>')
    background=inner(base64.b64decode(scene['background'].split(',',1)[1]).decode())
    return '<style>.scene-still{display:none}@media(prefers-reduced-motion:reduce){.scene-animated{display:none}.scene-still{display:inline}}</style>'+background+'<g class="scene-animated" font-family="Microsoft YaHei,Noto Sans CJK SC,sans-serif">'+''.join(body)+'</g><g class="scene-still" font-family="Microsoft YaHei,Noto Sans CJK SC,sans-serif">'+''.join(object_svg(o) for o in scene['frames'][0])+'</g>'
