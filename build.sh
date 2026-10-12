#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for tool in gcc g++ make flex bison; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Missing dependency: $tool" >&2
    echo "Install build-essential, flex, and bison, then rerun ./build.sh." >&2
    exit 1
  fi
done

make -C "$ROOT/src/icg" clean all
cp "$ROOT/src/icg/minic" "$ROOT/minic"
g++ -std=c++11 -O2 -w "$ROOT/src/ucode/ucodei.cpp" -o "$ROOT/ucodei"
chmod +x "$ROOT/minic" "$ROOT/ucodei"
echo "Build complete: ./minic and ./ucodei are ready."
