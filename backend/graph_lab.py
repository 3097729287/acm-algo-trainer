"""Curated lab replays reference original problems without copying identities."""
import json
from functools import lru_cache
from paths import resource
from integrations import canonical


@lru_cache(maxsize=1)
def courses():
    result = json.loads(resource('graph-lab.json').read_text(encoding='utf-8'))
    result.update(json.loads(resource('sorting-lab.json').read_text(encoding='utf-8')))
    for index, course in enumerate(json.loads(resource('sequence-replays.json').read_text(encoding='utf-8'))):
        result['sequence-' + str(index)] = course
    return result


def replay_rows(name, rows):
    course = next((item for item in courses().values() if name == '算法实验室 · ' + item['title']), None)
    if course is None:
        return None
    by_url = {canonical(row.get('url')): row for row in rows if not row.get('catalogHidden')}
    result = [by_url.get(canonical(problem['url'])) for problem in course['problems']]
    if any(row is None for row in result):
        from training import ServiceError
        raise ServiceError(422, '实验室跟做题尚未全部收录，无法生成完整题组')
    return result


def replay_events(rows):
    urls = {canonical(row.get('url')) for row in rows if not row.get('catalogHidden')}
    return [{'name': '算法实验室 · ' + course['title'], 'displayName': course['title'],
             'labTopic': course['title'], 'count': 5, 'expectedCount': 5,
             'complete': all(canonical(p['url']) in urls for p in course['problems']),
             'duration': 180, 'durationSource': '可调整的专题训练默认值', 'rules': 'acm',
             'platform': 'Codeforces', 'series': '算法实验室'} for course in courses().values()]
