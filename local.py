import os
import subprocess
from typing import List

import keys


def call(cmd, **kwargs) -> int:
    """subprocess.call, but a stop signal mid-call prints a clean line instead of
    a KeyboardInterrupt traceback -- tini (see the Dockerfile) forwards the
    signal to the child itself, so this is just about what shows up in the
    console, not about the child actually stopping."""
    try:
        return subprocess.call(cmd, **kwargs)
    except KeyboardInterrupt:
        print("Stopping...", flush=True)
        exit(0)


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
