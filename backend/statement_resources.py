"""Archive original statement resources without rasterising GIFs or dropping PDFs."""
import base64
import hashlib
import io
import re
from urllib.parse import unquote, urljoin, urlsplit

ATTACHMENT = re.compile(r'\.(?:pdf|zip|7z|rar|tgz|gz|gif|png|jpg|jpeg|svg|txt|in|out|cpp|cc|c|h|hpp|py|java)(?:[?#]|$)|(?:download|attachment)(?:[/.?=]|$)', re.I)


def resource_references(value):
    """Return source destinations, including Markdown reference-style images."""
    documents = [value.get('markdown') or '']
    documents.extend([value.get('currentSourceMarkdown') or '',value.get('statementSupplement') or ''])
    translation = value.get('translation')
    if isinstance(translation, dict):
        documents.append(translation.get('markdown') or '')
    result = {}
    for document in documents:
        definitions = {m[1].strip().casefold(): m[2] for m in re.finditer(r'(?m)^\s{0,3}\[([^\]]+)\]:\s*<?([^\s>]+)>?', document)}
        for match in re.finditer(r'(!?)\[(?:\\.|[^\]\\])*\]\(<?([^\s>]+?)(?:>|(?<!\\)\))', document):
            image, ref = bool(match[1]), match[2]
            if image or ATTACHMENT.search(ref):
                result[ref] = 'image' if image else 'attachment'
        for match in re.finditer(r'!\[([^\]]*)\](?:\[([^\]]*)\])?', document):
            label = (match[2] or match[1]).strip().casefold()
            if label in definitions:
                result[definitions[label]] = 'image'
    for ref in (value.get('sourcePdfUrl'), value.get('sourcePdf')):
        if isinstance(ref, str) and ref.startswith(('https://', 'http://')):
            result[ref] = 'attachment'
    for key, item in (value.get('attachments') or {}).items():
        if isinstance(item, dict) and item.get('sourceUrl'):
            result.setdefault(item['sourceUrl'], 'attachment')
    return [{'key': k, 'url': urljoin(value.get('url') or '', k), 'kind': v} for k, v in result.items()]


def inspect_resource(data, url, kind):
    if not isinstance(data, bytes) or not data or len(data) > 32 * 1024 * 1024:
        raise ValueError('Invalid or oversized original resource')
    result = {'sourceUrl': url, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    if data.startswith(b'%PDF-'):
        from pypdf import PdfReader
        pdf = PdfReader(io.BytesIO(data))
        if pdf.is_encrypted or not pdf.pages:
            raise ValueError('Encrypted or empty statement PDF')
        for page in pdf.pages:
            page.get_contents()  # Validate every page, not only page one.
        result.update(mime='application/pdf', pageCount=len(pdf.pages))
    elif data.startswith((b'\x89PNG\r\n', b'\xff\xd8\xff', b'GIF87a', b'GIF89a', b'BM')) or data[:4] == b'RIFF' or b'ftypavif' in data[:32]:
        from PIL import Image
        with Image.open(io.BytesIO(data)) as image:
            mime = Image.MIME.get(image.format)
            count = getattr(image, 'n_frames', 1)
            for frame in range(count):
                image.seek(frame)
                image.load()
            result.update(mime=mime, frameCount=count, width=image.width, height=image.height)
    elif re.search(br'<svg(?:\s|>)', data[:4096]):
        # Preserve exact bytes; an external SVG dependency needs its own review.
        if re.search(br'(?:href\s*=\s*["\'](?:https?:|//)|url\s*\(\s*["\']?https?:|<script\b|<foreignObject\b)', data, re.I):
            raise ValueError('SVG contains active content or external dependencies')
        result['mime'] = 'image/svg+xml'
    elif data.startswith(b'PK\x03\x04') or data.startswith(b'PK\x05\x06'):
        import zipfile
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if archive.testzip() is not None:
                raise ValueError('Corrupt original ZIP')
        result['mime'] = 'application/zip'
    elif kind == 'image':
        raise ValueError('The image URL did not return an original image')
    elif re.search(br'(?i)<!doctype\s+html|<html\b', data[:2048]):
        raise ValueError('Attachment URL returned an HTML page')
    else:
        result['mime'] = 'application/octet-stream'
    if kind == 'image' and result['mime'] == 'application/pdf':
        raise ValueError('An image destination returned a PDF')
    if urlsplit(url).path.lower().endswith('.gif') and result['mime'] != 'image/gif':
        raise ValueError('A GIF destination did not return original GIF bytes')
    return result


def archive_resources(value, client):
    """Keep the source Markdown/hash stable; resolve originals via embedded maps."""
    result = dict(value, images=dict(value.get('images') or {}), attachments=dict(value.get('attachments') or {}))
    manifest = {}; issues = []
    for ref in resource_references(result):
        key, url, kind = ref['key'], ref['url'], ref['kind']
        existing = result['images'].get(key) if kind == 'image' else result['attachments'].get(key, {}).get('data')
        if not existing and key.startswith('data:'):
            existing = key
        try:
            if isinstance(existing, str) and existing.startswith('data:'):
                data = base64.b64decode(existing.split(',', 1)[1], validate=True)
            else:
                if urlsplit(url).scheme not in ('https', 'http'):
                    raise ValueError('Unresolved relative resource')
                data = client.bytes(url)
            original = (value.get('resourceManifest') or {}).get(key, {})
            entry = inspect_resource(data, original.get('sourceUrl') or url, kind)
            page = re.search(r'-page-(\d+)\.png$', key)
            if kind == 'image' and page and value.get('sourcePdfUrl') and value.get('sourcePdfSha256'):
                entry.update(sourceUrl=value['sourcePdfUrl'],derivedFromPdfSha256=value['sourcePdfSha256'],pageNumber=int(page[1]))
            payload = 'data:' + entry['mime'] + ';base64,' + base64.b64encode(data).decode('ascii')
            if kind == 'image':
                result['images'][key] = payload
            else:
                result['attachments'][key] = dict(entry, data=payload,
                    fileName=result['attachments'].get(key, {}).get('fileName') or unquote(urlsplit(url).path.rsplit('/', 1)[-1]) or 'attachment')
            manifest[key] = entry
        except Exception as error:
            issues.append({'url': url, 'kind': kind, 'error': str(error)[:180]})
    result['resourceManifest'] = manifest
    result['resourceIssues'] = issues
    return result
