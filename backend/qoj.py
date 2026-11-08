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
            if pending=='input':
                if sample_input is not None:raise ValueError('QOJ 样例缺少对应输出')
                sample_input=text
            elif pending=='output' and sample_input is not None:
                result.append({'name':'样例 '+str(len(result)+1),'input':sample_input,'output':text});sample_input=None
            pending=None
        else:
            for child in node.children:visit(child)
    visit(article)
    if sample_input is not None:raise ValueError('QOJ 样例缺少对应输出')
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
    inputs=boxes('standard input')+boxes('стандартный ввод')
    output_headers=boxes('standard output')+boxes('стандартный вывод')
    for left_header in inputs:
        outputs=[box for box in output_headers if abs(box[1]-left_header[1])<4 and box[0]>left_header[2]]
        if len(outputs)!=1:continue
        right_header=outputs[0];y=(left_header[1]+left_header[3])/2
        borders=[line for line in vertical if line[1]<y<line[2]]
        a,b,c=([line for line in borders if line[0]<left_header[0]],
               [line for line in borders if left_header[2]<line[0]<right_header[0]],
               [line for line in borders if line[0]>right_header[2]])
        if not a or not b or not c:continue
        def border(lines, nearest):
            axis=nearest(lines,key=lambda v:v[0])[0]
            # A double vertical rule can have one full body stroke and a second
            # short header stroke 0.4pt away. Read below the header using the
            # continuous stroke, rather than treating the header as the table.
            return min((line for line in lines if abs(line[0]-axis)<.8),key=lambda v:v[1])
        left=border(a,max);middle=border(b,max);right=border(c,min)
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

def _pdf_unbordered_samples(textpage,width,horizontal=(),vertical=()):
    """Explicit numbered sample headings, including vertically stacked examples."""
    def boxes(word):
        result=[]
        with closing(textpage.search(word)) as search:
            while (found:=search.get_next()) is not None:
                chars=[textpage.get_charbox(i) for i in range(found[0],sum(found))]
                result.append((min(c[0] for c in chars),min(c[1] for c in chars),max(c[2] for c in chars),max(c[3] for c in chars)))
        return sorted(result,key=lambda b:(-b[1],b[0]))
    inputs,outputs=boxes('Sample Input'),boxes('Sample Output')
    if not inputs or len(inputs)!=len(outputs):return []
    headings=inputs+outputs;notes=boxes('Notes')+boxes('Explanation')+boxes('Hint')
    result=[]
    def text(left,bottom,right,top):
        return '\n'.join(line.rstrip(' \t') for line in textpage.get_text_bounded(left,bottom,right,top).replace('\r\n','\n').strip('\n').split('\n'))
    def outlined(header):
        # Some booklets put the heading ABOVE an independent input/output box.
        # Its true lower border excludes the footer and unrelated prose, even
        # when the input box is much taller than its neighbouring output box.
        found=[]
        for left,right,top in horizontal:
            if not header[0]-20<=left<=header[0]+2 or right<header[2] or not 0<header[1]-top<20:continue
            a=[v for v in vertical if abs(v[0]-left)<.8 and abs(v[2]-top)<.8]
            b=[v for v in vertical if abs(v[0]-right)<.8 and abs(v[2]-top)<.8]
            for x in a:
                for y in b:
                    base=max(x[1],y[1])
                    if abs(x[1]-y[1])<.8 and any(abs(h[0]-left)<.8 and abs(h[1]-right)<.8 and abs(h[2]-base)<.8 for h in horizontal):
                        found.append((left+.6,base+.6,right-.6,top-.6))
        return found[0] if len(found)==1 else None
    for inp,out in zip(inputs,outputs):
        inp_box,out_box=outlined(inp),outlined(out)
        if inp_box or out_box:
            if not inp_box or not out_box:return []
            a=text(*inp_box);b=text(*out_box)
        elif abs(inp[1]-out[1])<4 and out[0]>inp[2]:
            bottom=max([35]+[b[3]+1 for b in headings+notes if b[3]<min(inp[1],out[1])-2])
            a=text(0,bottom,out[0]-3,inp[1]-1);b=text(out[0]-2,bottom,width,out[1]-1)
        elif out[3]<inp[1] and abs(out[0]-inp[0])<20:
            bottom=max([35]+[b[3]+1 for b in headings+notes if b[3]<out[1]-2])
            a=text(0,out[3]+1,width,inp[1]-1);b=text(0,bottom,width,out[1]-1)
        else:return []
        if not b or '\ufffd' in a+b or re.search(r'(?m)^(?:In (?:the|this)|For (?:the|this)|Note that|The answer)\b',b):return []
        result.append({'name':'样例 '+str(len(result)+1),'input':a,'output':b})
    return result

def _pdf_chinese_code_samples(reader,document):
    """Chinese numbered examples, including input/output split across pages.

    Only explicitly labelled, monospaced code is read. A line-number gutter is
    excluded only when its smaller font, separate position and consecutive
    numbering independently distinguish it from the actual sample integers.
    """
    blocks={};current=None
    heading=re.compile(r'【\s*(?:样例\s*(\d+)\s*(输入|输出|解释)|题目描述|输入格式|输出格式)\s*】')
    for index,page in enumerate(document):
        with closing(page.get_textpage()) as textpage:
            events=[]
            for match in heading.finditer(textpage.get_text_range()):
                with closing(textpage.search(match[0])) as search:
                    found=search.get_next()
                if found is None:return []
                boxes=[textpage.get_charbox(i) for i in range(found[0],sum(found))]
                events.append((max(box[3] for box in boxes),0,match.groups()))
            spans=[]
            def visit(text,cm,tm,font,size):
                name=str((font or {}).get('/BaseFont',''))
                if not text.strip() or not re.search(r'Consolas|Courier|Mono|Typewriter|CMTT',name,re.I):return
                if abs(cm[1])+abs(cm[2])+abs(tm[1])+abs(tm[2])>.01:return
                x=cm[0]*tm[4]+cm[4];y=cm[3]*tm[5]+cm[5]
                spans.append((x,y,text,float(size)*abs(cm[3])))
            reader.pages[index].extract_text(visitor_text=visit)
            lines=[]
            for span in sorted(spans,key=lambda s:(-s[1],s[0])):
                if lines and abs(lines[-1][0][1]-span[1])<.8:lines[-1].append(span)
                else:lines.append([span])
            events.extend((line[0][1],1,line) for line in lines)
            for y,kind,item in sorted(events,key=lambda e:(-e[0],e[1])):
                if kind==0:
                    number,field=item
                    current=(number,'input' if field=='输入' else 'output') if number and field in ('输入','输出') else None
                    if current:blocks.setdefault(number,{}).setdefault(current[1],[])
                    continue
                if current is None:continue
                line=sorted(item,key=lambda s:s[0]);first=line[0];gutter=None
                if (len(line)>1 and re.fullmatch(r'\d+',first[2].strip())
                        and all(span[3]>first[3]+1 for span in line[1:])
                        and line[1][0]>first[0]+first[3]*.5*len(first[2].strip())+2):
                    gutter=int(first[2].strip());line=line[1:]
                left=min(span[0] for span in line);size=max(span[3] for span in line)
                text=textpage.get_text_bounded(left-.5,y-3,page.get_width(),y+size+1)
                text=text.replace('\r\n','\n').strip('\n').rstrip(' \t')
                if not text or '\ufffd' in text or '\n' in text:return []
                blocks[current[0]][current[1]].append((text,gutter))
        page.close()
    result=[]
    for fields in blocks.values():
        if 'input' not in fields or not fields.get('output'):return []
        sample={}
        for field,lines in fields.items():
            gutters=[number for _,number in lines]
            if any(number is not None for number in gutters) and gutters!=list(range(1,len(lines)+1)):return []
            sample[field]='\n'.join(text for text,_ in lines)
        result.append(dict(sample,name='样例 '+str(len(result)+1)))
    return result


def pdf_statement(data,pid,*,render_pages=True):
    if not isinstance(data,bytes) or not data.startswith(b'%PDF-') or len(data)>32*1024*1024:raise ValueError('QOJ 未返回有效公开 PDF')
    import pypdfium2 as pdfium
    from pypdf import PdfReader
    reader=PdfReader(io.BytesIO(data))
    if reader.is_encrypted or not 0<len(reader.pages)<=32:raise ValueError('QOJ PDF 页数或加密格式不支持')
    images={};body=[];samples=[];texts=[];pixels=0;size=0;extraction='unavailable'
    with PDF_LOCK,closing(pdfium.PdfDocument(data)) as document:
        for index,page in enumerate(document):
            width,height=page.get_size();pixels+=int(width*height*4)
            if width<=0 or height<=0 or pixels>64_000_000:raise ValueError('QOJ PDF 页面大小超过限制')
            with closing(page.get_textpage()) as textpage:
                texts.append(textpage.get_text_range())
                horizontal,vertical=_pdf_lines(reader.pages[index])
                extracted=_pdf_samples(textpage,horizontal,vertical)
                samples.extend(extracted or _pdf_unbordered_samples(textpage,width,horizontal,vertical))
            if render_pages:
                with closing(page.render(scale=2)) as bitmap:
                    buffer=io.BytesIO();bitmap.to_pil().save(buffer,format='PNG');png=buffer.getvalue();size+=len(png)
                if size>32*1024*1024:raise ValueError('QOJ PDF 配图超过限制')
                name=f'qoj-{pid}-{hashlib.sha256(data).hexdigest()[:12]}-page-{index+1}.png';images[name]='data:image/png;base64,'+base64.b64encode(png).decode('ascii')
                body.append(f'![原题题面第 {index+1} 页]({name})')
            page.close()
        if samples:extraction='pdf-table-geometry-v1'
        else:
            samples=_pdf_chinese_code_samples(reader,document)
            if samples:extraction='pdf-code-geometry-v1'
    source_text='\n\n'.join(texts)
    numbered=lambda field:set(re.findall(r'(?im)^[ \t]*Sample '+field+r'\s+([0-9]+)\s*$',source_text))
    expected_inputs,expected_outputs=numbered('Input'),numbered('Output')
    inventory_complete=not (expected_inputs or expected_outputs) or expected_inputs==expected_outputs and len(samples)==len(expected_inputs)
    if not inventory_complete:
        # Keep the complete original PDF readable, but never offer an extracted
        # subset as all official examples. Cross-page code needs explicit repair.
        samples=[];extraction='incomplete-numbered-inventory'
    for i,sample in enumerate(samples,1):sample['name']='样例 '+str(i)
    return {'markdown':'\n\n'.join(body),'images':images,'samples':samples,'pageCount':len(reader.pages),'sourceText':source_text,
            'statementFormat':'pdf-pages-v1' if render_pages else 'pdf-native-v1','sourcePdfSha256':hashlib.sha256(data).hexdigest(),
            'sampleExtraction':extraction,**({'localJudgeSupported':False} if not inventory_complete else {})}

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
        data=client.bytes(source,headers={'Accept':'application/pdf'})
        value=pdf_statement(data,pid,render_pages=False);value['sourcePdfUrl']=source
        from statement_resources import inspect_resource
        entry=inspect_resource(data,source,'attachment')
        value['attachments']={source:dict(entry,fileName=f'qoj-{pid}.pdf',data='data:application/pdf;base64,'+base64.b64encode(data).decode('ascii'))}
        value['statementPdf']=dict(value['attachments'][source])
        value['markdown']+='\n\n[PDF]('+source+')'
    else:
        article=next(root.find(lambda n:n.tag=='article' and 'uoj-article' in classes(n)),None)
        if article is None:raise ValueError('QOJ 题面正文缺失')
        body=markdown(article,url).strip()
        if not body:raise ValueError('QOJ 题面正文为空')
        images={};total=0;manifest={}
        for node in article.find(lambda n:n.tag=='img'):
            source=urljoin(url,node.attrs.get('src',''))
            if not source or urlsplit(source).hostname!='qoj.ac':raise ValueError('QOJ 题面图片来源待核验')
            data=client.bytes(source);total+=len(data)
            if len(data)>16*1024*1024 or total>32*1024*1024:raise ValueError('QOJ 题面图片超过限制')
            mime='image/png' if data.startswith(b'\x89PNG') else 'image/jpeg' if data.startswith(b'\xff\xd8') else 'image/gif' if data.startswith(b'GIF8') else 'image/webp' if data.startswith(b'RIFF') and data[8:12]==b'WEBP' else 'image/svg+xml' if b'<svg' in data[:1024] else None
            if mime is None:raise ValueError('QOJ 题面未返回可识别图片')
            name='qoj-image-'+hashlib.sha256(source.encode()).hexdigest()[:20]
            images[name]='data:'+mime+';base64,'+base64.b64encode(data).decode('ascii');body=body.replace(']('+source+')',']('+name+')')
            from statement_resources import inspect_resource
            manifest[name]=inspect_resource(data,source,'image')
        value={'markdown':body,'images':images,'resourceManifest':manifest,'samples':html_samples(article),'statementFormat':'html-v1'}
    value['markdown']='# '+actual+'\n\n'+value['markdown']
    value.update(id=identity,title=actual,url=url,statementAvailable=True,statementVersion=6,
                 limits={'timeMs':round(float(limit[1])*1000),'memoryMb':int(limit[2])},
                 sourceHtmlSha256=hashlib.sha256(page.encode()).hexdigest())
    if '/statement/zh_cn' in url:value.update(statementLanguage='zh-CN',translationProvider='QOJ 原站中文题面（含原站标记的机器译文）' if 'translated using AI' in page else 'QOJ 原站中文题面')
    from statement_integrity import annotate_type
    return annotate_type(value)
