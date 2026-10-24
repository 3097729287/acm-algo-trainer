"""Conservative Rasch benchmark score. See docs/knowledge-mastery.md."""
import math
from functools import lru_cache

MODEL = {'version': 5, 'method': 'rasch-cf2300-coverage', 'benchmark': 2300,
         'baselineMin': 800, 'baselineStep': 100, 'difficultyScale': 400/math.log(10),
         'priorMean': 1200, 'priorSd': 600, 'gridMin': 0, 'gridMax': 4000,
         'gridStep': 10, 'scoreQuantile': .1, 'interval': .95, 'calibrated': False}


def sigmoid(value):
    return 1/(1+math.exp(-value))


def benchmark_score(ability, model=None):
    """Relative expected score on a fixed, difficulty-balanced reference form."""
    p = {**MODEL, **(model or {})}
    if ability >= p['benchmark']:
        return 100.0
    anchors = range(p['baselineMin'], p['benchmark']+1, p['baselineStep'])
    numerator = sum(sigmoid((ability-d)/p['difficultyScale']) for d in anchors)
    denominator = sum(sigmoid((p['benchmark']-d)/p['difficultyScale']) for d in anchors)
    return min(100.0, 100*numerator/denominator)


@lru_cache(maxsize=8)
def _grid(parameters):
    p = dict(parameters)
    size = round((p['gridMax']-p['gridMin'])/p['gridStep'])+1
    return tuple((r, -.5*((r-p['priorMean'])/p['priorSd'])**2, benchmark_score(r, p))
                 for r in (p['gridMin']+i*p['gridStep'] for i in range(size)))


def estimate(evidence, model=None):
    p = {**MODEL, **(model or {})}
    items = sorted({item['id']: item for item in evidence}.values(), key=lambda item: item['id'])
    known = [item for item in items if item.get('rated') and type(item.get('difficulty')) in (int,float)
             and math.isfinite(item['difficulty']) and item['difficulty']>0]
    base = {'value': None, 'rawValue': None, 'interval': None, 'intervalKind': 'model',
            'participated': len(items), 'rated': len(known),
            'officialAccepted': sum(bool(item.get('solved')) for item in items)}
    if not known:
        return {**base, 'reason': '尚无已定级题目的有效作答；未练与未知难度均不补造掌握分。'}
    histogram = {}
    for item in known:
        total_weight, successes = histogram.get(item['difficulty'], (0.0,0.0))
        weight = max(0.0,min(1.0,float(item.get('weight',1))))
        histogram[item['difficulty']] = (total_weight+weight,successes+(weight if item.get('solved') else 0))
    factors = sorted(histogram.items())
    grid = _grid(tuple(sorted(p.items())))
    densities = []
    for ability, prior, _ in grid:
        density = prior
        for difficulty, (weight, successes) in factors:
            delta = (ability-difficulty)/p['difficultyScale']
            density += successes*delta-weight*(max(delta,0)+math.log1p(math.exp(-abs(delta))))
        densities.append(density)
    peak = max(densities)
    weights = [math.exp(value-peak) for value in densities]
    total = sum(weights)
    quantiles = [.025,p['scoreQuantile'],.975]
    scores, cumulative = [],0.0
    for weight, (_,_,score) in zip(weights,grid):
        cumulative += weight/total
        while len(scores)<3 and cumulative>=quantiles[len(scores)]:
            scores.append(score)
    scores += [100.0]*(3-len(scores))
    raw = scores[1]
    rounded = lambda x: math.floor(x+.5)
    value, interval = rounded(raw), [rounded(scores[0]),rounded(scores[2])]
    reason = (f"CF 2300 基准达标指数 {value}%；以 800–2300 整百难度层的参考答题能力为尺度，"
              'CF 2300 参考能力为 100%。取能力后验的 90% 单侧下界，避免少量简单题高估；'
              f"95% 模型区间 {interval[0]}–{interval[1]}%，有效已定级原题 {len(known)} 道。"
              '这是练习参考指数，非官方 CF rating 或经标定的考试通过率。')
    return {**base,'value':value,'rawValue':raw,'interval':interval,'reason':reason}
