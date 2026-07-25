#!/usr/bin/env python3
"""Fetch Counter-Strike 2 SDR configuration and persist its relay IPs."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_URL = "https://api.steampowered.com/ISteamApps/GetSDRConfig/v1/?appid=730"


def fetch_config(url: str = DEFAULT_URL) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "CounterStrike-IP/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)

    if not isinstance(data, dict) or data.get("success") is not True:
        raise ValueError("Steam returned an unsuccessful or invalid response")
    if not isinstance(data.get("pops"), dict):
        raise ValueError("Steam response does not contain a valid 'pops' object")
    return data


def extract_ips(config: dict[str, Any]) -> list[str]:
    """Return unique IPv4 relay addresses in a stable order."""
    addresses: set[str] = set()
    for pop in config["pops"].values():
        if not isinstance(pop, dict):
            continue
        relays = pop.get("relays", [])
        if not isinstance(relays, list):
            continue
        for relay in relays:
            if isinstance(relay, dict) and isinstance(relay.get("ipv4"), str):
                addresses.add(relay["ipv4"])
    return sorted(addresses, key=lambda ip: tuple(int(part) for part in ip.split(".")))


def write_result(path: Path, config: dict[str, Any]) -> None:
    ips = extract_ips(config)
    result = {
        "source": DEFAULT_URL,
        "revision": config.get("revision"),
        "count": len(ips),
        "ips": ips,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(result, output, indent=2, ensure_ascii=False)
            output.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        os.unlink(temporary_name)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("ips.json"))
    parser.add_argument("--url", default=DEFAULT_URL)
    args = parser.parse_args()
    write_result(args.output, fetch_config(args.url))


if __name__ == "__main__":
    main()
