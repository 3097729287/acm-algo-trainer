"""Embed local Markdown illustrations at import time; readers need no files."""
import base64
from html import unescape
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

MIME = {'.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp',
        '.avif': 'image/avif', '.bmp': 'image/bmp'}
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_DOCUMENT_BYTES = 32 * 1024 * 1024


def _prose(markdown):
    result, fence = [], None
    for line in markdown.splitlines():
        match = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            continue
        if match:
            fence = match[1]
            continue
        # Image examples in inline code are not dependencies.
        result.append(re.sub(r'(`+).*?\1', '', line))
    return '\n'.join(result)


def _destination(text):
    text = text.lstrip()
    if text.startswith('<'):
        end = text.find('>')
        return text[1:end] if end >= 0 else None
    chars, depth, escaped = [], 0, False
    for char in text:
        if escaped:
            chars.extend(('\\', char)); escaped = False
        elif char == '\\':
            escaped = True
        elif char == '(':
            depth += 1; chars.append(char)
        elif char == ')':
            if not depth: break
            depth -= 1; chars.append(char)
        elif char.isspace() and not depth:
            break
        else:
            chars.append(char)
    return ''.join(chars) or None


def _image_labels(text):
    """Find balanced image labels while respecting Markdown backslash escapes."""
    # Match brackets once, so many unmatched openers cannot cause quadratic scans.
    closing, opened, escaped = {}, [], False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == '[':
            opened.append(index)
        elif char == ']' and opened:
            closing[opened.pop()] = index

    index = 0
    while index < len(text):
        if text[index] == '\\':
            index += 2
            continue
        if text.startswith('![', index):
            end = closing.get(index + 1)
            if end is not None:
                yield index, text[index + 2:end], end + 1
        index += 1


def image_targets(markdown):
    prose = _prose(markdown)
    label = lambda value: ' '.join(value.split()).casefold()
    definitions = {label(m[1]): _destination(m[2]) for m in re.finditer(r'^ {0,3}\[([^]\n]+)\]:\s*(.+)$', prose, re.M)}
    targets, covered_until = [], 0
    for start, image_label, end in _image_labels(prose):
        if start < covered_until:
            continue
        tail = prose[end:]
        label_end = end
        if tail.startswith('('):
            target = _destination(tail[1:])
        elif tail.startswith('['):
            end = tail.find(']')
            target = definitions.get(label(tail[1:end] or image_label)) if end >= 0 else None
        else:
            target = definitions.get(label(image_label))
        if target:
            # An image inside a resolved image's alt text does not render itself.
            # If the outer label has no destination, an inner image can still render.
            covered_until = label_end
            target = unescape(re.sub(r'\\([!"#$%&\'()*+,\-./:;<=>?@\[\]\\^_`{|}~])', r'\1', target))
            if target not in targets: targets.append(target)
    return targets


def collect_images(markdown, source, root, *, ignore_outside=False):
    """Resolve only files inside the explicit import root, including Unicode paths."""
    root, source = Path(root).resolve(), Path(source).resolve()
    images, total = {}, 0
    for target in image_targets(markdown):
        parts = urlsplit(target)
        if parts.scheme or parts.netloc: continue
        filename = unquote(parts.path).replace('\\', '/')
        resolved = (source.parent / filename).resolve()
        if not resolved.is_relative_to(root):
            if ignore_outside: continue
            raise ValueError('图片路径超出导入目录：' + target)
        mime = MIME.get(resolved.suffix.lower())
        if not mime:
            raise ValueError('不支持的图片格式：' + target)
        if not resolved.is_file():
            raise ValueError('缺少题解配图，请将图片目录一起导入：' + target)
        size = resolved.stat().st_size
        if size > MAX_IMAGE_BYTES or total + size > MAX_DOCUMENT_BYTES:
            raise ValueError('配图过大：单图上限 8 MB，每篇合计 32 MB')
        raw = resolved.read_bytes()
        total += len(raw)
        images[target] = 'data:' + mime + ';base64,' + base64.b64encode(raw).decode('ascii')
    return images
