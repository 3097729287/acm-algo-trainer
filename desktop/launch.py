"""TB 桌面入口。快捷方式应使用 Python313/pythonw.exe 启动 launch.pyw。

python.exe launch.py --check 只检查组件和构建，不会打开窗口或修改题库。
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import importlib.metadata
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import threading
import time


APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR / "backend"))
sys.path.insert(0, str(APP_DIR / "desktop"))
from paths import STATE, FRONTEND, ADMIN_MODE
DSH_DIR = STATE.parent
LOG_FILE = DSH_DIR / "logs" / "tb-web.log"
PROFILE_DIR = DSH_DIR / "cache" / "tb-web-profile"
PORT = int(os.environ.get("TB_PACKAGE_PORT", "18766" if ADMIN_MODE else "18765"))
INSTANCE_DIR = PROFILE_DIR if ADMIN_MODE or os.environ.get('TB_OFFLINE') == '1' else Path(os.environ.get('LOCALAPPDATA', str(STATE))) / 'TB' / 'desktop-instance'
PID_FILE = INSTANCE_DIR / 'instance.pid'
MUTEX_NAME = "Local\\TB." + __import__("hashlib").sha256(str(INSTANCE_DIR).lower().encode()).hexdigest()[:16] + "." + str(PORT)
LOG = logging.getLogger("tb.desktop")


def configure_logging() -> None:
    if any(isinstance(handler, RotatingFileHandler) and Path(handler.baseFilename) == LOG_FILE
           for handler in logging.getLogger().handlers):
        return
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)


def show_error(message: str) -> None:
    """pythonw 没有控制台，启动失败必须让用户看见。"""
    text = f"{message}\n\n详细记录：{LOG_FILE}"
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(None, text, "ToBe 启动失败", 0x10)
    elif sys.stderr is not None:
        print(text, file=sys.stderr)


class SingleInstance:
    """持有命名互斥锁；重复打开只聚焦同一进程的 ToBe 窗口。"""

    def __init__(self) -> None:
        self.handle = None
        self.existing = False
        if os.name == "nt":
            self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            self.kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
            self.kernel.CreateMutexW.restype = wintypes.HANDLE
            self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            self.kernel.CloseHandle.restype = wintypes.BOOL
            ctypes.set_last_error(0)
            self.handle = self.kernel.CreateMutexW(None, False, MUTEX_NAME)
            if not self.handle:
                raise ctypes.WinError(ctypes.get_last_error())
            self.existing = ctypes.get_last_error() == 183

    def focus_existing(self) -> bool:
        if os.name != "nt":
            return False
        user = ctypes.WinDLL("user32", use_last_error=True)
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
        user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user.IsWindowVisible.argtypes = [wintypes.HWND]
        user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user.SetForegroundWindow.argtypes = [wintypes.HWND]
        user.BringWindowToTop.argtypes = [wintypes.HWND]
        for _ in range(30):
            try:
                expected_pid = int(PID_FILE.read_text(encoding="ascii").strip())
            except (OSError, ValueError):
                time.sleep(0.1)
                continue
            matches = []

            @callback_type
            def visit(hwnd, _param):
                pid = wintypes.DWORD()
                user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value == expected_pid and user.IsWindowVisible(hwnd):
                    title = ctypes.create_unicode_buffer(256)
                    user.GetWindowTextW(hwnd, title, len(title))
                    if title.value in {"TB", "ToBe", "TB 管理员", "ToBe 管理员"}:
                        matches.append(hwnd)
                        return False
                return True

            user.EnumWindows(visit, 0)
            if matches:
                user.ShowWindow(matches[0], 9)
                user.BringWindowToTop(matches[0])
                user.SetForegroundWindow(matches[0])
                return True
            time.sleep(0.1)
        return False

    def close(self) -> None:
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def check_dependencies() -> dict:
    if not (FRONTEND / "index.html").is_file():
        raise RuntimeError("界面构建尚未就绪，缺少 dist/index.html。请先完成 TB 界面构建。")
    try:
        import webview
    except ImportError as exc:
        raise RuntimeError("缺少桌面组件 pywebview。请使用已安装组件的 Python 3.13 启动 TB。") from exc
    import inspect

    if "storage_path" not in inspect.signature(webview.start).parameters:
        raise RuntimeError("桌面组件版本过旧，请更新 pywebview 后再启动。")
    runtime_version = None
    if os.name == "nt":
        import winreg

        client_ids = (
            "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
            "{2CD8A007-E189-409D-A2C8-9AF4EF3C72AA}",
            "{0D50BFEC-CD6A-4F9A-964C-C7416E3ACB10}",
            "{65C35B14-6C1D-4122-AC46-7148CC9D6497}",
        )
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for prefix in ("SOFTWARE\\Microsoft", "SOFTWARE\\WOW6432Node\\Microsoft"):
                for client_id in client_ids:
                    try:
                        with winreg.OpenKey(hive, f"{prefix}\\EdgeUpdate\\Clients\\{client_id}") as key:
                            version = str(winreg.QueryValueEx(key, "pv")[0])
                        if int(version.split(".")[0]) >= 86:
                            runtime_version = version
                    except (OSError, ValueError):
                        continue
        if runtime_version is None:
            raise RuntimeError("缺少 Microsoft Edge WebView2 运行组件，请安装后再打开 ToBe。")
    from backend import start_server

    if not callable(start_server):
        raise RuntimeError("ToBe 本地服务入口不可用。")
    return {
        "python": sys.executable,
        "pywebview": importlib.metadata.version("pywebview"),
        "webview2": runtime_version,
        "url": f"http://127.0.0.1:{PORT}",
        "bundle": str(FRONTEND / "index.html"),
        "profile": str(PROFILE_DIR),
    }


def configure_desktop_downloads() -> None:
    import webview
    # Explicit exports from the trusted local UI need WebView2's save dialog.
    webview.settings['ALLOW_DOWNLOADS'] = True


def bind_desktop_fullscreen(server, window) -> None:
    from window_memory import is_fullscreen

    def desktop_state():
        try:
            return {"available": True, "fullscreen": is_fullscreen(window)}
        except Exception:
            return {"available": False, "fullscreen": False}

    def desktop_fullscreen(value):
        if bool(value) != is_fullscreen(window):
            window.toggle_fullscreen()
        return {"available": True, "fullscreen": is_fullscreen(window)}

    server.desktop_state = desktop_state
    server.desktop_fullscreen = desktop_fullscreen


def run_desktop() -> int:
    instance = SingleInstance()
    server = None
    service_thread = None
    try:
        if instance.existing:
            if not instance.focus_existing():
                show_error("ToBe 已经在运行，但暂时未找到它的窗口。请稍等后再打开，或先关闭现有 ToBe。")
                return 1
            return 0
        check_dependencies()
        if getattr(sys, 'frozen', False) and not ADMIN_MODE and os.environ.get('TB_OFFLINE') != '1':
            from legacy_cleanup import prepare
            try:
                prepare(APP_DIR)
            except Exception as issue:
                LOG.warning('Legacy migration deferred; original data retained: %s', type(issue).__name__)
        import webview
        from backend import start_server

        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(os.getpid()), encoding="ascii")
        try:
            server = start_server(port=PORT, dist_dir=FRONTEND, admin_mode=ADMIN_MODE, integration_auto_start=False if os.environ.get("TB_OFFLINE")=="1" else None)
        except OSError as exc:
            LOG.info("Default port unavailable; choosing a free local port")
            server = start_server(port=0, dist_dir=FRONTEND, admin_mode=ADMIN_MODE, integration_auto_start=False if os.environ.get("TB_OFFLINE")=="1" else None)
        service_thread = threading.Thread(target=server.serve_forever, name="tb-local-service", daemon=True)
        service_thread.start()
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}"
        LOG.info("Launching TB at %s with %s", url, sys.executable)
        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
        configure_desktop_downloads()
        from window_memory import remembered, bind
        memory_path = STATE / 'desktop-window.json'
        bounds = remembered(memory_path)
        window = webview.create_window(
            "ToBe 管理员" if ADMIN_MODE else "ToBe", url, **bounds, min_size=(1050, 700),
            background_color="#101116", text_select=True, zoomable=False,
        )
        if window is None:
            raise RuntimeError("无法创建 ToBe 窗口。")
        bind(window, memory_path)
        from webview_resources import bind as bind_resources
        bind_resources(window)
        # 桌面全屏：受本机写接口保护，通过 pywebview 原生 toggle_fullscreen 实现。
        bind_desktop_fullscreen(server, window)
        def push_status(name, value):
            window.evaluate_js('window.dispatchEvent(new CustomEvent(' + json.dumps(name) +
                               ',{detail:' + json.dumps(value, ensure_ascii=True) + '}))')
        server.submission_listener = lambda value: push_status('tb:submission-status', value)
        def push_official(value):
            with server.official_session_lock:
                session = server.official_sessions.get(value.get('sessionId'))
            if session and session.get('_training') is server.training:
                push_status('tb:official-status', value)
        from external_browser import ExternalBrowserBridge, ExternalBrowserPreparation
        official = ExternalBrowserBridge(
            STATE.parent / 'cache' / 'tb-submission-browser',
            guard=server.validate_official_url,
            on_receipt=server.record_official_receipt,
            on_pending=server.record_official_pending,
            on_status=push_official,
        )
        server.browser_bridge = official
        from platform_login import PlatformLogins
        logins = PlatformLogins(official, server.browser_account_context, server.bind_browser_account)
        server.browser_preparation = ExternalBrowserPreparation(official, logins)
        server.official_opener = official.open
        server.official_acknowledger = official.acknowledge
        server.official_submitter = official.submit
        server.official_status = official.status
        server.official_closer = official.close
        window.events.closing += official.on_closing
        if getattr(sys, 'frozen', False):
            from update_installer import launch_installer
            from training import ServiceError
            def install_update(path, digest, version):
                if path.suffix.lower() == ".zip":
                    from update_patch import launch_patch
                    launch_patch(path, digest, version, APP_DIR)
                else:
                    launch_installer(path, digest, version, APP_DIR)
                threading.Timer(1, window.destroy).start()
            server.software_updates.launcher = install_update
        server.software_updates.start()
        if getattr(sys, 'frozen', False) and not ADMIN_MODE and os.environ.get('TB_OFFLINE') != '1':
            from legacy_cleanup import start as start_legacy_cleanup
            loaded = threading.Event()
            window.events.loaded += loaded.set
            start_legacy_cleanup(APP_DIR, lambda: loaded.is_set() and bool(server.accounts.session))
            def warm_submission_browser():
                while not official.stopping.wait(.5):
                    if loaded.is_set() and server.accounts.session:
                        try:
                            official.browser.ensure(background=True)
                        except Exception as issue:
                            LOG.info('Browser warmup deferred: %s', type(issue).__name__)
                        return
            threading.Thread(target=warm_submission_browser, name='tb-browser-warmup', daemon=True).start()
        webview.start(
            gui="edgechromium", private_mode=False, storage_path=str(PROFILE_DIR),
            icon=str(APP_DIR / "tb.ico"), debug=False,
        )
        return 0
    finally:
        if server is not None:
            if service_thread is not None and service_thread.is_alive():
                server.shutdown()
            server.server_close()
        if not instance.existing:
            try:
                PID_FILE.unlink(missing_ok=True)
            except OSError:
                LOG.warning("Could not remove instance marker", exc_info=True)
        instance.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="TB 桌面应用")
    parser.add_argument("--admin", action="store_true", help="使用独立管理员数据与浏览器配置")
    parser.add_argument("--check", action="store_true", help="只检查组件，不打开窗口")
    args = parser.parse_args(argv)
    try:
        configure_logging()
        if args.check:
            print(json.dumps(check_dependencies(), ensure_ascii=False, indent=2))
            return 0
        return run_desktop()
    except Exception as exc:
        LOG.exception("TB startup failed")
        if args.check:
            if sys.stderr is not None:
                print(f"TB 检查失败：{exc}", file=sys.stderr)
        else:
            show_error(f"TB 未能启动。\n{exc}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) == 7 and sys.argv[1] == "--apply-update-patch":
        from update_patch import helper_main
        raise SystemExit(helper_main(sys.argv[2:]))
    if getattr(sys, 'frozen', False):
        configure_logging()
        from release_metadata import refresh_release_metadata
        refresh_release_metadata(APP_DIR)
    if len(sys.argv) == 3 and sys.argv[1] in ("--package-check", "--serve-check", "--serve-account-check", "--native-account-check", "--native-check", "--account-network-check"):
        from release_probe import run
        raise SystemExit(run(sys.argv[1], sys.argv[2]))
    if len(sys.argv) == 2 and sys.argv[1] == "--migrate-local":
        from migration import migrate_legacy
        result = migrate_legacy(APP_DIR)
        raise SystemExit(0 if result.get('ok') else 1)
    if len(sys.argv) == 2 and sys.argv[1] == "--retire-legacy":
        from legacy_cleanup import finish_install
        finish_install(APP_DIR)
        raise SystemExit(0)
    raise SystemExit(main())
