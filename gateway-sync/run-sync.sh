#!/bin/bash
# Keep credentials out of command lines, and preserve Python's failure status.
set -euo pipefail
/usr/bin/python3 /data/unifi-additive-sync/sync.py --apply 2>&1 | /usr/bin/logger -t unifi-additive-sync
