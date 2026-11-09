#!/usr/bin/env python3
"""Synchronize an append-only DNS feed into one existing UniFi Content Filter.

Default is a preview. Credentials and all deployment state belong outside Git.
SPDX-License-Identifier: GPL-3.0-only
"""
import argparse
import copy
from datetime import datetime, timezone
import fcntl
import hashlib
import http.client
import ipaddress
import json
import os
from pathlib import Path
import re
import ssl
import sys
import tempfile
import urllib.parse
import urllib.request

MAX_BYTES = 32 * 1024 * 1024
LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")


def domains(values):
    if not isinstance(values, list) or not all(isinstance(x, str) for x in values):
        raise ValueError("Expected a list of plain domain names")
    result = set()
    for name in values:
        if name != name.strip().lower().rstrip("."):
            raise ValueError("Domain must be a lowercase literal hostname")
        labels = name.split(".")
        if len(name) > 253 or len(labels) < 2 or labels[-1].isdigit() or not all(LABEL.fullmatch(x) for x in labels):
            raise ValueError("Invalid domain in list")
        try:
            ipaddress.ip_address(name)
        except ValueError:
            result.add(name)
        else:
            raise ValueError("IP addresses are not DNS domains")
    return result


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as out:
            temporary = Path(out.name)
            json.dump(value, out, indent=2)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def private_read(path):
    info = path.stat()
    if info.st_mode & 0o077 or info.st_uid != os.geteuid():
        raise ValueError("Credential file must be owner-only and owned by the running user")
    return path.read_text().strip()


def download(url):
    if not url.startswith("https://"):
        raise ValueError("The feed requires HTTPS")
    with urllib.request.urlopen(url, timeout=90) as response:
        if not response.url.startswith("https://"):
            raise ValueError("Insecure feed redirect refused")
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Feed exceeds the download size limit")
    return data


class API:
    def __init__(self, config, root):
        base = urllib.parse.urlsplit(config["gateway"])
        if base.scheme != "https" or base.path not in ("", "/") or base.username or base.query or base.fragment:
            raise ValueError("Invalid gateway URL")
        self.host, self.port = base.hostname, base.port or 443
        self.pin = config["certificate_sha256"].lower()
        if not re.fullmatch(r"[a-f0-9]{64}", self.pin):
            raise ValueError("A gateway certificate SHA256 pin is required")
        self.key = private_read(root / "api-key")
        if not self.key or any(c.isspace() for c in self.key):
            raise ValueError("API key is empty or malformed")
        self.collection = "/proxy/network/v2/api/site/" + urllib.parse.quote(config.get("site", "default"), safe="") + "/content-filtering"

    def request(self, method, path, payload=None):
        # Verify the certificate pin BEFORE transmitting credentials. The pin is
        # obtained through the user's authenticated SSH connection at deployment.
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        connection = http.client.HTTPSConnection(self.host, self.port, context=context, timeout=120)
        try:
            connection.connect()
            actual = hashlib.sha256(connection.sock.getpeercert(binary_form=True)).hexdigest()
            if actual != self.pin:
                raise ValueError("Gateway certificate changed; verify and update the pin through SSH")
            headers = {"X-API-KEY": self.key, "Accept": "application/json"}
            body = None
            if payload is not None:
                body = json.dumps(payload, separators=(",", ":")).encode()
                headers["Content-Type"] = "application/json"
                if len(body) > MAX_BYTES:
                    raise ValueError("API payload exceeds the safety limit")
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            data = response.read(MAX_BYTES + 1)
            if not 200 <= response.status < 300:
                # Do not print response bodies that may contain account details.
                raise ValueError("UniFi API returned HTTP " + str(response.status))
            if len(data) > MAX_BYTES:
                raise ValueError("API response exceeds the safety limit")
            return json.loads(data) if data else None
        finally:
            connection.close()

    def get_profile(self, config):
        profiles = self.request("GET", self.collection)
        if not isinstance(profiles, list):
            raise ValueError("Unrecognized Content Filter API response")
        matches = [p for p in profiles if p.get("_id") == config["profile_id"]]
        if len(matches) != 1:
            raise ValueError("Expected Content Filter profile was not found uniquely")
        profile = matches[0]
        if profile.get("name") != config["profile_name"] or profile.get("network_ids") != config["network_ids"]:
            raise ValueError("Content Filter identity or network assignment changed; review before updating")
        if profile.get("enabled") is not True:
            raise ValueError("Target Content Filter is disabled; refusing to enable it automatically")
        return profile


def plan(profile, feed, history, maximum):
    current = domains(profile["block_list"])
    allowed = domains(profile["allow_list"])
    proposed = current | feed | history
    if len(proposed) > maximum:
        raise ValueError("Combined list exceeds the configured maximum")
    # Keep all historical names and preserve the user's current allowlist.
    result = copy.deepcopy(profile)
    result["block_list"] = sorted(proposed)
    result["allow_list"] = sorted(allowed)
    return result


def verify(expected, actual):
    if domains(actual.get("block_list")) != domains(expected["block_list"]):
        raise ValueError("API read-back did not retain the complete blocklist")
    if domains(actual.get("allow_list")) != domains(expected["allow_list"]):
        raise ValueError("API read-back did not retain the complete allowlist")
    for key, value in expected.items():
        if key not in ("block_list", "allow_list") and actual.get(key) != value:
            raise ValueError("Unrelated Content Filter setting changed: " + key)


def run(args):
    config_path = args.config.resolve()
    root = config_path.parent
    config = json.loads(config_path.read_text())
    os.umask(0o077)
    with (root / "sync.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        api = API(config, root)
        profile = api.get_profile(config)
        raw = download(config["feed_url"])
        feed = domains([x for x in raw.decode("utf-8-sig").splitlines() if x and not x.startswith("#")])
        if len(feed) < config.get("minimum_domains", 80000):
            raise ValueError("Feed is unexpectedly small; existing filter left intact")
        history_file = root / "history.json"
        if history_file.exists():
            history = domains(json.loads(history_file.read_text()))
        elif args.initialize:
            history = set()
        else:
            raise ValueError("History missing; explicit --initialize required on first deployment")
        expected = plan(profile, feed, history, config.get("maximum_domains", 500000))
        status = {"at": datetime.now(timezone.utc).isoformat(), "feed_domains": len(feed),
                  "total_domains": len(expected["block_list"]),
                  "added": len(set(expected["block_list"]) - set(profile["block_list"])),
                  "feed_sha256": hashlib.sha256(raw).hexdigest(), "applied": False}
        if args.apply:
            # Catch UI edits made during the download; never knowingly clobber them.
            if api.get_profile(config) != profile:
                raise ValueError("Profile changed during download; retry after the UI edit completes")
            backup = root / "backups" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
            atomic_json(backup, profile)
            if expected != profile:
                api.request("PUT", api.collection + "/" + urllib.parse.quote(config["profile_id"], safe=""), expected)
            verify(expected, api.get_profile(config))
            atomic_json(history_file, expected["block_list"])
            status["applied"] = True
            atomic_json(root / "last-success.json", status)
        print(json.dumps(status, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("/data/unifi-additive-sync/config.json"))
    parser.add_argument("--apply", action="store_true", help="write and verify the DNS Content Filter")
    parser.add_argument("--initialize", action="store_true", help="explicitly initialize missing history on first deployment")
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, OSError, KeyError, TypeError, http.client.HTTPException) as error:
        print("Sync failed: " + str(error), file=sys.stderr)
        sys.exit(1)
