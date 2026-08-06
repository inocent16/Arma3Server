import os
from typing import List

import keys


def lowercase(moddir: str) -> None:
    """Arma 3's Linux port needs lowercase paths inside mods -- Workshop items keep
    whatever case the uploader used, and manually-placed mods are easy to get wrong
    too. Deepest entries first, so a directory isn't renamed out from under its own
    not-yet-processed contents."""
    for root, dirs, files in os.walk(moddir, topdown=False):
        for name in dirs + files:
            src = os.path.join(root, name)
            dst = os.path.join(root, name.lower())
            if src != dst and not os.path.exists(dst):
                os.rename(src, dst)


def mods(d: str) -> List[str]:
    mods = []

    # Find mod folders
    for m in os.listdir(d):
        moddir = os.path.join(d, m)
        if os.path.isdir(moddir):
            lowercase(moddir)
            mods.append(moddir)
            keys.copy(moddir)

    return mods
