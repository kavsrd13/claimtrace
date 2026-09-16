"""
Package backend for Azure App Service Linux deployment with proper POSIX permissions.
"""

import os
import shutil
import stat
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "backend"
ZIP_OUT = ROOT / "deploy.zip"
TMP = ROOT / "tmp_deploy"


def make_zip():
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)

    # Copy files
    for item in ["main.py", "config.py", "database.py", "models.py", "requirements.txt"]:
        shutil.copy2(SRC / item, TMP / item)

    for folder in ["routers", "services", "static"]:
        shutil.copytree(SRC / folder, TMP / folder, dirs_exist_ok=True)

    # Clean __pycache__
    for p in TMP.rglob("__pycache__"):
        shutil.rmtree(p)
    for p in TMP.rglob("*.pyc"):
        p.unlink()

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()

    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(TMP):
            for d in dirs:
                full_dir = os.path.join(root, d)
                rel_dir = os.path.relpath(full_dir, TMP).replace("\\", "/") + "/"
                zinfo = zipfile.ZipInfo(rel_dir)
                # POSIX directory: drwxr-xr-x (0o40755)
                zinfo.external_attr = (stat.S_IFDIR | 0o755) << 16
                zf.writestr(zinfo, "")

            for f in files:
                full_file = os.path.join(root, f)
                rel_file = os.path.relpath(full_file, TMP).replace("\\", "/")
                with open(full_file, "rb") as fp:
                    data = fp.read()
                zinfo = zipfile.ZipInfo(rel_file)
                # POSIX file: -rw-r--r-- (0o100644)
                zinfo.external_attr = (stat.S_IFREG | 0o644) << 16
                zf.writestr(zinfo, data)

    shutil.rmtree(TMP)
    size_kb = ZIP_OUT.stat().st_size / 1024
    print(f"Created deploy.zip ({size_kb:.1f} KB) with POSIX permissions.")


if __name__ == "__main__":
    make_zip()
