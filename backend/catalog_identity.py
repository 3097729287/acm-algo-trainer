"""One visible row per original task; stored aliases and personal work survive."""
from insights import canonical_url
import re


def remote_aliases(row):
    """Stable historic discovery IDs, derived only from the original task URL."""
    url=str(row.get('url') or '').split('?')[0].rstrip('/')
    patterns=(('atcoder',r'https://atcoder\.jp/contests/([\w-]+)/tasks/[\w-]+_([a-zA-Z]\d?)'),
              ('codeforces',r'https://(?:www\.)?codeforces\.com/(?:contest|gym)/(\d+)/problem/([a-zA-Z]\d?)'),
              ('nowcoder',r'https://ac\.nowcoder\.com/acm/contest/(\d+)/([a-zA-Z]\d?)'))
    for platform,pattern in patterns:
        match=re.fullmatch(pattern,url)
        if match:return [f'remote:{platform}:{match[1]}::{match[2].upper()}']
    return []


def unique_catalog_rows(rows):
    grouped = {}
    for row in rows:
        key = canonical_url(row.get('url')) or ('id', row['id'])
        grouped.setdefault(key, []).append(row)
    result = []
    for entries in grouped.values():
        preferred = min(entries, key=lambda row: (
            bool(row.get('catalogHidden')), row.get('source') == 'remote',
            not bool(row.get('solutionAvailable')), not bool(row.get('statementAvailable')),
        ))
        item = dict(preferred)
        aliases = list(dict.fromkeys(identity for row in entries
                                   for identity in [row['id'], *row.get('aliasIds', []), *remote_aliases(row)]))
        if len(aliases) > 1:
            item['aliasIds'] = aliases
        for field in ('tags', 'knowledgeCategories'):
            item[field] = list(dict.fromkeys(value for row in entries for value in row.get(field, [])))
        for field in ('solutionAvailable', 'detailedSolutionAvailable', 'statementAvailable'):
            if any(row.get(field) for row in entries):
                item[field] = True
        result.append(item)
    return result
