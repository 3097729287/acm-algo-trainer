"""Promote the verified loader delivered below resources/ to an old 1.4 root."""
from pathlib import Path
import os
import shutil
import uuid

def prepare_loader(directory):
    root=Path(directory).resolve();source=root/'resources/legacy-upgrade/ToBeLoader.exe';target=root/'ToBeLoader.exe'
    if target.exists() or not source.is_file():return False
    if source.is_symlink() or any(parent.is_symlink() for parent in source.parents if parent!=root and parent.is_relative_to(root)):return False
    temporary=root/('loader-upgrade-'+uuid.uuid4().hex+'.part')
    try:
        shutil.copyfile(source,temporary)
        # This is the same small native loader authenticated in the update's
        # per-member manifest; no download or user-directory lookup happens.
        os.replace(temporary,target)
        return True
    except OSError:return False
