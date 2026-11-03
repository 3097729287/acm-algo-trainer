"""Export a bounded, source-verified public problem pool; never write the library."""
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent.parent


def build():
    source = ROOT / 'data/library.sqlite3'
    db = sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True)
    candidates = json.loads((ROOT / 'server/leaderboard/src/duel-problems.json').read_text('utf8'))['problems']
    problems = []
    per_rating = {}
    for item in candidates:
        difficulty = item['difficulty']
        if not 800 <= difficulty <= 1500 or per_rating.get(difficulty, 0) >= 4:
            continue
        row = db.execute('SELECT s.content,r.markdown FROM problems p JOIN statements s ON s.problem_id=p.id JOIN solutions r ON r.problem_id=p.id WHERE p.id=? AND p.url=?', (item['libraryId'], item['url'])).fetchone()
        if not row:
            continue
        statement = json.loads(row[0])
        markdown = statement.get('markdown', '')
        integrity = statement.get('integrity', {})
        if not integrity.get('sourceVerified') or integrity.get('status') != 'complete' or statement.get('images') or len(markdown) > 18000 or not statement.get('samples'):
            continue
        # Library cleanup may append the original samples after integrity audit.
        # Bind this exact public snapshot separately from its source-document hash.
        source_hash = hashlib.sha256(markdown.encode()).hexdigest()
        translated = statement.get('translation', {})
        display = translated.get('markdown') if translated.get('sourceHash') == source_hash else None
        problems.append({'id': item['libraryId'], 'title': item['title'], 'url': item['url'], 'difficulty': difficulty,
                         'markdown': markdown, 'displayMarkdown': display or markdown, 'limits': statement.get('limits', {}),
                         'reference': row[1][:18000], 'sourceSha256': source_hash, 'sourceDocuments': integrity['sourceDocuments']})
        per_rating[difficulty] = per_rating.get(difficulty, 0) + 1
    db.close()
    if not problems:
        raise RuntimeError('No source-verified complete problems')
    output = ROOT / 'server/leaderboard/src/thought-problems.json'
    output.write_text(json.dumps({'schema': 1, 'problems': problems}, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'problems': len(problems), 'ratings': per_rating, 'bytes': output.stat().st_size}))


if __name__ == '__main__':
    build()
