FROM debian:bullseye-slim
LABEL maintainer="Brett - github.com/brettmayson, modified for Pterodactyl by innocent16"
LABEL org.opencontainers.image.source=https://github.com/inocent16/Arma3Server

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update \
    && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        python3 \
        lib32stdc++6 \
        lib32gcc-s1 \
        libcurl4 \
        wget \
        ca-certificates \
        curl \
        libstdc++6 \
    && \
    apt-get remove --purge -y \
    && \
    apt-get clean autoclean \
    && \
    apt-get autoremove -y \
    && \
    rm -rf /var/lib/apt/lists/*

# Pterodactyl requires a user named "container" with home /home/container;
# Wings runs the container with its own configured uid/gid (chowning the
# mounted volume to match), overriding whatever USER is baked in here, so we
# don't pin a uid/gid ourselves.
RUN useradd -m -d /home/container -s /usr/sbin/nologin container

# Redirect Arma's fixed /arma3 working path to Pterodactyl's persistent mount point.
# All scripts (launch.py, workshop.py, local.py, keys.py) reference /arma3 either
# directly or via relative paths against WORKDIR /arma3 -- this symlink means every
# one of those writes transparently lands inside the volume Wings actually persists,
# with zero changes needed to the Python source. steamcmd is also installed inside
# this volume at runtime (not baked into the image) so it inherits the same,
# correctly-chowned permissions instead of a build-time uid that Wings may not use.
RUN rm -rf /arma3 && ln -s /home/container /arma3

ENV ARMA_BINARY=./arma3server_x64
ENV ARMA_CONFIG=main.cfg
ENV ARMA_PARAMS=
ENV ARMA_PROFILE=main
ENV ARMA_WORLD=empty
ENV ARMA_LIMITFPS=1000
ENV ARMA_CDLC=
ENV HEADLESS_CLIENTS=0
ENV HEADLESS_CLIENTS_PROFILE="\$profile-hc-\$i"
ENV PORT=2302
ENV STEAM_BRANCH=public
ENV STEAM_BRANCH_PASSWORD=
ENV STEAM_ADDITIONAL_DEPOT=
ENV MODS_LOCAL=true
ENV MODS_PRESET=
ENV SKIP_INSTALL=false

EXPOSE 2302/udp
EXPOSE 2303/udp
EXPOSE 2304/udp
EXPOSE 2305/udp
EXPOSE 2306/udp

WORKDIR /arma3

USER container

STOPSIGNAL SIGINT

COPY *.py /

CMD ["python3","/launch.py"]