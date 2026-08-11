# -*- coding: utf-8 -*-
"""Builds the two release archives at the repository root.

Written with zipfile rather than Compress-Archive: PowerShell stores entry
names with backslashes, which is not what the ZIP spec asks for and not what
the game's archive reader expects. Entries are sorted so the same source tree
always produces the same archive.
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BUILDS = [
    ("eTacho", "eTacho_v5.0.zip"),
    ("Forced-eTacho", "Forced-eTacho_v5.0.zip"),
]

for folder, archive in BUILDS:
    src = os.path.join(ROOT, folder)
    dst = os.path.join(ROOT, archive)
    files = []
    for base, _dirs, names in os.walk(os.path.join(src, "ui")):
        for name in names:
            full = os.path.join(base, name)
            files.append((os.path.relpath(full, src).replace(os.sep, "/"), full))
    files.sort()

    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for arcname, full in files:
            # Fixed timestamp: the archive should only change when the files do.
            info = zipfile.ZipInfo(arcname, date_time=(2026, 8, 11, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(full, "rb") as fh:
                z.writestr(info, fh.read())

    print("%-24s %6.1f KB  %d fichiers" % (archive, os.path.getsize(dst) / 1024.0, len(files)))
    for arcname, _ in files:
        print("    " + arcname)
