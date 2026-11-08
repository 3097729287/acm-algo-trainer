"""Follow verified formatting lineage without rewriting historical reviews."""
from functools import lru_cache
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def _format_revisions():
    proof=json.loads((ROOT/'data/editorial-evidence-format-20261108.json').read_text('utf8'))
    assert proof['schema']==1 and proof['proseAndStructurePreserved'] is True
    assert not proof['formatterFailures'] and not proof['formatterIssues']
    revisions={}
    for entry in proof['revisions']:
        allowed=revisions.setdefault(entry['beforeSha256'],set())
        allowed.add(entry['formattedSha256'])
        if entry.get('presentationOnly'):
            assert entry['codeAndExistingProseUnchanged'] is True and entry['addedImages']
            allowed.add(entry['presentationSha256'])
    return revisions

def reviewed_editorial_matches(markdown,reviewed_sha256):
    actual=hashlib.sha256(markdown.encode('utf8')).hexdigest()
    return actual==reviewed_sha256 or actual in _format_revisions().get(reviewed_sha256,set())
