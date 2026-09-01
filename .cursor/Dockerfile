FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Baseline tooling required by Cursor Cloud Agents (git clone, sudo, network).
# Plus the system dependencies for Inyfinn-photo-resizer:
#   - Python 3 + venv/dev headers
#   - libvips + image encoders (pngquant, cwebp via `webp`, gifsicle)
#   - xvfb + Qt/xcb runtime libraries so the PySide6 GUI can run headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    git sudo curl ca-certificates \
    python3 python3-venv python3-dev python3-pip \
    libvips42 libvips-tools \
    pngquant webp gifsicle \
    xvfb libgl1 libegl1 libglx-mesa0 libxkbcommon0 libxkbcommon-x11-0 \
    libdbus-1-3 fonts-dejavu \
    libxcb-cursor0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 \
    libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-util1 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user with passwordless sudo (idempotent — Ubuntu 24.04 already ships `ubuntu`).
RUN id -u ubuntu &>/dev/null || useradd -m -s /bin/bash ubuntu
RUN usermod -aG sudo ubuntu
RUN echo "ubuntu ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ubuntu

# Do NOT COPY the project — Cursor checks out the correct commit itself.
