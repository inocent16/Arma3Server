import os
import re
import shutil
import subprocess
from string import Template
from typing import List

import local
import workshop


def mod_param(name: str, mods: List[str]) -> str:
    return ' -{}="{}" '.format(name, ";".join(mods))


def env_defined(key: str) -> bool:
    return key in os.environ and len(os.environ[key]) > 0


CONFIG_FILE = os.environ["ARMA_CONFIG"]
KEYS = "/arma3/keys"

# Wings injects its own SERVER_PORT correctly, but doesn't expand the {{SERVER_PORT}}
# template in a custom egg variable's default_value -- our PORT variable is left as
# that literal, unexpanded string under Pterodactyl. Prefer SERVER_PORT when present
# (Pterodactyl) and fall back to PORT for standalone docker/docker-compose use, where
# SERVER_PORT doesn't exist and PORT is set directly.
SERVER_PORT = os.environ.get("SERVER_PORT") or os.environ["PORT"]

if env_defined("CLEAR_KEYS") and os.environ["CLEAR_KEYS"] == "true" and os.path.isdir(KEYS):
    shutil.rmtree(KEYS)
if not os.path.isdir(KEYS):
    if os.path.exists(KEYS):
        os.remove(KEYS)
    os.makedirs(KEYS)

# The Linux port still expects the Windows-style user-profile directories under
# ~/.local/share -- unrelated to the -profiles= CLI flag below, which only covers
# server config/profile .cfg files. Without these the server segfaults on startup.
for profile_dir in ("Arma 3", "Arma 3 - Other Profiles"):
    os.makedirs(os.path.join(os.environ["HOME"], ".local/share", profile_dir), exist_ok=True)

STEAMCMD_DIR = "/arma3/steamcmd"
STEAMCMD_SH = os.path.join(STEAMCMD_DIR, "steamcmd.sh")

if os.environ["SKIP_INSTALL"] in ["", "false"]:
    # Install Arma

    if not os.path.isfile(STEAMCMD_SH):
        os.makedirs(STEAMCMD_DIR, exist_ok=True)
        subprocess.run(
            "wget -qO- 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz' | tar zxf - -C {}".format(
                STEAMCMD_DIR
            ),
            shell=True,
            check=True,
        )

    steamcmd = [STEAMCMD_SH]
    steamcmd.extend(["+force_install_dir", "/arma3"])
    steamcmd.extend(["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]])
    steamcmd.extend(["+app_update", "233780"])
    if env_defined("STEAM_BRANCH"):
        steamcmd.extend(["-beta", os.environ["STEAM_BRANCH"]])
    if env_defined("STEAM_BRANCH_PASSWORD"):
        steamcmd.extend(["-betapassword", os.environ["STEAM_BRANCH_PASSWORD"]])
    steamcmd.extend(["validate"])
    if env_defined("STEAM_ADDITIONAL_DEPOT"):
        for depot in os.environ["STEAM_ADDITIONAL_DEPOT"].split("|"):
            depot_parts = depot.split(",")
            steamcmd.extend(
                ["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]]
            )
            steamcmd.extend(
                ["+download_depot", "233780", depot_parts[0], depot_parts[1]]
            )
    steamcmd.extend(["+quit"])
    result = subprocess.call(steamcmd)
    if result != 0:
        print(f"steamcmd exited with code {result}, aborting.", flush=True)
        exit(1)

if env_defined("STEAM_ADDITIONAL_DEPOT"):
    for depot in os.environ["STEAM_ADDITIONAL_DEPOT"].split("|"):
        depot_parts = depot.split(",")
        depot_dir = (
            f"{STEAMCMD_DIR}/linux32/steamapps/content/app_233780/depot_{depot_parts[0]}/"
        )
        for file in os.listdir(depot_dir):
            shutil.copytree(depot_dir + file, "/arma3/", dirs_exist_ok=True)
            print(f"Moved {file} to /arma3")

# Wings runs this container as its own uid:gid, which has no /etc/passwd entry in
# the image. The engine calls getpwuid() directly (not just $HOME) during startup,
# and a failed lookup there is what segfaults it -- not a config or dependency
# issue. Give it something to resolve via nss_wrapper's LD_PRELOAD shim, scoped to
# just the actual game binary so it doesn't affect steamcmd above.
uid, gid = os.getuid(), os.getgid()
with open(os.environ["NSS_WRAPPER_PASSWD"], "w") as f:
    f.write("root:x:0:0:root:/root:/bin/bash\n")
    f.write(f"container:x:{uid}:{gid}:container:{os.environ['HOME']}:/bin/bash\n")
with open(os.environ["NSS_WRAPPER_GROUP"], "w") as f:
    f.write("root:x:0:\n")
    f.write(f"container:x:{gid}:\n")
os.environ["LD_PRELOAD"] = (
    "/usr/lib/x86_64-linux-gnu/libnss_wrapper.so"
    if "x64" in os.environ["ARMA_BINARY"]
    else "/usr/lib/i386-linux-gnu/libnss_wrapper.so"
)

# Mods

mods = []

if os.environ["MODS_PRESET"] != "":
    mods.extend(workshop.preset(os.environ["MODS_PRESET"]))

if os.environ["MODS_LOCAL"] == "true" and os.path.exists("mods"):
    mods.extend(local.mods("mods"))

launch = "{} -limitFPS={} -world={} {} {}".format(
    os.environ["ARMA_BINARY"],
    os.environ["ARMA_LIMITFPS"],
    os.environ["ARMA_WORLD"],
    os.environ["ARMA_PARAMS"],
    mod_param("mod", mods),
)

if os.environ["ARMA_CDLC"] != "":
    for cdlc in os.environ["ARMA_CDLC"].split(";"):
        launch += " -mod={}".format(cdlc)

clients = int(os.environ["HEADLESS_CLIENTS"])
print("Headless Clients:", clients)

if clients != 0:
    with open("/arma3/configs/{}".format(CONFIG_FILE)) as config:
        data = config.read()
        regex = r"(.+?)(?:\s+)?=(?:\s+)?(.+?)(?:$|\/|;)"

        config_values = {}

        matches = re.finditer(regex, data, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            config_values[match.group(1).lower()] = match.group(2)

        if "headlessclients[]" not in config_values:
            data += '\nheadlessclients[] = {"127.0.0.1"};\n'
        if "localclient[]" not in config_values:
            data += '\nlocalclient[] = {"127.0.0.1"};\n'

        with open("/tmp/arma3.cfg", "w") as tmp_config:
            tmp_config.write(data)
        launch += ' -config="/tmp/arma3.cfg"'

    client_launch = launch
    client_launch += " -client -connect=127.0.0.1 -port={}".format(SERVER_PORT)
    if "password" in config_values:
        client_launch += " -password={}".format(config_values["password"])

    for i in range(0, clients):
        hc_template = Template(
            os.environ["HEADLESS_CLIENTS_PROFILE"]
        )  # eg. '$profile-hc-$i'
        hc_name = hc_template.substitute(
            profile=os.environ["ARMA_PROFILE"], i=i, ii=i + 1
        )

        hc_launch = client_launch + ' -name="{}"'.format(hc_name)
        print("LAUNCHING ARMA CLIENT {} WITH".format(i), hc_launch)
        subprocess.Popen(hc_launch, shell=True)

else:
    launch += ' -config="/arma3/configs/{}"'.format(CONFIG_FILE)

launch += ' -port={} -name="{}" -profiles="/arma3/configs/profiles"'.format(
    SERVER_PORT, os.environ["ARMA_PROFILE"]
)

if os.path.exists("servermods"):
    launch += mod_param("serverMod", local.mods("servermods"))

if not os.path.isfile(os.environ["ARMA_BINARY"]):
    print(
        f"ERROR: {os.environ['ARMA_BINARY']} not found in /arma3 -- install failed or never ran.",
        flush=True,
    )
    exit(1)

print("LAUNCHING ARMA SERVER WITH", launch, flush=True)
subprocess.call(launch, shell=True)
