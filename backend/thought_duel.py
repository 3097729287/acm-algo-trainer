"""Authenticated relay only. Shared service owns matchmaking, drafts and judging."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request
from leaderboard import service_opener
from training import ServiceError


class PkServiceError(ServiceError):
    def __init__(self, status, code, message):
        super().__init__(status, message)
        self.code = code


WRITES = {
    'match/join': {'requestId', 'minDifficulty', 'maxDifficulty'},
    'match/cancel': {'requestId', 'ticket'},
    'game/poll': set(),
    'game/draft': {'requestId', 'matchId', 'text', 'revision'},
    'game/submit': {'requestId', 'matchId', 'text', 'revision'},
    'game/dismiss': {'requestId', 'matchId'},
}


def relay(training, path='state', value=None):
    if value is not None and (path not in WRITES or not isinstance(value, dict) or set(value) - WRITES[path]):
        raise PkServiceError(400, 'PK_REQUEST_INVALID', '思维对决请求无效')
    if value is None and path not in {'state', 'history'}:
        import re
        if not re.fullmatch(r'history/[a-f0-9-]{36}', path):
            raise PkServiceError(404, 'PK_ROUTE_NOT_FOUND', '没有找到这个思维对决接口')
    profile = training._ranking_profile()
    owner = profile['user_id']
    if training.admin_mode or not profile['endpoint'] or not profile['auth_token']:
        raise PkServiceError(503, 'PK_UNAVAILABLE', '思维对决需要连接账号服务')
    if path == 'match/join':
        with training.lock:
            if training.active_contest():
                raise PkServiceError(409, 'PK_CONTEST_ACTIVE', '请先结束当前模拟赛')
    payload = None if value is None else json.dumps(value, ensure_ascii=False).encode('utf8')
    if payload is not None and len(payload) > 16384:
        raise PkServiceError(413, 'PK_REQUEST_TOO_LARGE', '思维对决请求内容过大')
    request = Request(profile['endpoint'] + '/api/pk/v1/' + path, data=payload,
                      headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + profile['auth_token'], 'X-TB-User': owner},
                      method='GET' if value is None else 'POST')
    try:
        with service_opener(profile['endpoint']).open(request, timeout=8) as response:
            raw = response.read(256 * 1024 + 1)
        if len(raw) > 256 * 1024:
            raise ValueError('size')
        result = json.loads(raw)
        if not isinstance(result, dict) or result.get('owner') != owner:
            raise ValueError('owner')
    except HTTPError as error:
        if error.code == 404 and path == 'state':
            error.close()
            result = {'owner': owner, 'serverNow': 0, 'status': 'idle', 'enabled': False, 'match': None, 'rating': 1000}
        else:
            code, message = 'PK_SERVICE_ERROR', '思维对决服务暂不可用'
            try:
                body = json.loads(error.read(16385))
                if isinstance(body, dict) and isinstance(body.get('code'), str) and body['code'].startswith('PK_'):
                    code = body['code'][:64]
                    if isinstance(body.get('error'), str):
                        message = body['error'][:200]
            except (OSError, ValueError):
                pass
            error.close()
            raise PkServiceError(error.code, code, message) from None
    except (URLError, TimeoutError, OSError, ValueError, RuntimeError):
        raise PkServiceError(503, 'PK_CONNECTION_FAILED', '思维对决连接中断，答卷将保留，请重新连接') from None
    if training._ranking_profile()['user_id'] != owner:
        raise PkServiceError(409, 'PK_OWNER_CHANGED', '账号已切换')
    return result
