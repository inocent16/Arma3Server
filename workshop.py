import os
import re
import subprocess
import urllib.request
from typing import List

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


def preset(mod_file: str) -> List[str]:
    html = _fetch(mod_file)
    mods = []
    moddirs = []
    regex = r"filedetails\/\?id=(\d+)\""
    matches = re.finditer(regex, html, re.MULTILINE)
    for _, match in enumerate(matches, start=1):
        mods.append(match.group(1))
        moddir = WORKSHOP + match.group(1)
        moddirs.append(moddir)
    download(mods)
    for moddir in moddirs:
        keys.copy(moddir)
    return moddirs


def cdlc(mod_file: str) -> List[str]:
    html = _fetch(mod_file)
    regex = r"store\.steampowered\.com/app/(\d+)"
    flags = []
    for match in re.finditer(regex, html):
        flag = CDLC_APPIDS.get(match.group(1))
        if flag and flag not in flags:
            flags.append(flag)
    return flags
