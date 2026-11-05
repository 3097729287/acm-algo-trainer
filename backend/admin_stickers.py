"""Administrator-only, local cosmetic collection with replenished stock units."""
import hashlib
import json
import math
import uuid

from sticker_rewards import catalogue
from training import ServiceError, iso

KEY = 'admin-stickers:v1'
NAMESPACE = uuid.UUID('9d16804d-99ae-4d43-886d-89bc5e26ea57')
FIELDS = {
    'place': {'requestId', 'unitId', 'revision', 'x', 'y', 'angle', 'scale'},
    'recycle': {'requestId', 'unitId', 'revision'},
    'outfit': {'requestId', 'unitId', 'revision', 'appearance'},
    'scene-save': {'requestId', 'name', 'presetId', 'inventoryRevision'},
    'scene-apply': {'requestId', 'presetId', 'inventoryRevision'},
    'scene-delete': {'requestId', 'presetId', 'inventoryRevision'},
}


def admin_catalogue():
    policy = catalogue()
    titles = dict(zip(('spark', 'leaf', 'drop', 'cloud', 'flame', 'bolt', 'sun', 'comet',
                       'moon', 'planet', 'crystal', 'butterfly', 'gem', 'crown', 'galaxy', 'phoenix'),
                      ('星星', '一片新叶', '蓝色水滴', '软绵云朵', '小火苗', '闪电', '小太阳', '彗星',
                       '月牙', '轨道星球', '水晶', '蝴蝶', '宝石', '王冠', '星河', '凤凰')))
    legacy = [{'id': rarity + '-' + shape, 'rarity': rarity, 'shape': shape}
              for rarity, shapes in [('common', ['spark', 'leaf', 'drop', 'cloud']),
                                    ('rare', ['flame', 'bolt', 'sun', 'comet']),
                                    ('epic', ['moon', 'planet', 'crystal', 'butterfly']),
                                    ('legendary', ['gem', 'crown', 'galaxy', 'phoenix'])] for shape in shapes]
    backgrounds = [{'id': f"background-{theme['id']}-{theme['rarity']}", 'kind': 'background',
                    'shape': 'background-' + theme['id'], 'theme': theme['id'],
                    'title': theme['title'], 'rarity': theme['rarity']} for theme in policy['backgroundThemes']]
    result = []
    for item in legacy + policy.get('collection', []) + policy['stickers'] + backgrounds:
        item = {'title': titles.get(item['shape'], item['shape']), **item}
        if item['id'] == 'epic-crystal':
            item['rarity'] = 'rare'
        item.update({'baseScale': 1, 'minScale': 1, 'maxScale': 1} if item.get('kind') == 'background'
                    else policy['shapePolicy'].get(item['shape'], {'baseScale': 1, 'minScale': .5, 'maxScale': 2}))
        result.append(item)
    return result


def _stock(owner, item, serials):
    identity = str(uuid.uuid5(NAMESPACE, owner + '\0' + item['id'] + '\0' + str(serials.get(item['id'], 0))))
    return {'id': identity, 'stickerId': item['id'], 'revision': 0, 'placement': None}


def _snapshot(owner, state, items):
    policy = catalogue()
    return {'owner': owner, 'revision': state['revision'], 'catalogue': items, 'unlimited': True,
            'units': state['units'] + [_stock(owner, item, state['serials']) for item in items],
            'discoveredStickers': [item['id'] for item in items], 'boxes': {}, 'backgroundRewards': {},
            'scenePresets': state['scenePresets'], 'activePresetId': state.get('activePresetId'),
            'wardrobe': policy['wardrobe'], 'packPolicy': policy['cardPacks'], 'boxPolicy': policy['levelBoxes'],
            'backgroundPolicy': policy['backgroundRewards'],
            'capabilities': {'scenes': True, 'backgrounds': True, 'wardrobe': True},
            'placementPolicy': {'scale': True, 'minScale': .35, 'maxScale': 6, 'perShape': True}}


def _placement(value, item):
    if item.get('kind') == 'background':
        return {'x': .5, 'y': .5, 'angle': 0, 'scale': 1}
    result = {key: value.get(key, 1 if key == 'scale' else None) for key in ['x', 'y', 'angle', 'scale']}
    for key, low, high in [('x', 0, 1), ('y', 0, 1), ('angle', -180, 180), ('scale', item['minScale'], item['maxScale'])]:
        number = result[key]
        if type(number) not in (int, float) or not math.isfinite(number) or not low <= number <= high:
            raise ServiceError(400, '贴纸位置或大小无效')
    return result


def stickers(training, kind=None, value=None):
    if not training.admin_mode:
        raise ServiceError(404, '没有找到这个接口')
    items = admin_catalogue()
    by_id = {item['id']: item for item in items}
    with training.lock:
        owner = training._ranking_profile()['user_id']
        row = training.connection.execute('SELECT value FROM account_preferences WHERE key=?', (KEY,)).fetchone()
        state = json.loads(row['value']) if row else {'revision': 0, 'serials': {}, 'units': [], 'scenePresets': [], 'requests': {}}
        if not kind:
            return _snapshot(owner, state, items)
        if kind not in FIELDS or not isinstance(value, dict) or set(value) - FIELDS[kind]:
            raise ServiceError(400, '贴纸操作无效')
        try:
            request = value['requestId']
            if not isinstance(request, str) or str(uuid.UUID(request)) != request or uuid.UUID(request).version != 4:
                raise ValueError()
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ServiceError(400, '请求编号无效') from None
        try:
            digest = hashlib.sha256(json.dumps([kind, value], sort_keys=True, allow_nan=False).encode()).hexdigest()
        except (ValueError, TypeError):
            raise ServiceError(400, '贴纸操作无效') from None
        previous = state['requests'].get(request)
        if previous:
            if previous != digest:
                raise ServiceError(409, '请求编号已用于其他操作')
            return _snapshot(owner, state, items)
        if kind.startswith('scene-'):
            if type(value.get('inventoryRevision')) is not int or value['inventoryRevision'] != state['revision']:
                raise ServiceError(409, '场景已在其他窗口更新，请刷新后重试')
            old = next((preset for preset in state['scenePresets'] if preset['id'] == value.get('presetId')), None)
            if kind == 'scene-save':
                name = value.get('name')
                if not isinstance(name, str) or not 1 <= len(name.strip()) <= 32:
                    raise ServiceError(400, '预设名称须为 1–32 个字')
                if value.get('presetId') and not old:
                    raise ServiceError(404, '没有找到这个预设')
                preset = {'id': old['id'] if old else str(uuid.uuid4()), 'name': name.strip(),
                          'updatedAt': iso(training._now()), 'items': [
                              {'unitId': unit['id'], **{key: unit[key] for key in ['stickerId', 'placement', 'appearance'] if key in unit}}
                              for unit in state['units']]}
                if old:
                    state['scenePresets'][state['scenePresets'].index(old)] = preset
                else:
                    state['scenePresets'].append(preset)
                state['activePresetId'] = preset['id']
            elif not old:
                raise ServiceError(404, '没有找到这个预设')
            elif kind == 'scene-delete':
                state['scenePresets'].remove(old)
                if state.get('activePresetId') == old['id']:
                    state['activePresetId'] = None
            else:
                state['units'] = []
                for entry in old['items']:
                    item = by_id.get(entry['stickerId'])
                    if not item:
                        continue
                    unit = _stock(owner, item, state['serials'])
                    state['serials'][item['id']] = state['serials'].get(item['id'], 0) + 1
                    state['units'].append({**unit, 'revision': 1, 'placement': _placement(entry['placement'], item),
                                           **({'appearance': entry['appearance']} if entry.get('appearance') else {})})
                state['activePresetId'] = old['id']
        else:
            snapshot = _snapshot(owner, state, items)
            unit = next((unit for unit in snapshot['units'] if unit['id'] == value.get('unitId')), None)
            if not unit:
                raise ServiceError(404, '没有找到这张贴纸')
            if type(value.get('revision')) is not int or value['revision'] != unit['revision']:
                raise ServiceError(409, '贴纸已更新，请刷新后重试')
            item = by_id[unit['stickerId']]
            if kind == 'place':
                point = _placement(value, item)
                if unit['placement'] is None:
                    state['serials'][item['id']] = state['serials'].get(item['id'], 0) + 1
                    state['units'].append(unit)
                if item.get('kind') == 'background':
                    state['units'] = [other for other in state['units'] if other['id'] == unit['id'] or by_id[other['stickerId']].get('kind') != 'background']
                unit.update(placement=point, revision=unit['revision'] + 1)
            elif unit['placement'] is None:
                raise ServiceError(400, '请先摆放这张贴纸')
            elif kind == 'recycle':
                state['units'].remove(unit)
            else:
                choices = catalogue()['wardrobe']
                appearance = value.get('appearance')
                if not item['shape'].startswith('person') or not isinstance(appearance, dict) or set(appearance) - set(choices):
                    raise ServiceError(400, '服装选项无效')
                if any(appearance.get(key, options[0]) not in options for key, options in choices.items()):
                    raise ServiceError(400, '服装选项无效')
                unit.update(appearance={key: appearance.get(key, options[0]) for key, options in choices.items()}, revision=unit['revision'] + 1)
        state['revision'] += 1
        state['requests'][request] = digest
        if len(state['requests']) > 512:
            state['requests'].pop(next(iter(state['requests'])))
        with training._write() as db:
            db.execute('INSERT INTO account_preferences VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                       (KEY, json.dumps(state, ensure_ascii=False, allow_nan=False), iso(training._now())))
        result = _snapshot(owner, state, items)
        if kind == 'scene-apply':
            result['scene'] = {'presetId': value['presetId'], 'missing': []}
        return result
