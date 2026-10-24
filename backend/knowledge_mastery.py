"""Rasch/EAP practice index; provisional parameters, not calibrated exam scores.
See docs/knowledge-mastery.md. This never modifies XP, rank or user history.
"""
from __future__ import annotations
import math

MODEL = {'version': 4, 'method': 'rasch-eap', 'difficultyCenter': 1600,
         'difficultyScale': 400, 'priorSd': 1.5, 'gridMin': -8,
         'gridMax': 8, 'gridStep': .05, 'referenceDifficulty': 1600,
         'interval': .95, 'calibrated': False}
JUDGED_FAILURES = {'WA', 'TLE', 'MLE', 'RE', 'OLE'}


def is_rated(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def problem_evidence(library, grouped, official):
    result = {}
    for identity in sorted(set(grouped) | set(official)):
        row = library.get(identity)
        if not row:
            continue
        records = sorted((record for record in grouped.get(identity, [])
                          if record.get('scope') == 'official'
                          and record.get('mode', 'submit') == 'submit'
                          and record.get('finished_at')
                          and record.get('verdict') in JUDGED_FAILURES | {'AC'}),
                         key=lambda record: record.get('submitted_at') or '')
        if not records and identity not in official:
            continue
        solved = identity in official
        first_ac = next((record for record in records if record.get('verdict') == 'AC'), None)
        failures = 0
        for record in records:
            if record.get('verdict') == 'AC':
                break
            failures += 1
        independent = (.25 if first_ac.get('solution_seen') else
                       1.0 if str(first_ac.get('code') or '').strip() else .65) if first_ac else .65
        stability = 1 / (1 + min(8, failures)) if solved else 0.0
        # Power likelihood: assisted/retried AC is weaker evidence. Retries do
        # not become independent questions. This is a TB-specific adaptation.
        strength = independent * math.sqrt(stability) if solved else 1.0
        difficulty = row.get('difficulty')
        rated = is_rated(difficulty)
        result[identity] = {'id': identity, 'weight': strength, 'solved': solved,
                            'rated': rated, 'difficulty': difficulty if rated else None,
                            'independence': independent if solved else 0.0,
                            'stability': stability}
    return result


def _sigmoid(value):
    return 1 / (1 + math.exp(-value))


def estimate(evidence, model=None):
    """Same quadrature as frontend/src/lib/knowledgeMastery.js."""
    p = {**MODEL, **(model or {})}
    items = sorted({item['id']: item for item in evidence}.values(), key=lambda item: item['id'])
    known = [item for item in items if item.get('rated') and is_rated(item.get('difficulty'))]
    base = {'value': None, 'interval': None, 'participated': len(items),
            'rated': len(known), 'officialAccepted': sum(bool(item.get('solved')) for item in items)}
    if not known:
        return {**base, 'reason': '尚无已定级题目的有效作答；未知难度不补造分数。'}
    histogram = {}
    for item in known:
        total_weight, successes = histogram.get(item['difficulty'], (0.0, 0.0))
        weight = max(0.0, min(1.0, float(item.get('weight', 1))))
        histogram[item['difficulty']] = (total_weight + weight, successes + (weight if item.get('solved') else 0.0))
    factors = [((difficulty-p['difficultyCenter'])/p['difficultyScale'], *weights)
               for difficulty, weights in sorted(histogram.items())]
    points = []
    size = round((p['gridMax'] - p['gridMin']) / p['gridStep']) + 1
    reference = (p['referenceDifficulty'] - p['difficultyCenter']) / p['difficultyScale']
    for index in range(size):
        theta = p['gridMin'] + index * p['gridStep']
        log_density = -.5 * (theta / p['priorSd']) ** 2
        for beta, total_weight, successes in factors:
            delta = theta - beta
            softplus = max(delta, 0) + math.log1p(math.exp(-abs(delta)))
            log_density += successes * delta - total_weight * softplus
        points.append((log_density, _sigmoid(theta - reference)))
    peak = max(point[0] for point in points)
    weights = [math.exp(point[0] - peak) for point in points]
    total = sum(weights)
    value = math.floor(100 * sum(weight * point[1] for weight, point in zip(weights, points)) / total + .5)
    bounds, cumulative = [], 0.0
    for weight, point in zip(weights, points):
        cumulative += weight / total
        while len(bounds) < 2 and cumulative >= (.025 if not bounds else .975):
            bounds.append(math.floor(100 * point[1] + .5))
    bounds += [100] * (2 - len(bounds))
    reason = (f"Rasch 估计指数 {value}%，95% 模型区间 {bounds[0]}–{bounds[1]}%；"
              f"{len(known)} 道不同的已定级题。辅助通过和反复试错降低证据强度；"
              '统一参照难度 1600。参数尚未经群体标定，区间不含模型误差，不代表考试通过率。')
    return {**base, 'value': value, 'interval': bounds, 'reason': reason}


def summarize(evidence):
    result = estimate(evidence)
    width = result['interval'][1] - result['interval'][0] if result['interval'] else 100
    confidence = 'none' if result['value'] is None else 'low' if width > 50 else 'medium' if width > 25 else 'high'
    return {'mastery': result['value'], 'masteryInterval': result['interval'],
            'confidence': confidence, 'evidenceCount': result['participated'],
            'ratedEvidenceCount': result['rated'], 'masteryReason': result['reason']}
