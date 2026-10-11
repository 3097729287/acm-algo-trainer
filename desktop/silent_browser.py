"""Wake only a registered OJ connector profile, with Chromium's no-window switch."""
import json
import os
from pathlib import Path
import subprocess

from browser_bridge import EXTENSION_ID


def registered_browsers(local=None, program=None):
    local = Path(local or os.environ.get('LOCALAPPDATA', ''))
    program = Path(program or os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)'))
    for vendor, executable in [('Microsoft/Edge', program / 'Microsoft/Edge/Application/msedge.exe'),
                               ('Google/Chrome', Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Google/Chrome/Application/chrome.exe')]:
        root = local / vendor / 'User Data'
        if not executable.is_file() or not root.is_dir():
            continue
        for profile in sorted(root.iterdir()):
            if not profile.is_dir() or (profile.name != 'Default' and not profile.name.startswith('Profile ')):
                continue
            for name in ('Preferences', 'Secure Preferences'):
                try:
                    settings = json.loads((profile / name).read_text(encoding='utf-8'))
                    entry = settings.get('extensions', {}).get('settings', {}).get(EXTENSION_ID, {})
                    if entry and entry.get('state', 1) == 1:
                        yield executable, profile.name
                        break
                except (OSError, ValueError):
                    pass


def wake_browser():
    if os.name != 'nt' or os.environ.get('TB_OFFLINE') == '1':
        return False
    for executable, profile in registered_browsers():
        # No URL, headless flag, window or profile copying. An already running
        # browser only receives a silent startup request. Never terminate it.
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        subprocess.Popen([str(executable), '--no-startup-window', '--profile-directory=' + profile],
                         startupinfo=startup, creationflags=subprocess.CREATE_NO_WINDOW,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    return False
