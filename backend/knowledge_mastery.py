"""Knowledge estimates use deduplicated judged work, never catalog coverage."""
from __future__ import annotations

import math

MODEL = {'version': 2, 'minEvidence': 5, 'minRatedEvidence': 3,
         'weights': {'solving': 50, 'independence': 20, 'stability': 15, 'difficulty': 15}}
JUDGED_FAILURES = {'WA', 'TLE', 'MLE', 'RE', 'OLE'}


def problem_evidence(library, grouped, official):
    result = {}
    for identity in set(grouped) | set(official):
        row = library.get(identity)
        if not row:
            continue
        records = sorted((record for record in grouped.get(identity, [])
                          if record.get('scope') == 'official'
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
        difficulty = row.get('difficulty')
        rated = isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool) and math.isfinite(difficulty)
        weight = .75 + min(2600, max(0, difficulty)) / 2600 if rated else 1.0
        # Imported public ACs prove a result, but cannot prove independence.
        independent = (0.25 if first_ac.get('solution_seen') else 1.0 if str(first_ac.get('code') or '').strip() else .65) if first_ac else .65
        solving = 1.0 if solved else 0.0
        stability = 1 / (1 + min(8, failures)) if solved else 0.0
        strength = min(1.0, max(0.0, (difficulty - 400) / 1800)) if solved and rated else 0.0
        score = (50 * solving + 20 * independent * solving + 15 * stability + 15 * strength)
        if not rated:
            score *= 100 / 85  # Unknown difficulty receives no invented rating.
        result[identity] = {'id': identity, 'weight': round(weight, 8), 'score': round(score, 8),
                            'solved': solved, 'rated': rated, 'difficulty': difficulty if rated else None,
                            'independence': independent * solving, 'stability': stability}
    return result


def summarize(evidence):
    unique = {item['id']: item for item in evidence}
    items = list(unique.values())
    count, rated = len(items), sum(item['rated'] for item in items)
    enough = count >= MODEL['minEvidence'] and rated >= MODEL['minRatedEvidence']
    weight = sum(item['weight'] for item in items)
    mastery = math.floor(sum(item['score'] * item['weight'] for item in items) / weight + .5) if enough and weight else None
    confidence = 'none' if not count else 'low' if not enough else 'medium' if count < 10 else 'high'
    if count < MODEL['minEvidence']:
        reason = f"有效作答 {count} 题，至少需要 {MODEL['minEvidence']} 道不同题目才能判断掌握程度"
    elif rated < MODEL['minRatedEvidence']:
        reason = f"已有难度的有效作答 {rated} 题，至少需要 {MODEL['minRatedEvidence']} 道才能判断难度表现"
    else:
        reason = '按已作答题目的解决率、独立完成、提交稳定性和难度加权；不以题库总数作为分母'
    return {'mastery': mastery, 'confidence': confidence, 'evidenceCount': count,
            'ratedEvidenceCount': rated, 'masteryReason': reason}
