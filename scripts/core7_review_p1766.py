"""Check the concrete semantic counterexamples, without assuming a tie rule."""
from fractions import Fraction
from functools import lru_cache
import json
from core7_authoring import OUT


def possible_exits(segments, start):
    @lru_cache(None)
    def drop(x, height):
        hits = []
        for a, b in segments:
            assert a[0] != b[0] and a[1] != b[1]
            if min(a[0], b[0]) < x < max(a[0], b[0]):
                y = Fraction(a[1]) + Fraction(b[1]-a[1], b[0]-a[0])*(x-a[0])
                if height is None or y <= height:
                    hits.append((y, a if a[1] < b[1] else b))
        if not hits:
            return frozenset([x])
        top = max(y for y, _ in hits)
        answer = set()
        for y, low in hits:
            if y == top:
                # The current slope ignores all crossings while sliding.
                assert Fraction(low[1]) < y
                answer.update(drop(Fraction(low[0]), Fraction(low[1])))
        return frozenset(answer)
    return sorted(int(v) for v in drop(Fraction(start), None))


if __name__ == '__main__':
    cases = [
        {'name': 'undefined simultaneous first collision', 'start': 0,
         'segments': [[[-1, 2], [1, 0]], [[-1, 0], [1, 2]]], 'possibleExits': [-1, 1]},
        {'name': 'endpoint departure meets another interior at equal height', 'start': 2,
         'segments': [[[1, 4], [3, 2]], [[2, 1], [4, 3]]], 'possibleExits': [2]},
    ]
    for case in cases:
        assert possible_exits(case['segments'], case['start']) == case['possibleExits']
    report = {'source': 'https://www.luogu.com.cn/problem/P1766', 'cases': cases,
              'completeEditorial': False, 'officialSubmissions': 0}
    (OUT/'p1766-semantic-review.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print('P1766: two exact-rational counterexample reviews passed; no complete solution claimed.')
