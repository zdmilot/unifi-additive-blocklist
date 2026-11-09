# Coverage review — November 9, 2026

The reviewed main feeds contain **207,310 domains**, up from 88,382: 118,928
additions and zero removals of committed history. The source is now HaGeZi NORMAL,
with targeted manual entries. The domain-only and Adblock outputs represent the
same set; use the Adblock output where explicit subdomain matching is required.

This is a list-content review, not by itself evidence that the router is enforcing
it. No gateway settings were changed during the initial review. A later deployment
removed the unsuitable IP-based policy and installed a separate DNS Content Filter
with scheduled gateway-local sync; see [deployment status](README.md#verified-deployment-status).

### User-requested follow-up

After the initial review, the user explicitly requested the remaining Chrome test
hosts be added through GitHub and synchronized to UniFi. The six names listed
below were promoted into `manual-additions.txt` and both generated main feeds,
bringing the total to **207,316** with zero removals. The other four failed checks
are browser-side cosmetic/script tests and cannot be represented as DNS domains.

A subsequent Chrome run of Super Adblock Test showed 59 reachable checks. The
user requested those missing names be added through GitHub as well. Another 56
exact hostnames were initially added. The user then explicitly overrode the
protected `cdn.cookielaw.org` and `udc.yahoo.com` exceptions, adding both and
bringing the main feeds to **207,374** with all 58 requested hostnames. These include
consent interfaces, feature flags, support/chat systems, affiliate routing,
social application APIs, and video routing as explicitly requested; they are not
all exclusively ad delivery. `vk.com/rtrg` is a URL path and was not converted into
a network-wide block on the whole `vk.com` hostname.

The user also requested additional missing hosts from the Safari OBFUSGATED test.
Its current published inventory supplied 83 plain hostnames not covered by the
main feed. Of these, 68 already returned blocking addresses through UniFi's native
filter, so a browser's "accessible" label was not treated as proof that the
gateway allowed the origin. Another 81 names were added explicitly to the main
feeds, bringing the total to **207,455**, with zero historical removals. The feed
was published to GitHub before the gateway sync.

Two candidates were held out: `youtubei.googleapis.com`, a YouTube application
API whose network-wide denial can disrupt YouTube, and `greatis.com`, a
[security-software vendor](https://greatis.com/) placed by the test under
"Malicious Scripts." These require a separate user choice. The URL-path case
`vk.com/rtrg` remains omitted. This is a domain-coverage change, not a claim of
100% advertising prevention or of safety for every benchmark entry.

### Meta and mobile ad delivery follow-up

A local device traffic review found successful connections to `ep7.facebook.com`
and several ad supply, creative delivery, and measurement hostnames that were
absent from the main feed. Twenty-one names were added: 13 Meta tracking/graph
endpoints and eight exact ad supply/creative/measurement hosts. The Meta siblings
and fallbacks are documented in [HaGeZi's service notes](https://github.com/hagezi/dns-blocklists/blob/main/share/facebook.txt).
The main feeds now contain **207,476** domains, with zero removals. Private device
logs, application usage, addresses, and captures are not published in this repo.

The observed Fyber/Inneractive delivery and event hostnames were already blocked
by the native Content Filter through the existing `fyber.com` and
`inner-active.mobi` rules. Adding the other observed ad hosts closes specific
gaps, but does not establish which partner supplied a branded ad. No broad Meta
content-CDN, CloudFront, S3, or shared-IP block was introduced. Meta graph/tracking
endpoints can also support normal Facebook/Instagram features; the aggressive
service scope is intentional. Cached DNS, existing connections, cached ads, and
encrypted alternative DNS remain limits of domain filtering.

The same review confirmed blocks for InMobi's `eus-r.w.inmobi.com`,
`et-eus.w.inmobi.com`, `unif-id.ssp.inmobi.com`, `supply.inmobicdn.net`, and
`i.l.inmobicdn.net`. The existing `inmobi.com` and `inmobicdn.net` rules already
cover those names. A visible InMobi label alone is not evidence that those DNS
blocks failed or that any unrelated content CDN should be denied.

A subsequent live capture found successful DNS answers and TLS handshakes for
`cdn.4dvertible.com` and `api3.4dvertible.com` during another ad attempt, while
Fyber's endpoints returned blocking answers. Both exact names were added, bringing
the feeds to **207,478** domains. The [AdCP registry](https://adcontextprotocol.org/registry/)
associates the `4dvertible.com` service with Advertible Inc.; that does not
establish ownership by Digital Turbine or prove which encrypted response carried
a particular ad. The user chose to retain access to Meta's shared CNAME aliases
rather than disable Facebook/Instagram applications through those shared names.

The user then explicitly requested the advertiser `cantina.com` and DSP Moloco
Ads be blocked. `cantina.com`, `dsp-api.moloco.com`, and `adsmoloco.com` were added;
`molocoads.com` was already historical and is now also recorded in manual inputs.
The three new parent rules bring the feeds to **207,481** domains and cover the
advertiser site and regional Moloco delivery subdomains. This includes the
previously observed `eventfnt-us.dsp-api.moloco.com`, `noti-us.adsmoloco.com`, and
`cdn-f.adsmoloco.com` hosts. The ordinary corporate `moloco.com` parent was not
converted into a whole-site rule.

## What was checked

Compared the existing feed, four HaGeZi tiers, AdGuard DNS and its
exclusions/exceptions, OISD big, Peter Lowe, EasyList's ad-server section, and
EasyPrivacy's tracking-server section. The EasyPrivacy section checked is small
and is not the complete EasyPrivacy collection. The lists overlap and often share
upstreams; agreement is corroboration, not independent proof of safety.

[`coverage-review.json`](coverage-review.json) records exact URLs, hashes,
review time, all 25 Safari domain results, relevant vendor hostnames, named-host
protection checks, and cross-publisher disagreements. These are dated snapshots;
the daily build report records the continuously fetched NORMAL source separately.

NORMAL supplies broader coverage without automatically adding PRO's crash
reporting restrictions. PRO/ULTIMATE, threat feeds, whole gambling categories,
and browser-specific contextual rules were inspected or considered but not blindly
merged. The main feed still includes tracking and telemetry, not just visual ads.

## Bally Bet: root and every subdomain

The requested restriction is intentional blocking of the betting service, rather
than classifying its entire website as an ad server. Plain-domain entries include:

```text
ballybet.com
play.ballybet.com
```

For AdGuard Home or another compatible Adblock DNS filter, the complete rule is:

```text
||ballybet.com^
```

This covers the root, `play`, and other subdomains at any depth. A bare hostname
can be exact-only depending on the resolver. `*.ballybet.com` is not accepted in
this repository's domain-only files. `ballys.com` and shared platforms used by
other betting operators were not added. This request was not expanded into a
block of every gambling site or every Bally-branded service.

## Digital Turbine

The main feed contains 38 names in the reviewed Digital Turbine families:
AdColony, Fyber, Inneractive, SponsorPay, TPBid, and specific DT Ignite endpoints.
Several roots were already in the LIGHT baseline:

```text
adcolony.com
fyber.com
inner-active.mobi
sponsorpay.com
tpbid.com
```

The explicit suffix-rule output covers their subdomains, including AdColony's
advertising hosts. The expanded feed also includes 32 specific `dtignite.com`
client API/download hosts and the additional Inneractive family root recorded in
the JSON audit. Root-level `dtignite.com` and `digitalturbine.com` blocks were
withheld: the latter hosts corporate information/documentation, while Ignite also
provides app installation and recommendations. No domains were invented from
branding or registration similarities.

Blocking these services can prevent rewarded ads, offer-wall rewards, developer
console access under already-blocked vendor roots, and promotional app installs.
These are limits of DNS blocking, even when the intended ad delivery is caught.
Corporate documentation on `docs.digitalturbine.com` is checked as a protected
name; this does not guarantee access to every legacy Fyber console or website.

Vendor context: [Digital Turbine legal/acquisitions](https://www.digitalturbine.com/legal),
[app-install service description](https://www.digitalturbine.com/legal/dt-clients-ignite-terms-of-service).

## Yahoo-hosted ads

The main feed contains 48 names across reviewed Yahoo, Yahoo CDN, legacy ad-tech,
and related families. It includes specific ad and measurement endpoints such as:

```text
ads.yahoo.com
adserver.yahoo.com
analytics.yahoo.com
analytics.query.yahoo.com
beap-bc.yahoo.com
cookiex.ngd.yahoo.com
gemini.yahoo.com
log.fc.yahoo.com
partnerads.ysm.yahoo.com
udcm.yahoo.com
adtech.yahooinc.com
ads.yimg.com
```

Two additional endpoints, `3p-udc.yahoo.com` and `bats.video.yahoo.com`, were
corroborated in both AdGuard DNS and OISD. NORMAL and retained history provide the
other family entries listed in the audit. The family count measures names, not
distinct companies or the number of requests blocked.

Do not replace this with blanket blocks on `yahoo.com`, `yahoo.net`, `yimg.com`,
`s.yimg.com`, `yahooinc.com`, or `yahoodns.net`. Named-host checks prevent a parent
block from covering Yahoo Mail, login, finance/news/search/sports pages, and the
shared `s.yimg.com` content host. `udc.yahoo.com`, which AdGuard excludes from
DNS-wide blocking, is protected too; it is different from `udcm.yahoo.com`.

Some Yahoo ads/tracking share a hostname with useful images or scripts. DNS
cannot distinguish those URL paths. A browser content blocker using maintained
EasyList/AdGuard Base and privacy filters is needed for that part. No browser
URL/path rule was broadened into an entire shared-host DNS block. See the
[maintainer's Yahoo Mail report](https://github.com/uBlockOrigin/uAssets/issues/31800)
and [AdGuard's contextual Yahoo rules](https://github.com/AdguardTeam/AdguardFilters/blob/master/BaseFilter/sections/allowlist.txt).

## The Safari test and why a perfect score is not the target

The displayed 29 failures were 25 domains plus Static Ad, Dynamic Ad, `ads.js`,
and `pagead.js`. The latter four are page/script tests, not missing domains.
Do not block the test site itself to hide these failures.

Eighteen of the 25 domain failures were already covered by LIGHT under suffix
matching. NORMAL covers one more (`business-api.tiktok.com`). All 19 are now
explicit manual hostnames as well. Observed failures on names already present
can indicate that the supplemental feed is not enforced, that a resolver is
using exact matching, an allow rule, a bypass, or cached results; this audit did
not isolate which applies to the current Safari session.

The remaining six were initially **optional**, separately provided in
[`optional-privacy-adblock.txt`](optional-privacy-adblock.txt):

```text
api.bugsnag.com
app.bugsnag.com
app.getsentry.com
appmetrica.yandex.ru
browser.sentry-cdn.com
metrika.yandex.ru
```

They cover error reporting, its interfaces, and app analytics. They occur in
HaGeZi PRO but not NORMAL. They are not all ad delivery endpoints, and forcing
them into the default to improve a score is a separate privacy choice. The user
subsequently requested that choice explicitly; they are now in the main feeds.

## False-positive review and remaining uncertainty

Three new source candidates were withheld before publication: `totaladblock.com`
(AdGuard says its website is not used to show ads), `admin.dable.io`, and
`proto2ad.durasite.net` (AdGuard exception entries). They are in `exclude-new.txt`
and checked against future parent-block reintroduction.

The build also checks named critical hosts and your exact CookieLaw/OneTrust
exceptions. A collision fails before output writes. This protects only the named
hosts against matching parent rules; it is not a broad live allowlist, a CNAME
test, or certification that every other domain is safe to block.

The cross-publisher scan found **18 pre-existing direct hostname disagreements**
with AdGuard exclusions/exceptions, detailed in the JSON audit. Examples include
`api.amplitude.com`, `cxpublic.com`, `etracker.com`, and specific content/console
hosts underneath historical ad-network roots. These are compatibility risks or
policy differences, not confirmed household breakage. No blanket allow was
silently applied. CNAME-target disagreements and complex contextual exceptions
need additional runtime evaluation; this scan does not enumerate all of them.

Also, 552 historical LIGHT names are absent from the current NORMAL snapshot.
That alone does not establish false positives, but the append-only policy keeps
them, and future upstream corrections cannot remove historical names. Therefore
neither this review nor a 100% ad-test score can establish zero false positives.
Confirmed unwanted blocks need a resolver allow rule or an explicitly approved
change to the repository's historical-retention policy.

Before considering the feed deployed, verify the resolver actually imports the
expected rule count and logs blocked queries; test the Bally root and `play`, an
unlisted Bally subdomain for suffix behavior, and representative Yahoo/DT ad
hosts. Separately check Yahoo login, inbox, attachments, images/video and ordinary
sites such as `ui.com` and Xfinity. The previously paused UniFi IP-based firewall
rule was unsuitable for this DNS feed and has since been removed.

## Validation performed

The 13 local tests pass, including failure-before-write for protected-name
collisions, output-format consistency, checksum tampering, failed sources,
concurrent updates, and retention of committed domains. Offline validation checks
both generated feeds against the build report and the original 88,382-domain
baseline. Every reviewed main-feed hostname and protected name is checked for
label-boundary suffix coverage. These are content/build checks; live DNS,
browser, Yahoo account, app-install, and rewarded-ad behavior were not tested.

Matching reference: [AdGuard DNS syntax](https://adguard-dns.io/kb/general/dns-filtering-syntax/).
UniFi configuration reference: [Ubiquiti DNS Content Filtering](https://help.ui.com/hc/en-us/articles/12568927589143-Content-and-Domain-Filtering-in-UniFi).
