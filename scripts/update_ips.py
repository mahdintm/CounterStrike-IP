#!/usr/bin/env python3
"""Download Steam's CS2 SDR configuration and write its relay IPv4 addresses."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

DEFAULT_URL = os.environ.get(
    "STEAM_API_URL",
    "https://api.steampowered.com/ISteamApps/GetSDRConfig/v1/?appid=730",
)


def fetch_config(
    url: str = DEFAULT_URL,
    *,
    attempts: int = 3,
    timeout: float = 30,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Fetch and validate an SDR response, retrying temporary network failures."""
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "CounterStrike-IP/2.0"},
    )
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                config = json.load(response)
            validate_config(config)
            return config
        except (OSError, ValueError, json.JSONDecodeError) as error:
            last_error = error
            if attempt < attempts:
                sleep(5 * attempt)
    raise RuntimeError(f"Steam API failed after {attempts} attempts: {last_error}")


def validate_config(config: Any) -> None:
    if not isinstance(config, dict) or config.get("success") is not True:
        raise ValueError("Steam returned an unsuccessful or invalid response")
    if not isinstance(config.get("pops"), dict):
        raise ValueError("Steam response does not contain a valid 'pops' object")


def extract_ips(config: dict[str, Any]) -> list[str]:
    """Return unique, validated IPv4 relay addresses in numeric order."""
    validate_config(config)
    addresses: set[ipaddress.IPv4Address] = set()
    for pop in config["pops"].values():
        if not isinstance(pop, dict) or not isinstance(pop.get("relays", []), list):
            continue
        for relay in pop.get("relays", []):
            if not isinstance(relay, dict) or not isinstance(relay.get("ipv4"), str):
                continue
            try:
                address = ipaddress.ip_address(relay["ipv4"])
            except ValueError as error:
                raise ValueError(f"Steam returned an invalid IP: {relay['ipv4']}") from error
            if not isinstance(address, ipaddress.IPv4Address):
                raise ValueError(f"Steam returned a non-IPv4 relay: {address}")
            addresses.add(address)
    if not addresses:
        raise ValueError("Steam response contains no IPv4 relay addresses")
    return [str(address) for address in sorted(addresses)]


def build_result(config: dict[str, Any], source: str = DEFAULT_URL) -> dict[str, Any]:
    ips = extract_ips(config)
    return {
        "source": source,
        "revision": config.get("revision"),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(ips),
        "ips": ips,
    }


def write_result(path: Path, config: dict[str, Any], source: str = DEFAULT_URL) -> dict[str, Any]:
    """Atomically write the result and return the serialized object."""
    result = build_result(config, source)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(result, output, indent=2, ensure_ascii=False)
            output.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
        raise
    return result


def write_mikrotik(path: Path, ips: list[str], address_list: str = "CounterStrike") -> None:
    """Atomically write an importable RouterOS address-list script."""
    if not address_list or any(character in address_list for character in '"\r\n'):
        raise ValueError("MikroTik address-list name contains invalid characters")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            output.write(f'/ip firewall address-list remove [find list="{address_list}"]\n')
            for address in ips:
                output.write(
                    f'/ip firewall address-list add address={address} '
                    f'list="{address_list}" comment="Steam CS2 relay"\n'
                )
        os.replace(temporary_name, path)
    except BaseException:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("ips.json"))
    parser.add_argument("--mikrotik-output", type=Path, default=Path("list.rsc"))
    parser.add_argument("--mikrotik-list", default="CounterStrike")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--input", type=Path, help="read a saved Steam response instead")
    args = parser.parse_args()

    if args.input:
        with args.input.open(encoding="utf-8") as source_file:
            config = json.load(source_file)
        source = str(args.input)
    else:
        config = fetch_config(args.url)
        source = args.url
    result = write_result(args.output, config, source)
    write_mikrotik(args.mikrotik_output, result["ips"], args.mikrotik_list)
    print(
        f"Wrote {result['count']} relay IPs (revision {result['revision']}) "
        f"to {args.output} and {args.mikrotik_output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
