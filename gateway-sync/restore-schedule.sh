#!/bin/bash
# Reconstruct only this project's scheduler files. Never restart the gateway,
# Network application, DNS service, or unrelated jobs.
set -euo pipefail
task_root=/data/unifi-additive-sync
test "$(id -u)" = 0
test -x /usr/bin/python3
test -s "$task_root/history.json"
test -s "$task_root/config.json"
test -s "$task_root/api-key"
test "$(timedatectl show --property=Timezone --value)" = America/New_York || {
    echo 'Timezone changed; review the 02:00 schedule before restoring.' >&2
    exit 1
}
install -m 0644 "$task_root/unifi-additive-sync-restore.service" /etc/systemd/system/unifi-additive-sync-restore.service
install -m 0644 "$task_root/cron" /etc/cron.d/unifi-additive-sync
install -m 0755 "$task_root/manual-sync.sh" /usr/local/sbin/unifi-blocklist-sync
systemctl daemon-reload
systemctl enable unifi-additive-sync-restore.service
systemctl enable --now cron.service
logger -t unifi-additive-sync 'Restored Sunday/Wednesday 02:00 America/New_York schedule'
