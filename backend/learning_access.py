"""Keep early daily challenges achievable within the unlocked foundation lists."""
import json
from functools import lru_cache
from knowledge import asset_path


@lru_cache(maxsize=1)
def units():
    return json.loads(asset_path('learning-access.json').read_text(encoding='utf-8'))['units']


def challenge_filter(training):
    level = training.navigation()['level']
    if level >= 3:
        return lambda task: True
    allowed = {identity for unit in units() if unit['level'] <= level for identity in unit['problemIds']}
    rows = [row for row in training._library() if row['id'] in allowed]
    known = [row.get('difficulty') for row in rows if type(row.get('difficulty')) in (int, float)]
    ceiling = max(known, default=0)
    return lambda task: task.get('kind') != 'platforms' and task.get('minDifficulty', 0) <= ceiling
