"""One visible row per original task; stored aliases and personal work survive."""
from insights import canonical_url


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
                                   for identity in [row['id'], *row.get('aliasIds', [])]))
        if len(aliases) > 1:
            item['aliasIds'] = aliases
        for field in ('tags', 'knowledgeCategories'):
            item[field] = list(dict.fromkeys(value for row in entries for value in row.get(field, [])))
        for field in ('solutionAvailable', 'detailedSolutionAvailable', 'statementAvailable'):
            if any(row.get(field) for row in entries):
                item[field] = True
        result.append(item)
    return result
