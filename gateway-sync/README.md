# Gateway-local DNS Content Filter sync

This optional tool downloads the repository's **plain domain** feed into a
separately named UniFi DNS Content Filter. It runs on the gateway, so no Pi-hole,
AdGuard Home, separate Linux server, or always-on computer is required.

## Verified deployment

On November 9, 2026, the Dream Machine Beast running UniFi OS 6.0.17 and Network
11.0.99 accepted and returned all **207,455** domains in **UniFi Additive DNS
Blocklist**. The original **AD Blocking Filter** has empty custom allow/block
lists and is not the scheduled job's target. Both profiles retain native Ad Block:
the inspected UI requires a filtering category or Ad Block to be enabled when
creating a custom-domain Content Filter. Creating the supplemental profile with
Filtering Off and Ad Block disabled was rejected by the UI.

The IP-based firewall policy and Dynamic Network List were removed. Neither is
needed by this tool. Historical flow logs and backups were not erased.

The API read-back retained the complete new profile; the generated CoreDNS config
had separate hostSet nodes for the two profiles and a separate supplemental domain file
for the supplemental profile. From the LAN, `app-measurement.com` returned UniFi's
blocking address `203.0.113.250`; `ui.com` and `example.com` returned normal DNS
answers and HTTPS 200. This is a live deployment check, not a guarantee of every
feed domain's suitability or of matching unknown subdomains.

The native global `content_filtering_blocking_page_enabled` setting was then set
to false, with a read-back confirming that this was the only changed setting.
This controls the response presentation; it does not remove either filter or
weaken its domain rules. The Turtlecute test counts any successful HTTP response
as reachable, including a gateway block page. Before this change, direct DNS
queries blocked 120 of its 126 current test hosts, including every one of the 115
test hosts covered by the supplemental feed. A low browser score alone therefore
did not establish a failed DNS import.

## Schedule and manual use

The gateway uses **America/New_York**. `/etc/cron.d/unifi-additive-sync` runs on
**Sunday and Wednesday at 02:00 local time**. Like ordinary local-time cron,
a nonexistent 02:00 during the spring DST transition can be skipped.

Run these commands **on the gateway**, after signing in over SSH:

```sh
unifi-blocklist-sync
```

Equivalent command independent of the installed shortcut:

```sh
python3 /data/unifi-additive-sync/sync.py --apply
```

Preview without changing the filter:

```sh
python3 /data/unifi-additive-sync/sync.py
```

Status and logs:

```sh
cat /data/unifi-additive-sync/last-success.json
journalctl -t unifi-additive-sync -n 20 --no-pager
systemctl status unifi-additive-sync-restore.service cron.service
cat /etc/cron.d/unifi-additive-sync
```

Manual runs print their result directly. Cron logs through the system journal.
`last-success.json` is updated only after a successful API read-back. A reported
API success does not by itself prove completed gateway provisioning: DNS changes
can take time to apply and clients may retain cached answers.

## Safety and behavior

- The updater targets a fixed profile ID, name, and network assignment and refuses
  to enable a disabled profile or write a different one.
- It unions the feed, its local history, and the target profile's existing custom
  domains. Previously recorded domains remain even after source or UI deletions.
- It preserves the target's current allowlist, native categories, schedule, source,
  Safe Search, and unknown fields. It does **not** add any whitelist entries.
  Manage exceptions in the supplemental filter's UniFi UI when needed.
- The first deployment requires `--initialize`; later missing history stops the
  job. Restore history from a backup rather than initializing over a loss.
- It rejects malformed hostnames, small/empty downloads, and more than 500,000
  combined domains. The maximum is a local guard, not a claimed UniFi capacity.
- Failed downloads leave the target untouched. Before a write it saves a complete
  profile backup, checks for concurrent UI edits, and verifies the read-back.
  The undocumented API has no verified atomic compare-and-swap; avoid editing the
  supplemental profile during a sync.
- An owner-only API key is read from `/data/unifi-additive-sync/api-key`, never
  passed on the command line or published. Gateway TLS is pinned to a certificate
  hash obtained through authenticated SSH; a certificate change stops the job
  before the key is transmitted. Public feed downloads use normal HTTPS checks.
- No resolver files are edited directly and no gateway, Network, or DNS restart
  is performed by the updater.

## Persistent storage and recovery

The code, key, configuration, domain history, backups, and schedule source live in
`/data/unifi-additive-sync` on persistent SSD storage. A dedicated systemd startup
service reconstructs this project's cron file and manual shortcut from that
directory. The service definition is copied into the root overlay so it is
available during systemd's early unit discovery; it is not a symlink to an
unmounted SSD. The service is enabled for multi-user startup.

The restore service was started and tested by temporarily moving its installed
cron file and confirming the service recreated an identical copy. The manual
command and exact cron runner both completed successfully afterward.

**No reboot or firmware upgrade was performed to test persistence.** This is a
custom, unsupported integration using an undocumented API. It is designed to
retain its data and restore its schedule across normal reboots and firmware
updates that preserve the custom root overlay. A firmware release that removes
custom startup units or changes the API can still require repair; no on-gateway
custom cron arrangement can guarantee compatibility with every future release.
Check the service and `last-success.json` after an upgrade.

If the job's scheduler or shortcut needs restoration, run on the gateway:

```sh
bash /data/unifi-additive-sync/restore-schedule.sh
systemctl restart unifi-additive-sync-restore.service
unifi-blocklist-sync
```

The restore script refuses to install its 02:00 cron schedule if the gateway's
timezone has changed. If the TLS certificate changes, verify its new fingerprint
over authenticated SSH and update `certificate_sha256` locally; do not disable
pin verification. If credentials are revoked or expire, enter a replacement with
`python3 /data/unifi-additive-sync/store-key.py` in an interactive SSH session.

## Deployment configuration

This deployment was installed over the user's authenticated SSH connection.
`config.json` and the key are intentionally not in Git. The configuration contains:

```json
{
  "gateway": "https://127.0.0.1",
  "certificate_sha256": "<64 lowercase hexadecimal digits verified over SSH>",
  "site": "default",
  "profile_id": "<separate supplemental profile UUID>",
  "profile_name": "UniFi Additive DNS Blocklist",
  "network_ids": ["<intended network UUID>"],
  "feed_url": "https://raw.githubusercontent.com/zdmilot/unifi-additive-blocklist/main/blocklist.txt",
  "minimum_domains": 80000,
  "maximum_domains": 500000
}
```

Requires Python 3 with the standard library, Linux flock, cron, and systemd.
Do not use `blocklist-adblock.txt` with this API: it expects plain hostnames.

API shape on the tested installation:

```text
GET /proxy/network/v2/api/site/default/content-filtering
PUT /proxy/network/v2/api/site/default/content-filtering/<existing-profile-id>
```

The collection accepts reads; `POST` to that collection returned 405 on this
version. The separate profile was created through UniFi's UI, then populated by
the updater. The original filter is not edited by normal sync runs.
