# Sources and attribution

## HaGeZi DNS Blocklists — Multi LIGHT

- Author: HaGeZi and contributors.
- Project and preferred source: https://github.com/hagezi/dns-blocklists
- Input: https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/light-onlydomains.txt
- Upstream license: GNU General Public License version 3, https://github.com/hagezi/dns-blocklists/blob/main/LICENSE
- A copy of GPL version 3 is included in `LICENSE`.

`blocklist.txt` is a modified compilation: upstream comments are omitted for import,
domains are normalized, deduplicated and sorted, and prior domains and local additions
are retained by union. These transformations were introduced November 9, 2026.
The input byte hash and retrieval time for each build are recorded in
`build-report.json`. Historical source hashes and the original generated versions
remain in Git history. This project makes no claim to have authored upstream domains.
Historical entries may no longer occur in today's upstream list.

Review the license and attribution of any additional source before adding it to
`sources.json`. Each source must specify its name and license. Sources remain
independently maintained; inclusion is not an endorsement.
