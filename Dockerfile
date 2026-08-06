FROM debian:bullseye-slim
LABEL maintainer="Brett - github.com/brettmayson, modified for Pterodactyl by innocent16"
LABEL org.opencontainers.image.source=https://github.com/inocent16/Arma3Server

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# arma3server_x64 links against a handful of engine dependencies -- libtbb2
# (threading) and libsdl2 in particular -- that aren't part of a minimal Debian
# install; without them it can fail in ways that don't surface as a normal
# missing-library error. libnss-wrapper is separate and required: Wings runs the
# container as its own uid:gid with no matching /etc/passwd entry (see the
# useradd comment below), and the engine calls getpwuid() directly rather than
# only reading $HOME -- with no entry to resolve, that returns NULL and the
# engine promptly dereferences it, segfaulting on startup before printing
# anything. launch.py sets up nss_wrapper's LD_PRELOAD shim with a synthetic
# passwd/group entry for whatever uid it's actually running as before it
# launches the game binary.
RUN dpkg --add-architecture i386 \
    && \
    apt-get update \
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
        libstdc++6:i386 \
        libtbb2 \
        libtbb2:i386 \
        libsdl2-2.0-0 \
        libsdl2-2.0-0:i386 \
        numactl \
        libnss-wrapper \
        libnss-wrapper:i386 \
        tini \
    && \
    apt-get remove --purge -y \
    && \
    apt-get clean autoclean \
    && \
    apt-get autoremove -y \
    && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -d /home/container -s /usr/sbin/nologin container
ENV HOME=/home/container
ENV NSS_WRAPPER_PASSWD=/tmp/passwd
ENV NSS_WRAPPER_GROUP=/tmp/group
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
ENV VALIDATE_INSTALL=false

EXPOSE 2302/udp
EXPOSE 2303/udp
EXPOSE 2304/udp
EXPOSE 2305/udp
EXPOSE 2306/udp

WORKDIR /arma3

USER container

STOPSIGNAL SIGINT

COPY *.py /

# launch.py runs steamcmd and the game binary as its own subprocesses; without a
# real init as PID 1, a stop signal only reaches launch.py itself and those
# children are left running/orphaned rather than shut down with it. -g forwards
# signals to the whole process group, not just tini's direct child, since the
# game binary is launched via a shell wrapper (subprocess.call(..., shell=True))
# rather than being tini's immediate child.
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
CMD ["python3","/launch.py"]