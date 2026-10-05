#!/usr/bin/env python3
"""Refuse a world restart while a client or probe process runs."""
import os
import subprocess
from pathlib import Path

matches = subprocess.run(["pgrep", "-af", "probe-|target/debug/benilla"],
                         text=True, capture_output=True, check=False)
active = []
for line in matches.stdout.splitlines():
    pid = line.split(" ", 1)[0]
    try:
        args = Path(f"/proc/{pid}/cmdline").read_bytes().decode().split("\0")
    except (OSError, UnicodeError):
        continue
    # Ignore shell command strings and the pgrep invocation itself.
    if pid == str(os.getpid()) or not args or Path(args[0]).name == "pgrep":
        continue
    if any(Path(arg).name == "benilla" or
           (Path(arg).name.startswith("probe-") and not any(c.isspace() for c in arg))
           for arg in args if arg):
        active.append(line)
if active:
    print("World restart blocked: client probes are active.")
    print("\n".join(active))
    raise SystemExit(1)
print("No active client probes.")
