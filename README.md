# UniFi additive blocklist

A supplemental DNS domain list for UniFi with **append-only updates**:

```text
next blocklist = every previously added domain ∪ new accepted domains
```

UniFi's built-in ad blocking and content-filter policies stay in place. This project
builds an additional, plain-text list; it does not log into a gateway or modify its
firmware, DNS configuration, built-in lists, or existing policies.

## Files you can use

- [`blocklist.txt`](blocklist.txt): sorted, unique domains, one per line, served as the subscription feed.
- [`build-report.json`](build-report.json): source hashes, counts, additions, and output checksum.
- [`sources.json`](sources.json): upstream list and validation limits.
- [`manual-additions.txt`](manual-additions.txt): your extra domains.
- [`exclude-new.txt`](exclude-new.txt): exact names to exclude before their first addition.

The user-requested exceptions `cdn.cookielaw.org` and `mobile-data.onetrust.io`
are excluded from new upstream/manual additions. Neither was in the initial
historical feed. Add these literal hostnames to the applicable UniFi allowlist
as well to override built-in or other filtering lists; `cdn.cookielaw\\.org`
is regex notation and should not be pasted into a hostname-only field.

The starting source is [HaGeZi Multi LIGHT](https://github.com/hagezi/dns-blocklists#light),
which supplies ad/tracker domains. Its current snapshot is included in the generated
list. Historical domains remain even if HaGeZi removes or reclassifies them later.
Source attribution and licensing are in [SOURCES.md](SOURCES.md).

## Subscription URL and UniFi limitation

The repository and list are public. Use this stable, anonymous HTTPS feed URL:

```text
https://raw.githubusercontent.com/zdmilot/unifi-additive-blocklist/main/blocklist.txt
```

**This is a DNS domain feed. Do not enforce this broad feed through a UniFi
Domain-list firewall rule.** That rule resolves names to IP addresses and blocks
those addresses, including unrelated sites on the same CDN. UniFi Network 11's
External/Dynamic Network Lists support URL downloads, but this is not a URL
subscription for the DNS Content Filter. The DNS Content Filter does not accept
a blocklist URL in the inspected Network 11.0.99 UI. See the
[UniFi integration guide's domain-filtering limitation](https://qfeeds.com/knowledge-base/unifi-setup/#malicious-domains).

For URL-based, domain-specific blocking, add the feed URL to a DNS filter such as
Pi-hole, AdGuard Home, or Technitium, verify the full imported count against
`build-report.json`, and configure the intended clients/gateway to use that DNS
filter. Keep the existing UniFi ad-block settings and requested allowlist entries.
The resolver host and DNS routing must be selected before deploying that approach;
this repository does not install a resolver or alter DNS routing automatically.

Use the raw file URL, not this repository's HTML page. It serves plain UTF-8 text
with one domain per line; no token, login, wildcard conversion, or file import is
needed. GitHub Actions maintains the feed daily; the subscribing DNS filter polls
it on its configured schedule. Do not paste the feed URL into a field expecting
an individual blocked domain. Delivery uses a URL subscription, not a router-side
script or a one-time file import. Publishing on GitHub Pages would not change
UniFi's enforcement semantics.

### UniFi version requirements

On November 9, 2026, the target Dream Machine Beast reported OS 5.1.35 and Network
10.6.109, with only the Official release channel available. It therefore needs a
compatible OS 6 upgrade before Network 11 can expose External Network Lists.
Ubiquiti's Network 11 notes say the migration resets existing statistics history
and may take up to 20 minutes. Back up the configuration and review the offered
device-specific upgrade before proceeding. This repository does not upgrade the
gateway automatically. An OS/Network upgrade exposes Dynamic Network Lists but
does not add DNS-level URL subscription support to Content Filter.

### Verified deployment status

On November 9, 2026, UniFi Network 11.0.99 successfully loaded all 88,382 domains
into the dynamic **UniFi Additive Blocklist** network list, with a 24-hour refresh
interval. The separate **UniFi Additive Content Blocker** firewall policy was
created and tested, then **paused** after its flow logs showed it blocking
`ui.com`, `example.com`, and `idm.xfinity.com`, even though none of these names or
their parents is in the feed. `ui.com` and `example.com` returned HTTP 200 after
the rule was paused. Do not resume it as a general DNS ad blocker.

The downloaded list remains under **Settings → Networks → Network Lists**. The
paused policy remains under **Settings → Policy Engine → Policy Table** for
inspection. The supplemental feed is not currently enforced by a DNS filter.

The original **AD Blocking Filter** remains in place, including the CookieLaw and
OneTrust allowlist entries. The two exception domains and their parents are absent
from the published supplemental feed.

## Update locally

Requires Python 3.11+ on macOS or Linux; no third-party packages.

```sh
git clone https://github.com/zdmilot/unifi-additive-blocklist.git
cd unifi-additive-blocklist
python3 update.py                    # fetch and preview; no list/report writes
python3 update.py --write            # retain history and add new domains
python3 update.py --check            # offline format, count, and checksum check
python3 -m unittest discover -s tests -v
```

To preserve an existing custom domain list too:

```sh
python3 update.py --write --import /path/to/existing-domains.txt
```

For extra domains, edit `manual-additions.txt` and run the updater. Removing a
manual entry, excluding a historical domain, removing a source, or an upstream
deletion **never removes an already-added domain**. `exclude-new.txt` is exact-match
only; it does not create UniFi allow rules or exclude subdomains automatically.
Use UniFi's own allowlist for false-positive exceptions while retaining the list's
history. Imported existing domains bypass new-entry exclusions so an existing
custom list is preserved in full. An allow rule's actual precedence should be
verified on your firmware.

If history is missing, normal updates stop. Restore `blocklist.txt` from Git;
`--initialize --write` is reserved for creating a brand-new list. Do not use it to
recover lost history. This append-only policy deliberately accumulates stale domains
and false positives, so review additions and use allow rules as needed. DNS filtering
cannot selectively block ads served from the same domain as wanted content.

## Automation and guarantees

The **Update blocklist** workflow runs daily and can also be run manually. It tests
the updater, validates current history, fetches all configured sources, adds domains,
checks the result against the prior committed file, uploads the generated files,
and commits updates to `main`. It needs repository `contents: write` for that commit.
The separate **Checks** workflow has read-only permissions and checks pull requests
and pushes for domain removal against their previous Git revision.

Required-source failure, invalid syntax, a suspiciously small source, or exceeding
the configured maximum stops the update before any output changes. Sources accept
domain-only and sinkhole hosts formats; wildcard/Adblock rules are rejected.
Updates use a process lock and an atomic replacement of the canonical list. A crash
between the list and report writes can leave a stale report; `--check` detects it,
and a successful rerun repairs it without dropping domains. Keep Git history and
backups: deliberate file edits or force pushes can bypass the updater's guarantees.

To verify against a saved previous version:

```sh
python3 update.py --check --baseline /path/to/previous-blocklist.txt
```

Automated tests exercise upstream deletion, local/imported history retention,
exclusions, failed sources, format errors, size/count limits, dry runs, checksum
tampering, and the history check. Gateway behavior is a separate validation step.

## License

GPL-3.0-only. See [LICENSE](LICENSE). Generated domain data includes HaGeZi content;
see [SOURCES.md](SOURCES.md). Unofficial project; not affiliated with Ubiquiti.
