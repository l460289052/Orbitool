# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['Main.py'],
             pathex=['put-your-path-here'],
             binaries=[],
             datas=[
                ('Orbitool/utils/readers/*.dll','Orbitool/utils/readers'),
                ('resources/*', 'resources') ],
            hiddenimports=['scipy.special._ufuncs_cxx',
                'scipy.linalg.cython_blas',
                'scipy.linalg.cython_lapack',
                'scipy.integrate',
                'scipy.integrate.quadrature',
                'scipy.integrate.odepack',
                'scipy.integrate._odepack',
                'scipy.integrate.quadpack',
                'scipy.integrate._quadpack',
                'scipy.integrate._ode',
                'scipy.integrate.vode',
                'scipy.integrate._dop',
                'scipy.integrate.lsoda',
                
                'pkg_resources.py2_warn'],
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
          name='Orbitool',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Orbitool')
