"""Read an actual Gym statement attachment, using its real roster and PDF labels.

Never infer QOJ IDs or contest letters. A PDF title/cover must independently
agree with the native Gym roster before any pages are associated with a task.
"""
import base64
import hashlib
import io
import re
import unicodedata
from urllib.parse import urljoin, urlsplit
from statement_format import Tree, classes, plain


def normalized(text):
    return re.sub(r'[\W_]+', '', unicodedata.normalize('NFKC', text)).casefold()


def roster(page, contest_id):
    result = {}
    for row in Tree(page).root.find(lambda n: n.tag == 'tr'):
        links = list(row.find(lambda n: n.tag == 'a' and re.fullmatch(
            '/gym/' + contest_id + r'/problem/[A-Z][0-9]?', n.attrs.get('href', ''))))
        if len(links) < 2:
            continue
        letter = links[0].attrs['href'].rsplit('/', 1)[-1]
        title = plain(links[1]).strip()
        limits = re.search(r'([\d.]+)\s*s,\s*(\d+)\s*MB', plain(row))
        if limits:
            result[letter] = {'title': title, 'limits': {'timeMs':round(float(limits[1])*1000), 'memoryMb':int(limits[2])}}
    return result


def selected_pages(reader, letter, title):
    texts = [page.extract_text() or '' for page in reader.pages]
    starts = []
    for index, text in enumerate(texts):
        match = re.search(r'(?im)^\s*(?:Problem|题目)\s+([A-Z][0-9]?)(?:[ \t]*[.：:][ \t]*|[ \t]*\n)([^\n]*)', text[:1800])
        if match:
            starts.append((index, match[1], match[2]))
    found = [(pos, start, header) for pos,(start, label, header) in enumerate(starts) if label == letter]
    if len(found) != 1:
        raise ValueError('原版 PDF 未提供唯一、明确的题号分页')
    pos, start, header = found[0]
    end = starts[pos+1][0] if pos+1 < len(starts) else len(reader.pages)
    # Some embedded CJK heading fonts have a broken ToUnicode map. In that case
    # the independently extracted cover table must still match letter AND title.
    title_key = normalized(title)
    cover = '\n'.join(texts[:min(start,3)])
    cover_match = any(re.match(r'^\s*'+re.escape(letter)+r'\s+', line)
                      and title_key in normalized(line) for line in cover.splitlines())
    if title_key != normalized(header) and not cover_match:
        raise ValueError('原版 PDF 题名与原站题单未能双侧核对')
    return list(range(start,end)), texts


def statement(client, identity, title, url, page):
    from pypdf import PdfReader, PdfWriter
    from qoj import pdf_statement
    from statement_resources import inspect_resource
    match = re.fullmatch(r'/gym/(\d+)/problem/([A-Z][0-9]?)', urlsplit(url).path)
    if not match:
        raise ValueError('原站未返回完整公开题面')
    cid, letter = match.groups()
    candidates = []
    for link in Tree(page).root.find(lambda n:n.tag=='a'):
        text = plain(link).strip(); href = urljoin(url,link.attrs.get('href',''))
        parts=urlsplit(href)
        if parts.scheme=='https' and parts.hostname=='codeforces.com' and not parts.username and not parts.password and re.search(r'^Statements?\b',text,re.I) and re.fullmatch(
            r'/gym/'+cid+r'/attachments/download/\d+/[^/]+\.pdf',urlsplit(href).path):
            candidates.append((0 if re.search(r'\(en\)',text,re.I) else 1,href))
    if not candidates:
        raise ValueError('原站未返回完整公开题面')
    roster_url = 'https://codeforces.com/gym/'+cid
    roster_page = client.text(roster_url)
    tasks = roster(roster_page,cid)
    if letter not in tasks:
        raise ValueError('原站题单未确认该题身份与资源限制')
    failures = []
    for _,source in sorted(set(candidates)):
        try:
            data=client.bytes(source);reader=PdfReader(io.BytesIO(data))
            indices,_=selected_pages(reader,letter,tasks[letter]['title'])
            writer=PdfWriter()
            for index in indices:writer.add_page(reader.pages[index])
            output=io.BytesIO();writer.write(output)
            value=pdf_statement(output.getvalue(),cid+'-'+letter,render_pages=False)
            entry=inspect_resource(data,source,'attachment')
            value.update(id=identity,title=tasks[letter]['title'],url=url,limits=tasks[letter]['limits'],
                sourcePdfUrl=source,sourcePdfSha256=entry['sha256'],sourcePageNumbers=[i+1 for i in indices],
                sourceRosterUrl=roster_url,sourceRosterSha256=hashlib.sha256(roster_page.encode()).hexdigest(),
                statementAvailable=True,statementVersion=7,statementSource='Codeforces 原站 PDF',
                attachments={source:dict(entry,fileName=f'gym-{cid}.pdf',data='data:application/pdf;base64,'+base64.b64encode(data).decode('ascii'))})
            display=output.getvalue()
            value['statementPdf']={'sourceUrl':source,'sha256':hashlib.sha256(display).hexdigest(),
                'data':'data:application/pdf;base64,'+base64.b64encode(display).decode('ascii'),
                'pageCount':len(indices),'sourcePageNumbers':[i+1 for i in indices],
                'sourceSha256':entry['sha256'],'fileName':f'gym-{cid}-{letter}.pdf'}
            value['markdown']='# '+value['title']+'\n\n'+value['markdown']+'\n\n[PDF]('+source+')'
            from statement_integrity import annotate_type
            return annotate_type(value)
        except (OSError,ValueError,RuntimeError) as error:
            failures.append(str(error))
    raise ValueError('; '.join(failures))
