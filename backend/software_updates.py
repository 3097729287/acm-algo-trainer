"""Opt-in installation, automatic stable-release discovery, no user data upload."""
from __future__ import annotations

from contextlib import closing
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import threading
from urllib.parse import urlsplit
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from persistence import load_document, save_document
from version import VERSION

REPOSITORY = "3097729287/acm-algo-trainer"
RELEASES = "https://github.com/" + REPOSITORY + "/releases"
FEED = "https://api.github.com/repos/" + REPOSITORY + "/releases/latest"
MAX_INSTALLER = 2 * 1024 * 1024 * 1024


def version_tuple(value):
    match = re.fullmatch(r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", str(value))
    if not match:
        raise ValueError("版本号无效")
    return tuple(map(int, match.groups()))


def trusted_url(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
        return False
    return parsed.hostname in {"api.github.com", "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}


class ReleaseRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not trusted_url(newurl):
            raise ValueError("更新下载跳转到了不受信任的地址")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class MissingDelta(ValueError):
    pass


def release_info(payload, current):
    if not isinstance(payload, dict) or payload.get("draft") or payload.get("prerelease"):
        raise ValueError("更新源没有提供正式版本")
    tag = payload.get("tag_name", "")
    latest = version_tuple(tag)
    if latest <= version_tuple(current):
        return None
    version = ".".join(map(str, latest))
    incremental = version_tuple(current) >= (1, 0, 13)
    name = ("TB-Update-" + current + "-to-" + version + "-win64.zip") if incremental else "TB-Setup-" + version + "-win64.exe"
    assets = [asset for asset in payload.get("assets", []) if asset.get("name") == name and asset.get("state") == "uploaded"]
    if len(assets) != 1:
        if incremental:
            raise MissingDelta("此版本的增量更新尚未发布完整，请稍后重试")
        raise ValueError("新版本的更新包尚未发布完整，请稍后重试")
    asset = assets[0]
    expected = RELEASES + "/download/" + tag + "/" + name
    if asset.get("browser_download_url") != expected or not re.fullmatch(r"sha256:[a-f0-9]{64}", asset.get("digest") or ""):
        raise ValueError("新版本缺少可信的更新包地址或 SHA-256 校验值")
    size = asset.get("size")
    if type(size) is not int or not 0 < size <= MAX_INSTALLER:
        raise ValueError("更新包大小无效")
    return {"kind": "delta" if incremental else "installer", "version": version, "name": name, "url": expected, "sha256": asset["digest"][7:], "size": size,
            "releaseUrl": RELEASES + "/tag/" + tag, "notes": str(payload.get("body") or "")[:12000]}


def backup_databases(state, destination):
    """Online SQLite backup includes committed WAL, never replaces live databases."""
    destination.mkdir(parents=True, exist_ok=False)
    for name in ("tb-personal.sqlite3", "tb-library.sqlite3", "tb-documents.sqlite3"):
        source = state / name
        if not source.is_file():
            continue
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as src, closing(sqlite3.connect(destination / name)) as dst:
            src.backup(dst)
            if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("个人数据库备份未通过校验，已停止更新")


class SoftwareUpdates:
    def __init__(self, state, *, current=VERSION, opener=None, offline=None):
        self.state_dir = Path(state).resolve()
        self.settings_path = self.state_dir / "software-updates.json"
        settings = load_document(self.settings_path, {"autoCheck": True})
        self.auto_check = settings.get("autoCheck", True) is not False
        self.current = current
        self.offline = os.environ.get("TB_OFFLINE") == "1" if offline is None else offline
        self.opener = opener or build_opener(ReleaseRedirect())
        self.direct_opener = None if opener is not None else build_opener(ProxyHandler({}), ReleaseRedirect())
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.workers = []
        self.release = None
        self.installer = None
        self.launcher = None
        self.guard = None
        self.status, self.error, self.checked_at = "idle", "", None
        self.downloaded = 0

    def snapshot(self):
        with self.lock:
            return {"currentVersion": self.current, "status": self.status, "autoCheck": self.auto_check,
                    "lastCheckedAt": self.checked_at, "error": self.error, "canInstall": self.launcher is not None,
                    "latestVersion": self.release["version"] if self.release else None,
                    "updateKind": self.release.get("kind") if self.release else "delta",
                    "releaseUrl": self.release["releaseUrl"] if self.release else RELEASES,
                    "notes": self.release["notes"] if self.release else "",
                    "downloadedBytes": self.downloaded, "totalBytes": self.release["size"] if self.release else 0}

    def configure(self, body):
        from training import ServiceError
        if set(body) != {"autoCheck"} or type(body["autoCheck"]) is not bool:
            raise ServiceError(400, "自动检查设置无效")
        with self.lock:
            self.auto_check = body["autoCheck"]
            save_document(self.settings_path, {"autoCheck": self.auto_check})
        if self.auto_check:
            self.check()
        return self.snapshot()

    def _spawn(self, action):
        worker = threading.Thread(target=action, name="tb-software-update", daemon=True)
        self.workers = [worker for worker in self.workers if worker.is_alive()]
        self.workers.append(worker)
        worker.start()

    def start(self):
        def automatic():
            if self.stop.wait(12):
                return
            while not self.stop.is_set():
                if self.auto_check:
                    self.check()
                if self.stop.wait(24 * 3600):
                    return
        if not self.offline:
            self._spawn(automatic)

    def _open(self, url):
        if not trusted_url(url):
            raise ValueError("更新地址无效")
        request = Request(url, headers={"User-Agent": "TB/" + self.current + " updater",
                                        "Accept": "application/vnd.github+json" if url == FEED else "application/octet-stream"})
        try:
            return self.opener.open(request, timeout=30)
        except HTTPError as error:
            # A Windows system proxy may share GitHub's anonymous API quota with
            # many users. Try one verified HTTPS direct request for this public
            # metadata only; private endpoints and asset validation stay unchanged.
            if url == FEED and self.direct_opener is not None and error.code == 403 and error.headers.get("X-RateLimit-Remaining") == "0":
                error.close()
                # ProxyHandler mutates Request.host/_tunnel_host. A fresh Request
                # is necessary, otherwise the "direct" opener still uses the proxy.
                direct_request = Request(url, headers={"User-Agent": "TB/" + self.current + " updater",
                                                      "Accept": "application/vnd.github+json"})
                return self.direct_opener.open(direct_request, timeout=30)
            raise

    def check(self):
        with self.lock:
            if self.offline or self.stop.is_set() or self.status in {"checking", "downloading", "ready", "installing"}:
                return self.snapshot()
            self.status, self.error = "checking", ""
            self._spawn(self._check)
        return self.snapshot()

    def _check(self):
        try:
            with self._open(FEED) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError("更新信息过大")
            try:
                release = release_info(json.loads(raw), self.current)
            except MissingDelta:
                # An installation that skipped releases follows verified deltas
                # through an intermediate version, without a full installer fallback.
                with self._open(FEED.rsplit('/', 1)[0] + '?per_page=100') as response:
                    history = response.read(2 * 1024 * 1024 + 1)
                if len(history) > 2 * 1024 * 1024:
                    raise ValueError('更新信息过大')
                records = json.loads(history)
                if not isinstance(records, list):
                    raise ValueError('更新版本列表无效')
                compatible = []
                for record in records:
                    if not isinstance(record,dict):continue
                    try:version_tuple(record.get('tag_name'))
                    except ValueError:continue
                    if record.get('draft') or record.get('prerelease'):
                        continue
                    try:
                        candidate = release_info(record, self.current)
                    except MissingDelta:
                        continue
                    if candidate:
                        compatible.append(candidate)
                if not compatible:
                    raise MissingDelta('暂时没有适用于当前版本的增量包，请稍后重试')
                release = max(compatible, key=lambda item: version_tuple(item['version']))
            with self.lock:
                self.release = release
                self.status = "available" if release else "current"
                self.checked_at = dt.datetime.now(dt.timezone.utc).isoformat()
        except Exception as error:
            with self.lock:
                self.status = "error"
                self.error = str(error) if isinstance(error, ValueError) else "无法连接 GitHub 检查更新，请稍后重试"

    def download(self):
        from training import ServiceError
        with self.lock:
            if not self.launcher:
                raise ServiceError(409, "请在 Windows 桌面版中安装更新")
            if self.status in {"downloading", "ready", "installing"}:
                return self.snapshot()
            if not self.release:
                raise ServiceError(409, "请先检查可用更新")
            self.status, self.error, self.downloaded = "downloading", "", 0
            self._spawn(self._download)
        return self.snapshot()

    def _download(self):
        partial = None
        try:
            release = dict(self.release)
            directory = self.state_dir.parent / "cache" / "updates"
            directory.mkdir(parents=True, exist_ok=True)
            destination = directory / release["name"]
            partial = destination.with_suffix(".download")
            digest = hashlib.sha256()
            size = 0
            with self._open(release["url"]) as response, partial.open("wb") as output:
                while True:
                    if self.stop.is_set():
                        raise RuntimeError("closed")
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    size += len(block)
                    if size > release["size"]:
                        raise ValueError("更新包大小不匹配，已停止下载")
                    digest.update(block)
                    output.write(block)
                    with self.lock:
                        self.downloaded = size
            if size != release["size"] or digest.hexdigest() != release["sha256"]:
                raise ValueError("更新包校验失败，请重新下载")
            partial.replace(destination)
            with self.lock:
                self.installer, self.status = destination, "ready"
        except Exception as error:
            if partial:
                partial.unlink(missing_ok=True)
            with self.lock:
                self.status = "error"
                self.error = str(error) if isinstance(error, ValueError) else "安装包下载失败，请检查网络后重试"

    def install(self):
        from training import ServiceError
        with self.lock:
            if self.status != "ready" or not self.installer or not self.launcher:
                raise ServiceError(409, "请先下载并校验安装包")
            if self.guard:
                self.guard()
            try:
                with self.installer.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                if digest != self.release["sha256"]:
                    self.installer = None
                    self.status = "error"
                    raise ValueError("更新包校验失败，请重新下载")
                stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                backup_databases(self.state_dir, self.state_dir / "backups" / ("before-update-" + stamp))
                self.launcher(self.installer, self.release["sha256"], self.release["version"])
                self.status = "installing"
            except Exception as error:
                raise ServiceError(409, str(error) if isinstance(error, ValueError) else "更新准备失败，程序和个人数据已保留，请重试") from error
        return self.snapshot()

    def close(self):
        self.stop.set()

