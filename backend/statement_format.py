"""Public HTML to Markdown without flattening formulae, code, lists or tables."""
from html.parser import HTMLParser
import re
from urllib.parse import parse_qs, urljoin, urlsplit


class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def find(self, predicate):
        if predicate(self):
            yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.find(predicate)


class Tree(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'wbr'}:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, value):
        self.stack[-1].children.append(value)


def classes(node):
    return set((node.attrs.get('class') or '').split())


def plain(node):
    if isinstance(node, str):
        return node
    if node.tag == 'br':
        return '\n'
    return ''.join(plain(child) for child in node.children)


def fence(value):
    delimiter = '`' * max(3, max((len(match[0]) + 1 for match in re.finditer(r'`+', value)), default=3))
    return '\n\n' + delimiter + 'text\n' + value.rstrip('\n') + '\n' + delimiter + '\n\n'


def markdown(node, base='', prose_pre=False):
    if isinstance(node, str):
        return re.sub(r'\s+', ' ', node.replace('\xa0', ' '))
    tag, names = node.tag, classes(node)
    if 'part' in names and any(re.match(r'Sample (?:Input|Output)\b', plain(heading).strip(), re.I)
                               for heading in node.find(lambda item: item.tag == 'h3')):
        return ''
    if tag in {'script', 'style', 'button', 'textarea', 'svg'} or names & {'code-copy-btn', 'js-clipboard', 'sample-tests', 'sample-test', 'question-oi', 'header'}:
        return ''
    if tag == 'br':
        return '\n'
    if tag == 'img':
        src = node.attrs.get('src') or ''
        parsed = urlsplit(urljoin(base, src))
        formula = parse_qs(parsed.query).get('tex', [''])[0]
        if formula:
            if re.fullmatch(r'\s*\\hspace\{[^}]+\}\s*', formula):
                return ''
            return '$' + formula.strip() + '$'
        if parsed.scheme not in ('https', 'http'):
            return ''
        return '![' + (node.attrs.get('alt') or '').replace(']', '\\]') + '](' + parsed.geturl().replace(')', '%29') + ')'
    if tag == 'var':
        return '$' + plain(node).strip() + '$'
    if tag == 'pre' and not prose_pre:
        return fence(plain(node))
    if tag == 'table':
        rows = []
        for row in node.find(lambda item: item.tag == 'tr'):
            cells = [markdown(cell, base, prose_pre).strip().replace('\n', ' ').replace('|', '\\|')
                     for cell in row.children if isinstance(cell, Node) and cell.tag in ('td', 'th')]
            if cells:
                rows.append(cells)
        if not rows:
            return ''
        width = max(map(len, rows))
        rows = [row + [''] * (width - len(row)) for row in rows]
        rows.insert(1, ['---'] * width)
        return '\n\n' + '\n'.join('| ' + ' | '.join(row) + ' |' for row in rows) + '\n\n'
    content = ''.join(markdown(child, base, prose_pre) for child in node.children)
    if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6') or 'section-title' in names:
        return '\n\n' + ('##' if 'section-title' in names else '#' * int(tag[1])) + ' ' + content.strip() + '\n\n'
    if tag == 'li':
        return '\n- ' + content.strip().replace('\n\n', '\n  ') + '\n'
    if tag in ('b', 'strong') and content.strip():
        return '**' + content.strip() + '**'
    if tag in ('em', 'i') and content.strip():
        return '*' + content.strip() + '*'
    if tag == 'code' or 'tex-font-style-tt' in names:
        return '`' + plain(node).strip() + '`'
    if tag == 'a':
        href = urljoin(base, node.attrs.get('href') or '')
        return '[' + content.strip() + '](' + href.replace(')', '%29') + ')' if content.strip() and urlsplit(href).scheme in ('http', 'https') else ''
    if tag == 'sub':
        return '$_{' + plain(node).strip() + '}$'
    if tag == 'sup':
        return '$^{' + plain(node).strip() + '}$'
    if tag in ('p', 'div', 'section', 'pre', 'ul', 'ol', 'blockquote'):
        return '\n\n' + content.strip() + '\n\n'
    return content


def html_markdown(html, base='', prose_pre=False):
    text = markdown(Tree(html).root, base, prose_pre)
    # Protect preformatted code while removing HTML indentation elsewhere.
    parts = re.split(r'(`{3,}text\n.*?\n`{3,})', text, flags=re.S)
    for index in range(0, len(parts), 2):
        parts[index] = re.sub(r'\n{3,}', '\n\n', re.sub(r'[ \t]+\n', '\n', parts[index]))
        parts[index] = re.sub(r'\n[ \t]+', '\n', parts[index])
    return ''.join(parts).strip()


def nowcoder_statement(page, base):
    # Samples are extracted from authoritative textarea blocks separately.
    root = Tree(page).root
    description = next(root.find(lambda node: 'subject-describe' in classes(node)), None)
    if description is not None:
        return '## 题目描述\n\n' + re.sub(r'\n{3,}', '\n\n', markdown(description, base, prose_pre=True)).strip()
    start = re.search(r'<h2\b[^>]*class=["\'][^"\']*subject-item-title', page, re.I)
    if not start:
        start = re.search(r'<(?:h[1-6]|div)\b[^>]*>\s*题目描述\s*(?:</|\n)', page, re.I)
    if not start:
        raise ValueError('牛客未返回公开题面')
    segment = page[start.start():]
    end = re.search(r'<div\b[^>]*class=["\'][^"\']*question-oi', segment, re.I)
    if end:
        segment = segment[:end.start()]
    else:
        end = re.search(r'<(?:div|section)\b[^>]*class=["\'][^"\']*(?:subject-action|subject-footer|editor)', segment, re.I)
        if end:
            segment = segment[:end.start()]
    return html_markdown(segment, base, prose_pre=True)


def nowcoder_explanations(page, base):
    starts = [match.start() for match in re.finditer(r'<div class="question-oi">', page)]
    results = []
    for index, start in enumerate(starts):
        block = page[start:starts[index + 1] if index + 1 < len(starts) else len(page)]
        match = re.search(r'<h2>\s*说明\s*</h2>\s*<div class="question-oi-cont">(.*?)</div>', block, re.S)
        results.append(html_markdown(match[1], base, prose_pre=True) if match else '')
    return results
