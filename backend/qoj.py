"""QOJ original HTML/PDF statements. Points are never a difficulty rating."""
import base64
from contextlib import closing
import hashlib
import io
import re
import threading
from urllib.parse import parse_qs,urljoin,urlsplit
from statement_format import Tree,classes,plain,markdown

PDF_LOCK=threading.RLock()  # PDFium forbids simultaneous calls across threads.

def _joined_lines(lines):
    """Join border pieces separated by a PDF stroke's small endpoint gap."""
    result=[]
    for axis,low,high in sorted(lines):
        if result and abs(result[-1][0]-axis)<.3 and low<=result[-1][2]+.8:
            previous=result[-1]
            result[-1]=(previous[0],min(previous[1],low),max(previous[2],high))
        else:result.append((axis,low,high))
    return result

def problem_id(url):
    parts=urlsplit(url)
    match=re.fullmatch(r'/(?:contest/\d+/)?problem/(\d+)(?:/statement/(?:default|zh_cn))?/?',parts.path)
    if parts.scheme!='https' or parts.hostname!='qoj.ac' or parts.username or parts.password or parts.port not in (None,443) or not match:
        raise ValueError('QOJ 原题链接无效')
    return match[1]

def html_samples(article):
    result=[];pending=None;sample_input=None
    def visit(node):
        nonlocal pending,sample_input
        if isinstance(node,str):return
        if re.fullmatch(r'h[1-6]',node.tag):
            text=plain(node).strip()
            if re.search(r'sample\s*input|input\s*(?:sample|example)?\s*\d*$|输入样例|样例输入|输入格式\s*\d+\s*$',text,re.I):pending='input'
            elif re.search(r'sample\s*output|output\s*(?:sample|example)?\s*\d*$|输出样例|样例输出|输出格式\s*\d+\s*$',text,re.I):pending='output'
        elif node.tag=='pre':
            text=plain(node).replace('\r\n','\n').strip('\n')
            if pending=='input':sample_input=text
            elif pending=='output' and sample_input is not None:
                result.append({'name':'样例 '+str(len(result)+1),'input':sample_input,'output':text});sample_input=None
            pending=None
        else:
            for child in node.children:visit(child)
    visit(article)
    return result

def _pdf_lines(page):
    """Read drawn table borders, independently of the PDF's text order."""
    horizontal=[];vertical=[];current=None;first=None
    def transform(x,y,cm):return (cm[0]*float(x)+cm[2]*float(y)+cm[4],cm[1]*float(x)+cm[3]*float(y)+cm[5])
    def line(a,b):
        if abs(a[1]-b[1])<.15:horizontal.append((min(a[0],b[0]),max(a[0],b[0]),(a[1]+b[1])/2))
        elif abs(a[0]-b[0])<.15:vertical.append(((a[0]+b[0])/2,min(a[1],b[1]),max(a[1],b[1])))
    def visit(op,args,cm,tm):
        nonlocal current,first
        if op==b'm':current=first=transform(args[0],args[1],cm)
        elif op==b'l':
            target=transform(args[0],args[1],cm)
            if current:line(current,target)
            current=target
        elif op==b'h' and current and first:line(current,first);current=first
        elif op==b're':
            x,y,w,h=map(float,args);points=[transform(x,y,cm),transform(x+w,y,cm),transform(x+w,y+h,cm),transform(x,y+h,cm)]
            for i in range(4):line(points[i],points[(i+1)%4])
    contents=page.get_contents()
    if contents and len(contents.get_data())>32*1024*1024:raise ValueError('QOJ PDF 页面内容过大')
    page.extract_text(visitor_operand_before=visit)
    return [(low,high,y) for y,low,high in _joined_lines([(y,low,high) for low,high,y in horizontal])],_joined_lines(vertical)

def _pdf_samples(textpage,horizontal,vertical):
    def boxes(word):
        result=[]
        with closing(textpage.search(word)) as search:
            while (found:=search.get_next()) is not None:
                chars=[textpage.get_charbox(i) for i in range(found[0],sum(found))]
                result.append((min(c[0] for c in chars),min(c[1] for c in chars),max(c[2] for c in chars),max(c[3] for c in chars)))
        return result
    samples=[]
    for left_header in boxes('standard input'):
        outputs=[box for box in boxes('standard output') if abs(box[1]-left_header[1])<4 and box[0]>left_header[2]]
        if len(outputs)!=1:continue
        right_header=outputs[0];y=(left_header[1]+left_header[3])/2
        borders=[line for line in vertical if line[1]<y<line[2]]
        a,b,c=([line for line in borders if line[0]<left_header[0]],
               [line for line in borders if left_header[2]<line[0]<right_header[0]],
               [line for line in borders if line[0]>right_header[2]])
        if not a or not b or not c:continue
        left=max(a,key=lambda v:v[0]);middle=max(b,key=lambda v:v[0]);right=min(c,key=lambda v:v[0])
        bottom=max(left[1],middle[1],right[1])
        separators=sorted({round(h[2],2) for h in horizontal if h[0]<=left[0]+2 and h[1]>=right[0]-2 and bottom-.5<=h[2]<left_header[1]},reverse=True)
        if len(separators)<2:continue
        for top,base in zip(separators,separators[1:]):
            if top-base<2:continue
            normalize=lambda text:'\n'.join(line.rstrip(' \t') for line in text.replace('\r\n','\n').strip('\n').split('\n'))
            inp=normalize(textpage.get_text_bounded(left[0]+.6,base+.6,middle[0]-.6,top-.6))
            out=normalize(textpage.get_text_bounded(middle[0]+.6,base+.6,right[0]-.6,top-.6))
            if not out or '\ufffd' in inp+out:continue
            samples.append({'name':'样例 '+str(len(samples)+1),'input':inp,'output':out})
    return samples

def pdf_statement(data,pid):
    if not isinstance(data,bytes) or not data.startswith(b'%PDF-') or len(data)>32*1024*1024:raise ValueError('QOJ 未返回有效公开 PDF')
    import pypdfium2 as pdfium
    from pypdf import PdfReader
    reader=PdfReader(io.BytesIO(data))
    if reader.is_encrypted or not 0<len(reader.pages)<=32:raise ValueError('QOJ PDF 页数或加密格式不支持')
    images={};body=[];samples=[];pixels=0;size=0
    with PDF_LOCK,closing(pdfium.PdfDocument(data)) as document:
        for index,page in enumerate(document):
            width,height=page.get_size();pixels+=int(width*height*4)
            if width<=0 or height<=0 or pixels>64_000_000:raise ValueError('QOJ PDF 页面大小超过限制')
            with closing(page.get_textpage()) as textpage:
                horizontal,vertical=_pdf_lines(reader.pages[index])
                samples.extend(_pdf_samples(textpage,horizontal,vertical))
            with closing(page.render(scale=2)) as bitmap:
                buffer=io.BytesIO();bitmap.to_pil().save(buffer,format='PNG');png=buffer.getvalue();size+=len(png)
            if size>32*1024*1024:raise ValueError('QOJ PDF 配图超过限制')
            name=f'qoj-{pid}-{hashlib.sha256(data).hexdigest()[:12]}-page-{index+1}.png';images[name]='data:image/png;base64,'+base64.b64encode(png).decode('ascii')
            body.append(f'![原题题面第 {index+1} 页]({name})');page.close()
    return {'markdown':'\n\n'.join(body),'images':images,'samples':samples,'pageCount':len(reader.pages),
            'statementFormat':'pdf-pages-v1','sourcePdfSha256':hashlib.sha256(data).hexdigest(),
            'sampleExtraction':'pdf-table-geometry-v1' if samples else 'unavailable'}

def statement(client,identity,title,url):
    pid=problem_id(url);page=client.text(url);root=Tree(page).root
    heading=next((n for n in root.find(lambda n:n.tag=='h1') if re.match(r'#?\s*'+re.escape(pid)+r'\.',plain(n).strip())),None)
    if heading is None:raise ValueError('QOJ 题面尚未公开、需要登录或原站请求受限')
    actual=re.sub(r'^#?\s*'+re.escape(pid)+r'\.\s*','',plain(heading).strip());text=plain(root)
    limit=re.search(r'Time Limit:\s*([0-9.]+)\s*s\s*Memory Limit:\s*(\d+)\s*MB',text,re.I)
    if not limit:raise ValueError('QOJ 原站未提供可识别的资源限制')
    iframe=next(root.find(lambda n:n.tag=='iframe' and n.attrs.get('id')=='statements-pdf'),None)
    if iframe is not None:
        source=urljoin(url,iframe.attrs.get('src',''));parts=urlsplit(source);query=parse_qs(parts.query)
        if parts.scheme!='https' or parts.hostname!='qoj.ac' or parts.username or parts.password or parts.port not in (None,443) or parts.fragment or parts.path!='/download.php' or query.get('type')!=['statement'] or query.get('id')!=[pid] or set(query)-{'type','id','ver','contest_id'}:
            raise ValueError('QOJ PDF 题面来源与原题不一致')
        value=pdf_statement(client.bytes(source,headers={'Accept':'application/pdf'}),pid);value['sourcePdfUrl']=source
    else:
        article=next(root.find(lambda n:n.tag=='article' and 'uoj-article' in classes(n)),None)
        if article is None:raise ValueError('QOJ 题面正文缺失')
        body=markdown(article,url).strip()
        if not body:raise ValueError('QOJ 题面正文为空')
        images={};total=0
        for node in article.find(lambda n:n.tag=='img'):
            source=urljoin(url,node.attrs.get('src',''))
            if not source or urlsplit(source).hostname!='qoj.ac':raise ValueError('QOJ 题面图片来源待核验')
            data=client.bytes(source);total+=len(data)
            if len(data)>16*1024*1024 or total>32*1024*1024:raise ValueError('QOJ 题面图片超过限制')
            mime='image/png' if data.startswith(b'\x89PNG') else 'image/jpeg' if data.startswith(b'\xff\xd8') else 'image/gif' if data.startswith(b'GIF8') else 'image/webp' if data.startswith(b'RIFF') and data[8:12]==b'WEBP' else 'image/svg+xml' if b'<svg' in data[:1024] else None
            if mime is None:raise ValueError('QOJ 题面未返回可识别图片')
            name='qoj-image-'+hashlib.sha256(source.encode()).hexdigest()[:20]
            images[name]='data:'+mime+';base64,'+base64.b64encode(data).decode('ascii');body=body.replace(']('+source+')',']('+name+')')
        value={'markdown':body,'images':images,'samples':html_samples(article),'statementFormat':'html-v1'}
    value['markdown']='# '+actual+'\n\n'+value['markdown']
    value.update(id=identity,title=actual,url=url,statementAvailable=True,statementVersion=6,
                 limits={'timeMs':round(float(limit[1])*1000),'memoryMb':int(limit[2])},
                 sourceHtmlSha256=hashlib.sha256(page.encode()).hexdigest())
    if '/statement/zh_cn' in url:value.update(statementLanguage='zh-CN',translationProvider='QOJ 原站中文题面（含原站标记的机器译文）' if 'translated using AI' in page else 'QOJ 原站中文题面')
    return value
