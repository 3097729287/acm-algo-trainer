"""Separate official CF ratings from uncertain cross-platform training bands.

The old CF-EQ representative values remain available to selection/XP migration.
Skill evidence uses their conservative bounds, never treats them as exact ratings.
"""
import math
import re


def evidence(row):
    value = row.get('difficulty')
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        return {'known': False, 'lower': None, 'upper': None, 'weight': 0, 'kind': 'unknown'}
    value = round(value / 100) * 100
    source = str(row.get('difficultySource') or '')
    official = (row.get('platform') in ('Codeforces', 'codeforces') and not row.get('difficultyEstimated')
                and bool(re.search(r'官方|official', source, re.I)) and not re.search(r'未提供|无官方', source))
    if official:
        return {'known': True, 'lower': value, 'upper': value, 'weight': 1.0, 'kind': 'official-cf'}
    band = row.get('difficultyBand')
    valid_band = (isinstance(band, (list, tuple)) and len(band) == 2
                  and all(type(x) in (int, float) and math.isfinite(x) for x in band) and 0 < band[0] <= band[1])
    # Cross-site mappings have not been population calibrated. A narrow stored
    # rounding band is not empirical confidence; do not mislabel it as such.
    width = 300 if 'AtCoder Problems' in source else 400
    low, high = (min(band[0], value-width), max(band[1], value+width)) if valid_band else (value-width, value+width)
    return {'known': True, 'lower': max(800, math.floor(low/100)*100),
            'upper': max(800, math.ceil(high/100)*100),
            'weight': .5 if 'AtCoder Problems' in source else .25, 'kind': 'estimated-cf-band'}
