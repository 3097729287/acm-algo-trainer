"""Read the public Nowcoder list's actual numeric difficulty column.

The individual statement page omits this column. Blank values stay unknown.
Full HTML snapshots are cached in the system temporary directory, outside the
workspace's nearly full volume. No login, mutation or submission is involved.
"""
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import tempfile
import time
from urllib.request import Request, urlopen

from nowcoder_editorials import CONTENT, OUT, ROOT, read, sha, write


class Rows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.identity = None
        self.cells = []
        self.cell = None
        self.title = None
        self.title_parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr' and 'data-problemid' in attrs:
            self.identity = int(attrs['data-problemid'])
            self.cells = []
            self.title_parts = []
        elif self.identity is not None and tag == 'td':
            self.cell = []
        elif self.identity is not None and tag == 'a' and attrs.get('class') == 'title':
            self.title = True

    def handle_data(self, text):
        if self.cell is not None:
            self.cell.append(text)
        if self.title:
            self.title_parts.append(text)

    def handle_endtag(self, tag):
        if tag == 'a':
            self.title = False
        if tag == 'td' and self.cell is not None:
            self.cells.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and self.identity is not None:
            assert len(self.cells) == 5, self.cells
            rating = self.cells[2]
            assert not rating or rating.isdigit(), rating
            self.rows.append({'id': 'nowcoder-global::' + str(self.identity),
                              'title': ''.join(self.title_parts).strip(),
                              'difficulty': int(rating) if rating else None,
                              'acceptedUsers': int(self.cells[3])})
            self.identity = None


def main():
    cache = Path(tempfile.gettempdir()) / 'tobe-nowcoder-public-rating-20261108'
    cache.mkdir(exist_ok=True)

    def page(number):
        url = ('https://ac.nowcoder.com/acm/problem/list?asc=true&difficulty=0&keyword=&order=id'
               f'&page={number}&pageSize=50&platformTagId=0&sourceTagId=0&status=all&tagId=')
        path = cache / f'{number:03}.html'
        for attempt in range(4):
            try:
                if path.exists():
                    data = path.read_bytes()
                else:
                    time.sleep(0.3)
                    request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urlopen(request, timeout=25) as response:
                        data = response.read()
                text = data.decode('utf-8')
                match = re.search(r'pageInfo:\s*(\{[^\n]+\})', text)
                assert match, 'No public list pagination'
                info = json.loads(match[1])
                parser = Rows()
                parser.feed(text)
                assert len(parser.rows) == info['pageSize'] or number == info['pageCount']
                if not path.exists():
                    path.write_bytes(data)
                return info, [dict(row, sourceUrl=url, sourceHtmlSha256=sha(data)) for row in parser.rows]
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(1 + 2 * attempt)

    first_info, first = page(1)
    pages = first_info['pageCount']
    all_rows = {row['id']: row for row in first}
    print('Public list pages:', pages, 'rows:', first_info['totalCount'], flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        for count, (info, rows) in enumerate(pool.map(page, range(2, pages + 1)), 2):
            assert info['totalCount'] == first_info['totalCount'], 'List changed during scan; retry cached scan'
            for row in rows:
                assert row['id'] not in all_rows, row['id']
                all_rows[row['id']] = row
            if count % 20 == 0 or count == pages:
                print('Read pages:', count, '/', pages, flush=True)
    assert len(all_rows) == first_info['totalCount']
    scope = {x['id']: x for x in read(ROOT / 'data/next-local/nowcoder-training-coverage.json')['problems']}
    result = {identity: all_rows.get(identity, {'id': identity, 'difficulty': None, 'notInPublicList': True})
              for identity in scope}
    report = {'checkedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
              'source': 'Nowcoder public problem list; numeric difficulty column, not accepted-user count',
              'listTotal': len(all_rows), 'listPages': pages, 'scopeTotal': len(scope),
              'ratedScope': sum(x['difficulty'] is not None for x in result.values()),
              'scope': result}
    write(CONTENT / 'official-ratings.json', report)
    write(OUT / 'official-rating-fetch.json', {k: v for k, v in report.items() if k != 'scope'})
    print(json.dumps({k: v for k, v in report.items() if k != 'scope'}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
