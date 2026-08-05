import os
import re
import subprocess
import urllib.request
from typing import List, Tuple

import keys

WORKSHOP = "steamapps/workshop/content/107410/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"  # noqa: E501

# Creator DLC don't have Workshop file IDs -- the launcher preset links to their
# Steam store page instead (store.steampowered.com/app/<appid>). Maps those to the
# -mod= flag Arma expects, per https://community.bistudio.com/wiki/Category:Arma_3:_CDLCs
CDLC_APPIDS = {
    "1294440": "CSLA",
    "1042220": "GM",
    "1227700": "vn",
    "1681170": "WS",
    "1175380": "spe",
    "2647760": "rf",
    "2647830": "ef",
}


def download(mods: List[str]) -> None:
    steamcmd = ["/arma3/steamcmd/steamcmd.sh"]
    steamcmd.extend(["+force_install_dir", "/arma3"])
    steamcmd.extend(["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]])
    for id in mods:
        steamcmd.extend(["+workshop_download_item", "107410", id])
    steamcmd.extend(["+quit"])
    subprocess.call(steamcmd)


def _fetch(mod_file: str) -> str:
    if mod_file.startswith("http"):
        req = urllib.request.Request(
            mod_file,
            headers={"User-Agent": USER_AGENT},
        )
        remote = urllib.request.urlopen(req)
        with open("preset.html", "wb") as f:
            f.write(remote.read())
        mod_file = "preset.html"
    with open(mod_file) as f:
        return f.read()


def parse(mod_file: str) -> Tuple[List[str], List[str]]:
    """Read a Launcher preset once, returning (workshop mod ids, CDLC flags).

    Split from downloading so CDLC can be known before steamcmd runs -- it needs
    to pick the creatordlc branch upfront, while the mods themselves can only be
    downloaded once steamcmd is already installed.
    """
    html = _fetch(mod_file)
    mod_ids = [
        match.group(1)
        for match in re.finditer(r"filedetails\/\?id=(\d+)\"", html, re.MULTILINE)
    ]
    cdlc_flags = []
    for match in re.finditer(r"store\.steampowered\.com/app/(\d+)", html):
        flag = CDLC_APPIDS.get(match.group(1))
        if flag and flag not in cdlc_flags:
            cdlc_flags.append(flag)
    return mod_ids, cdlc_flags


def download_mods(mod_ids: List[str]) -> List[str]:
    download(mod_ids)
    moddirs = [WORKSHOP + mod_id for mod_id in mod_ids]
    for moddir in moddirs:
        keys.copy(moddir)
    return moddirs
