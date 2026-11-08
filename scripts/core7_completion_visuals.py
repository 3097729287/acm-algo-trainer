"""Small animated SVGs of actual algorithm states, with a static motion fallback."""
import base64
import json
import xml.etree.ElementTree as ET
from html import escape


def text(x,y,value,size=20,color='#e2e8f0',anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(str(value))}</text>'


def cells(values,selected=(),x=36,y=120,width=64):
    out=''
    for i,value in enumerate(values):
        chosen=i in selected
        out+=f'<rect x="{x+i*width}" y="{y}" width="{width-8}" height="52" rx="8" fill="{"#115e59" if chosen else "#1e293b"}" stroke="{"#5eead4" if chosen else "#64748b"}"/>'
        out+=text(x+i*width+(width-8)/2,y+33,value,23,anchor='middle')
        out+=text(x+i*width+(width-8)/2,y+75,i+1,14,'#94a3b8','middle')
    return out


def animation(title,frames,static=0):
    n=len(frames);duration=4*n
    body=f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="310" viewBox="0 0 760 310"><title>{escape(title)}</title><desc>每四秒显示下一步；减少动态效果时显示静态关键帧。</desc><style>text{{font-family:Microsoft YaHei,Noto Sans CJK SC,sans-serif}}.static{{display:none}}@media(prefers-reduced-motion:reduce){{.motion{{display:none}}.static{{display:inline}}}}</style><rect width="760" height="310" rx="14" fill="#0f172a"/>'
    steps=[]
    for i,frame in enumerate(frames):
        plain=ET.fromstring('<g>'+frame+'</g>')
        caption=next((node.text for node in plain.iter('text') if node.text),f'第 {i+1} 步')
        still=f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="310" viewBox="0 0 760 310"><title>{escape(title)}</title><style>text{{font-family:Microsoft YaHei,Noto Sans CJK SC,sans-serif}}</style><rect width="760" height="310" rx="14" fill="#0f172a"/>'+text(26,37,title,22,'#f8fafc')+frame+text(715,288,f'{i+1}/{n}',15,'#94a3b8','end')+'</svg>'
        steps.append({'caption':caption,'duration':4000,'image':'data:image/svg+xml;base64,'+base64.b64encode(still.encode()).decode()})
    body+='<metadata id="tb-editorial-motion">'+escape(json.dumps({'version':1,'title':title,'steps':steps},ensure_ascii=False))+'</metadata>'
    body+=text(26,37,title,22,'#f8fafc')
    for i,frame in enumerate(frames):
        values=['1' if j==i else '0' for j in range(n)]+['1' if i==0 else '0']
        times=[str(j/n) for j in range(n+1)]
        body+=f'<g class="motion" opacity="{1 if i==0 else 0}"><animate attributeName="opacity" dur="{duration}s" repeatCount="indefinite" calcMode="discrete" values="{";".join(values)}" keyTimes="{";".join(times)}"/>{frame}{text(715,288,f"{i+1}/{n}",15,"#94a3b8","end")}</g>'
    body+=f'<g class="static">{frames[static]}</g></svg>'
    return body


def attach(entries):
    def put(pid,name,title,frames,explanation,static=0):
        entry=entries.get(pid)
        key='assets/'+name
        if not entry or key in entry.images:return
        svg=animation(title,frames,static)
        entry.images[key]='data:image/svg+xml;base64,'+base64.b64encode(svg.encode('utf8')).decode()
        entry.explanation+='\n\n'+explanation+f'\n\n![{title}]({key})'
        entry.overview+='\n\n'+explanation+f'\n\n![{title}]({key})'

    frames=[]
    for label,stack,state,highlight in [
        ('读入 a：匹配长度 1','a',1,()),
        ('再读入 a：失配回退后仍匹配 a','aa',1,()),
        ('读入 b：匹配到 ab','aab',2,(1,2)),
        ('读入 a：末尾 aba 已完整匹配','aaba',3,(1,2,3)),
        ('删除末尾 aba，恢复剩余栈顶的状态','a',1,()),
        ('读入 b、a，再次形成 aba','aba',3,(0,1,2)),
        ('再次删除，字符栈为空','',0,())]:
        frame=text(28,76,label)+text(28,105,'原串 aababa，删除模式 aba',16,'#94a3b8')
        frame+=cells(stack,highlight)+text(28,244,f'当前 KMP 匹配长度：{state}',20,'#5eead4')
        if not stack:frame+=text(58,154,'空栈',22,'#94a3b8')
        frames.append(frame)
    put('P4824','stack-kmp.svg','删除后为什么要恢复栈顶状态',frames,
        '看原串 aababa、模式 aba：第一次删掉末尾 aba 后，栈里还剩 a，匹配长度应恢复为 1；后面读入 ba 会再次删除。若错误地清零，就会漏掉第二次匹配。',4)

    frames=[]
    for values,selected,caption in [
        ('LLLLLL',(0,),'初始全为 L，最长交替段长度 1'),
        ('LRLLLL',(0,1,2),'翻转第 2 位，最长交替段长度 3'),
        ('LRLRLL',(0,1,2,3,4),'再翻转第 4 位，最长交替段长度 5'),
        ('LRLRLR',(0,1,2,3,4,5),'再翻转第 6 位，最长交替段长度 6')]:
        frames.append(text(28,83,caption)+cells(values,selected)+text(28,244,'相邻字符不同，左右两段才允许跨界拼接。',18,'#5eead4'))
    put('P6492','alternation.svg','单点翻转怎样改变交替区间',frames,
        '以六个 L 为例，依次翻转位置 2、4、6，最长交替段从 1 变为 3、5、6。亮起的格子是当前一段最长合法子串；合并节点时只需判断中间两字符是否不同。',2)

    frames=[]
    for root,contributions,total,caption in [
        (0,(6,1),7,'根在 1：两条边分别影响 2 个点、1 个点'),
        (1,(3,1),4,'根移到 2：边 1—2 的影响点数从 2 变成 1'),
        (2,(3,2),5,'根移到 3：边 2—3 的影响点数从 1 变成 2')]:
        frame=text(28,78,caption,18)
        for i in range(2):frame+=f'<path d="M {145+i*230} 148 H {335+i*230}" stroke="#64748b" stroke-width="3"/>'+text(240+i*230,125,f'异或边权 {3 if i==0 else 1}',16,'#cbd5e1','middle')+text(240+i*230,207,f'贡献 {contributions[i]}',18,'#5eead4','middle')
        for i,v in enumerate([1,2,3]):
            frame+=f'<circle cx="{125+i*230}" cy="148" r="25" fill="{"#0f766e" if i==root else "#334155"}" stroke="#94a3b8"/>'+text(125+i*230,155,v,22,anchor='middle')
        frame+=text(28,265,f'当前根：{root+1}；总代价：{total}',21,'#5eead4');frames.append(frame)
    put('CF1882D','reroot-xor.svg','换根时只有跨过的这条边改变贡献',frames,
        '三点链的点值为 1、2、3，两条边权为 3 与 1。根从 1 移到 2，再移到 3，总代价依次为 7、4、5；动图中仅跨过的那条边改变乘上的点数。',1)

    frames=[]
    for caption,active,pairs,count in [
        ('前缀区间 [0,1]：有一对差为 1',(0,1),[(0,1)],1),
        ('向右加入前缀 0：没有新增的早期 −1',(0,1,2),[(0,1)],1),
        ('向右加入前缀 2：与早期前缀 1 配对',(0,1,2,3),[(0,1),(1,3)],2),
        ('移走最左前缀 0：删除它到前缀 1 的配对',(1,2,3),[(1,3)],1)]:
        frame=text(28,80,caption,18)+text(28,110,'原数组 [1, −1, 2]，k=1，前缀值如下',16,'#94a3b8')
        frame+=cells([0,1,0,2],active,x=80,y=145,width=130)
        for a,b in pairs:frame+=f'<path d="M {108+130*a} 143 Q {108+65*(a+b)} {105-15*(b-a)} {108+130*b} 143" fill="none" stroke="#5eead4" stroke-width="2"/>'
        frame+=text(28,264,f'符合下标先后且前缀差为 1 的配对数：{count}',20,'#5eead4');frames.append(frame)
    put('CF877F','mo-prefix.svg','莫队的左右端点为什么用不同配对公式',frames,
        '例如数组 [1,−1,2]，前缀为 [0,1,0,2]，k=1。向右加入 2，要找较早的 1；移走最左的 0，要删除它与较晚的 1 的配对。下标先后决定减法方向，不能按无序值对计数。',3)

    frames=[]
    for caption,root,left,right,bits in [
        ('初始：八盏灯全部熄灭',(0,0),(0,0),(0,0),'00000000'),
        ('翻转 [1,8]：根节点直接翻转并挂标记',(8,1),(0,0),(0,0),'11111111'),
        ('查询 [1,4]：先下传，两个孩子各亮四盏',(8,0),(4,1),(4,1),'11111111'),
        ('再翻转 [1,4]：左孩子的两次翻转抵消',(4,0),(0,0),(4,1),'00001111')]:
        frame=text(28,76,caption,18)
        for x,y,label,value in [(286,92,'[1,8]',root),(105,160,'[1,4]',left),(468,160,'[5,8]',right)]:
            frame+=f'<rect x="{x}" y="{y}" width="180" height="49" rx="8" fill="#1e293b" stroke="#64748b"/>'+text(x+90,y+20,label,15,'#94a3b8','middle')+text(x+90,y+41,f'亮 {value[0]}，标记 {value[1]}',17,'#5eead4','middle')
        frame+=f'<path d="M 330 141 L 195 160 M 422 141 L 558 160" stroke="#64748b" fill="none"/>'+text(28,260,'实际灯态：'+' '.join(bits),21,'#e2e8f0');frames.append(frame)
    put('P2846','lazy-flip.svg','整段翻转与延迟下传',frames,
        '动图中，整段翻转后根节点已经正确，孩子仍保留旧值；只有查询左半时才下传。再翻转左半，它的待翻转标记从 1 异或为 0，说明两次翻转抵消。',2)

    frames=[]
    boards=['oooo****--','ooo--***o*','ooo*o**--*','o--*o**oo*','o*o*o*--o*','--o*o*o*o*']
    moves=['初始：四白、四黑、两个空位','移动第 4、5 格到空位','移动第 8、9 格到空位','移动第 2、3 格到空位','移动第 7、8 格到空位','移动第 1、2 格，完成交替']
    for label,board in zip(moves,boards):
        frames.append(text(28,78,label,19)+cells(board,tuple(i for i,c in enumerate(board) if c=='-'),width=68)+text(28,258,'每次移动一对相邻棋子，左右次序保留。',18,'#94a3b8'))
    put('P1259','paired-pieces.svg','四对棋子的五步收尾',frames,'这里逐帧重放四对棋子的固定收尾，编号与代码中的 move 参数一致。空位用绿色标出，前后完整状态可以暂停核对。',5)

    frames=[]
    for label,values,selected,note in [
        ('原串 abaa，尝试移位 d=1',list('abaa'),(),'三条比较边：a≠b，b≠a，a=a'),
        ('首末失配为 l=0、r=1',list('abaa'),(0,1,2),'两条失配相邻，共用位置 1 的字符 b。'),
        ('两外端都是 a，修改中间 b 为 a',list('aaaa'),(1,),'共同顶点改一次，两条失配同时消失。'),
        ('前缀 aaa 等于后缀 aaa',list('aaaa'),(0,1,2,3),'真 border 长度 n−d=3。')]:
        frames.append(text(28,78,label,20)+cells(values,selected,x=90,width=120)+text(28,257,note,19,'#94a3b8'))
    put('P13790','border-one-edit.svg','一次修改修复两条相邻比较',frames,'以样例 abaa 为例，比较距离为一的字符。两条失配共享 b，且它两边均为 a，因此只改这个共享位置即可得到长度三的 border。',2)

    frames=[]
    for caption,values,count in [
        ('原排列 [2,1,3]，阈值 m=4',[2,1,3],1),
        ('新最大值 4 插在最左空隙',[4,2,1,3],2),
        ('插进原来的坏边 2+1',[2,4,1,3],3),
        ('插进原来的好边 1+3',[2,1,4,3],2),
        ('插在最右空隙',[2,1,3,4],2)]:
        frame=text(28,78,caption,19)+cells(values,tuple(i for i,x in enumerate(values) if x==4),x=84,width=130)
        sums=[f'{a}+{b}={a+b}' for a,b in zip(values,values[1:])]
        frame+=text(28,242,'相邻和：'+'，'.join(sums),18,'#94a3b8')+text(28,275,f'好边数量 {count}；原好边数 j=1。',18,'#5eead4');frames.append(frame)
    put('CF1909I','good-edge-insertion.svg','插入最大值时，好边数如何改变',frames,'固定阈值四，从 [2,1,3] 的一条好边开始。四个空隙中，三个使好边数加一，一个使好边数加二，分别验证转移系数 j+2 与 i−1−j。',2)

    frames=[]
    for caption,bits,selected,left,right in [
        ('初始两半，逆序数分别 1 和 3',[0,0,0,1,0,1,0,0,0,1],(),1,3),
        ('选中中线两侧相邻的 0、1',[0,0,0,1,0,1,0,0,0,1],(4,5),1,3),
        ('交换一次，两半逆序数均为零',[0,0,0,1,1,0,0,0,0,1],(4,5),0,0)]:
        frame=text(28,78,caption,19)+cells(bits,selected,width=68)
        frame+=f'<path d="M 371 111 V 202" stroke="#fbbf24" stroke-width="3"/>'+text(28,258,f'左半逆序 {left}，右半逆序 {right}，差 Δ={left-right}。',19,'#5eead4');frames.append(frame)
    put('P5426','central-inversion-swap.svg','跨中线交换对逆序差的影响',frames,'样例中把中线的 01 换成 10，只需一次交换便使两半逆序数相等。跨中线操作可能同时改变两侧逆序数，计算时使用推导的固定差值。',2)

    frames=[]
    for caption,lights,result in [
        ('事件 1：打开灯 2',[0,1,0],'版本 1：仅灯 2 开启。'),
        ('事件 2：打开灯 3',[0,1,1],'版本 2：灯 2、3 开启。'),
        ('事件 3：查询点 2，同深度距离 2',[0,1,1],'唯一候选是点 3，答案 1。'),
        ('事件 4：回到事件 1 后的状态',[0,1,0],'新版本继承版本 1，灯 3 关闭。'),
        ('事件 5：再次查询点 2，同深度距离 2',[0,1,0],'候选点 3 当前关闭，答案 0。')]:
        frame=text(28,77,caption,18)
        points={1:(370,120),2:(240,201),3:(500,201)}
        frame+='<path d="M 370 120 L 240 201 M 370 120 L 500 201" stroke="#64748b" fill="none"/>'
        for v,(x,y) in points.items():
            frame+=f'<circle cx="{x}" cy="{y}" r="26" fill="{"#115e59" if lights[v-1] else "#1e293b"}" stroke="#5eead4"/>'+text(x,y+8,v,22,anchor='middle')
        frame+=text(28,271,result,19,'#94a3b8');frames.append(frame)
    put('P7394','history-versions.svg','回到历史版本后的灯状态',frames,'示例树是一号点连接二、三号点。两个孩子同深度，距离二。逐帧保留事件编号，展示回到旧版本如何改变随后查询的结果。',3)
