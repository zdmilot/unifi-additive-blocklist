# Sources and attribution

## HaGeZi DNS Blocklists — Multi NORMAL, with retained LIGHT history

- Author: HaGeZi and contributors.
- Project and preferred source: https://github.com/hagezi/dns-blocklists
- Current input: https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/multi-onlydomains.txt
- Historical input: https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/light-onlydomains.txt
- Upstream license: GNU General Public License version 3, https://github.com/hagezi/dns-blocklists/blob/main/LICENSE
- A copy of GPL version 3 is included in `LICENSE`.

`blocklist.txt` is a modified compilation: upstream comments are omitted for import,
domains are normalized, deduplicated and sorted, and prior domains and local additions
are retained by union. These transformations were introduced November 9, 2026.
The input byte hash and retrieval time for each build are recorded in
`build-report.json`. Historical source hashes and the original generated versions
remain in Git history. This project makes no claim to have authored upstream domains.
Historical entries may no longer occur in today's upstream list. On November 9,
2026, the maintained tier changed to NORMAL while preserving every historical
entry. Both `blocklist.txt` and `blocklist-adblock.txt` contain the same domain set;
the latter wraps names in explicit Adblock suffix rules.

## Targeted comparison and manual review, November 9, 2026

The review consulted AdGuard DNS, its exclusions/exceptions, OISD big,
Peter Lowe's ad server list, EasyList's ad-server section, EasyPrivacy's
tracking-server section, and HaGeZi LIGHT/NORMAL/PRO/ULTIMATE. These overlapping
lists are not independent votes and were not blindly unioned into the feed.
Only NORMAL is a new continuously imported upstream source.

The two targeted Yahoo additions `3p-udc.yahoo.com` and `bats.video.yahoo.com`
were listed by both [AdGuard DNS](https://github.com/AdguardTeam/AdGuardSDNSFilter)
and [OISD](https://oisd.nl/). Bally Bet is an explicit user-requested site block,
not a claim that the entire betting site is an ad server. The other manual names
make reviewed Safari-test hostnames explicit; their parent coverage is documented
in `coverage-review.json`. The optional privacy rules are separately selected
hostnames supported by HaGeZi PRO and are not merged into the main feeds.

Exact comparison URLs, retrieval-review time, byte counts, and SHA-256 hashes
are recorded in [`coverage-review.json`](coverage-review.json). This is a dated
audit snapshot, not a promise of current membership in those comparison lists.
See [`COVERAGE-REVIEW.md`](COVERAGE-REVIEW.md) for the decisions and remaining limits.

Review the license and attribution of any additional source before adding it to
`sources.json`. Each source must specify its name and license. Sources remain
independently maintained; inclusion is not an endorsement.
