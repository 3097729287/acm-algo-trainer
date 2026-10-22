"""Accurate, portable SVG diagrams for the from-zero lessons.

All coordinates and displayed quantities come from the small examples in the
Markdown sources. No generated bitmap or external font is required.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'foundations' / 'assets'
INK, BLUE, RED, GREEN, GRAY = '#243449', '#2365ab', '#bc3645', '#12805c', '#68778b'


class Figure:
    def __init__(self, title, height=350, width=760):
        self.width, self.height = width, height
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title"><title id="title">{escape(title)}</title>',
                      '<rect width="100%" height="100%" rx="12" fill="#fff"/>',
                      '<g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" fill="#243449">']
        self.text(28, 36, title, size=23, weight='bold')

    def text(self, x, y, text, color=INK, size=21, anchor='start', weight='normal'):
        self.parts.append(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(text))}</text>')

    def line(self, x1, y1, x2, y2, color=GRAY, dash=False, width=3):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="7 5"' if dash else '')+'/>')

    def circle(self, x, y, label='', color=BLUE, radius=23):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="#fff" stroke="{color}" stroke-width="3"/>')
        if label != '': self.text(x, y+7, label, color, anchor='middle')

    def box(self, x, y, w, h, text, color=BLUE, fill='#edf5ff', size=21):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="{color}" stroke-width="2"/>')
        self.text(x+w/2, y+h/2+7, text, color, size, 'middle')

    def row(self, values, y, x=145, width=76, colors=None):
        for i, value in enumerate(values):
            color = (colors or {}).get(i, BLUE)
            self.box(x+i*width, y, width-3, 48, value, color)

    def save(self, name, directory=OUT):
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (name+'.svg')
        path.write_text('\n'.join(self.parts+['</g></svg>'])+'\n', encoding='utf-8')
        return path


def draw():
    f = Figure('二分返回边界位置；边界前的格子数是数量', 310)
    f.row([1,2,2,2,5,8], 105, x=115, width=92, colors={1:RED,2:RED,3:RED})
    for i in range(7): f.text(115+i*92, 88, i, GRAY, size=18, anchor='middle')
    f.text(690,137,'end',GRAY,size=18)
    for index,label,color in [(1,'lower_bound(2) = 1',GREEN),(4,'upper_bound(2) = 4',RED)]:
        x=115+index*92;f.line(x,155,x,210,color);f.text(x,240,label,color,size=20,anchor='middle')
    f.text(35,284,'< 2：1 个      ≤ 2：4 个      = 2：4 − 1 = 3 个',size=22)
    f.save('bounds')

    f=Figure('lambda：捕获来自定义处，参数来自每次调用',330)
    f.box(30,90,205,65,'threshold = 10',GREEN)
    f.box(300,85,420,105,'[threshold](int value)',BLUE)
    f.line(235,120,295,120,GREEN)
    f.box(30,235,205,58,'enough(12)',RED)
    f.line(235,260,320,190,RED)
    f.text(360,225,'判断 12 ≥ 10',BLUE)
    f.text(360,275,'返回 true',GREEN)
    f.save('lambda')

    f=Figure('逐位比较：5 = 0101，3 = 0011',370)
    for i,(label,bits) in enumerate([('5',[0,1,0,1]),('3',[0,0,1,1]),('AND → 1',[0,0,0,1]),('OR → 7',[0,1,1,1]),('XOR → 6',[0,1,1,0])]):
        y=65+i*55;f.text(30,y+31,label,size=20);f.row(bits,y,x=255,width=95)
    f.save('bits')

    f=Figure('区间和：整段减掉多算的前缀',315)
    f.row([2,3,1,4],95,x=200,width=120)
    f.text(45,128,'a',size=22)
    f.line(200,165,677,165,BLUE,width=7);f.text(400,200,'S₄ = 10',BLUE,anchor='middle')
    f.line(200,225,317,225,RED,width=7);f.text(200,265,'减去 S₁ = 2',RED)
    f.line(320,225,677,225,GREEN,width=7);f.text(510,265,'留下 3 + 1 + 4 = 8',GREEN,anchor='middle')
    f.save('prefix')

    f=Figure('区间加三：开始位置 +3，结束后一位 −3',330)
    f.text(35,105,'差分事件');f.row([0,'+3',0,0,'−3'],75,x=205,width=96,colors={1:GREEN,4:RED})
    f.text(35,205,'前缀累计');f.row([0,3,3,3,0],175,x=205,width=96)
    f.text(70,285,'只有第 2、3、4 位保留额外的三',GREEN)
    f.save('difference')

    f=Figure('二分答案：最小可行容量是五',280)
    f.row([2,3,4,5,6,7],90,x=90,width=100,colors={0:RED,1:RED,2:RED,3:GREEN,4:GREEN,5:GREEN})
    for i in range(6): f.text(137+i*100,175,'不行' if i<3 else '可行',RED if i<3 else GREEN,anchor='middle')
    f.line(387,80,387,205,GRAY,dash=True)
    f.text(80,247,'13 件物品，3 个容器；判定：ceil(13 / c) ≤ 3',size=22)
    f.save('binary-answer')

    f=Figure('DP：当前答案来自已经算好的子问题',290)
    f.box(75,85,180,60,'f₂ = 2');f.box(425,85,180,60,'f₃ = 3')
    f.box(240,205,270,60,'f₄ = 2 + 3 = 5',GREEN)
    f.line(165,145,320,205);f.line(515,145,430,205)
    f.save('dp')

    f=Figure('0/1 背包：比较两个独立的候选装法',360)
    f.box(25,90,325,65,'旧容量 5：选 A，价值 7')
    f.box(405,90,325,65,'旧容量 3：选 B，价值 5')
    f.text(420,205,'加 C：重量 2，价值 3',RED,size=21)
    f.line(185,155,290,265,BLUE);f.line(565,155,490,265,RED)
    f.box(175,265,410,65,'新容量 5：max(7, 5+3) = 8',GREEN)
    f.save('knapsack')

    f=Figure('贪心交换：更早结束留下更多可用时间',300)
    for y,l,r,label,color in [(105,110,370,'原首项',RED),(190,110,270,'替换后首项',GREEN)]:
        f.line(l,y,r,y,color,width=10);f.text(30,y+7,label,color,size=19)
        f.line(r+15,y,690,y,GRAY,dash=True);f.text(520,y-20,'后续可使用的时间',GRAY,size=19,anchor='middle')
    f.text(90,270,'替换不减少后续可接活动，已选数量保持不变',size=22)
    f.save('greedy')

    f=Figure('两端配对：每个编号恰用一次',330)
    f.row([1,2,3,4,5,6],220,x=90,width=100)
    for level,(l,r) in enumerate([(0,5),(1,4),(2,3)]):
        y=85+level*48;x1=138+l*100;x2=138+r*100
        f.line(x1,220,x1,y,BLUE);f.line(x1,y,x2,y,BLUE);f.line(x2,y,x2,220,BLUE)
        f.text((x1+x2)/2,y-10,'和为 7',GREEN,size=19,anchor='middle')
    f.save('construction')

    f=Figure('有序对到无序组：每组恰好数了两遍',300)
    for i,(top,low,label) in enumerate([('AB','BA','{A,B}'),('AC','CA','{A,C}'),('BC','CB','{B,C}')]):
        x=45+i*240;f.box(x,90,95,48,top);f.box(x+110,90,95,48,low);f.text(x+100,220,label,GREEN,anchor='middle');f.line(x+100,145,x+100,185)
    f.text(125,275,'6 个有序方案 ÷ 2 = 3 个无序小组',size=23)
    f.save('counting')

    f=Figure('非负数组窗口：加右项，超限才移左项',300)
    f.row([2,1,3,2],90,x=200,width=120)
    f.text(200,185,'原窗口 [1,3]：和 4',BLUE)
    f.text(200,225,'加右侧 2：和 6；移走左侧 1',RED)
    f.text(200,265,'新窗口 [3,2]：和 5',GREEN)
    f.save('two-pointers')

    f=Figure('BFS 按层到达；DFS 沿分支深入',360)
    for (u,v) in [((370,95),(210,190)),((370,95),(540,190)),((210,190),(210,285))]:f.line(*u,*v)
    for x,y,label in [(370,95,0),(210,190,1),(540,190,2),(210,285,3)]:f.circle(x,y,label)
    f.text(590,105,'距离 0',GREEN);f.text(590,200,'距离 1',GREEN);f.text(420,295,'距离 2',GREEN)
    f.text(30,340,'BFS：0 → 1,2 → 3      DFS 可为：0 → 1 → 3 → 2',size=21)
    f.save('graphs')

    f=Figure('并查集：父指针最终指向同一代表',290)
    for x in [140,380,620]:f.circle(x,115,{140:0,380:1,620:2}[x])
    f.line(356,115,164,115);f.line(596,115,404,115)
    f.text(375,190,'2 → 1 → 0；三个点属于同一组',anchor='middle')
    f.text(375,245,'压缩后 2 直接指向 0，组内关系不变',GREEN,anchor='middle')
    f.save('dsu')

    f=Figure('树状数组：前六项拆成两个不重叠块',300)
    f.row([1,2,3,4,5,6],90,x=90,width=100)
    f.line(90,175,485,175,BLUE,width=8);f.text(290,215,'tree[4]：第 1 至 4 项',BLUE,anchor='middle')
    f.line(490,175,685,175,GREEN,width=8);f.text(588,250,'tree[6]：第 5、6 项',GREEN,anchor='middle')
    f.text(40,280,'6 − lowbit(6) = 4；4 − lowbit(4) = 0',size=20)
    f.save('fenwick')

    f=Figure('线段树：节点代表区间，父亲合并孩子',350)
    for u,v in [((380,95),(210,185)),((380,95),(550,185)),((210,185),(125,280)),((210,185),(295,280)),((550,185),(465,280)),((550,185),(635,280))]:f.line(*u,*v)
    for x,y,label in [(380,95,'10'),(210,185,'5'),(550,185,'5'),(125,280,'2'),(295,280,'3'),(465,280,'1'),(635,280,'4')]:f.circle(x,y,label)
    f.text(380,335,'[2,3,1,4]：根的 10 = 左半 5 + 右半 5',anchor='middle',size=22)
    f.save('segment-tree')

    f=Figure('叉积：有向 AB 左侧为正，面积取绝对值',340)
    A=(150,265);B=(595,265);C=(300,90)
    f.line(*A,*B,BLUE);f.line(*A,*C,GREEN);f.line(*B,*C,GRAY,dash=True)
    for p,label in [(A,'A (0,0)'),(B,'B (3,0)'),(C,'C (1,2)')]:f.circle(*p,radius=5);f.text(p[0],p[1]+32,label,anchor='middle')
    f.text(400,185,'AB × AC = 3×2 − 0×1 = 6',size=20,anchor='middle')
    f.text(400,220,'三角形面积 = 6 / 2 = 3',GREEN,size=21,anchor='middle')
    f.save('geometry')

    f=Figure('最短路：直接费用五，经 b 只需三',330)
    for p,q,w in [((120,160),(630,160),5),((120,160),(380,265),1),((380,265),(630,160),2)]:
        f.line(*p,*q);f.text((p[0]+q[0])/2,(p[1]+q[1])/2-15,w,RED,size=23)
    for x,y,label in [(120,160,'s'),(630,160,'a'),(380,265,'b')]:f.circle(x,y,label)
    f.text(245,85,'dist[a]：5 → 1+2 = 3',GREEN,size=23)
    f.save('shortest-path')

    f=Figure('树：定根后父子关系与子树范围',350)
    for u,v in [((380,90),(210,180)),((380,90),(550,180)),((210,180),(130,280)),((210,180),(290,280))]:f.line(*u,*v)
    f.parts.append('<rect x="78" y="142" width="270" height="175" rx="24" fill="#e7f6ed" fill-opacity="0.6" stroke="#12805c" stroke-dasharray="7 4"/>')
    for x,y,l in [(380,90,0),(210,180,1),(550,180,2),(130,280,3),(290,280,4)]:f.circle(x,y,l)
    f.text(405,280,'子树 1 包含 1、3、4',GREEN,size=22)
    f.save('trees')

    f=Figure('单调栈：遇到三，依次解决一和二',270)
    f.row([2,1,3],85,x=210,width=115)
    f.text(150,195,'3 > 1：弹出 1，答案是当前位置',GREEN)
    f.text(150,235,'3 > 2：弹出 2，答案也是当前位置',GREEN)
    f.save('monotonic')

    f=Figure('Trie：路径存前缀，结束标记另外保存',360)
    for u,v in [((380,90),(380,180)),((380,180),(220,280)),((380,180),(540,280))]:f.line(*u,*v)
    for x,y,l in [(380,90,'根'),(380,180,'a'),(220,280,'b'),(540,280,'c')]:f.circle(x,y,l)
    f.text(425,185,'a 在这里结束',GREEN,size=20)
    f.text(180,335,'ab 结束',GREEN,size=20);f.text(500,335,'ac 结束',GREEN,size=20)
    f.save('trie')

    f=Figure('置换 p=[2,0,1,4,3] 的两个环',310)
    f.text(170,100,'0 → 2 → 1 → 0',BLUE,size=27)
    f.text(440,210,'3 → 4 → 3',GREEN,size=27)
    f.text(90,265,'环长三与二；每个编号恰在一个环中',size=23)
    f.save('permutations')
    return coverage()


def coverage():
    intervals=[('A',1,3),('B',2,4),('C',1,7),('D',3,5),('E',4,8),('F',5,6),('G',6,8),('H',7,9)]
    f=Figure('闭区间覆盖 x=5：先计入 6 条，再扣掉 2 条',675)
    x=lambda v:120+(v-1)*65
    f.line(x(5),75,x(5),520,RED,dash=True,width=2)
    f.text(x(5),70,'查询 x=5',RED,size=20,anchor='middle')
    for i,(label,l,r) in enumerate(intervals):
        y=112+i*49
        ended=r<5;cover=l<=5<=r;color=GREEN if ended else RED if cover else GRAY
        f.text(25,y+7,label,size=21)
        f.line(x(l),y,x(r),y,color,width=6)
        for v in [l,r]:
            f.parts.append(f'<circle cx="{x(v)}" cy="{y}" r="6" fill="{color}"/>')
        state='已结束' if ended else '覆盖 x' if cover else '未开始'
        f.text(675,y+7,state,color,size=19)
        if label=='D':f.text(x(5)-12,y-13,'r=x，仍覆盖',RED,size=18,anchor='end')
        if label=='F':f.text(x(5)+12,y-13,'l=x，已开始',RED,size=18)
    axis=535;f.line(x(1)-15,axis,x(9)+15,axis)
    for i in range(1,10):
        f.line(x(i),axis-5,x(i),axis+5);f.text(x(i),axis+30,i,anchor='middle',size=19)
    f.text(35,602,'l ≤ x：A、B、C、D、E、F，共 6 条',RED,size=22)
    f.text(35,635,'r < x：A、B，共 2 条；留下 C、D、E、F',GREEN,size=22)
    path=f.save('interval-coverage')
    assert sum(l<=5 for _,l,r in intervals)==6
    assert sum(r<5 for _,l,r in intervals)==2
    assert sum(l<=5<=r for _,l,r in intervals)==4
    return path


if __name__=='__main__':
    draw()
    print('Generated 23 SVG illustrations from checked lesson examples.')
