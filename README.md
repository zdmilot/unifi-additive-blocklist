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

The starting source is [HaGeZi Multi LIGHT](https://github.com/hagezi/dns-blocklists#light),
which supplies ad/tracker domains. Its current snapshot is included in the generated
list. Historical domains remain even if HaGeZi removes or reclassifies them later.
Source attribution and licensing are in [SOURCES.md](SOURCES.md).

## Subscribe from UniFi

The repository and list are public. Use this stable, anonymous HTTPS feed URL:

```text
https://raw.githubusercontent.com/zdmilot/unifi-additive-blocklist/main/blocklist.txt
```

**Prerequisites: UniFi Network 11 with External Network Lists and UniFi OS
6.0.10 or newer.** Ubiquiti documents this feature and requirement in its
[Network 11 release notes](https://community.ui.com/releases/UniFi-Network-Application-11-0-97/15662d06-8122-44e2-a1ba-af5d71b8a045).
Network 10.6 and OS 5 do not provide this native URL-subscription feature.
Publishing the feed on GitHub Pages does not change that version requirement.

1. Open **Network Lists** in UniFi Settings and create a domain list named
   `UniFi Additive Blocklist`.
2. Select **External** as its source and enter the HTTPS feed URL above.
3. Refresh the list and verify successful retrieval and the full domain count
   against `build-report.json`. Capacity and refresh controls depend on the device
   and firmware. Never truncate history silently to fit a capacity limit.
4. Reference this list in a blocking policy for the intended client networks.
   Merely creating the list does not enforce blocking. Keep the existing built-in
   ad-block and content-filter settings in place.
5. Verify blocking from a client in scope and verify an unrelated domain still
   resolves. Check the external list's status after the next scheduled refresh.

Use the raw file URL, not this repository's HTML page. It serves plain UTF-8 text
with one domain per line; no token, login, wildcard conversion, or file import is
needed. UniFi polls the feed according to its configured refresh behavior; GitHub
Actions maintains the feed daily. Do not paste the feed URL into a field that
expects an individual blocked domain. This project uses URL subscriptions only
for gateway delivery; it does not install a router-side script or substitute a
one-time file import.

### Why the External/URL option may be missing

On November 9, 2026, the target Dream Machine Beast reported OS 5.1.35 and Network
10.6.109, with only the Official release channel available. It therefore needs a
compatible OS 6 upgrade before Network 11 can expose External Network Lists.
Ubiquiti's Network 11 notes say the migration resets existing statistics history
and may take up to 20 minutes. Back up the configuration and review the offered
device-specific upgrade before proceeding. This repository does not upgrade the
gateway automatically. No URL subscription is claimed active until its retrieval
and blocking policy are verified on the gateway.

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
