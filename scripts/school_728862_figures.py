"""Small diagrams drawn from the same concrete examples as the editorials."""
from html import escape

def text(x,y,s,size=20,color='#233348',anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(str(s))}</text>'
def line(x1,y1,x2,y2,color='#62748a',arrow=False,dash=False):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="3"'+(' marker-end="url(#arrow)"' if arrow else '')+(' stroke-dasharray="7 5"' if dash else '')+'/>'
def node(x,y,s,color='#2879b4',r=24):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="{color}" stroke-width="3"/>'+text(x,y+7,s,20,color,'middle')
def box(x,y,w,h,fill='#eef4f9',stroke='#7c91a5'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
def svg(title,body,h=320):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="780" height="{h}" viewBox="0 0 780 {h}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#62748a"/></marker></defs>
<rect width="780" height="{h}" rx="12" fill="#fff"/><g font-family="Microsoft YaHei,Segoe UI,sans-serif">{text(24,35,title,22)}{body}</g></svg>'''

def figures():
    result={}
    b=''
    for row,selected in enumerate([{0,1,2},{1,2,3}]):
        y=75+row*105
        b+=text(24,y+28,'原窗口' if row==0 else '右移后',18)
        for i,v in enumerate([1,2,6,1,1,7,1]):
            color='#e6f3e9' if i in selected else '#f6f7f9'
            border='#25834a' if i in selected else '#b0bcc8'
            if (row==0 and i==0) or (row==1 and i==3):color='#fff0dc';border='#b96b11'
            b+=box(130+76*i,y,62,48,color,border)+text(161+76*i,y+31,v,22,anchor='middle')+text(161+76*i,y+71,i+1,15,'#64748b','middle')
    b+=text(128,303,'橙色：移出 1 / 移入 1；绿色：窗口中的公共部分。',18)
    result['c-window.svg']=svg('固定长度为 3：只更新两端',b,330)
    b=''
    for i,(state,value,cut) in enumerate([(5,2,2),(4,2,3),(2,1,5)]):
        y=74+i*80
        b+=box(35,y,180,48)+text(125,y+31,f'dp[{state}] = {value}',21,anchor='middle')
        b+=line(230,y+24,493,178,arrow=True)+text(290,y+18,f'最后切 {cut}，段数 +1',18)
    b+=box(510,153,235,53,'#e6f3e9','#25834a')+text(627,187,'dp[7] = max(3,3,2)',19,anchor='middle')
    result['h-dp.svg']=svg('长度 7 的来源：允许切 2、3、5',b,330)
    b=line(95,280,95,60,arrow=True)+line(95,280,600,280,arrow=True)
    b+=text(78,62,'y',18)+text(604,302,'x',18)
    b+=line(180,240,180,110,'#b96b11',dash=True)+line(180,110,480,110,'#b96b11',dash=True)
    b+=node(180,240,'P')+node(480,110,'Q')+node(180,110,'新','#b96b11')
    b+=text(205,245,'(1,1)',19)+text(510,115,'(3,3)',19)+text(110,82,'新增 (1,3)',19,'#b96b11')
    b+=text(120,325,'P → 新雪堆 → Q；一次增加转弯点，合并两个连通块。',18)
    result['i-bridge.svg']=svg('雪堆：沿列滑行，再沿行滑行',b,355)
    b=text(30,78,'真实供电方案',19)+line(150,170,275,245)+line(275,245,350,115)
    b+=node(150,170,'1')+node(275,245,'2','#25834a')+node(350,115,'3')
    b+=text(180,198,'电线 10',17)+text(322,190,'电线 15',17)+text(220,292,'城市 2 建站：2',18,'#25834a')
    b+=text(435,78,'加入虚拟电源 0',19)+line(465,150,590,245,'#25834a')+line(490,300,590,245)+line(590,245,700,145)
    b+=node(465,150,'0','#25834a')+node(490,300,'1')+node(590,245,'2')+node(700,145,'3')
    b+=text(485,190,'建站边 2',17,'#25834a')+text(530,306,'10',17)+text(675,220,'15',17)
    b+=text(430,342,'三条边费用：2 + 10 + 15 = 27',18)
    result['j-power.svg']=svg('建站 = 连接虚拟顶点；电线 = 城市间连边',b,370)
    b=box(30,70,270,205,'#e6f3e9','#25834a')+text(55,104,'已加入 S',19,'#25834a')
    b+=node(110,200,'0')+node(225,160,'2')+node(570,120,'1')+node(570,245,'3')
    b+=line(249,155,546,124,'#b96b11')+line(249,169,546,240,'#62748a')
    b+=text(375,122,'10：本轮选择',18,'#b96b11')+text(370,229,'15：之后候选',18)
    b+=text(40,318,'best[1] = min(23,10)；best[3] = min(23,15)。',19)
    result['j-cut.svg']=svg('Prim：选择跨越 S 的最便宜边',b,345)
    b=text(28,83,'固定边：1 → 3、2 → 3；待定边：1 — 2、3 — 4。',20)
    b+='<path d="M126,154 C185,99 395,99 454,154" fill="none" stroke="#2879b4" stroke-width="3" marker-end="url(#arrow)"/>'
    for i in range(4):b+=node(110+i*180,176,str(i+1)) + text(110+i*180,229,f'位置 {i}',18,anchor='middle')
    b+=line(136,176,264,176,arrow=True)+line(316,176,444,176,arrow=True)+line(496,176,624,176,arrow=True)
    b+=text(45,285,'所有边都从较小位置走向较大位置，不可能沿边绕回起点。',20)
    result['k-order.svg']=svg('拓扑序：统一决定所有新增边的方向',b,320)
    b=''
    for row,(title,chosen,total) in enumerate([('加入第三本：超时',{0,1,2},6),('移走第一本：合法',{1,2},3),('再加入第四本',{1,2,3},4)]):
        y=69+row*85;b+=text(20,y+29,title,17)
        for i,v in enumerate([3,1,2,1]):
            b+=box(240+i*80,y,64,46,'#e6f3e9' if i in chosen else '#f6f7f9','#25834a' if i in chosen else '#a5b4c4')+text(272+i*80,y+30,v,22,anchor='middle')
        b+=text(590,y+30,f'总时间 {total}',19,'#b96b11' if total>5 else '#25834a')
    b+=text(240,350,'预算 t = 5；最终保留第 2、3、4 本，共 3 本。',18)
    result['l-books.svg']=svg('正数窗口：超时就从左端移走整本书',b,380)
    return result
