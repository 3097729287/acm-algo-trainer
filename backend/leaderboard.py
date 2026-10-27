"""Bounded background client for the shared TB ranking service; no code upload."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import json
import hashlib
import re
import logging
import os
from pathlib import Path
import sys
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from progression import SHANGHAI

NOTICE = "排行统计 ToBe 保存的原站已确认首次 AC 题数；样例、运行与重复题不计入。记录由客户端同步，暂不提供独立防作弊认证。"


class RankingRequestError(RuntimeError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def validate_endpoint(value):
    from training import ServiceError
    if not isinstance(value, str) or len(value) > 2048:
        raise ServiceError(400, "排行榜服务地址无效")
    value = value.strip().rstrip("/")
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ServiceError(400, "排行榜服务地址无效")
    loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.scheme != "https" and not (loopback and parsed.scheme == "http"):
        raise ServiceError(400, "排行榜须使用 HTTPS 地址；本机测试可使用回环 HTTP")
    if parsed.scheme == "https" and port not in (None, 443) and not loopback:
        raise ServiceError(400, "排行榜 HTTPS 地址须使用标准 443 端口")
    return value


def default_endpoint():
    if os.environ.get("TB_OFFLINE") == "1":return ""
    if "TB_LEADERBOARD_URL" in os.environ:return validate_endpoint(os.environ["TB_LEADERBOARD_URL"])
    return bundled_endpoint()


def bundled_endpoint():
    value = ""
    from paths import resource
    path = resource('leaderboard.defaults.json')
    if not value and path.exists():
        try:
            value = json.loads(path.read_text(encoding="utf-8")).get("endpoint", "")
        except (OSError, ValueError):
            value = ""
    return validate_endpoint(value)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        # A configured service must not redirect the installation's bearer secret.
        raise URLError("排行榜服务发生重定向，请使用最终 HTTPS 地址")


def service_opener(endpoint):
    """The bundled service is reachable directly; do not tunnel it via an OJ proxy."""
    host = urlsplit(endpoint).hostname
    bundled_host = urlsplit(bundled_endpoint()).hostname
    handlers = [NoRedirect()]
    if host in {"127.0.0.1", "localhost", "::1"} or host and host == bundled_host:
        handlers.append(ProxyHandler({}))
    # Custom servers retain the user's system proxy. HTTPS verification stays
    # enabled, redirects remain forbidden and requests are never replayed.
    return build_opener(*handlers)


class LeaderboardClient:
    def __init__(self, training, timeout=10):
        self.training = training
        self.timeout = timeout
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tb-ranking")
        self.opener = None
        self.opener_endpoint = None
        self.running = False
        self.closed = False
        self.dirty = False
        self.cache = {}
        self.status = "unconfigured"
        self.error = ""
        self.last_attempt = 0
        self.retry_timer = None
        self.last_public_progress = None
        self.avatar_cache = {}

    def _request(self, profile, method, path, data=None):
        if getattr(self.training, "admin_mode", False):
            raise RankingRequestError(403, "管理员工作区不连接公共排行")
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else None
        request = Request(profile["endpoint"] + path, data=payload, method=method,
                          headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": "Bearer " + profile["auth_token"],
                                   "X-TB-User": profile["user_id"], "User-Agent": "TB/1.0.20 Ranking", "X-TB-State-Protocol": "1"})
        try:
            if self.opener_endpoint != profile['endpoint']:
                self.opener = service_opener(profile['endpoint'])
                self.opener_endpoint = profile['endpoint']
            maximum = 1024 * 1024 if method == 'GET' and path == '/v1/social' else 256 * 1024
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read(maximum + 1)
            if len(raw) > maximum:
                raise ValueError("排行榜响应过大")
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError("排行榜响应格式无效")
            return value
        except HTTPError as error:
            raise RankingRequestError(error.code, "只有管理员可以删除排行榜成绩" if error.code == 403 else f"排行榜服务返回 HTTP {error.code}") from None
        except (URLError, TimeoutError, OSError, ValueError) as error:
            # Never echo response bodies, credentials or URLs containing secrets.
            cause = getattr(error, 'reason', error)
            logging.getLogger('tb.ranking').warning('Ranking connection failed: %s %s %s',
                                                   method, path.partition('?')[0], type(cause).__name__)
            if isinstance(cause, TimeoutError):
                raise RuntimeError("排行榜服务响应超时，后台将自动重试") from error
            raise RuntimeError("排行榜服务连接失败，请检查服务地址或稍后重试") from error

    def snapshot(self):
        # TrainingService.close marks closed and later closes SQLite under this
        # same lock. A timer that already fired must not read after that barrier.
        with self.training.lock:
            if self.closed or self.training.closed or getattr(self.training, "admin_mode", False):
                return {"configured": False, "status": "closed", "endpoint": "", "lastSyncedAt": None,
                        "error": "", "notice": ""}
            profile = self.training._ranking_profile()
        with self.lock:
            configured = bool(profile["endpoint"])
            return {"configured": configured, "status": self.status if configured else "unconfigured", "endpoint": profile["endpoint"],
                    "lastSyncedAt": profile.get("last_synced_at"), "error": self.error if configured else "",
                    "notice": NOTICE if configured else "排行榜服务尚未配置；设置服务地址后自动同步。"}

    def queue_sync(self, force=False):
        with self.training.lock:
            if self.closed or self.training.closed or getattr(self.training, "admin_mode", False):
                return self.snapshot()
            profile = self.training._ranking_profile()
        with self.lock:
            if self.closed or not profile["endpoint"] or not profile['auth_token']:
                pass
            elif self.running:
                self.dirty = True
            elif force or self.status != "error" or time.monotonic() - self.last_attempt >= 60:
                if self.retry_timer:
                    self.retry_timer.cancel()
                    self.retry_timer = None
                self.running = True
                self.dirty = False
                self.status = "syncing"
                self.last_attempt = time.monotonic()
                self.executor.submit(self._sync)
        return self.snapshot()

    def invalidate(self):
        with self.lock:
            self.cache.clear()
            self.error = ""
        return self.queue_sync(force=True)

    def _sync(self):
        profile = {}
        try:
            profile = self.training._ranking_profile()
            if not profile["endpoint"] or not profile['auth_token']:
                return
            registered = self._request(profile, "GET", "/v1/profile")
            if registered.get("userId") != profile["user_id"]:
                raise RuntimeError("排行榜身份响应不匹配")
            if registered.get("publicProgressProtocol") == 1:
                payload = self.training.public_profile() if registered.get("publicAppearanceProtocol") == 1 else {"publicProgress": self.training.public_progress()}
                progress = payload["publicProgress"]
                signature = (profile["endpoint"], profile["user_id"], profile["auth_token"], payload)
                if self.last_public_progress != signature:
                    published = self._request(profile, "PUT", "/v1/profile", payload)
                    if published.get("userId") != profile["user_id"] or published.get("publicProgress") != progress:
                        raise RuntimeError("排行榜成长资料响应不匹配")
                    if "avatarData" in payload and published.get("avatarHash") != (hashlib.sha256(payload["avatarData"].encode()).hexdigest() if payload["avatarData"] else None):
                        raise RuntimeError("排行榜头像响应不匹配")
                    self.last_public_progress = signature
            events = self.training._ranking_events(profile["endpoint"])
            for offset in range(0, len(events), 100):
                with self.lock:
                    if self.closed:
                        return
                batch = events[offset:offset + 100]
                answer = self._request(profile, "POST", "/v1/events", {"events": batch})
                if answer.get("processed") != len(batch) or answer.get("scope") != "official":
                    raise RuntimeError("排行榜通过记录未完整接收")
                self.training._ranking_receipts(profile["endpoint"], batch)
            failures = []
            for period in ("daily", "weekly", "total"):
                with self.lock:
                    if self.closed:
                        return
                try:
                    value = self._request(profile, "GET", "/v1/leaderboard?" + urlencode({"period": period}))
                    if value.get("period") != period or not isinstance(value.get("entries"), list):
                        raise RuntimeError("排行榜响应格式无效")
                except RankingRequestError as error:
                    if error.status in (401, 429):
                        raise
                    failures.append(str(error))
                    continue
                except RuntimeError as error:
                    failures.append(str(error))
                    continue
                local_day = self.training._now().astimezone(SHANGHAI).date().isoformat()
                current = self.training._ranking_profile()
                with self.lock:
                    if not self.closed and all(profile[key] == current[key] for key in ('endpoint', 'user_id', 'auth_token')):
                        # An empty board is also a valid result. Publish each
                        # period before a later board or reward request can fail.
                        self.cache[period] = (time.monotonic(), value, local_day)
            rewards = self._request(profile, "GET", "/v1/rewards")
            self.training._ranking_rewards(profile, rewards)
            if failures:
                raise RuntimeError(failures[0])
            self.training._ranking_synced(profile["endpoint"])
            current_endpoint = self.training._ranking_profile()["endpoint"]
            with self.lock:
                if profile["endpoint"] == current_endpoint:
                    self.status, self.error = "ready", ""
        except Exception as error:
            if isinstance(error, RankingRequestError) and error.status == 401:
                owner = getattr(self.training.account_provider, '__self__', None)
                if owner is not None:
                    owner.invalidate(profile.get('auth_token'))
            with self.lock:
                self.status, self.error = "error", str(error)[:200]
        finally:
            with self.lock:
                rerun = self.dirty and not self.closed
                self.running = False
                self.dirty = False
            if rerun:
                self.queue_sync()
            else:
                with self.lock:
                    if not self.closed and profile.get("endpoint") and profile.get('auth_token'):
                        self.retry_timer = threading.Timer(65, self.queue_sync)
                        self.retry_timer.daemon = True
                        self.retry_timer.start()

    def rankings(self, period="daily"):
        from training import ServiceError
        if period not in {"daily", "weekly", "total"}:
            raise ServiceError(400, "排行周期须为 daily、weekly 或 total")
        state = self.snapshot()
        date = self.training._now().astimezone(SHANGHAI).date().isoformat()
        with self.lock:
            cached = self.cache.get(period)
            if cached and cached[2] != date:
                cached = None
        if state["configured"] and (cached is None or time.monotonic() - cached[0] > 60):
            self.queue_sync()
            state = self.snapshot()
        value = dict(cached[1]) if cached else {"period": period, "date": date, "entries": [], "self": None}
        value.update(state)
        value['hasSnapshot'] = cached is not None
        value['isAdmin'] = False  # User edition never exposes management authority.
        return value

    def avatar(self, user_id, expected_hash):
        from training import ServiceError
        from preferences import validate_avatar
        if not isinstance(user_id, str) or not re.fullmatch(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}', user_id) or not isinstance(expected_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_hash):
            raise ServiceError(400, '头像查询参数无效')
        profile = self.training._ranking_profile()
        if not profile.get('endpoint') or not profile.get('auth_token'):
            raise ServiceError(401, '请先登录账号')
        key = (profile['endpoint'], profile['user_id'], profile['auth_token'], user_id, expected_hash)
        with self.lock:
            if key in self.avatar_cache:
                return dict(self.avatar_cache[key])
        try:
            value = self._request(profile, 'GET', '/v1/avatars/' + user_id)
        except (RankingRequestError, RuntimeError):
            raise ServiceError(503, '头像暂时无法读取') from None
        validate_avatar(value.get('avatarData'))
        digest = hashlib.sha256(value['avatarData'].encode()).hexdigest() if value['avatarData'] else None
        if value.get('avatarHash') != digest:
            raise ServiceError(502, '头像校验失败')
        # A changed/deleted avatar is fetched under its new board hash next time.
        value = {'avatarData': value['avatarData'], 'avatarHash': digest}
        current = self.training._ranking_profile()
        if (current.get('user_id'), current.get('auth_token')) != (profile['user_id'], profile['auth_token']):
            raise ServiceError(401, '账号已切换')
        if digest == expected_hash:
            with self.lock:
                if len(self.avatar_cache) >= 100:
                    self.avatar_cache.pop(next(iter(self.avatar_cache)))
                self.avatar_cache[key] = value
        return dict(value)

    def admin_delete(self, body):
        from training import ServiceError
        raise ServiceError(403,'排行榜管理仅在独立管理员版中提供')

    def social(self, body=None, action=None):
        """Protocol boundary: an older service remains usable without social tables."""
        from training import ServiceError
        profile = self.training._ranking_profile()
        empty = {'available': False, 'protocol': 1, 'totalLikes': 0, 'unreadCount': 0, 'notifications': [], 'activity': []}
        if not profile.get('endpoint') or not profile.get('auth_token'):
            if action:
                raise ServiceError(409, '请先登录账号')
            return empty
        allowed = {'likes': ({'targetId'},), 'comments': ({'targetId', 'text', 'requestId'},), 'read': ({'ids'}, {'all'})}
        if action and (action not in allowed or not isinstance(body, dict) or set(body) not in allowed[action]
                       or action == 'read' and 'all' in body and body['all'] is not True):
            raise ServiceError(400, '互动请求格式无效')
        try:
            value = self._request(profile, 'POST' if action else 'GET', '/v1/social' + ('/' + action if action else ''), body if action else None)
        except RankingRequestError as error:
            if error.status in (404, 405, 501):
                if not action:
                    return empty
                raise ServiceError(503, '互动服务正在升级，请稍后重试') from None
            if error.status == 401:
                owner = getattr(self.training.account_provider, '__self__', None)
                if owner is not None:
                    owner.invalidate(profile.get('auth_token'))
            messages = {400: '互动内容无效，留言须为 1–500 字', 401: '登录已失效，请重新登录', 409: '这条留言请求已被使用，请重新打开后发送', 429: '操作较频繁，请稍后重试', 503: '互动服务正在升级，请稍后重试'}
            raise ServiceError(error.status, messages.get(error.status, '互动服务暂时不可用')) from None
        except RuntimeError as error:
            raise ServiceError(503, str(error)) from None
        if action == 'likes':
            # A stale ranking refresh must not restore an unliked button.
            with self.lock:
                self.cache.clear()
        return value

    def list_likes(self, ids=None, body=None):
        from training import ServiceError
        from urllib.parse import urlencode
        profile = self.training._ranking_profile()
        empty = {'available': False, 'likes': {}}
        if body is not None and (not isinstance(body, dict) or not {'listId'} <= set(body) <= {'listId','liked'} or
                                 'liked' in body and type(body['liked']) is not bool):
            raise ServiceError(400, '题单点赞格式无效')
        if ids is not None and (len(ids) > 100 or any(not isinstance(item, str) or len(item) > 160 for item in ids)):
            raise ServiceError(400, '题单编号无效')
        if not profile.get('endpoint') or not profile.get('auth_token'):
            if body is not None:
                raise ServiceError(409, '请先登录账号')
            return empty
        path = '/v1/training-list-likes'
        if body is None:
            path += '?' + urlencode([('id', item) for item in ids or []])
        try:
            return self._request(profile, 'POST' if body is not None else 'GET', path, body)
        except RankingRequestError as error:
            if body is None and error.status in (404, 405, 501):
                return empty
            if error.status == 401:
                owner = getattr(self.training.account_provider, '__self__', None)
                if owner is not None:
                    owner.invalidate(profile.get('auth_token'))
            raise ServiceError(error.status if error.status not in (404,405,501) else 503,
                               '题单点赞暂不可用，请稍后重试') from None
        except RuntimeError as error:
            raise ServiceError(503, str(error)) from None

    def close(self):
        with self.lock:
            self.closed = True
            if self.retry_timer:
                self.retry_timer.cancel()
                self.retry_timer = None
        self.executor.shutdown(wait=True, cancel_futures=True)
