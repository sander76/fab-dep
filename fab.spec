# -*- mode: python ; coding: utf-8 -*-
from sys import platform

if platform == "linux":
    pass
else:
    # work-around for https://github.com/pyinstaller/pyinstaller/issues/4064
    import distutils
    import os

    if distutils.distutils_path.endswith("__init__.py"):
        distutils.distutils_path = os.path.dirname(distutils.distutils_path)

from PyInstaller.building.api import COLLECT

block_cipher = None


a = Analysis(['fab_deploy/cli.py'],
             pathex=['C:\\Users\\sander\\Dropbox\\data\\aptana\\fab-dep'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='fab',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='fab')
