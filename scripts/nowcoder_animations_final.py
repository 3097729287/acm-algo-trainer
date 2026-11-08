"""Checked augmenting paths, circle-envelope changes, and native rolling traces."""
import json,math,subprocess
from PIL import Image
from nowcoder_animations import (ACTIVE,BLUE,DEAD,INK,MUTED,RED,SOFT,TEAL,
    RECORDS,OUT,ROOT,CONTENT,read,write,sha,canvas,text,wrap,box,save,attach)


def augmenting():
    edges=[(0,0),(0,1),(1,0)]
    states=[
        ([],[], '两行分别需要一个不同的列。合法边为1→A、1→B、2→A，先从空匹配开始。'),
        ([(0,0)],[], '先匹配第1行与A列。当前只有一条匹配边，第2行唯一能选的A列已经被占用。'),
        ([(0,0)],[(1,0)], '从第2行出发尝试A列，继续沿A列当前的匹配边，找到第1行。'),
        ([(0,0)],[(1,0),(0,0),(0,1)], '交替路为 第2行→A列→第1行→B列。B列空闲，已经找到可扩充的路径。'),
        ([(0,1),(1,0)],[], '沿交替路翻转：撤掉1→A，加入1→B和2→A。匹配数从1增加到2，答案Yes。')
    ]
    assert len(set(c for r,c in states[-1][0]))==2
    assert set(states[-1][0])<=set(edges)
    result=subprocess.run([str(OUT/'compiled/20472/main.exe')],input='1\n2\n1 1\n1 0',text=True,capture_output=True,check=True)
    assert result.stdout.strip()=='Yes'
    frames=[]
    for step,(matching,path,note) in enumerate(states):
        frame,draw=canvas('增广路：腾出已占列，匹配数才能继续增加',step,len(states),note)
        coordinate={(0,0):(270,168),(0,1):(270,338),(1,0):(620,168),(1,1):(620,338)}
        for r,c in edges:
            a=coordinate[0,r];b=coordinate[1,c]
            draw.line((a,b),fill=RED if (r,c) in path else TEAL if (r,c) in matching else '#c6d1de',
                      width=8 if (r,c) in path or (r,c) in matching else 3)
        for side in range(2):
            for i in range(2):
                x,y=coordinate[side,i];draw.ellipse((x-40,y-40,x+40,y+40),fill=ACTIVE if any((r==i if side==0 else c==i) for r,c in matching) else SOFT,outline=BLUE,width=3)
                text(draw,(x,y),str(i+1) if side==0 else 'AB'[i],28,INK,'mm')
        text(draw,(270,100),'行',23,MUTED,'mm');text(draw,(620,100),'列',23,MUTED,'mm')
        text(draw,(50,395),'绿色：当前匹配      红色：本次交替路',21,MUTED)
        frames.append(frame)
    save('augmenting-path',frames,[20472,20483],
         '两行两列的具体例子：第2行经已占用的A列找到第1行，再改配B列；翻转三条边后匹配数增加1。',
         {'matrix':[[1,1],[1,0]],'before':[[0,0]],'alternatingPath':[[1,0],[0,0],[0,1]],'after':[[0,1],[1,0]]})


def plates():
    discs=[(0,1),(2,1),(3,1),(1,1)]
    result=subprocess.run([str(OUT/'compiled/230850/main.exe')],input='4\n0 1\n2 1\n3 1\n1 1',text=True,capture_output=True,check=True)
    areas=list(map(float,result.stdout.split()))
    expected=[math.pi,2*math.pi,(14*math.pi+3*math.sqrt(3))/6,(4*math.pi+3*math.sqrt(3))/2]
    assert all(math.isclose(a,b,rel_tol=1e-11) for a,b in zip(areas,expected))
    colors=[BLUE,TEAL,RED,'#8753ac']
    frames=[]
    states=[0,1,2,3,4]
    for step,count in enumerate(states):
        note=('尚未放圆。每个圆的高度平方是−x²+L(x)，只需维护直线L的上包络。' if not count else
              f'放入圆心x={discs[count-1][0]}的半径1圆；新圆可能接管一段边界。此时总面积为{areas[count-1]:.6f}。')
        frame,draw=canvas('动态圆覆盖：只积分当前上包络获胜的圆弧',step,len(states),note)
        xy=lambda x,y:(110+(x+1)*130,260-y*130)
        draw.line((xy(-1.2,0),xy(4.2,0)),fill='#a8b8ca',width=2)
        for j,(x,r) in enumerate(discs[:count]):
            a=xy(x-r,r);b=xy(x+r,-r)
            draw.ellipse((*a,*b),fill='#e8eef5',outline=colors[j],width=2)
        winners=[]
        for i in range(650):
            x=-1+5*i/649
            heights=[r*r-(x-c)**2 for c,r in discs[:count]]
            if heights and max(heights)>=0:
                best=max(range(count),key=lambda j:heights[j]);y=math.sqrt(max(heights))
                sx,sy=xy(x,y);_,bottom=xy(x,-y)
                draw.line((sx,sy,sx,bottom),fill='#d3e7ed',width=2)
                draw.ellipse((sx-1,sy-1,sx+1,sy+1),fill=colors[best])
                draw.ellipse((sx-1,bottom-1,sx+1,bottom+1),fill=colors[best])
                winners.append(best)
        for j,(x,r) in enumerate(discs[:count]):
            sx,sy=xy(x,0);draw.ellipse((sx-4,sy-4,sx+4,sy+4),fill=colors[j])
            text(draw,(sx,414),f'x={x}',17,colors[j],'mm')
        text(draw,(805,135),'已放入的直线',20,MUTED,'mm')
        for j,(x,r) in enumerate(discs[:count]):
            text(draw,(805,185+j*48),f'L={2*x}x{r*r-x*x:+}',20,colors[j],'mm')
        if count:assert set(winners)<=set(range(count))
        frames.append(frame)
    save('circle-envelope-insertion',frames,[230850],
         '沿用原题四个半径1圆：按圆心0、2、3、1依次插入，彩色边界表示此刻获胜圆弧，面积与参考程序逐步一致。',
         {'discs':discs,'areas':areas,'referenceProgramSha256':read(CONTENT/'reviewed.json')['nowcoder-global::230850']['programSha256']})


def rolling():
    folder=OUT/'compiled/236487'
    source=(folder/'main.cpp').read_text(encoding='utf-8')
    marker='answer += h * best;'
    assert source.count(marker)==1
    trace=r'''cerr << setprecision(20) << pivot.x << ' ' << pivot.y << ' ' << head.x << ' ' << head.y << ' ' << tail.x << ' ' << tail.y << ' ' << best << ' ' << contact.x << ' ' << contact.y << ' ' << stop << '\n';'''
    traced=source.replace(marker,trace+'\n'+marker)
    (folder/'trace.cpp').write_text(traced,encoding='utf-8')
    subprocess.run(['g++','-std=c++17','-O2',str(folder/'trace.cpp'),'-o',str(folder/'trace.exe')],check=True,capture_output=True)
    result=subprocess.run([str(folder/'trace.exe')],input='2\n0.2 0.8\n1 1',text=True,capture_output=True,check=True)
    assert math.isclose(float(result.stdout),4.465554239614399,abs_tol=1e-10)
    events=[list(map(float,row.split())) for row in result.stderr.splitlines()]
    states=[];length=0
    for index,(px,py,hx,hy,tx,ty,angle,cx,cy,stop) in enumerate(events):
        assert math.isclose(math.hypot(hx-tx,hy-ty),1,abs_tol=1e-10)
        radius=math.hypot(hx-px,hy-py)
        note=(f'阶段{index+1}：支点({px:.2f},{py:.2f})，头臂长{radius:.3f}。头路程增加=头臂长×转角。')
        for k in range(5):
            theta=angle*k/4;c,s=math.cos(theta),math.sin(theta)
            rotate=lambda x,y:(px+(x-px)*c-(y-py)*s,py+(x-px)*s+(y-py)*c)
            head,tail=rotate(hx,hy),rotate(tx,ty)
            states.append(((px,py),head,tail,note,length+radius*theta,index))
        length+=radius*angle
        if not stop:
            assert cy<py+1e-10
            states.append(((cx,cy),states[-1][1],states[-1][2],
                           '发生更低接触，支点切换。下一阶段要重新计算头臂长度；头在支点上时暂时不走路。',length,index))
    assert math.isclose(length,float(result.stdout),rel_tol=1e-11)
    assert abs(states[-1][1][1])<1e-10
    frames=[]
    xy=lambda p:(80+(p[0]+1.8)*180,408-p[1]*145)
    for step,(pivot,head,tail,note,distance,index) in enumerate(states):
        frame,draw=canvas('山坡滚动：转到下次接触，再切换最低支点',step,len(states),note)
        mountain=[(-2,0),(0,0),(.2,.8),(1,1)]
        draw.line([xy(p) for p in mountain],fill='#8a9a7a',width=5)
        draw.line((xy(tail),xy(head)),fill=BLUE,width=8)
        groups=[]
        for p,label,color in [(tail,'尾',MUTED),(head,'头',RED),(pivot,'支点',TEAL)]:
            same=next((g for g in groups if math.dist(g[0],p)<1e-8),None)
            if same:same[1].append(label);same[2]=color
            else:groups.append([p,[label],color])
        for p,labels,color in groups:
            x,y=xy(p);draw.ellipse((x-7,y-7,x+7,y+7),fill=color);text(draw,(x+12,y-12),' / '.join(labels),18,color)
        text(draw,(700,123),'原题样例2',22,MUTED)
        text(draw,(700,176),f'阶段 {index+1}',25,BLUE)
        text(draw,(700,231),'头累计路程',21,MUTED)
        text(draw,(700,272),f'{distance:.6f}',26,TEAL)
        frames.append(frame)
    save('rolling-contact-events',frames,[236487],
         '按原题样例2与同一份参考程序的接触事件绘制：观察尾、头及支点的切换，并按各阶段头臂长度累加圆弧路程。',
         {'mountain':[[.2,.8],[1,1]],'events':events,'totalHeadDistance':length,
          'referenceProgramSha256':read(CONTENT/'reviewed.json')['nowcoder-global::236487']['programSha256']})


def run():
    augmenting();plates();rolling();attach()
    print(json.dumps({'newAnimations':len(RECORDS),'frames':sum(x['frames'] for x in RECORDS),'checked':True}))
    # Replace obsolete diagnostic sheets with previews of the actual final GIF files.
    records=read(CONTENT/'animations.json')
    sheet=Image.new('RGB',(940,150*len(records)),'white')
    for i,record in enumerate(records):
        with Image.open(ROOT/record['file']) as gif:
            gif.seek(min(gif.n_frames-1,gif.n_frames//2))
            sheet.paste(gif.convert('RGB').resize((261,150)),(0,150*i))
    sheet.save(OUT/'final-animations-contact.png')


if __name__=='__main__':run()
