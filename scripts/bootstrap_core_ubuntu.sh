#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---dry-run}"
if [[ "$MODE" != "--dry-run" && "$MODE" != "--apply" ]]; then
  echo "usage: $0 [--dry-run|--apply]" >&2
  exit 2
fi

packages=(
  ca-certificates curl git git-lfs jq make
  python3 python3-venv python3-pip
  build-essential clang cmake ninja-build pkg-config
  lshw pciutils numactl iproute2 util-linux
)

printf 'ForgeLLM core bootstrap mode: %s\n' "$MODE"
printf 'Packages: %s\n' "${packages[*]}"
echo "GPU drivers, CUDA, ROCm, container runtimes and privileged services are intentionally excluded."

if [[ "$MODE" == "--dry-run" ]]; then
  printf 'Would run: sudo apt-get update\n'
  printf 'Would run: sudo apt-get install -y %q ' "${packages[@]}"
  printf '\n'
  exit 0
fi

sudo apt-get update
sudo apt-get install -y "${packages[@]}"
git lfs install --skip-repo
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
echo "Core bootstrap complete. Review docs/tooling/TOOLCHAIN.md before any accelerator installation."
