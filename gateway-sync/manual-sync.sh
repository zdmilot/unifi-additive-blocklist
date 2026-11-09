#!/bin/bash
set -euo pipefail
exec /usr/bin/python3 /data/unifi-additive-sync/sync.py --apply "$@"
