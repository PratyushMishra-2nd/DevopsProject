#!/usr/bin/env bash
# Run a command for real and keep a verbatim transcript for docs/evidence.
#
#   scripts/record.sh <name> <command...>
#
# Writes docs/evidence/transcripts/<name>.txt containing a shell-style prompt
# line for each command followed by its untouched stdout/stderr (ANSI colour
# codes stripped). The exit code of the command is preserved.
set -uo pipefail

name="$1"; shift
root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/docs/evidence/transcripts/$name.txt"
mkdir -p "$(dirname "$out")"

prompt="pratyush-mishra@pantrypulse:~/DevopsProject\$"
{
  printf '# recorded %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"
  printf '%s %s\n' "$prompt" "$*"
} >> "$out"

bash -c "$*" 2>&1 | sed -u 's/\x1b\[[0-9;?]*[a-zA-Z]//g; s/\r$//' | tee -a "$out"
status=${PIPESTATUS[0]}
printf '\n' >> "$out"
exit "$status"
