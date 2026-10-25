"""Conservative CF2300-referenced Rasch index; not calibrated exam scores.
See docs/knowledge-mastery.md. This never modifies XP, rank or user history.
"""
from __future__ import annotations
import math

from mastery_scale import MODEL, estimate

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
        from rating_evidence import evidence as difficulty_evidence
        rating = difficulty_evidence(row)
        # For uncertain scales, a solve supports the lower bound; a failure
        # is judged against the upper bound. Neither becomes false precision.
        difficulty = rating['lower'] if solved else rating['upper']
        strength *= rating['weight']
        rated = rating['known']
        result[identity] = {'id': identity, 'weight': strength, 'solved': solved,
                            'rated': rated, 'difficulty': difficulty if rated else None,
                            'independence': independent if solved else 0.0,
                            'stability': stability}
    return result


def summarize(evidence):
    result = estimate(evidence)
    width = result['interval'][1] - result['interval'][0] if result['interval'] else 100
    confidence = 'none' if result['value'] is None else 'low' if width > 50 else 'medium' if width > 25 else 'high'
    return {'mastery': result['value'], 'masteryInterval': result['interval'],
            'confidence': confidence, 'evidenceCount': result['participated'],
            'ratedEvidenceCount': result['rated'], 'masteryReason': result['reason']}
