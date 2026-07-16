import os
from typing import List

import keys


def mods(d: str) -> List[str]:
    mods = []

    # Find mod folders
    for m in os.listdir(d):
        moddir = os.path.join(d, m)
        if os.path.isdir(moddir):
            mods.append(moddir)
            keys.copy(moddir)

    return mods
