"""Build the separate, attributed OI Wiki SQLite snapshot. Never opens a user library.

The upstream rendered article supplies MathML, resolved snippets and contributors.
Refreshes are explicit, reviewed release operations, not a background crawler.
"""
import argparse
import base64
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'backend'))
from statement_format import Tree, Node, plain, classes

PAGES = {
    '算法基础': ['basic/complexity', 'basic/enumerate', 'basic/simulate', 'basic/divide-and-conquer', 'basic/greedy', 'basic/prefix-sum', 'basic/binary', 'misc/two-pointer'],
    '搜索与动态规划': ['search/dfs', 'search/bfs', 'dp/basic', 'dp/memo', 'dp/knapsack/basic', 'dp/interval', 'dp/tree', 'dp/state'],
    '数据结构': ['ds/stack', 'ds/queue', 'ds/dsu', 'ds/heap', 'ds/monotonic-stack', 'ds/monotonic-queue', 'ds/sparse-table', 'ds/fenwick', 'ds/seg'],
    '图论': ['graph/save', 'graph/topo', 'graph/shortest-path', 'graph/mst', 'graph/lca', 'graph/scc', 'graph/bcc', 'graph/flow/max-flow'],
    '字符串与数学': ['string/hash', 'string/trie', 'string/kmp', 'string/z-func', 'math/binary-exponentiation', 'math/number-theory/gcd', 'math/number-theory/sieve', 'math/number-theory/inverse'],
}
ALLOWED = set('article h1 h2 h3 h4 h5 h6 p div span a img pre code blockquote ul ol li table thead tbody tr td th br hr details summary dl dt dd em strong b i s sup sub kbd figure figcaption abbr math semantics annotation mrow mi mn mo ms mtext mspace mfrac msqrt mroot msub msup msubsup munder mover munderover mtable mtr mtd menclose mpadded mphantom mfenced mstyle'.split())
DROP = {'script', 'style', 'iframe', 'object', 'embed', 'input', 'button', 'label', 'svg'}
VOID = {'img', 'br', 'hr', 'mspace'}

def fetch(url, limit=8*1024*1024):
    with urlopen(Request(url, headers={'User-Agent': 'ToBe-OI-Wiki-Snapshot/1 (+https://github.com/3097729287/acm-algo-trainer)'}), timeout=40) as response:
        if urlsplit(response.url).hostname not in {'oi-wiki.org', 'raw.githubusercontent.com', 'api.github.com'}:
            raise ValueError('Unexpected upstream redirect')
        data = response.read(limit + 1)
        if len(data) > limit: raise ValueError('Upstream resource too large')
        return data, response.headers.get_content_type()

def sanitize(node, base, images):
    if isinstance(node, str): return html.escape(node)
    tag = node.tag
    if tag in DROP or classes(node) & {'md-content__button', 'headerlink', 'linenos', 'md-source-file__fact--comments'}: return ''
    if tag == 'mjx-container':
        math = next(node.find(lambda item: item.tag == 'math'), None)
        if math is None: raise ValueError('MathJax article is missing accessible MathML')
        return sanitize(math, base, images)
    if 'tabbed-set' in classes(node):
        labels=next(node.find(lambda item:'tabbed-labels' in classes(item)),None)
        labels=[plain(item).strip() for item in labels.children if isinstance(item,Node) and item.tag=='label'] if labels else []
        content=next(node.find(lambda item:'tabbed-content' in classes(item)),None)
        blocks=[item for item in content.children if isinstance(item,Node) and 'tabbed-block' in classes(item)] if content else []
        if labels and len(labels)==len(blocks):
            return ''.join('<section class="wiki-code-variant"><h4>'+html.escape(label)+'</h4>'+sanitize(block,base,images)+'</section>' for label,block in zip(labels,blocks))
    children = ''.join(sanitize(child, base, images) for child in node.children)
    if tag not in ALLOWED: return children
    attrs = {}
    for key, value in node.attrs.items():
        if key in {'id', 'class', 'title', 'alt', 'colspan', 'rowspan', 'display', 'mathvariant', 'encoding', 'stretchy', 'fence', 'separator', 'linethickness', 'notation', 'columnalign', 'rowalign'}:
            attrs[key] = value
    if tag == 'math':
        attrs['xmlns'] = 'http://www.w3.org/1998/Math/MathML'
        if node.attrs.get('display') == 'block': attrs['display'] = 'block'
    if tag == 'a':
        link = node.attrs.get('href', '')
        url = urljoin(base, link)
        if urlsplit(url).scheme in {'https', 'http'}:
            attrs.update(href=url, target='_blank', rel='noopener noreferrer')
    if tag == 'img':
        url = urljoin(base, node.attrs.get('src') or node.attrs.get('data-src') or '')
        if urlsplit(url).hostname != 'oi-wiki.org':
            raise ValueError('Review external image before redistributing: ' + url)
        if url not in images:
            data, mime = fetch(url)
            if data.startswith(b'\x89PNG\r\n\x1a\n'): mime='image/png'  # Includes animated PNG, unchanged.
            elif data.startswith((b'GIF87a',b'GIF89a')): mime='image/gif'
            elif data.startswith(b'\xff\xd8\xff'): mime='image/jpeg'
            elif data[:4]==b'RIFF' and data[8:12]==b'WEBP': mime='image/webp'
            if mime not in {'image/png', 'image/jpeg', 'image/gif', 'image/apng', 'image/webp', 'image/svg+xml'}: raise ValueError('Invalid image: ' + url)
            # SVG is loaded as an image in a script-disabled sandbox, never inline.
            images[url] = 'data:' + mime + ';base64,' + base64.b64encode(data).decode()
        attrs['src'] = images[url]
        attrs['loading'] = 'lazy'
    attributes = ''.join(' ' + key + '="' + html.escape(value or '', quote=True) + '"' for key, value in attrs.items())
    return '<' + tag + attributes + '>' + ('' if tag in VOID else children + '</' + tag + '>')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'backend/resources/oi-wiki.sqlite3')
    parser.add_argument('--render-only', action='store_true', help='Re-render preserved originals without network access')
    args = parser.parse_args()
    output = args.output.resolve()
    if output == (ROOT/'data/library.sqlite3').resolve() or output.name != 'oi-wiki.sqlite3': raise ValueError('Only a separate wiki snapshot is allowed')
    if output.exists():
        backup = ROOT/'.backups/next-150/wiki-before-refresh.sqlite3'
        if backup.exists() and not args.render_only: raise ValueError('Review previous refresh recovery before refreshing again')
        if not backup.exists():
            with sqlite3.connect(output) as source, sqlite3.connect(backup) as target: source.backup(target)
    if args.render_only:
        with sqlite3.connect(output) as db:
            rows=db.execute('SELECT id,url,html,original_html FROM articles').fetchall()
            for identity,url,rendered,data in rows:
                article=next(Tree(data.decode('utf8')).root.find(lambda node:node.tag=='article'))
                class SourceImages(dict):
                    def __contains__(self,key):return True
                    def __getitem__(self,key):return key
                probe=sanitize(article,url,SourceImages())
                source_images=[node.attrs['src'] for node in Tree(probe).root.find(lambda node:node.tag=='img')]
                cached_images=[node.attrs['src'] for node in Tree(rendered).root.find(lambda node:node.tag=='img')]
                if len(source_images)!=len(cached_images):raise ValueError('Image mapping needs review: '+identity)
                db.execute('UPDATE articles SET html=? WHERE id=?',(sanitize(article,url,dict(zip(source_images,cached_images))),identity))
            db.commit()
        print('Re-rendered preserved articles:',len(rows));return
    revision = subprocess.check_output(['git','ls-remote','https://github.com/OI-wiki/OI-wiki.git','refs/heads/gh-pages'], text=True).split()[0]
    if not re.fullmatch('[a-f0-9]{40}', revision): raise ValueError('Missing immutable upstream revision')
    readme = fetch('https://raw.githubusercontent.com/OI-wiki/OI-wiki/master/README.md')[0].decode()
    if 'by-sa/4.0' not in readme or 'sata-license' not in readme: raise ValueError('Upstream license changed; review required')
    rows, images = [], {}
    for category, paths in PAGES.items():
        for path in paths:
            url = 'https://oi-wiki.org/' + path + '/'
            data, _ = fetch('https://raw.githubusercontent.com/OI-wiki/OI-wiki/' + revision + '/' + path + '/index.html')
            root = Tree(data.decode('utf8')).root
            article = next(root.find(lambda node: node.tag == 'article'), None)
            if article is None: raise ValueError('No article: ' + url)
            title = plain(next(article.find(lambda node: node.tag == 'h1'))).replace('¶', '').strip()
            text = plain(article)
            if '本页面贡献者' not in text or 'CC BY-SA 4.0' not in text or 'SATA' not in text:
                raise ValueError('Page needs individual license review: ' + url)
            rendered = sanitize(article, url, images)
            searchable = re.sub(r'\s+', ' ', plain(Tree(rendered).root))
            rows.append((path, title, category, url, revision, hashlib.sha256(data).hexdigest(), rendered, searchable, data))
            print(path, title, len(rendered), flush=True)
    # Do not publish a partial snapshot when a download or license check fails.
    with sqlite3.connect(output) as db:
        db.executescript('CREATE TABLE IF NOT EXISTS articles(id TEXT PRIMARY KEY,title TEXT,category TEXT,url TEXT,revision TEXT,sha256 TEXT,html TEXT,search_text TEXT,original_html BLOB); CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT);')
        with db:
            db.execute('DELETE FROM articles')
            db.executemany('INSERT INTO articles VALUES(?,?,?,?,?,?,?,?,?)', rows)
            for key, value in {'capturedAt':dt.datetime.now(dt.timezone.utc).isoformat(), 'revision':revision, 'license':'CC BY-SA 4.0 + SATA; individual notices retained', 'upstreamReadme':readme, 'adaptations':'Safe article extraction; accessible MathML; embedded original images; ToBe typography. No content paraphrasing.'}.items():
                db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)', (key, value))
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    print(json.dumps({'articles':len(rows), 'images':len(images), 'revision':revision}, ensure_ascii=False))

if __name__ == '__main__': main()
