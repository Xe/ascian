#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "$0")/.." && pwd)"
docker build -t ascian/sage-builder -f "$root/sage/Dockerfile.build" "$root"
docker run --rm --user "$(id -u):$(id -g)" -v "$root:/src" ascian/sage-builder sh -c '
cmake -S /src -B /src/build/container -G Ninja -DCMAKE_BUILD_TYPE=Release -DENABLE_CPPTRACE=OFF -DDEBUG_SYMBOLS=OFF -DBUILD_FOR_HOST_CPU=OFF -DCMAKE_INSTALL_PREFIX=/opt/vmangos
cmake --build /src/build/container --target mangosd -j "${SAGE_BUILD_JOBS:-6}"
'
# Stage a separate inode. Never overwrite the executable of a running server.
stage="$root/build/runtime-next"
mkdir -p "$stage/lib"
cp "$root/build/container/src/mangosd/mangosd" "$stage/mangosd"
docker run --rm --user "$(id -u):$(id -g)" -v "$stage:/runtime" ascian/sage-builder sh -c '
ldd /runtime/mangosd | awk "/=> \\/.* \\(/ {print \$3}" | while read lib; do cp -L "$lib" /runtime/lib/; done
'
echo "Staged binary and libraries in $stage."
