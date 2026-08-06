# Arma 3 Dedicated Server

An Arma 3 Dedicated Server. Updates to the latest version every time it is restarted.

## Usage

### Docker CLI

```s
    docker create \
        --name=arma-server \
        -p 2302:2302/udp \
        -p 2303:2303/udp \
        -p 2304:2304/udp \
        -p 2305:2305/udp \
        -p 2306:2306/udp \
        -v path/to/missions:/arma3/mpmissions \
        -v path/to/configs:/arma3/configs \
        -v path/to/mods:/arma3/mods \
        -v path/to/servermods:/arma3/servermods \
        -e ARMA_CONFIG=main.cfg \
        -e STEAM_USER=myusername \
        -e STEAM_PASSWORD=mypassword \
        ghcr.io/inocent16/arma3server:latest
```

### docker-compose

Use the docker-compose.yml file inside a folder. It will automatically create 4 folders in which the missions, configs, mods and servermods can be loaded.

Copy the `.env.example` file to `.env`, containing at least `STEAM_USER` and `STEAM_PASSWORD`.

Use `docker-compose start` to start the server.

Use `docker-compose logs` to see server logs.

Use `docker-compose down` to shutdown the server.

The `network_mode: host` can be changed to explicit ports if needed.

Use `docker-compose up -d` to start the server, detached.

See [Docker-compose](https://docs.docker.com/compose/install/#install-compose) for an installation guide.

Profiles are saved in `/arma3/configs/profiles`

### Pterodactyl

This image runs as an unprivileged `container` user with home directory `/home/container`, which Wings chowns to the
server's configured uid/gid and mounts as the server's data volume. A symlink (`/arma3` -> `/home/container`) means
none of the Python scripts needed to change to support this -- steamcmd, the game files, mods, configs and keys all
end up inside that same persistent volume.

To add it to a panel:

1. Import [`egg-arma-3.json`](egg-arma-3.json) via **Admin -> Nests -> Import Egg**.
2. Make sure a Docker image is published to `ghcr.io/inocent16/arma3server:latest` (the `Publish Docker` GitHub Actions
   workflow builds and pushes this automatically on pushes to `v2`, or can be triggered manually).
3. When creating the server, allocate **5 contiguous UDP ports** (e.g. `2302-2306`) and set the primary allocation to
   the first one. Arma 3 binds to the primary port through primary+3; the extra allocations must exist on the node
   for Wings to publish them, even though only the primary one is exposed as an egg variable.
4. Set the `Steam Username`/`Steam Password` variables. Steam Guard must be disabled on that account.

The first boot will take a while, since steamcmd downloads the full Arma 3 server (and re-validates it on every
subsequent boot unless `Skip Install` is set to `true`). The egg's "server started" detection looks for
`Host identity created.` in the console output -- if your setup doesn't emit that (some mod configurations or Arma
updates change console output), adjust the `startup.done` string in the egg's Startup Detection settings.

## Parameters

| Parameter                     | Function                                                  | Default |
| -------------                 |--------------                                             | - |
| `-p 2302-2306`                | Ports required by Arma 3 |
| `-v /arma3/mpmission`         | Folder with MP Missions |
| `-v /arma3/configs`           | Folder containing config files |
| `-v /arma3/mods`              | Mods that will be loaded by clients |
| `-v /arma3/servermods`        | Mods that will only be loaded by the server |
| `-e PORT`                     | Port used by the server, (uses PORT to PORT+3)            | 2302 |
| `-e ARMA_BINARY`              | Arma 3 server binary to use, `./arma3server_x64` for x64   | `./arma3server` |
| `-e ARMA_CONFIG`              | Config file to load from `/arma3/configs`                 | `main.cfg` |
| `-e ARMA_PARAMS`              | Additional Arma CLI parameters |
| `-e ARMA_PROFILE`             | Profile name, stored in `/arma3/configs/profiles`         | `main` |
| `-e ARMA_WORLD`               | World to load on startup                                  | `empty` |
| `-e ARMA_LIMITFPS`            | Maximum FPS | `1000` |
| `-e ARMA_CDLC`                | cDLCs to load |
| `-e STEAM_BRANCH`             | Steam branch used by steamcmd | `public` |
| `-e STEAM_BRANCH_PASSWORD`    | Steam branch password used by steamcmd |
| `-e STEAM_USER`               | Steam username used to login to steamcmd |
| `-e STEAM_PASSWORD`           | Steam password |
| `-e HEADLESS_CLIENTS`         | Launch n number of headless clients                       | `0` |
| `-e HEADLESS_CLIENTS_PROFILE` | Headless client profile name (supports placeholders)      | `$profile-hc-$i` |
| `-e MODS_LOCAL`               | Should the mods folder be loaded | `true` |
| `-e MODS_PRESET`              | An Arma 3 Launcher preset to load |
| `-e SKIP_INSTALL`             | Skip Arma 3 installation | `false` |
| `-e VALIDATE_INSTALL`         | Force steamcmd to checksum-verify every file on every boot, not just check for updates. Slow -- leave off for routine restarts | `false` |
| `-e CLEAR_KEYS`               | Clear the keys directory every launch (keys will still be copied from mods) | `false` |
| `-e SETTINGS_ENABLED`         | Master switch for pulling mod configuration/server config from a presets repo -- see [Presets and settings](#presets-and-settings) | `false` |
| `-e SETTINGS_REPO`            | Base raw-content URL (or local path) of a presets/settings repo | |
| `-e SETTINGS_SOURCES`         | Semicolon-separated `presets/<name>`/`settings/<name>` folders to apply, in order | |

The Steam account does not need to own Arma 3, but must have Steam Guard disabled.

List of Steam branches can be found on the Community Wiki, [Arma 3: Steam Branches](https://community.bistudio.com/wiki/Arma_3:_Steam_Branches)

## Creator DLC

To use a Creator DLC the `STEAM_BRANCH` must be set to `creatordlc`

| Name | Flag |
| ---- | ---- |
| [CSLA Iron Curtain](https://store.steampowered.com/app/1294440/Arma_3_Creator_DLC_CSLA_Iron_Curtain/) | CSLA |
| [Global Mobilization - Cold War Germany](https://store.steampowered.com/app/1042220/Arma_3_Creator_DLC_Global_Mobilization__Cold_War_Germany/) | GM |
| [S.O.G. Prairie Fire](https://store.steampowered.com/app/1227700/Arma_3_Creator_DLC_SOG_Prairie_Fire) | vn |
| [Western Sahara](https://store.steampowered.com/app/1681170/Arma_3_Creator_DLC_Western_Sahara/) | WS |
| [Spearhead 1944](https://store.steampowered.com/app/1175380/Arma_3_Creator_DLC_Spearhead_1944/) | spe |
| [Reaction Forces](https://store.steampowered.com/app/2647760/Arma_3_Creator_DLC_Reaction_Forces/) | rf |
| [Expeditionary Forces](https://store.steampowered.com/app/2647830/Arma_3_Creator_DLC_Expeditionary_Forces/) | ef |

Bohemia-updated list of codes here: <https://community.bistudio.com/wiki/Category:Arma_3:_CDLCs>

### Example

`-e ARMA_CDLC="csla;gm;vn;ws;spe"`

If `MODS_PRESET` is set, any Creator DLC included in that preset are detected
automatically from their Steam store links and loaded the same as if listed in
`ARMA_CDLC` -- you don't need to list them in both places. The preset is parsed
before steamcmd runs specifically so this can also switch `STEAM_BRANCH` to
`creatordlc` on its own when it's still at the default `public`, so in the common
case you don't need to set that yourself either. If you *have* set `STEAM_BRANCH`
to something else explicitly, that choice is left alone rather than overridden --
the console will warn on startup if that leaves detected CDLC without a branch
that actually carries their content.

## Loading mods

### Local

1. Place the mods inside `/mods` or `/servermods`.
2. Start the server.

Everything inside each mod folder (the `addons` folder, `.pbo` files, etc.) is lowercased
automatically on every boot before launch, since Arma's Linux port needs lowercase paths but
neither local uploads nor Steam Workshop preserve that -- this applies the same way whether
the mod came from `/mods`, `/servermods`, or a Workshop preset. The mod folder's own name
(e.g. `@ACE`) isn't touched by this and is used as-is, so avoid quotation marks or other
characters there that could cause issues elsewhere.

### Workshop

Set the environment variable `MODS_PRESET` to the HTML preset file exported from the Arma 3 Launcher. The path can be local file or a URL. A volume can be created at `/arma3/steamapps/workshop/content/107410` to preserve the mods between containers.

`-e MODS_PRESET="my_mods.html"`

`-e MODS_PRESET="http://example.com/my_mods.html"`

Each mod is only re-downloaded (and re-lowercased/re-keyed) when it's actually changed --
before touching steamcmd, each mod's Steam Workshop changelog is checked against a marker
file left in its folder from the last time it was updated. New mods (no marker yet) and
anything that can't be checked always update, so this errs toward re-downloading rather than
silently running stale content; it just skips the redundant work for everything that hasn't
changed, which matters once a preset has more than a handful of mods.

## Presets and settings

`MODS_PRESET`/`ARMA_CDLC` above only control *which* mods and CDLC load -- they have no
concept of how those mods are configured, or of the main server config file itself. That's
what this section is for: pulling mod configuration (`userconfig/<ModFolderName>/`) and the
server config (`configs/<ARMA_CONFIG>`) from a separate GitHub repo, instead of hand-editing
them over SFTP on every server individually.

Set `SETTINGS_ENABLED=true`, `SETTINGS_REPO` to that repo's raw base URL (e.g.
`https://raw.githubusercontent.com/<org>/<repo>/<branch>/`) or a local path, and
`SETTINGS_SOURCES` to a semicolon-separated list of folders to apply, in order:

`-e SETTINGS_SOURCES="presets/hardcore-op;settings/ace-no-med;settings/thermals-off"`

The repo itself has no fixed format to learn beyond two conventions:

```
presets/<name>/
    server.cfg          # optional -- full main.cfg-equivalent content
    ace3/                # optional -- one folder per mod, named to match that
        config.hpp       #   mod's own userconfig folder name exactly
settings/<name>/
    ...                  # same shape, meant to be picked individually
```

A **preset** is applied first as the baseline. Each **setting** listed after it is then
layered on top, and for anything it provides -- a whole mod's folder, or `server.cfg` --
that entirely replaces whatever the preset (or an earlier setting) had for that same thing.
Nothing else is touched: overriding ACE3's tuning with a setting never disturbs some other
mod's userconfig the preset also set up, and a setting with no `server.cfg` of its own leaves
the preset's server config alone. This is why authoring one is simple -- copy your own local
`userconfig/<mod>/` folder in as-is, no reformatting, no manifest file to maintain.

Two things worth knowing before turning this on:
- Once a source resolves a `server.cfg` or a given mod's userconfig folder, that gets
  overwritten on **every boot** -- direct SFTP edits to those specific files won't survive a
  restart. Anything not covered by your presets/settings is left alone as normal.
- This adds a GitHub dependency to every boot the same way `MODS_PRESET` already does for
  `mods.html` -- if GitHub is unreachable when a source is configured, startup fails loudly
  rather than silently running with an incomplete config.
