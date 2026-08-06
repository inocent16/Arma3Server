import json
import os
import urllib.request
from typing import Dict, List

import workshop

_TREE_CACHE: Dict[str, Dict[str, str]] = {}


def _repo_parts(base: str):
    # https://raw.githubusercontent.com/<owner>/<repo>/<branch>/ -> (owner, repo, branch)
    parts = base.rstrip("/").split("/")
    branch, repo, owner = parts[-1], parts[-2], parts[-3]
    return owner, repo, branch


def _tree(base: str) -> Dict[str, str]:
    """Every file under a preset/settings repo, as {relative_path: source}.
    For a URL base, source is a raw.githubusercontent.com URL to fetch the file
    from directly; for a local base, source is the absolute local path. One Git
    Trees API call gets the whole repo's file list at once, which is what makes
    discovering arbitrary mod-folder names (there's no fixed filename to probe,
    unlike workshop.py's mods.html) practical without hitting GitHub's
    unauthenticated 60/hr rate limit -- only this one call counts against it,
    not the later per-file downloads (those go through raw.githubusercontent.com,
    which isn't API-rate-limited). Cached per base so multiple entries from the
    same repo only pay for this once."""
    if base in _TREE_CACHE:
        return _TREE_CACHE[base]

    if base.startswith("http"):
        owner, repo, branch = _repo_parts(base)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        req = urllib.request.Request(api_url, headers={"User-Agent": workshop.USER_AGENT})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        raw_base = base.rstrip("/")
        tree = {
            entry["path"]: f"{raw_base}/{entry['path']}"
            for entry in data["tree"]
            if entry["type"] == "blob"
        }
    else:
        tree = {}
        for root, _dirs, files in os.walk(base):
            for name in files:
                abspath = os.path.join(root, name)
                relpath = os.path.relpath(abspath, base).replace(os.sep, "/")
                tree[relpath] = abspath

    _TREE_CACHE[base] = tree
    return tree


def resolve(base: str, entries: List[str]) -> Dict[str, str]:
    """Layer each entry's files over the previous ones. A fresh server.cfg
    replaces any prior server.cfg; a fresh <mod>/... path replaces prior paths
    under that same <mod>/ prefix only, leaving other mods' folders (from an
    earlier entry) untouched. Returns {relative_path: source} for the final
    winning set, same source semantics as _tree()."""
    tree = _tree(base)
    resolved: Dict[str, str] = {}
    for entry in entries:
        prefix = entry.rstrip("/") + "/"
        matches = {
            path[len(prefix):]: source
            for path, source in tree.items()
            if path.startswith(prefix)
        }
        if not matches:
            print(
                f"ERROR: settings source '{entry}' matched no files under {base} "
                "-- check the path/spelling.",
                flush=True,
            )
            exit(1)

        # Drop anything already resolved under one of this entry's top-level
        # names (a mod folder, or the standalone "server.cfg" file) before
        # adding this entry's version of it -- a later, smaller entry that only
        # re-provides one file inside a mod's folder still replaces that whole
        # folder atomically, rather than merging file-by-file with whatever an
        # earlier, larger entry left there.
        tops = {relpath.split("/", 1)[0] for relpath in matches}
        for top in tops:
            for existing in [p for p in resolved if p == top or p.startswith(top + "/")]:
                del resolved[existing]
        resolved.update(matches)

    return resolved


def apply(resolved: Dict[str, str]) -> None:
    for relpath, source in resolved.items():
        if relpath == "server.cfg":
            dest = os.path.join("/arma3/configs", os.environ["ARMA_CONFIG"])
        else:
            dest = os.path.join("/arma3/userconfig", relpath)

        os.makedirs(os.path.dirname(dest), exist_ok=True)

        if source.startswith("http"):
            req = urllib.request.Request(source, headers={"User-Agent": workshop.USER_AGENT})
            content = urllib.request.urlopen(req, timeout=15).read()
            with open(dest, "wb") as f:
                f.write(content)
        else:
            with open(source, "rb") as f:
                content = f.read()
            with open(dest, "wb") as f:
                f.write(content)
