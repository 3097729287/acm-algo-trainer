"""Small account-owned preferences. Device state and credentials stay local."""
import json
import re

from training import ServiceError, iso

ALLOWED = frozenset(('panelStyle', 'backdrop', 'panelOpacity', 'widgets', 'theme', 'accent', 'motion', 'compact', 'collapsed', 'favorites', 'views',
                     'readerWidth', 'fontSize', 'navOrder', 'navLabels', 'navGroups', 'seenAchievements'))


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
    for name, allowed in (('panelStyle', {'minimal', 'outlined', 'aurora', 'blueprint'}),
                          ('backdrop', {'none', 'aurora', 'grid', 'sunset', 'custom'})):
        if name in value and (not isinstance(value[name], str) or value[name] not in allowed):
            raise ServiceError(400, '外观选项无效')
    if 'widgets' in value and type(value['widgets']) is not bool:
        raise ServiceError(400, '训练挂件选项无效')
    if 'panelOpacity' in value and (type(value['panelOpacity']) is not int or not 25 <= value['panelOpacity'] <= 100):
        raise ServiceError(400, '面板不透明度须为 25–100')
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
