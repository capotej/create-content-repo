#!/usr/bin/env bash
# Build entrypoint for CI (Netlify) and local use.
#
# Installs a pinned mise (sha256-verified, x86_64 + aarch64) if not already
# present, installs the tools pinned in mise.toml, then runs the build.
# mise.toml stays the single source of truth for tool versions.
#
# Checksums from:
# https://github.com/jdx/mise/releases/download/v2026.9.6/SHASUMS256.txt
set -euo pipefail

MISE_VERSION=2026.9.6
MISE_AMD64_SHA256=04260a49d2cb7f46c91d3f90547f8486ba6c6c9e545b98e69b685cdcf0db8576
MISE_ARM64_SHA256=7892401c3a3b8166e8be3a3bbd564f48b36946e580e031f2df94a4935edfd907

export PATH="$HOME/.local/bin:$PATH"

if ! command -v mise >/dev/null 2>&1; then
    ARCH="$(uname -m)"
    case "${ARCH}" in
        x86_64) MISE_ARCH=x64; EXPECTED="${MISE_AMD64_SHA256}" ;;
        aarch64) MISE_ARCH=arm64; EXPECTED="${MISE_ARM64_SHA256}" ;;
        *) echo "unsupported arch: ${ARCH}"; exit 1 ;;
    esac
    mkdir -p "$HOME/.local/bin"
    curl -fsSL \
        "https://github.com/jdx/mise/releases/download/v${MISE_VERSION}/mise-v${MISE_VERSION}-linux-${MISE_ARCH}" \
        -o "$HOME/.local/bin/mise"
    echo "${EXPECTED}  $HOME/.local/bin/mise" | sha256sum --check --strict
    chmod +x "$HOME/.local/bin/mise"
fi

mise install
python3 .agents/skills/build/scripts/build.py
