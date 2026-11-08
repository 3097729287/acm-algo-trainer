"""Account-bound team transport; authority and shared documents stay on server."""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request

from leaderboard import service_opener
from training import ServiceError


class TeamServiceError(ServiceError):
    def __init__(self, status, code, message):
        super().__init__(status, message)
        self.code = code


WRITES = {
    'create': {'requestId', 'name'}, 'join': {'requestId', 'inviteCode'},
    'leave': {'requestId', 'teamRevision'},
    'configure': {'requestId', 'teamRevision', 'contestId', 'durationMinutes'},
    'ready': {'requestId', 'teamRevision', 'configurationRevision', 'ready'}, 'start': {'requestId', 'teamRevision'},
    'poll': {'requestId', 'roomId', 'leaseToken'}, 'claim': {'requestId', 'roomId'},
    'release': {'requestId', 'roomId', 'leaseToken'},
    'select': {'requestId', 'roomId', 'leaseToken', 'problemId'},
    'draft': {'requestId', 'roomId', 'leaseToken', 'problemId', 'revision', 'code', 'language'},
    'authorize': {'requestId', 'roomId', 'leaseToken', 'problemId', 'revision', 'language', 'purpose', 'inputSha256'},
    'finish': {'requestId', 'roomId'},
}


def _stamp(profile):
    return tuple(profile.get(key) for key in ('user_id', 'endpoint', 'auth_token'))


def relay(training, path='state', value=None, query=None, *, internal=False):
    query = query or {}
    if value is not None:
        fields = {'requestId', 'intentId', 'submissionId', 'handle'} if internal and path == 'native-receipt' else WRITES.get(path)
        if fields is None or not isinstance(value, dict) or set(value) - fields or query:
            raise TeamServiceError(400, 'TEAM_REQUEST_INVALID', '团队训练请求无效')
    elif path not in {'state', 'catalogue', 'standings', 'history'} and not re.fullmatch(r'history/[a-f0-9-]{36}', path):
        raise TeamServiceError(404, 'TEAM_ROUTE_NOT_FOUND', '没有找到这个团队训练接口')
    if query:
        key = 'id' if path == 'catalogue' else 'problemId' if re.fullmatch(r'history/[a-f0-9-]{36}', path) else None
        if key is None or set(query) != {key} or not isinstance(query[key], list) or len(query[key]) != 1:
            raise TeamServiceError(400, 'TEAM_REQUEST_INVALID', '比赛编号无效')
        identity = query[key][0]
        valid = isinstance(identity, str) and (re.fullmatch(r'[a-z0-9:_-]{1,100}', identity) if key == 'id'
                    else 0 < len(identity) <= 512 and not re.search(r'[\x00-\x1f\x7f]', identity))
        if not valid:raise TeamServiceError(400, 'TEAM_REQUEST_INVALID', '题目编号无效')
    profile = training._ranking_profile()
    owner = profile['user_id'];context = _stamp(profile)
    if training.admin_mode or not profile.get('endpoint') or not profile.get('auth_token'):
        raise TeamServiceError(503, 'TEAM_UNAVAILABLE', '团队训练需要连接账号服务')
    if value is not None and (path == 'start' or path == 'ready' and value.get('ready') is True):
        with training.lock:
            if training.active_contest():
                raise TeamServiceError(409, 'TEAM_CONTEST_ACTIVE', '请先结束当前比赛')
    try:
        payload = None if value is None else json.dumps(value, ensure_ascii=False).encode('utf8')
    except UnicodeError:
        raise TeamServiceError(400, 'TEAM_REQUEST_INVALID', '代码必须是有效文本') from None
    if payload is not None and len(payload) > 262144:
        raise TeamServiceError(413, 'TEAM_REQUEST_TOO_LARGE', '团队训练请求内容过大')
    suffix = '?' + urlencode({key:values[0] for key,values in query.items()}) if query else ''
    request = Request(profile['endpoint'] + '/v1/team-training/' + path + suffix, data=payload,
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + profile['auth_token'], 'X-TB-User': owner},
        method='GET' if value is None else 'POST')
    try:
        with service_opener(profile['endpoint']).open(request, timeout=8) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError('size')
        result = json.loads(raw)
        if not isinstance(result, dict) or result.get('owner') != owner:
            raise ValueError('owner')
    except HTTPError as error:
        if error.code == 404 and path == 'state':
            error.close();result = {'owner': owner, 'serverNow': 0, 'enabled': False, 'protocol': 0, 'team': None, 'room': None}
        else:
            code, message = 'TEAM_SERVICE_ERROR', '团队训练服务暂不可用'
            try:
                body = json.loads(error.read(16385))
                if isinstance(body, dict) and isinstance(body.get('code'), str) and body['code'].startswith('TEAM_'):
                    code = body['code'][:64]
                    if isinstance(body.get('error'), str):
                        message = body['error'][:200]
            except (OSError, ValueError):
                pass
            error.close();raise TeamServiceError(error.code, code, message) from None
    except (URLError, TimeoutError, OSError, ValueError, RuntimeError):
        raise TeamServiceError(503, 'TEAM_CONNECTION_FAILED', '团队训练连接中断，请重新连接') from None
    if _stamp(training._ranking_profile()) != context:
        raise TeamServiceError(409, 'TEAM_OWNER_CHANGED', '账号已切换，请重新读取')
    return result
