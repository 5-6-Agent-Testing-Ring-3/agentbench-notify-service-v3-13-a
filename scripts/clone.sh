#!/bin/sh
set -eu
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 DESTINATION" >&2
    exit 2
fi
git clone -- https://github.com/5-6-Agent-Testing-Ring-3/agentbench-notify-service-v3-13-a.git "$1"
"$1/scripts/setup.sh"
