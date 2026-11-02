"""Bounded, private administrator test workspaces; never reset a user journal."""
from contextlib import contextmanager
import datetime as dt
from pathlib import Path
import secrets
import threading
import uuid

from persistence import load_document, save_document
from training import ServiceError


class AdminScenarios:
    LIMIT = 5

    def __init__(self, server, factory):
        if not server.admin_mode:
            raise ServiceError(404, '没有找到这个接口')
        self.server, self.factory = server, factory
        self.original = server.training
        self.root = server.state_dir / 'admin-scenarios'
        self.path = server.state_dir / 'admin-scenarios.json'
        self.condition = threading.Condition()
        self.readers = self.waiting = 0
        self.writer = self.closed = False
        self.services = {'maintenance': self.original}
        value = load_document(self.path, {})
        self.records = value.get('workspaces', []) if value.get('schema') == 1 else []
        if (not isinstance(self.records, list) or len(self.records) > self.LIMIT
                or any(not isinstance(row, dict) or not self.valid_id(row.get('id')) for row in self.records)
                or len({row['id'] for row in self.records}) != len(self.records)):
            raise ServiceError(409, '测试工作区清单无效，原文件已保留')
        self.active = value.get('active', 'maintenance')
        if self.active != 'maintenance' and not any(row['id'] == self.active for row in self.records):
            raise ServiceError(409, '测试工作区清单无效，原文件已保留')
        if self.active != 'maintenance':
            server.training = self._open(self.active)

    @staticmethod
    def valid_id(value):
        try:
            return isinstance(value, str) and str(uuid.UUID(value)) == value
        except (ValueError, TypeError, AttributeError):
            return False

    @contextmanager
    def request_context(self, changing=False):
        with self.condition:
            if changing:
                self.waiting += 1
            try:
                ready = self.condition.wait_for(
                    lambda: not self.writer and (self.readers == 0 if changing else self.waiting == 0), 3)
                if not ready or self.closed:
                    raise ServiceError(503, '上一次账号操作仍在收尾，本机数据已保留，请稍后重试')
                if changing:
                    self.writer = True
                else:
                    self.readers += 1
            finally:
                if changing:
                    self.waiting -= 1
                    self.condition.notify_all()
        try:
            yield
        finally:
            with self.condition:
                if changing:
                    self.writer = False
                else:
                    self.readers -= 1
                self.condition.notify_all()

    def _folder(self, identity):
        if not self.valid_id(identity):
            raise ServiceError(400, '测试工作区无效')
        target = self.root / identity
        if self.root.is_symlink() or self.root.is_junction() or target.is_symlink() or target.is_junction():
            raise ServiceError(409, '测试工作区路径无效，原文件已保留')
        if target.resolve().parent != self.root.resolve():
            raise ServiceError(409, '测试工作区路径无效，原文件已保留')
        return target

    def _open(self, identity):
        if identity not in self.services:
            target = self._folder(identity) / 'tb-personal.sqlite3'
            if not target.is_file():
                raise ServiceError(409, '测试工作区缺失，原清单已保留')
            service = self.factory(target)
            service.admin_simulation = True
            self.services[identity] = service
        return self.services[identity]

    def _save(self):
        save_document(self.path, {'schema': 1, 'active': self.active, 'workspaces': self.records})

    def snapshot(self):
        service = self.server.training
        new_account = False
        if self.active != 'maintenance':
            from preferences import read_preferences
            new_account = (read_preferences(service)['preferences'] or {}).get('onboardingCompleted') is not True
        return {'active': self.active, 'kind': 'maintenance' if self.active == 'maintenance' else 'fresh',
                'newAccount': new_account, 'workspaces': list(self.records), 'limit': self.LIMIT}

    def apply(self, body):
        if not isinstance(body, dict):
            raise ServiceError(400, '测试工作区无效')
        action = body.get('action')
        if action == 'fresh' and set(body) == {'action', 'requestId'} and self.valid_id(body['requestId']):
            identity = body['requestId']
            # Replaying an acknowledged reset cannot create another journal or
            # switch away from a later explicit workspace choice.
            if any(row['id'] == identity for row in self.records):
                return dict(self.snapshot(), replayed=True)
            if len(self.records) >= self.LIMIT:
                raise ServiceError(409, '请先回收旧的测试工作区')
            from accounts import Accounts
            Accounts._assert_idle(self)
            folder = self._folder(identity)
            if folder.exists():
                raise ServiceError(409, '测试工作区已存在，原文件已保留')
            folder.mkdir(parents=True)
            service = self.factory(folder / 'tb-personal.sqlite3')
            service.admin_simulation = True
            service._admin_simulation_raw_xp = 0
            from admin import controls
            controls(service, {'level': 1, 'tier': 0, 'allAchievements': False})
            record = {'id': identity, 'createdAt': dt.datetime.now(dt.timezone.utc).isoformat()}
            self.records.append(record)
            self.services[identity] = service
            self.active = identity
            try:
                self._save()
            except Exception:
                self.records.remove(record)
                self.active = next((key for key, value in self.services.items() if value is self.server.training), 'maintenance')
                self.services.pop(identity).close()
                raise
            self.server.training = service
            self.server.store.token = secrets.token_urlsafe(32)
        elif (action == 'maintenance' and set(body) == {'action'} or
              action == 'select' and set(body) == {'action', 'id'} and
              (body['id'] == 'maintenance' or any(row['id'] == body['id'] for row in self.records))):
            target = 'maintenance' if action == 'maintenance' else body['id']
            if self.active != target:
                from accounts import Accounts
                Accounts._assert_idle(self)
                service = self.original if target == 'maintenance' else self._open(target)
                previous = self.active
                self.active = target
                try:
                    self._save()
                except Exception:
                    self.active = previous
                    raise
                self.server.training = service
                self.server.store.token = secrets.token_urlsafe(32)
        elif action == 'recycle' and set(body) == {'action', 'id'} and self.valid_id(body['id']):
            identity = body['id']
            if identity == self.active:
                raise ServiceError(409, '请先返回维护工作区')
            record = next((row for row in self.records if row['id'] == identity), None)
            if record is None:
                return self.snapshot()
            service = self.services.pop(identity, None)
            if service is not None:
                service.close()
            from system_recycle import recycle
            folder = self._folder(identity)
            from system_recycle import _receipts
            if not (not folder.exists() and _receipts(folder)) and not recycle(folder):
                raise ServiceError(409, '回收失败，原文件已保留')
            self.records.remove(record)
            try:
                self._save()
            except Exception:
                self.records.append(record)
                raise
        else:
            raise ServiceError(400, '测试工作区无效')
        return self.snapshot()

    def close(self):
        with self.condition:
            self.closed = True
        for service in set(self.services.values()):
            service.close()
