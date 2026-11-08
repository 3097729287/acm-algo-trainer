"""Original Gym booklets, including Chinese PDFs beside an English HTML body."""
import base64
import copy
from contextlib import closing
import hashlib
import io
import re
import unicodedata
from urllib.parse import urljoin, urlsplit
from statement_format import Tree, plain

CHECK_VERSION = 1
HEADING = re.compile(r'(?im)^[ \t]*(?:(Problem|题目|试题|Задача)[ \t]*)?([A-Z][0-9]?)[ \t]*[.：:][ \t]*([^\r\n]+)')
SPLIT_HEADING = re.compile(r'(?im)^[ \t]*(Problem|题目|试题|Задача)[ \t]+(P?[A-Z][0-9]?)[ \t.：:\r]*\n(?:[ \t\r]*\n)*[ \t]*([^\r\n]+)')


def gym_identity(url):
    parts = urlsplit(url or '')
    try:
        match = re.fullmatch(r'/gym/(\d+)/problem/([A-Z][0-9]?)/?', parts.path)
        if (parts.scheme == 'https' and parts.hostname == 'codeforces.com'
                and not parts.username and not parts.password and parts.port in (None, 443)
                and not parts.query and not parts.fragment and match):
            return match.groups()
    except ValueError:
        pass
    raise ValueError('Codeforces Gym 原题链接无效')


def needs_localized_pdf(value):
    """An old readable cache can be enriched without replacing its original text."""
    try:
        gym_identity(value.get('url'))
    except ValueError:
        return False
    return bool(value.get('statementAvailable') and not value.get('translation')
                and not str(value.get('statementLanguage') or '').startswith('zh')
                and (value.get('sitePdfCheckVersion') or 0) < CHECK_VERSION)


def candidates(page, url, *, chinese_only=False):
    cid, _ = gym_identity(url)
    result = set()
    for link in Tree(page).root.find(lambda n: n.tag == 'a'):
        text = plain(link).strip()
        href = urljoin(url, link.attrs.get('href', ''))
        parts = urlsplit(href)
        try:
            valid = (parts.scheme == 'https' and parts.hostname == 'codeforces.com'
                and not parts.username and not parts.password and parts.port in (None, 443)
                and not parts.query and not parts.fragment
                and re.search(r'^Statements?\b', text, re.I)
                and re.fullmatch(r'/gym/' + cid + r'/attachments/download/\d+/[^/]+\.pdf', parts.path, re.I))
        except ValueError:
            valid = False
        if not valid:
            continue
        zh = bool(re.search(r'\((?:zh(?:[-_]cn)?|chinese|中文)\)', text, re.I))
        if not chinese_only or zh:
            result.add((0 if zh else 1 if re.search(r'\(en\)', text, re.I) else 2, href))
    return sorted(result)


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


def roster_titles(page, contest_id):
    """Read only explicit native task links; localized pages omit limit text."""
    result = {}
    for row in Tree(page).root.find(lambda n: n.tag == 'tr'):
        links = list(row.find(lambda n: n.tag == 'a' and re.fullmatch(
            '/gym/' + contest_id + r'/problem/[A-Z][0-9]?', n.attrs.get('href', ''))))
        if len(links) != 2 or links[0].attrs['href'] != links[1].attrs['href']:
            continue
        label = links[0].attrs['href'].rsplit('/', 1)[-1]
        name = plain(links[1]).strip()
        if plain(links[0]).strip() != label or not name or label in result:
            raise ValueError('原站本地化题单的题号或题名有歧义')
        result[label] = name
    return result


def _selection_roster(client, cid, letter, tasks, starts):
    # Bind the whole booklet, including interactive tasks omitted by importers,
    # to the independently published native names for the same problem links.
    if not any(label == letter and re.search(r'[А-Яа-яЁё]', name)
               and normalized(name) != normalized(tasks[letter]['title']) for _, label, name in starts):
        return tasks, None
    native_url = 'https://codeforces.com/gym/' + cid + '?locale=ru'
    native_page = client.text(native_url)
    titles = roster_titles(native_page, cid)
    if (set(titles) != set(tasks) or len(starts) != len(titles)
            or {label for _, label, _ in starts} != set(titles)
            or any(normalized(name) != normalized(titles[label]) for _, label, name in starts)):
        raise ValueError('原版 PDF 未能与原站本地化完整题单核对')
    selected = {label: dict(task, title=titles[label]) for label, task in tasks.items()}
    return selected, (native_url, native_page)


def _starts(texts, tasks=None):
    starts = []
    for index, text in enumerate(texts):
        matches = [m for pattern in (HEADING, SPLIT_HEADING) for m in pattern.finditer(text[:1800])
                   if (m[1] or text[:m.start()].count('\n') < 6)
                   and not re.search(r'\bPage\s+\d+\s+of\s+\d+\s*$', m[3], re.I)]
        # A contents page listing multiple tasks is not the first problem page.
        if len(matches) != 1:
            continue
        match = matches[0]
        if starts and starts[-1][1:] == (match[2], match[3].strip()):
            continue  # Repeated running headings on continuation pages.
        starts.append((index, match[2], match[3].strip()))
    # Taiwan's native booklet prints PA..PM; the Gym uses A..M. Accept that
    # prefix only when every printed task agrees with the complete roster.
    if (tasks and starts and all(re.fullmatch(r'P[A-Z][0-9]?', label) for _, label, _ in starts)
            and len(starts) == len(tasks) and {label[1:] for _, label, _ in starts} == set(tasks)):
        starts = [(index, label[1:], title) for index, label, title in starts]
    return starts


def _cover(texts, starts):
    result = {}
    headings = {label: title for _, label, title in starts}
    for text in texts[:starts[0][0]] if starts else []:
        for line in text.splitlines():
            match = re.fullmatch(r'\s*([A-Z][0-9]?)(?:[ \t]*[.：:][ \t]*|[ \t]+)(.+?)\s*', line)
            if match:
                title = match[2]
                # A printed contents page may append a physical page number.
                # Strip it only when the remainder agrees with the full title
                # independently extracted from that problem's actual heading.
                without_page = re.sub(r'[ \t.·…]+\d+[ \t]*$', '', title)
                if normalized(without_page) == normalized(headings.get(match[1], '')):
                    title = without_page
                if match[1] in result and normalized(result[match[1]]) != normalized(title):
                    raise ValueError('原版 PDF 目录题名有歧义')
                result[match[1]] = title
    return result


def selected_pages(reader, letter, title, *, texts=None, tasks=None, bilingual=False):
    texts = texts if texts is not None else [page.extract_text() or '' for page in reader.pages]
    starts = _starts(texts, tasks)
    found = [(pos, start, header) for pos,(start, label, header) in enumerate(starts) if label == letter]
    if len(found) != 1:
        raise ValueError('原版 PDF 未提供唯一、明确的题号分页')
    pos, start, header = found[0]
    end = starts[pos+1][0] if pos+1 < len(starts) else len(reader.pages)
    title_key = normalized(title)
    cover = _cover(texts, starts)
    if title_key != normalized(header) and title_key != normalized(cover.get(letter, '')):
        # A native Chinese booklet and its English Gym roster have different
        # titles. Require the complete label inventory and every PDF heading to
        # agree with the independently printed cover, not just a guessed letter.
        if not (bilingual and tasks and list(tasks) == [label for _, label, _ in starts]
                and set(cover) == set(tasks)
                and all(normalized(cover[label]) == normalized(name) for _, label, name in starts)
                and re.search(r'[\u3400-\u9fff]', header)):
            raise ValueError('原版 PDF 题名与原站题单未能双侧核对')
    return list(range(start,end)), texts


def _read(client, identity, url, source, tasks, roster_page, *, chinese=False, expected_samples=None):
    from pypdf import PdfReader, PdfWriter
    import pypdfium2 as pdfium
    from qoj import PDF_LOCK, pdf_statement
    from statement_resources import inspect_resource
    cid, letter = gym_identity(url)
    data = client.bytes(source)
    entry = inspect_resource(data, source, 'attachment')
    reader = PdfReader(io.BytesIO(data))
    if entry.get('mime') != 'application/pdf' or reader.is_encrypted or not 0 < len(reader.pages) <= 256:
        raise ValueError('原站未返回有效题面 PDF')
    # PDFium correctly resolves the overprinted CJK bold glyphs in SUA booklets;
    # pypdf's plain text extraction repeats each such character three times.
    texts = [];dimensions = []
    with PDF_LOCK, closing(pdfium.PdfDocument(data)) as document:
        for page in document:
            dimensions.append(page.get_size())
            with closing(page.get_textpage()) as textpage:
                texts.append(textpage.get_text_range())
            page.close()
    starts = _starts(texts, tasks)
    selection_tasks, localized_roster = _selection_roster(client, cid, letter, tasks, starts)
    first_lines = [line.strip() for line in texts[0].splitlines() if line.strip()][:6]
    title_line = next((line for line in first_lines if normalized(line) == normalized(tasks[letter]['title'])), None)
    other_titles = {normalized(task['title']) for label, task in tasks.items() if label != letter}
    competing = any(normalized(line.strip()) in other_titles for text in texts for line in text.splitlines() if line.strip())
    standalone = source == url and not starts and title_line is not None and not competing
    if standalone:
        indices = list(range(len(reader.pages)));header = title_line
    else:
        indices, _ = selected_pages(reader, letter, selection_tasks[letter]['title'], texts=texts, tasks=selection_tasks, bilingual=chinese)
        header = next(name for start, label, name in starts if label == letter)
    writer = PdfWriter()
    for index in indices:
        writer.add_page(reader.pages[index])
    output = io.BytesIO()
    writer.write(output)
    display = output.getvalue()
    value = pdf_statement(display, cid + '-' + letter, render_pages=False)
    def sample_pairs(samples):
        def normalize(text):
            return '\n'.join(line.rstrip(' \t') for line in text.replace('\r\n', '\n').replace('\r', '\n').strip('\n').split('\n'))
        return [(normalize(s['input']), normalize(s['output'])) for s in samples]
    if expected_samples and sample_pairs(value['samples']) != sample_pairs(expected_samples):
        raise ValueError('中文 PDF 的样例未能与原站 HTML 完整核对')
    roster_url = 'https://codeforces.com/gym/' + cid
    value.update(id=identity, title=tasks[letter]['title'], url=url, limits=tasks[letter]['limits'],
        sourcePdfUrl=source, sourcePdfSha256=entry['sha256'], sourcePageNumbers=[i+1 for i in indices],
        sourceRosterUrl=roster_url, sourceRosterSha256=hashlib.sha256(roster_page.encode()).hexdigest(),
        sourceBinding={'kind': 'native-problem-pdf-title' if standalone else 'official-bilingual-roster' if normalized(header) != normalized(tasks[letter]['title']) else 'exact-title',
                       'problem': letter, 'pdfTitle': header, 'rosterTitle': tasks[letter]['title'],
                       'samplePairsVerified': len(expected_samples or [])},
        statementAvailable=True, statementVersion=8, statementSource='Codeforces 原站 PDF',
        attachments={source: dict(entry, fileName=f'gym-{cid}.pdf', data='data:application/pdf;base64,'+base64.b64encode(data).decode('ascii'))})
    if localized_roster:
        value['sourceBinding'].update(kind='official-localized-roster',
            localizedRosterUrl=localized_roster[0],
            localizedRosterSha256=hashlib.sha256(localized_roster[1].encode()).hexdigest())
    if not standalone:
        printed = next((label for index, label, _ in _starts(texts) if index == indices[0]), letter)
        if printed != letter:
            value['sourceBinding'].update(pdfProblemLabel=printed, problemInventoryVerified=len(tasks))
    value['statementPdf'] = {'sourceUrl':source, 'sha256':hashlib.sha256(display).hexdigest(),
        'data':'data:application/pdf;base64,'+base64.b64encode(display).decode('ascii'),
        'pageCount':len(indices), 'sourcePageNumbers':[i+1 for i in indices],
        'widthPoints':dimensions[indices[0]][0],
        'sourceSha256':entry['sha256'], 'fileName':f'gym-{cid}-{letter}.pdf'}
    value['markdown'] = '# ' + header + '\n\n' + value['sourceText'] + '\n\n[PDF](' + source + ')'
    if chinese or len(re.findall(r'[\u3400-\u9fff]', value['sourceText'])) > 20:
        value['statementLanguage'] = 'zh-CN'
    elif re.search(r'(?im)^\s*Задача [A-Z][0-9]?\.', value['sourceText']):
        value['statementLanguage'] = 'ru'
    from statement_integrity import annotate_type
    return annotate_type(value)


def _roster(client, url):
    cid, letter = gym_identity(url)
    page = client.text('https://codeforces.com/gym/' + cid)
    tasks = roster(page, cid)
    if letter not in tasks:
        raise ValueError('原站题单未确认该题身份与资源限制')
    return tasks, page


def statement(client, identity, title, url, page):
    from pypdf.errors import PdfReadError
    if page.startswith('%PDF-'):
        # Some Gym problem URLs return a single-problem PDF directly. Keep its
        # exact original, then discover the contest's Chinese booklet as usual.
        tasks, roster_page = _roster(client, url)
        value = _read(client, identity, url, url, tasks, roster_page)
        return localized(client, value, roster_page)
    sources = candidates(page, url)
    if not sources:
        raise ValueError('原站未返回完整公开题面')
    tasks, roster_page = _roster(client, url)
    failures = []
    for rank, source in sources:
        try:
            return _read(client, identity, url, source, tasks, roster_page, chinese=rank == 0)
        except (OSError, ValueError, RuntimeError, PdfReadError) as error:
            failures.append(str(error))
    raise ValueError('; '.join(failures)[:1000])


def localized(client, original, page=None):
    """Add verified native Chinese pages; never replace cached prose or samples."""
    from pypdf.errors import PdfReadError
    value = copy.deepcopy(original)
    if value.get('translation') or str(value.get('statementLanguage') or '').startswith('zh'):
        return value
    url = value['url']
    gym_identity(url)
    page = page if page is not None else client.text(url)
    tasks = roster_page = None
    if page.startswith('%PDF-'):
        tasks, roster_page = _roster(client, url)
        page = roster_page
    sources = candidates(page, url, chinese_only=True)
    value.update(sitePdfCheckVersion=CHECK_VERSION, sitePdfStatus='not-provided')
    if not sources:
        return value
    try:
        if tasks is None:tasks, roster_page = _roster(client, url)
    except (OSError, ValueError, RuntimeError) as error:
        value.update(sitePdfStatus='unavailable', sitePdfError=str(error)[:250])
        return value
    failures = []
    for _, source in sources:
        try:
            pdf = _read(client, value['id'], url, source, tasks, roster_page,
                        chinese=True, expected_samples=value.get('samples'))
            translation = {key: pdf[key] for key in ('markdown', 'sourceText', 'statementPdf', 'sourcePdfUrl',
                'sourcePdfSha256', 'sourcePageNumbers', 'sourceRosterUrl', 'sourceRosterSha256', 'sourceBinding')}
            translation.update(kind='site', targetLanguage='zh-CN', sourceLanguage='en',
                               provider='Codeforces 原站中文 PDF', sourceUrl=source)
            value['translation'] = translation
            value['attachments'] = dict(value.get('attachments') or {}, **pdf['attachments'])
            value['resourceManifest'] = dict(value.get('resourceManifest') or {}, **{
                key: {k: v for k, v in item.items() if k not in ('data', 'fileName')}
                for key, item in pdf['attachments'].items()})
            value['sitePdfStatus'] = 'verified'
            value.pop('sitePdfError', None)
            return value
        except (OSError, ValueError, RuntimeError, PdfReadError) as error:
            failures.append(str(error))
    value.update(sitePdfStatus='unavailable', sitePdfError='; '.join(failures)[:250])
    return value
