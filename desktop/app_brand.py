"""Display branding; legacy executable lookup keeps existing upgrades usable."""
from pathlib import Path

NAME = 'ToBe'
EXECUTABLE = 'ToBe.exe'
ADMIN_EXECUTABLE = 'ToBe管理员版.exe'
LEGACY_EXECUTABLE = 'TB新版.exe'


def executable(directory):
    directory = Path(directory)
    current = directory / EXECUTABLE
    return current if current.is_file() else directory / LEGACY_EXECUTABLE
