"""Concrete flow, schedule, graph and position examples for the greedy unit."""
import base64
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import OUT

def attach_figures(specs):
    figures={};history={}
    def save(pid,figure,caption,filename=None):
        filename=filename or pid
        path=figure.save(filename,OUT/'figures');key='assets/core7/'+filename+'.svg'
        if pid in figures:
            old_key,old_data,_=figures[pid];history.setdefault(pid,{})[old_key]=old_data
        figures[pid]=(key,'data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode(),caption)

    f=Figure('四堆平均十张：三条分界线的前缀差都非零',330)
    f.row([9,8,17,6],90,x=110,width=145)
    for x,label in [(255,'少 1'),(400,'少 3'),(545,'多 4')]:
        f.line(x,155,x,220,RED,dash=True);f.text(x,255,label,RED,size=22,anchor='middle')
    f.text(60,310,'这些线都至少跨一次；次数为 3，不是搬牌张数 8',size=21)
    save('P1031',f,'前缀总数分别为九、十七、三十四，目标为十、二十、三十；对应差为负一、负三、正四。')

    def frog_diagram(height,footer_y):
        f=Figure('高度三、五、六：按 0→6→3→5 跳，共耗 49',height)
        points=[(120,290),(290,80),(460,185),(630,115)]
        for i in range(3):f.line(*points[i],*points[i+1],BLUE)
        for (x,y),value in zip(points,[0,6,3,5]):f.circle(x,y,value);f.text(x,y+48,'地面' if value==0 else '高度 '+str(value),size=17,anchor='middle')
        for x,y,cost in [(180,160,36),(360,110,9),(545,125,4)]:f.text(x,y,'耗 '+str(cost),GREEN,size=21,anchor='middle')
        f.text(95,footer_y,'每段计高度差的平方：36+9+4=49',size=22)
        return f
    caption='点的纵向高度对应零、六、三、五；连线表示先后跳跃，不能把画面线段长度直接当体力。'
    save('P4995',frog_diagram(370,345),caption)
    save('P4995',frog_diagram(405,380),caption,filename='P4995-readable')

    f=Figure('给定零把 1、2、3 连通；给定一的边赋零',350)
    points=[(125,130),(290,250),(455,130),(650,130)]
    for a,b in [(0,1),(1,2),(0,2)]:f.line(*points[a],*points[b],BLUE)
    f.line(*points[2],*points[3],RED,width=5)
    for i,(x,y) in enumerate(points):f.circle(x,y,i+1,BLUE if i<3 else RED)
    for x,y in [(180,190),(370,190),(290,113)]:f.text(x,y,'权 1',BLUE,size=20,anchor='middle')
    f.text(550,113,'权 0',RED,size=20,anchor='middle')
    f.text(65,305,'前三点有正边路径，最小 mex=0；3 到 4 最小 mex=1',size=20)
    save('P12041',f,'蓝边权为一，红边权为零；数字标的是顶点，边上的权值与输入给定的最小 mex 不是同一个量。')

    f=Figure('目标 BWWW：叶子要求中心原色 W，中心要多数 B',390)
    center=(380,125);leaves=[(200,280),(380,280),(560,280)]
    for point in leaves:f.line(*center,*point,GRAY)
    f.circle(*center,'W',GREEN);f.text(380,90,'点 1，目标 B',size=20,anchor='middle')
    for i,(x,y) in enumerate(leaves,2):f.circle(x,y,'B',BLUE);f.text(x,y+45,'点 '+str(i)+'，目标 W',size=18,anchor='middle')
    f.text(75,375,'操作前 WBBB → 邻居取多数 → 操作后 BWWW',size=22)
    save('AT_arc161_c',f,'圆内是操作前颜色，旁边是目标色；中心看三个 B，叶子各只看中心的 W。')

    f=Figure('目标 4：保留 3，让剩余区间先得到 5',485)
    for y,row,label in [(85,[3,4,5,6],'初始'),(185,[3,5,5],'选位置 1、3'),(285,[3,5],'选位置 1、2'),(385,[4],'选位置 0、1')]:
        for i in range(len(row)):f.text(295+i*95,y-8,str(i),GRAY,size=16,anchor='middle')
        f.text(45,y+31,label,size=20);f.row(row,y,x=250,width=95)
    f.text(60,465,'上方小字是当前下标；删掉数后必须重新编号',size=21)
    save('B4225',f,'先把四和六合成五，再合并两个五，最后将三与五平均成四；位置始终按当前序列计算。')

    f=Figure('同样占用槽 3、4、5，让增量集中在一个元素',395)
    f.text(180,80,'先到者先放',size=22,anchor='middle');f.text(550,80,'后到者先放',size=22,anchor='middle')
    for x,rows in [(70,[(3,3,0),(4,3,1),(5,4,1)]),(440,[(3,3,0),(4,4,0),(5,3,2)])]:
        for i,(slot,original,delta) in enumerate(rows):
            y=105+i*65;f.text(x,y+31,'槽 '+str(slot),size=19);f.box(x+75,y,90,48,'原 '+str(original),GREEN if delta==0 else RED,size=20);f.text(x+190,y+31,'增 '+str(delta),size=20)
    f.text(40,345,'增量 1、1、0 配费用 1、2、3：3',size=17)
    f.text(410,345,'增量 2、0、0 配费用 1、2、3：2',size=17)
    f.text(70,382,'费用允许重排，大增量配小费用；两边最终数值相同',size=21)
    save('P6155',f,'每个框是原数被放入某个最终数值槽；两套方案都得到三、四、五，但后一套费用更低。')

    f=Figure('三行五列：比较每个数字的位置，不是每列和',410)
    rows=[[1,2,3,4,5],[4,5,1,2,3],[3,5,2,4,1]]
    for c in range(5):f.text(235+c*80,85,'位置 '+str(c+1),size=17,anchor='middle')
    for r,row in enumerate(rows):
        y=105+r*65;f.text(70,y+31,'第 '+str(r+1)+' 行',size=20)
        for c,value in enumerate(row):f.box(200+c*80,y,74,48,value,GREEN if value==1 else GRAY,size=22)
    f.text(80,335,'数字 1：位置 1、3、5，合计 9',GREEN,size=22)
    f.text(80,385,'数字 2：位置 2、4、3，也合计 9',size=22)
    save('P12676',f,'绿色标出三个一；它们分属不同行，所在列号才是需要累加的位置。')

    for spec in specs:
        if spec.pid not in figures:continue
        spec.images.update(history.get(spec.pid,{}))
        key,data,caption=figures[spec.pid];spec.images[key]=data
        alt=caption.replace('[','［').replace(']','］')
        image='!['+alt+']('+key+')\n\n'+caption
        for name in ['brief','detail']:
            paragraphs=getattr(spec,name).split('\n\n',1)
            setattr(spec,name,paragraphs[0]+'\n\n'+image+('\n\n'+paragraphs[1] if len(paragraphs)>1 else ''))
