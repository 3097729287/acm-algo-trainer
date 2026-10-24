"""Small account-owned preferences. Device state and credentials stay local."""
import base64
import binascii
import json
import re

from training import ServiceError, iso

ALLOWED = frozenset(('panelStyle', 'backdrop', 'panelOpacity', 'pageOpacities', 'widgets', 'theme', 'accent', 'motion', 'compact', 'collapsed', 'favorites', 'views',
                     'readerWidth', 'fontSize', 'libraryPageSize', 'navOrder', 'navLabels', 'navGroups', 'seenAchievements', 'showPlatforms', 'onboardingCompleted', 'avatarData', 'navSchema', 'learningPaths', 'shortcuts'))
AVATAR_DATA_MAX_BYTES = 48 * 1024


def validate_avatar(value):
    """Only bounded, embedded raster images belong in private preferences."""
    if value == '':
        return  # Clear avatar; retain the account's default initials.
    if not isinstance(value, str) or len(value) > AVATAR_DATA_MAX_BYTES:
        raise ServiceError(400, '头像须为不超过 48 KB 的 PNG、JPEG 或 WebP 图片')
    match = re.fullmatch(r'data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/]+={0,2})', value)
    if not match:
        raise ServiceError(400, '头像图片格式无效')
    try:
        data = base64.b64decode(match[2], validate=True)
    except (ValueError, binascii.Error):
        raise ServiceError(400, '头像图片编码无效') from None
    kind = match[1]
    signatures = {'png': len(data) >= 24 and data.startswith(b'\x89PNG\r\n\x1a\n') and data[12:16] == b'IHDR',
                  'jpeg': len(data) >= 4 and data.startswith(b'\xff\xd8\xff') and data.endswith(b'\xff\xd9'),
                  'webp': len(data) >= 16 and data.startswith(b'RIFF') and data[8:12] == b'WEBP'
                          and int.from_bytes(data[4:8], 'little') == len(data) - 8}
    if not signatures[kind]:
        raise ServiceError(400, '头像内容与图片类型不一致')


def receipt_bindings(rows):
    """Numeric owner IDs travel in the existing private preference journal."""
    saved = next((row.get('value') for row in rows if row.get('key') == 'receipt-bindings'), '{}')
    try:
        value = json.loads(saved)
    except (TypeError, ValueError):
        value = {}
    if not isinstance(value, dict):
        value = {}
    return {site: handle if isinstance(handle := value.get(site), str) and re.fullmatch(r'\d{1,20}', handle) else ''
            for site in ('nowcoder', 'luogu')}


def save_receipt_bindings(training, accounts):
    value = json.dumps({site: accounts.get(site, '') for site in ('nowcoder', 'luogu')}, sort_keys=True)
    with training.lock:
        previous = training.connection.execute("SELECT value FROM account_preferences WHERE key='receipt-bindings'").fetchone()
        if previous is None or previous['value'] != value:
            with training._write() as connection:
                connection.execute("INSERT INTO account_preferences VALUES('receipt-bindings',?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
                                   (value, iso(training._now())))


def read_preferences(training):
    with training.lock:
        row = training.connection.execute("SELECT value,updated_at FROM account_preferences WHERE key='ui'").fetchone()
        if row is None:
            return {'preferences': None, 'updatedAt': None}
        return {'preferences': json.loads(row['value']), 'updatedAt': row['updated_at']}


def save_preferences(training, body):
    if not isinstance(body, dict) or set(body) != {'preferences'} or not isinstance(body['preferences'], dict):
        raise ServiceError(400, '偏好设置格式无效')
    value = dict(body['preferences'])
    if set(value) - ALLOWED:
        raise ServiceError(400, '偏好设置包含不支持的字段')
    if 'shortcuts' in value:
        shortcuts = value['shortcuts']
        allowed = {'commands','sidebar','settings','search','refresh','regions','help','practice','solution','favorite','listSearch',
                   'run','submit','official','save','pane-0','pane-1','pane-2',
                   'page-mine','page-library','page-training-lists','page-paths','page-competitions','page-mock','page-records','page-growth','page-activity','page-lectures'}
        if (not isinstance(shortcuts, dict) or set(shortcuts) - allowed or any(
                not isinstance(binding, str) or len(binding) > 64 or any(ord(char) < 32 for char in binding)
                for binding in shortcuts.values())):
            raise ServiceError(400, '快捷键设置格式无效')
    if 'learningPaths' in value and (not isinstance(value['learningPaths'], dict) or len(value['learningPaths']) > 64):
        raise ServiceError(400, '题单进度格式无效')
    if 'navSchema' in value and (type(value['navSchema']) is not int or not 1 <= value['navSchema'] <= 2):
        raise ServiceError(400, '导航版本无效')
    if 'avatarData' in value:
        validate_avatar(value['avatarData'])
    for name, allowed in (('panelStyle', {'minimal', 'outlined', 'aurora', 'blueprint'}),
                          ('backdrop', {'none', 'aurora', 'grid', 'sunset', 'custom'})):
        if name in value and (not isinstance(value[name], str) or value[name] not in allowed):
            raise ServiceError(400, '外观选项无效')
    if 'widgets' in value and type(value['widgets']) is not bool:
        raise ServiceError(400, '训练挂件选项无效')
    for name in ('showPlatforms', 'onboardingCompleted'):
        if name in value and type(value[name]) is not bool:
            raise ServiceError(400, '界面选项格式无效')
    if 'panelOpacity' in value and (type(value['panelOpacity']) is not int or not 0 <= value['panelOpacity'] <= 100):
        raise ServiceError(400, '面板不透明度须为 0–100')
    if 'fontSize' in value and (type(value['fontSize']) is not int or not 13 <= value['fontSize'] <= 22):
        raise ServiceError(400, '界面字号须为 13–22')
    if 'libraryPageSize' in value and (type(value['libraryPageSize']) is not int or not 10 <= value['libraryPageSize'] <= 200):
        raise ServiceError(400, '题库每页题数须为 10–200')
    if 'pageOpacities' in value:
        opacities = value['pageOpacities']
        if (not isinstance(opacities, dict) or set(opacities) - {'mine','library','training-lists','competitions','mock','rankings','growth','records','activity','lectures','settings','statement','editor','solution','paths'}
                or any(type(opacity) is not int or not 0 <= opacity <= 100 for opacity in opacities.values())):
            raise ServiceError(400, '界面不透明度须为 0–100')
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    except (ValueError, TypeError):
        raise ServiceError(400, '偏好设置格式无效') from None
    if len(text.encode('utf-8')) > 128 * 1024:
        raise ServiceError(400, '偏好设置过大，请减少收藏或保存的筛选')
    for name in ('favorites', 'seenAchievements', 'navOrder', 'views'):
        if name in value and not isinstance(value[name], list):
            raise ServiceError(400, '偏好设置列表格式无效')
    for name in ('navLabels', 'navGroups'):
        if name in value and not isinstance(value[name], dict):
            raise ServiceError(400, '导航偏好格式无效')
    if 'seenAchievements' in value and (len(value['seenAchievements']) > 256 or any(
            not isinstance(identity, str) or not re.fullmatch(r'[a-z0-9-]{1,80}', identity)
            for identity in value['seenAchievements'])):
        raise ServiceError(400, '成就已读记录格式无效')
    with training.lock:
        row = training.connection.execute("SELECT value FROM account_preferences WHERE key='ui'").fetchone()
        # Read acknowledgements are monotonic. A delayed save of appearance or
        # favourites must not make an already inspected achievement unread.
        previous = json.loads(row['value']) if row else {}
        if previous.get('onboardingCompleted'):
            value['onboardingCompleted'] = True
            text = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
        if 'seenAchievements' in previous or 'seenAchievements' in value:
            value['seenAchievements'] = merge_seen_achievements(previous.get('seenAchievements'), value.get('seenAchievements'))
            text = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
        if row is None or row['value'] != text:
            with training._write() as connection:
                connection.execute("INSERT INTO account_preferences VALUES('ui',?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
                                   (text, iso(training._now())))
        return read_preferences(training)


def merge_seen_achievements(*values):
    """Union legacy/read acknowledgements while discarding malformed entries."""
    return list(dict.fromkeys(identity for value in values if isinstance(value, list)
                              for identity in value if isinstance(identity, str)
                              and re.fullmatch(r'[a-z0-9-]{1,80}', identity)))
