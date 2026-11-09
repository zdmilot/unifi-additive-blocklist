# UniFi additive blocklist

A supplemental DNS domain list for UniFi with **append-only updates**:

```text
next blocklist = every previously added domain ∪ new accepted domains
```

UniFi's built-in ad blocking and content-filter policies stay in place. This project
builds an additional, plain-text list; it does not log into a gateway or modify its
firmware, DNS configuration, built-in lists, or existing policies.

## Files you can use

- [`blocklist.txt`](blocklist.txt): sorted, unique domains, one per line, ready for review/import.
- [`build-report.json`](build-report.json): source hashes, counts, additions, and output checksum.
- [`sources.json`](sources.json): upstream list and validation limits.
- [`manual-additions.txt`](manual-additions.txt): your extra domains.
- [`exclude-new.txt`](exclude-new.txt): exact names to exclude before their first addition.

The starting source is [HaGeZi Multi LIGHT](https://github.com/hagezi/dns-blocklists#light),
which supplies ad/tracker domains. Its current snapshot is included in the generated
list. Historical domains remain even if HaGeZi removes or reclassifies them later.
Source attribution and licensing are in [SOURCES.md](SOURCES.md).

## Use with UniFi

1. Download `blocklist.txt` from this repository while signed in.
2. In the existing content-filter policy, use its custom **Blocklist** controls to
   add/import supplemental domains. Retain the existing domains and settings.
3. Keep built-in Ad Blocking enabled if you already use it. Test the policy on a
   small device/network scope before broad use.

Ubiquiti documents additional custom domains under
[Settings → CyberSecure → Content Filter](https://help.ui.com/hc/en-us/articles/12568927589143-Content-and-Domain-Filtering-in-UniFi).
Exact controls, import support, and capacity vary by Network/gateway version; this
project does not claim a tested capacity or automatic subscription support for a
particular gateway. If your UI only replaces an existing custom list, export that
list first and include it with `--import` before replacing its contents. Preserve
your existing allowlist separately.

This repository is currently private. Anonymous raw GitHub URLs will not work as
gateway subscriptions. Download the file or use the Actions artifact; never put a
GitHub access token into a subscription URL. No router configuration has been
applied or tested by this project.

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
