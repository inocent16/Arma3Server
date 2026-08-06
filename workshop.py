import os
import re
import time
import urllib.request
from typing import List, Optional, Tuple

import keys
import local

WORKSHOP = "steamapps/workshop/content/107410/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"  # noqa: E501
CHANGELOG_URL = "https://steamcommunity.com/sharedfiles/filedetails/changelog/{}"
UPDATED_MARKER = ".workshop_updated"

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


def download(mod_id: str) -> None:
    steamcmd = ["/arma3/steamcmd/steamcmd.sh"]
    steamcmd.extend(["+force_install_dir", "/arma3"])
    steamcmd.extend(["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]])
    steamcmd.extend(["+workshop_download_item", "107410", mod_id])
    steamcmd.extend(["+quit"])
    local.call(steamcmd)


def _latest_update(mod_id: str) -> Optional[int]:
    """The epoch timestamp of a Workshop item's most recent changelog entry, or
    None if it can't be determined (no changelog page, network error, etc)."""
    try:
        req = urllib.request.Request(
            CHANGELOG_URL.format(mod_id), headers={"User-Agent": USER_AGENT}
        )
        html = urllib.request.urlopen(req, timeout=10).read().decode(errors="replace")
        match = re.search(r'<p id="(\d+)"', html)
        return int(match.group(1)) if match else None
    except (OSError, ValueError):
        return None


def _is_stale(mod_id: str, latest: Optional[int]) -> bool:
    """Whether a mod has to go through steamcmd this boot at all. Re-running
    +workshop_download_item and re-walking a mod's files for every item on every
    single restart doesn't scale to large presets -- most of it is already
    current. Unable to tell either way (no marker yet, no changelog reachable)
    errs toward updating rather than silently going stale."""
    marker = os.path.join(WORKSHOP + mod_id, UPDATED_MARKER)
    if not os.path.isfile(marker) or latest is None:
        return True
    try:
        with open(marker) as f:
            known = int(f.read().strip())
    except (OSError, ValueError):
        return True
    return latest > known


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
    latest = {mod_id: _latest_update(mod_id) for mod_id in mod_ids}
    stale = [mod_id for mod_id in mod_ids if _is_stale(mod_id, latest[mod_id])]
    if stale:
        print(f"Updating {len(stale)} of {len(mod_ids)} mods...", flush=True)

    # One steamcmd call per mod, each immediately followed by writing that mod's
    # own marker -- not one batched call for the whole preset with markers
    # written at the end, so a mod already downloaded this boot stays counted as
    # current even if something (a restart, a crash, the server getting stopped)
    # cuts the run short before the rest of the preset finishes.
    moddirs = []
    for i, mod_id in enumerate(mod_ids, start=1):
        moddir = WORKSHOP + mod_id
        moddirs.append(moddir)
        if mod_id not in stale:
            continue
        print(f"Updating mod {mod_id} ({i}/{len(mod_ids)})...", flush=True)
        download(mod_id)
        if os.path.isdir(moddir):
            local.lowercase(moddir)
            keys.copy(moddir)
            with open(os.path.join(moddir, UPDATED_MARKER), "w") as f:
                f.write(str(latest[mod_id] if latest[mod_id] is not None else int(time.time())))
    return moddirs
