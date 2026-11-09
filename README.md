# UniFi additive blocklist

A supplemental DNS domain list for UniFi with **append-only updates**:

```text
next blocklist = every previously added domain ∪ new accepted domains
```

UniFi's built-in ad blocking and content-filter policies stay in place. The feed
builder creates additional plain-text lists. The optional [gateway sync](gateway-sync/README.md)
updates a separately named DNS Content Filter through UniFi's internal API; it
does not modify built-in list files or firmware.

## Files you can use

- [`blocklist.txt`](blocklist.txt): sorted, unique domains, one per line, served as the subscription feed.
- [`blocklist-adblock.txt`](blocklist-adblock.txt): the same set as explicit `||domain^` rules; recommended for AdGuard Home and Pi-hole v6+ so parent entries also block subdomains.
- [`build-report.json`](build-report.json): source hashes, counts, additions, and output checksum.
- [`sources.json`](sources.json): upstream list and validation limits.
- [`manual-additions.txt`](manual-additions.txt): your extra domains.
- [`exclude-new.txt`](exclude-new.txt): exact names to exclude before their first addition.
- [`protected-domains.txt`](protected-domains.txt): named service hosts that must not match a block rule; a collision aborts a build, including if it is historical.
- [`COVERAGE-REVIEW.md`](COVERAGE-REVIEW.md): Yahoo/Digital Turbine review, Bally Bet scope, Safari-test findings, and validation limits.
- [`optional-privacy-adblock.txt`](optional-privacy-adblock.txt): standalone reference subset of six error-reporting/app-analytics rules, now also included in both main feeds at the user's request.

`mobile-data.onetrust.io` remains excluded from new upstream/manual additions.
The user explicitly overrode the former `cdn.cookielaw.org` and `udc.yahoo.com`
protections when requesting the Chrome test's missing hostnames; both are now
blocked by the main feeds. Router allowlists are managed by the user; the scheduled
gateway sync preserves the supplemental filter's current allowlist without
adding exceptions automatically. Use literal hostnames in UniFi's hostname-only
fields, not regex notation such as `cdn.cookielaw\\.org`.

The maintained source is [HaGeZi Multi NORMAL](https://github.com/hagezi/dns-blocklists#normal),
selected for broader coverage with a lower risk of breakage than PRO/PRO++/ULTIMATE.
The historical LIGHT snapshot is retained. Historical domains remain even if HaGeZi
removes or reclassifies them later; the list is not guaranteed free of false positives.
Source attribution and licensing are in [SOURCES.md](SOURCES.md).

## Subscription URL and UniFi limitation

The repository and lists are public. For AdGuard Home or Pi-hole v6+, use:

```text
https://raw.githubusercontent.com/zdmilot/unifi-additive-blocklist/main/blocklist-adblock.txt
```

For a resolver that explicitly supports suffix matching of plain domain feeds, use:

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

For URL-based, domain-specific blocking, add the appropriate feed URL to a DNS filter such as
Pi-hole, AdGuard Home, or Technitium, verify the full imported count against
`build-report.json`, and configure the intended clients/gateway to use that DNS
filter. Keep the existing UniFi ad-block settings and requested allowlist entries.
Bare domains are exact-only in AdGuard Home; do not assume a plain-domain import
blocks unknown subdomains. The Adblock variant explicitly covers a domain and all
its subdomains. In particular `||ballybet.com^` covers `play.ballybet.com` and other
Bally Bet hosts without blocking the unrelated parent brand `ballys.com`.
Do not paste `*.ballybet.com` into this project's domain-only source files, or paste
Adblock rules into a UniFi hostname-only field. UniFi's documented custom Content
Filter accepts domains, but its subdomain behavior needs verification on your
firmware; the documentation's DNS-forwarding wildcard example is not proof of
Content Filter matching semantics.

The resolver host and DNS routing must be selected before deploying that approach.
For the installed gateway-only alternative, see [gateway sync](gateway-sync/README.md):
a scheduled script fetches the plain-domain feed into a separate native DNS
Content Filter, without an external DNS server.

Use a raw file URL, not this repository's HTML page. Both serve plain UTF-8 text,
one domain or rule per line, with no token or login needed.
GitHub Actions maintains both feeds daily; the subscribing DNS filter polls
it on its configured schedule. Do not paste the feed URL into a field expecting
an individual blocked domain. External DNS filters can subscribe to the URL;
the installed UniFi integration uses the gateway-side script. Publishing on GitHub
Pages would not change UniFi's enforcement semantics.

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

On November 9, 2026, the obsolete **UniFi Additive Content Blocker** firewall policy
and **UniFi Additive Blocklist** Dynamic Network List were removed. They had
caused unrelated sites to be blocked through shared IP addresses. Historical logs
and backups were retained.

The separately named **UniFi Additive DNS Blocklist** Content Filter now contains
all **207,476** domains from the plain-domain feed. The original **AD Blocking
Filter** remains enabled with empty custom allow/block lists. The gateway job
targets only the supplemental profile, preserving any future user-managed
allowlist there without inserting exceptions automatically.

The gateway sync runs **Sunday and Wednesday at 02:00 America/New_York**, with a
manual `unifi-blocklist-sync` command on the gateway. A startup restore service
recreates its cron file from persistent SSD storage. Both manual and cron runner
tests succeeded, and the restore service recreated a temporarily moved cron file.
No reboot or firmware upgrade was performed; future firmware/API compatibility
is not guaranteed. See [deployment, verification, and recovery](gateway-sync/README.md).

The tested system is UniFi OS 6.0.17 / Network 11.0.99. The native Content Filtering
Block Page setting was disabled after Safari's test treated returned block pages
as reachable hosts. The site's JavaScript counts any successful HTTP response as
not blocked; it does not identify which server answered. Direct DNS tests showed
every test hostname covered by this feed was being blocked. `ui.com` and
`example.com` remained reachable over HTTPS.

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
between generated-file writes can leave a stale derivative or report; `--check` detects it,
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
