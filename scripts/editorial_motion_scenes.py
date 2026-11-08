"""Continuous object motion for processes where physical order or travel matters.

The numerical snapshots still come from the reviewed algorithm traces. Stable
object identities make queue entries, ships, characters and cursors move between
those snapshots; DP comparisons keep their deliberate step presentation.
"""
import base64
from copy import deepcopy
from html import escape
from editorial_motion_assets import Board, PREFIX, BLUE, GREEN, RED, GRAY, ORANGE, PALE


def obj(key, kind, x, y, **kw):
    return dict(id=key, kind=kind, x=round(x, 3), y=round(y, 3), **kw)


def box(key, x, y, text, color=BLUE, w=76, **kw):
    return obj(key, 'box', x, y, text=str(text), color=color, fill=PALE[color], w=w, h=46, size=19, **kw)


def text(key, x, y, value, color=GREEN, size=19, **kw):
    return obj(key, 'text', x, y, text=str(value), color=color, size=size, **kw)


def slots(board, n, y, label, values=None, indices=False, start=1):
    cell=(840-175)/n
    board.text(25, y+7, label, size=18)
    centers=[]
    for i in range(n):
        x=145+(i+.5)*cell-2.5
        centers.append(x)
        board.box(x-(cell-5)/2, y-23, cell-5, 46, '' if values is None else values[i], GRAY, '#f7f9fc', size=19)
        if indices:board.text(x,y-34,i+start,GRAY,size=16,anchor='middle')
    return centers,cell-5


def object_svg(item):
    """The exact endpoint used for static stepping and portable SVG export."""
    k=item['kind'];x=item['x'];y=item['y'];color=item.get('color',BLUE);fill=item.get('fill',PALE[BLUE]);width=item.get('width',2)
    result=f'<g opacity="{item.get("opacity",1)}">'
    if k=='box':
        w=item.get('w',65);h=item.get('h',46)
        result+=f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="{color}" stroke-width="{width}"/>'
    elif k=='rect':result+=f'<rect x="{x}" y="{y}" width="{item["w"]}" height="{item["h"]}" rx="3" fill="{fill}" stroke="{color}" stroke-width="{width}"/>'
    elif k=='dot':result+=f'<circle cx="{x}" cy="{y}" r="{item.get("r",23)}" fill="{fill}" stroke="{color}" stroke-width="{width}"/>'
    elif k=='line':result+=f'<line x1="{x}" y1="{y}" x2="{item["u"]}" y2="{item["v"]}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'
    if 'text' in item:
        anchor=item.get('anchor','start') if k=='text' else 'middle'
        result+=f'<text x="{x}" y="{y if k=="text" else y+7}" text-anchor="{anchor}" font-size="{item.get("size",19)}" fill="{color}">{escape(item["text"])}</text>'
    return result+'</g>'


def finish(clip,board,frames):
    assert len(frames)==len(clip.steps)
    clip.height=board.height
    source=board.svg()
    clip.scene={'version':1,'width':board.width,'height':board.height,'background':PREFIX+base64.b64encode(source.encode()).decode(),'frames':frames}
    for step,objects in zip(clip.steps,frames):
        assert len({o['id'] for o in objects})==len(objects)
        svg=source.replace('</g></svg>',''.join(object_svg(o) for o in objects)+'</g></svg>')
        step['image']=PREFIX+base64.b64encode(svg.encode()).decode()


def add_scenes(clips):
    by_id={c.key:c for c in clips}
    # Both queue policies use stable entry IDs. New entries fly from the actual
    # input cell, surviving entries shift, and removed entries leave the queue.
    for key in ['window-deques','previous-window','bounded-prefix-queue','next-greater-stack']:
        c=by_id[key];f=Board(c.title,500);frames=[]
        a={'window-deques':[1,3,-1,-3,5,3,6,7],'previous-window':[7,8,1,4],
           'bounded-prefix-queue':[-2,3,-1,4,-5],'next-greater-stack':[1,4,2,3,5]}[key]
        xs,w=slots(f,len(a),115,'原数组',a,True)
        if key=='window-deques':
            qx,qw=slots(f,8,220,'最小队列');slots(f,8,310,'最大队列')
            ox,ow=slots(f,6,405,'窗口最小');slots(f,6,465,'窗口最大')
            low=[];high=[]
            for step in c.steps:
                s=step['facts'];i=s['i'];left=max(0,i-2);objects=[obj('window','rect',145+left*(w+5),83,w=(i-left+1)*(w+5)-5,h=64,color=GREEN,fill=PALE[GREEN],opacity=.25)]
                for name,y in [('low',220),('high',310)]:
                    objects.extend(box(f'{name}:{j}',qx[k],y,f'{j+1}:{a[j]}',BLUE,qw,enter=[xs[j],115],exit=[qx[k],y-40]) for k,j in enumerate(s[name]))
                if 'mins' in s:low=s['mins'];high=s['maxs']
                for name,values,y,color,origin in [('min',low,405,GREEN,220),('max',high,465,BLUE,310)]:
                    objects.extend(box(f'out-{name}:{k}',ox[k],y,v,color,ow,enter=[qx[0],origin],delay=.8) for k,v in enumerate(values))
                frames.append(objects)
        elif key=='previous-window':
            qx,qw=slots(f,4,240,'队列候选');ox,ow=slots(f,4,370,'已输出');answers=[]
            f.note(460,'绿色框是可查询的旧项；红框当前项在查询后才入队。',size=19)
            for step in c.steps:
                s=step['facts'];i=s['i'];left=max(0,i-2);objects=[]
                if i>0:objects.append(obj('old-window','rect',145+left*(w+5),83,w=(i-left)*(w+5)-5,h=64,color=GREEN,fill=PALE[GREEN],opacity=.27))
                objects.append(obj('current','rect',xs[i]-w/2,92,w=w,h=46,color=RED,fill=PALE[RED],opacity=.35))
                objects.extend(box(f'q:{j}',qx[k],240,f'{j+1}:{a[j]}',BLUE,qw,enter=[xs[j],115],exit=[qx[k],200]) for k,j in enumerate(s['queue']))
                if 'answers' in s:answers=s['answers']
                objects.extend(box(f'answer:{k}',ox[k],370,v,GREEN,ow,enter=[qx[0],240],delay=.8) for k,v in enumerate(answers))
                frames.append(objects)
        elif key=='bounded-prefix-queue':
            prefix=[0,-2,1,0,4,-1];px,pw=slots(f,6,235,'前缀和',prefix,True,0);qx,qw=slots(f,6,350,'候选 j');best=-2
            for step in c.steps:
                s=step['facts'];i=s['i'];best=s.get('best',best);objects=[obj('right','rect',xs[i-1]-w/2,92,w=w,h=46,color=RED,fill=PALE[RED],opacity=.3)]
                objects.extend(box(f'prefix:{j}',qx[k],350,f'{j}:{prefix[j]}',BLUE,qw,enter=[px[j],235],exit=[qx[k],310]) for k,j in enumerate(s['queue']))
                if 'j' in s:objects.append(obj('left','rect',px[s['j']]-pw/2,212,w=pw,h=46,color=GREEN,fill=PALE[GREEN],opacity=.3))
                objects.append(text('best',32,455,f'长度上限 3；最佳非空和 = {best}'))
                frames.append(objects)
        else:
            qx,qw=slots(f,5,250,'等待栈');ox,ow=slots(f,5,380,'答案位置',[0]*5)
            f.note(470,'弹出的旧位置已找到答案；新位置随后才入栈。',size=19)
            for step in c.steps:
                s=step['facts'];i=s['i'];objects=[obj('current','rect',xs[i]-w/2,92,w=w,h=46,color=GREEN,fill=PALE[GREEN],opacity=.3)]
                objects.extend(box(f'stack:{j}',qx[k],250,f'{j+1}:{a[j]}',BLUE,qw,enter=[xs[j],115],exit=[qx[k],210]) for k,j in enumerate(s['stack']))
                objects.extend(box(f'answer:{j}',ox[j],380,v,GREEN,ow,enter=[qx[max(0,len(s['stack'])-1)],250],delay=.75) for j,v in enumerate(s['answer']) if v)
                frames.append(objects)
        finish(c,f,frames)

    c=by_id['stable-letter-swaps'];f=Board(c.title,440);xs,w=slots(f,4,115,'目标',['C','A₁','B','A₂']);slots(f,4,250,'当前顺序');frames=[]
    f.note(345,'只交换相邻字符；A₁ 始终排在 A₂ 前面。',size=19)
    for i,step in enumerate(c.steps):
        s=step['facts'];objects=[box('letter:'+{'A₁':'A1','A₂':'A2','B':'B','C':'C'}[t],xs[k],250,t,GREEN if t=='C' else BLUE,w,arc=-45 if t=='C' else 45) for k,t in enumerate(s['tokens'])]
        objects.append(text('count',32,405,f'已交换 {i} 次；剩余逆序 {s["inversions"]} 对。'))
        frames.append(objects)
    finish(c,f,frames)

    c=by_id['color-window'];f=Board(c.title,470);beads=['1红','1蓝','5红','6绿','8蓝'];xs,w=slots(f,5,120,'有序珠子',beads,True);cx,cw=slots(f,3,290,'红 蓝 绿');frames=[];best=None
    for step in c.steps:
        s=step['facts'];l=s['left'];r=s['right'];best=s.get('best',best);objects=[]
        if l<=r:objects.append(obj('window','rect',145+l*(w+5),87,w=(r-l+1)*(w+5)-5,h=65,color=GREEN,fill=PALE[GREEN],opacity=.3))
        objects.extend(box('count:'+str(k),cx[k],290,s['counts'][name],[RED,BLUE,GREEN][k],cw) for k,name in enumerate(['红','蓝','绿']))
        objects.append(text('bounds',32,220,f'左端 {l+1}；右端 {r+1}；当前含 {sum(v>0 for v in s["counts"].values())}/3 色'))
        objects.append(text('best',32,415,f'最短坐标差：{best}' if best is not None else '还没有完整窗口'))
        frames.append(objects)
    finish(c,f,frames)

    c=by_id['playlist-wrap'];f=Board(c.title,470);a=[3,3,2,5,3,3,2];xs,w=slots(f,7,130,'实际播放',a,True)
    f.line(145+4*(w+5)-2,85,145+4*(w+5)-2,200,ORANGE,dash=True);f.note(235,'虚线后是第二圈；用进入本首歌之前的历史最大值判断。',size=19);frames=[]
    for step in c.steps:
        s=step['facts'];objects=[obj('cursor','dot',xs[s['i']],185,r=9,color=RED if s['bad'] else GREEN,fill=PALE[GREEN])]
        objects.extend([text('old',32,310,f'旧最大值 {s["oldHistory"]}；新最大值 {s["history"]}'),text('heard',32,370,f'已听 {s["heard"]} 首'),text('decision',32,435,f'2×{s["x"]} < {s["oldHistory"]}，在听它之前停止。' if s['bad'] else '可以听完这一首。',RED if s['bad'] else GREEN)])
        frames.append(objects)
    finish(c,f,frames)

    c=by_id['fountain-successors'];f=Board(c.title,570);diam=[2,5,4,3,6];caps=[2,3,9,9,4];frames=[]
    for i,(d,cap) in enumerate(zip(diam,caps)):
        y=110+i*70;f.text(35,y+7,f'{i+1} 号',size=19);f.box(190-d*10,y-23,d*20,46,'',GRAY,'#fff');f.text(400,y+7,f'直径 {d}，容量 {cap}',GRAY,size=19)
    f.note(490,'实际后继链 1 → 2 → 5；3、4 号始终不接水。',size=19)
    for step in c.steps:
        s=step['facts'];objects=[]
        for i,amount in enumerate(s['amounts']):
            d=diam[i];height=42*amount/caps[i];objects.append(obj(f'water:{i}','rect',192-d*10,110+i*70+21-height,w=d*20-4,h=height,color=BLUE,fill='#9ecbfa',width=0,opacity=1 if height else 0))
            objects.append(text(f'amount:{i}',635,117+i*70,f'{amount}/{caps[i]}',GREEN if amount else GRAY))
        objects.append(text('remaining',32,540,f'尚待下流 {s["remaining"]} 单位水；恰好装满时停在最后一盘。',size=19))
        frames.append(objects)
    finish(c,f,frames)

    c=by_id['fleet-root-and-head'];f=Board(c.title,500);xs,w=slots(f,4,130,'实际各列');px,pw=slots(f,4,255,'父亲编号',indices=True);ox,ow=slots(f,4,370,'相对偏移',indices=True);frames=[]
    for step in c.steps:
        s=step['facts'];order=[v for group in s['groups'] for v in group];objects=[box(f'ship:{v}',xs[k],130,v,GREEN if s['parent'][v]==v else BLUE,w) for k,v in enumerate(order)]
        cursor=0
        for group in s['groups'][:-1]:
            cursor+=len(group);x=145+cursor*(w+5)-2
            objects.append(obj('boundary:'+str(group[-1]),'line',x,95,u=x,v=170,color=GRAY,width=4))
        for j in range(1,5):objects.extend([box(f'parent:{j}',px[j-1],255,s['parent'][j],BLUE,pw),box(f'offset:{j}',ox[j-1],370,s['offset'][j],BLUE,ow)])
        objects.append(text('root',32,465,'绿色舰号是集合代表；根留在中间时，前方舰偏移可为负。',size=19))
        frames.append(objects)
    finish(c,f,frames)

    c=by_id['weighted-parent-compression'];f=Board(c.title,520);points={0:(650,115),1:(390,245),2:(135,365),3:(650,365)}
    f.graph(points,[]);f.note(450,'边标签 = S[x] − S[parent[x]]；改父亲时同时累加。',size=19);f.note(495,'S₀=0，S₁=4，S₂=2，S₃=0；关系保持不变。',size=19);frames=[]
    for step in c.steps:
        objects=[]
        for a,b,value in step['facts']['edges']:
            x,y=points[a];u,v=points[b];objects.append(obj(f'parent-edge:{a}','line',x,y,u=u,v=v,color=GREEN if a==2 else GRAY,width=3))
            objects.append(box(f'edge-label:{a}',(x+u)/2+30,(y+v)/2,str(value),GREEN if a==2 else BLUE,60))
        # Nodes sit above moving edges; a connection cannot cover their labels.
        objects.extend(obj(f'node:{n}','dot',x,y,r=23,text=str(n),color=BLUE,fill='#ffffff') for n,(x,y) in points.items())
        frames.append(objects)
    finish(c,f,frames)

    c=by_id['lca-paired-lifting'];f=Board(c.title,540);points={1:(420,90),2:(235,180),3:(610,180),4:(135,280),5:(330,280),6:(135,375),7:(550,280),8:(720,280)}
    f.graph(points,[(1,2),(1,3),(2,4),(2,5),(4,6),(3,7),(3,8)]);f.note(505,'本图以 1 为根；只接受两端祖先不同的同步跳跃。',size=19);frames=[]
    for step in c.steps:
        s=step['facts'];objects=[obj('u','dot',*points[s['u']],r=31,color=GREEN,fill='none',width=4),obj('v','dot',*points[s['v']],r=35,color=RED,fill='none',width=4),text('state',32,455,f'u={s["u"]}，v={s["v"]}；'+('返回共同父亲 1。' if s['answer'] else '先对齐深度，再同步跳。'))]
        frames.append(objects)
    finish(c,f,frames)

    c=by_id['fuel-expanded-state'];f=Board(c.title,540);points={0:(125,145),1:(420,285),2:(715,145)}
    f.graph(points,[(0,1,'路长 2'),(1,2,'路长 2'),(0,2,'路长 4')])
    for n,price in enumerate([5,1,9]):f.text(points[n][0],points[n][1]+56,f'油价 {price}',BLUE,size=20,anchor='middle')
    sx,sw=slots(f,3,420,'城 / 油 / 费');f.note(505,'容量 4；直接买满走直路需 20，这条方案只需 12。',size=19);frames=[]
    for step in c.steps:
        s=step['facts'];objects=[obj('traveller','dot',*points[s['city']],r=31,color=GREEN,fill='none',width=5)]
        objects.extend(box('state:'+str(i),sx[i],420,value,GREEN,sw) for i,value in enumerate([s['city'],s['fuel'],s['cost']]))
        frames.append(objects)
    finish(c,f,frames)

    c=by_id['forbidden-triple-state'];f=Board(c.title,520);points={1:(130,115),2:(130,315),3:(450,215),4:(725,215)}
    f.graph(points,[(1,2),(2,3),(3,4),(1,3)]);sx,sw=slots(f,3,400,'前 / 现 / 边');frames=[]
    for step in c.steps:
        s=step['facts'];objects=[obj('traveller','dot',*points[s['current']],r=31,color=RED if s['blocked'] else GREEN,fill='none',width=5)]
        if s['blocked']:objects.append(obj('blocked','line',485,215,u=690,v=215,color=RED,width=6))
        objects.extend(box('state:'+str(i),sx[i],400,value,BLUE,sw) for i,value in enumerate([s['previous'],s['current'],len(s['path'])-1]))
        objects.append(text('path',32,490,'路径：'+' → '.join(map(str,s['path']))))
        frames.append(objects)
    finish(c,f,frames)

    # Pointer traversal is shown as travel over the original numbered lockers.
    c=by_id['successor-wrap-and-compress'];f=Board(c.title,500);xs,w=slots(f,7,135,'原格 / 哨兵',['1','2','3','4','5','6','7 哨兵']);px,pw=slots(f,7,325,'后继父亲');frames=[];answer=0;pos=6
    f.note(450,'先按原环计步，再找空格；7 是哨兵，越界后从 1 找。',size=19)
    for step in c.steps:
        s=step['facts'];answer=s.get('answer',answer);pos=s.get('pos',s.get('start',pos));objects=[]
        for n in s['occupied']:objects.append(obj('occupied:'+str(n),'rect',xs[n-1]-w/2,112,w=w,h=46,color=GRAY,fill='#d8dfe8',opacity=.65))
        if s.get('path'):pos=s['path'][-1]
        objects.append(obj('cursor','dot',xs[pos-1],208,r=10,color=GREEN,fill=PALE[GREEN]))
        objects.extend(box('parent:'+str(n),px[n-1],325,s['parent'][n],BLUE,pw) for n in range(1,8))
        objects.append(text('sum',32,390,f'累计标签和 {answer}；标签依次为 10、20、30、40、50、60。',size=19))
        frames.append(objects)
    finish(c,f,frames)

    return clips
