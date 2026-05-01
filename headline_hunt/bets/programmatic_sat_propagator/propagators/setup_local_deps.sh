#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
DEPS="$ROOT/.deps"
CADICAL_DIR="$DEPS/cadical"
CADICAL_COMMIT="7b99c07f0bcab5824a5a3ce62c7066554017f641"
NLOHMANN_VERSION="3.12.0"
NLOHMANN_HEADER="$DEPS/nlohmann/include/nlohmann/json.hpp"
JOBS="${JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)}"

mkdir -p "$DEPS"

if [ ! -d "$CADICAL_DIR/.git" ]; then
  git clone https://github.com/arminbiere/cadical.git "$CADICAL_DIR"
fi
git -C "$CADICAL_DIR" checkout "$CADICAL_COMMIT"

(
  cd "$CADICAL_DIR"
  ./configure
  make -j"$JOBS"
)

mkdir -p "$(dirname "$NLOHMANN_HEADER")"
curl -L "https://github.com/nlohmann/json/releases/download/v${NLOHMANN_VERSION}/json.hpp" \
  -o "$NLOHMANN_HEADER"

printf 'ready: %s\n' "$CADICAL_DIR/build/libcadical.a"
printf 'ready: %s\n' "$NLOHMANN_HEADER"
