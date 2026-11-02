"""Account-owned reading projection; the public corpus and references stay intact."""
import json
from functools import lru_cache
from knowledge import asset_path


@lru_cache(maxsize=1)
def foundation_ids():
    source = json.loads(asset_path('learning-curriculum.json').read_text(encoding='utf-8'))
    return [row['id'] for row in sorted(source['lessons'], key=lambda row: row['order'])
            if row['kind'] == 'language']


def project(training, snapshot, library):
    """Opening a problem leaves durable training evidence, even after removal.

    Drafts and receipts preserve access for older clients. Neither code nor
    receipt details leave this projection, and no new progress is manufactured.
    """
    with training.lock:
        reached = [row[0] for row in training.connection.execute('''SELECT identity FROM (
            SELECT id AS identity, active_at AS stamp FROM training
            UNION ALL SELECT problem_id,saved_at FROM drafts
            UNION ALL SELECT problem_id,submitted_at FROM submissions)
            GROUP BY identity ORDER BY MIN(stamp),identity''') if row[0]]
    references = getattr(library, 'references', {})
    queued = dict.fromkeys(identity for problem in reached for identity in references.get(problem, []))
    for entry in snapshot.get('lectures', []):
        if set(reached).intersection(entry.get('sourceProblemIds') or []):
            queued[entry['id']] = None
    return {**snapshot, 'learningQueue': {'version': 1, 'foundationIds': foundation_ids(),
            'encounteredIds': list(queued)}}
