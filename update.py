#!/usr/bin/env python3
"""Build a supplemental DNS blocklist whose committed domain set only grows.

SPDX-License-Identifier: GPL-3.0-only
"""

import argparse
import fcntl
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parent
MAX_BYTES = 32 * 1024 * 1024
LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


def normalize(value):
    value = value.lower().rstrip(".")
    try:
        value = value.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError(f"Invalid domain: {value!r}") from exc
    try:
        ipaddress.ip_address(value)
    except ValueError:
        pass
    else:
        raise ValueError(f"IP addresses are not domains: {value!r}")
    labels = value.split(".")
    if (len(value) > 253 or len(labels) < 2
            or not all(LABEL.fullmatch(label) for label in labels)
            or labels[-1].isdigit()):
        raise ValueError(f"Invalid domain: {value!r}")
    return value


def parse(text, hosts=False):
    """Accept domain lines, comments, and optionally sinkhole hosts lines.

    Reject unsupported filter syntax rather than silently broadening its scope.
    """
    domains = set()
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith(("#", "!")):
            continue
        fields = line.split("#", 1)[0].split()
        if hosts and fields[0] in ("0.0.0.0", "127.0.0.1", "::", "::1"):
            fields = fields[1:]
            if not fields:
                raise ValueError(f"Line {number}: hosts entry has no domain")
        elif len(fields) != 1:
            raise ValueError(f"Line {number}: expected one domain")
        for field in fields:
            if hosts and field.lower().rstrip(".") in ("localhost", "localhost.localdomain", "broadcasthost"):
                continue
            try:
                domains.add(normalize(field))
            except ValueError as exc:
                raise ValueError(f"Line {number}: {exc}") from exc
    return domains


def read_domains(path, hosts=False):
    return parse(path.read_text(encoding="utf-8-sig"), hosts=hosts)


def encode(domains):
    return "".join(domain + "\n" for domain in sorted(domains))


def encode_adblock(domains):
    """Explicit suffix matching; a bare domain is exact-only in some resolvers."""
    return "".join("||" + domain + "^\n" for domain in sorted(domains))


def require_protected_names(domains, protected):
    """Reject blocks on a protected hostname or any of its parent domains."""
    conflicts = []
    for hostname in sorted(protected):
        labels = hostname.split(".")
        for index in range(len(labels) - 1):
            parent = ".".join(labels[index:])
            if parent in domains:
                conflicts.append(f"{parent} blocks protected name {hostname}")
    if conflicts:
        raise ValueError("Protected-domain violation: " + "; ".join(conflicts))


def require_superset(previous, proposed):
    missing = previous - proposed
    if missing:
        raise ValueError(f"Additive-only violation: {len(missing)} domains would be removed")


def fetch(source, root):
    if ("url" in source) == ("path" in source):
        raise ValueError("Each source needs exactly one of url or path")
    if "path" in source:
        data = (root / source["path"]).read_bytes()
    else:
        url = source["url"]
        if not url.startswith("https://"):
            raise ValueError("Remote sources must use HTTPS")
        request = urllib.request.Request(url, headers={"User-Agent": "unifi-additive-blocklist/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            if not response.url.startswith("https://"):
                raise ValueError("Source redirected away from HTTPS")
            data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Source exceeds 32 MiB")
    domains = parse(data.decode("utf-8-sig"), hosts=True)
    minimum = source.get("minimum_domains", 1)
    if minimum < 1 or len(domains) < minimum:
        raise ValueError(f"{source['name']}: source has {len(domains)} domains; minimum is {minimum}")
    return domains, hashlib.sha256(data).hexdigest()


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run(args):
    # Serialize read/union/write as one operation. Kernel releases the lock on exit.
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    lock_path = (config_path.parent / config["output"]).parent / ".update.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        build(args)


def build(args):
    config_path = args.config.resolve()
    root = config_path.parent
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output = root / config["output"]
    report_path = root / config["report"]
    adblock_path = root / config["adblock_output"] if config.get("adblock_output") else None
    paths = [output, report_path] + ([adblock_path] if adblock_path else [])
    if len({path.resolve() for path in paths}) != len(paths):
        raise ValueError("Output and report paths must differ")
    protected = read_domains(root / config["protected_domains"]) if config.get("protected_domains") else set()
    if args.check and (args.initialize or args.import_file):
        raise ValueError("--check cannot be combined with --initialize or --import")
    if args.check:
        actual = output.read_text(encoding="utf-8")
        domains = parse(actual)
        if not domains or actual != encode(domains):
            raise ValueError("Blocklist must be nonempty, sorted, unique, and canonical")
        require_protected_names(domains, protected)
        if args.baseline:
            require_superset(read_domains(args.baseline), domains)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report["sha256"] != hashlib.sha256(actual.encode()).hexdigest() or report["total"] != len(domains):
            raise ValueError("Build report does not match the blocklist")
        if adblock_path:
            actual_adblock = adblock_path.read_text(encoding="utf-8")
            if (actual_adblock != encode_adblock(domains)
                    or report.get("adblock_sha256") != hashlib.sha256(actual_adblock.encode()).hexdigest()):
                raise ValueError("Adblock output does not match the blocklist/report")
        print(f"Verified {len(domains)} domains")
        return
    if args.baseline:
        raise ValueError("--baseline is used with --check")
    if not output.exists() and not args.initialize:
        raise ValueError("Existing blocklist missing; restore it from Git. Use --initialize only for the first build")
    if output.exists() and args.initialize:
        raise ValueError("--initialize requires an absent blocklist")
    old_text = output.read_text(encoding="utf-8") if output.exists() else ""
    previous = parse(old_text)
    if output.exists() and (not previous or old_text != encode(previous)):
        raise ValueError("Existing blocklist is invalid; restore its canonical version before updating")
    candidates = set()
    sources = []
    if not config["sources"]:
        raise ValueError("At least one source is required")
    for source in config["sources"]:
        domains, digest = fetch(source, root)
        candidates.update(domains)
        sources.append({"name": source["name"], "location": source.get("url", source.get("path")),
                        "license": source["license"], "domains": len(domains), "sha256": digest})
    candidates.update(read_domains(root / config["manual_additions"]))
    imported = set()
    for path in args.import_file:
        imported.update(read_domains(path, hosts=True))
    # Historical entries are deliberately never passed through exclusions.
    exclusions = read_domains(root / config["exclude_new"])
    candidates.difference_update(exclusions)
    proposed = previous | imported | candidates
    require_superset(previous, proposed)
    require_protected_names(proposed, protected)
    if not proposed:
        raise ValueError("Refusing an empty blocklist")
    if len(proposed) > config["maximum_domains"]:
        raise ValueError("Domain limit exceeded; review the sources before raising maximum_domains")
    text = encode(proposed)
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "previous": len(previous),
              "added": len(proposed - previous), "removed": 0, "total": len(proposed),
              "sha256": hashlib.sha256(text.encode()).hexdigest(), "sources": sources}
    adblock_text = encode_adblock(proposed) if adblock_path else None
    if adblock_path:
        report["adblock_sha256"] = hashlib.sha256(adblock_text.encode()).hexdigest()
    if args.write:
        # Refuse stale writes when another updater changed the file during downloads.
        current = output.read_text(encoding="utf-8") if output.exists() else ""
        if current != old_text:
            raise ValueError("Blocklist changed during update; retry against the latest version")
        atomic_write(output, text)
        if adblock_path:
            atomic_write(adblock_path, adblock_text)
        atomic_write(report_path, json.dumps(report, indent=2) + "\n")
    print(json.dumps({"mode": "written" if args.write else "dry-run", **report}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "sources.json")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write the union; default is a dry run")
    mode.add_argument("--check", action="store_true", help="validate committed output offline")
    parser.add_argument("--initialize", action="store_true", help="explicit first build only")
    parser.add_argument("--import", dest="import_file", type=Path, action="append", default=[],
                        help="also retain domains from a local list; repeatable")
    parser.add_argument("--baseline", type=Path, help="with --check, require retention of this prior list")
    args = parser.parse_args()
    try:
        run(args)
    except (OSError, ValueError, KeyError, UnicodeError) as exc:
        print(f"Update failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
