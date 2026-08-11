"""Propagates the shared component files from this canonical build to the two
repository builds at the repo root.

eTacho/ and Forced-eTacho/ hold the SAME component under different manifests:
only app.json (identity) and app.vue's header comment differ between them.
Everything else must stay byte-identical, and hand-copying is exactly how the
two silently drift apart -- hence this script.

app.vue is synced too, but only its CODE: each build keeps its own header
comment, which describes whether that build overrides the stock dial or stands
alone. Everything after the closing comment marker is replaced.

Run after every rebuild:
    python _sync-builds.py
"""
import filecmp
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ui", "modules", "apps", "Tacho2")
ROOT = os.path.dirname(HERE)
TARGETS = [
    os.path.join(ROOT, "eTacho", "ui", "modules", "apps", "enhancedTacho"),
    os.path.join(ROOT, "Forced-eTacho", "ui", "modules", "apps", "Tacho2"),
]
SHARED = ["tacho.vue", "layout.js", "config.js", "settings.vue", "sliderRow.vue"]


MARKER = "-->"


def split_app_vue(path):
    """(header comment including its closing marker, code after it)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if MARKER not in text:
        return "", text
    cut = text.index(MARKER) + len(MARKER)
    return text[:cut], text[cut:]


src_code = split_app_vue(os.path.join(SRC, "app.vue"))[1]

for dst in TARGETS:
    if not os.path.isdir(dst):
        print("ABSENT   %s" % dst)
        continue

    for name in SHARED:
        shutil.copy2(os.path.join(SRC, name), os.path.join(dst, name))

    # app.vue: graft the source's code onto this build's own header.
    dst_app = os.path.join(dst, "app.vue")
    header = split_app_vue(dst_app)[0]
    with open(dst_app, "w", encoding="utf-8", newline="\n") as f:
        f.write(header + src_code)

    same = all(
        filecmp.cmp(os.path.join(SRC, n), os.path.join(dst, n), shallow=False)
        for n in SHARED
    )
    app_ok = split_app_vue(dst_app)[1] == src_code
    print("%-8s %s%s" % ("OK" if same else "MISMATCH", dst,
                         "" if app_ok else "   [!] app.vue graft failed"))
