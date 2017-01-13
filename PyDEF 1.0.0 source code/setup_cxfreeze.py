import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os"], 'excludes': ['collections.abc']}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

target = Executable(
    script="pydef_main_window.py",
    base=base,
    compress=False,
    copyDependentFiles=True,
    appendScriptToExe=True,
    appendScriptToLibrary=False,
    icon="icon.ico"
    )

setup(
    name="Python for Defect Energy Formation",
    version="1.0.0",
    description="Python for Defect Energy Formation",
    author="E. Pean",
    options={"build_exe": build_exe_options},
    executables=[target]
    )
