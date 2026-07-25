import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.update_ips import extract_ips, fetch_config, write_mikrotik, write_result


def _ip_sort_key(value):
    return tuple(int(part) for part in value.split("."))


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class UpdateIpsTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "success": True,
            "revision": 42,
            "pops": {
                "one": {"relays": [{"ipv4": "10.0.0.2"}, {"ipv4": "10.0.0.1"}]},
                "two": {"relays": [{"ipv4": "10.0.0.2"}]},
                "no-relays": {"tier": 1},
            },
        }

    def test_fetches_and_validates_response(self):
        response = Response(json.dumps(self.config).encode())
        with patch("urllib.request.urlopen", return_value=response) as urlopen:
            self.assertEqual(fetch_config(attempts=1), self.config)
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 30)

    def test_retries_network_errors(self):
        response = Response(json.dumps(self.config).encode())
        with patch(
            "urllib.request.urlopen", side_effect=[OSError("offline"), response]
        ) as urlopen:
            self.assertEqual(fetch_config(attempts=2, sleep=lambda _: None), self.config)
        self.assertEqual(urlopen.call_count, 2)

    def test_extracts_unique_numerically_sorted_addresses(self):
        self.assertEqual(extract_ips(self.config), ["10.0.0.1", "10.0.0.2"])

    def test_rejects_empty_or_invalid_addresses(self):
        self.config["pops"] = {"empty": {}}
        with self.assertRaisesRegex(ValueError, "no IPv4"):
            extract_ips(self.config)
        self.config["pops"] = {"bad": {"relays": [{"ipv4": "not-an-ip"}]}}
        with self.assertRaisesRegex(ValueError, "invalid IP"):
            extract_ips(self.config)

    def test_writes_expected_json_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "ips.json"
            result = write_result(output, self.config, "fixture.json")
            data = json.loads(output.read_text(encoding="utf-8"))
            leftovers = list(output.parent.glob(".ips.json.*"))
        self.assertEqual(data, result)
        self.assertEqual(data["source"], "fixture.json")
        self.assertEqual(data["revision"], 42)
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["ips"], ["10.0.0.1", "10.0.0.2"])
        self.assertRegex(data["updated_at"], r"^\d{4}-\d{2}-\d{2}T")
        self.assertEqual(leftovers, [])

    def test_committed_output_is_valid_and_nonempty(self):
        result = json.loads(Path("ips.json").read_text(encoding="utf-8"))
        self.assertEqual(result["count"], len(result["ips"]))
        self.assertGreater(result["count"], 0)
        self.assertEqual(result["ips"], sorted(result["ips"], key=_ip_sort_key))
        self.assertEqual(len(result["ips"]), len(set(result["ips"])))

    def test_writes_importable_mikrotik_script(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "list.rsc"
            write_mikrotik(output, ["10.0.0.1", "10.0.0.2"])
            lines = output.read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            lines[0],
            '/ip firewall address-list remove [find list="CounterStrike"]',
        )
        self.assertIn('address=10.0.0.1 list="CounterStrike"', lines[1])
        self.assertIn('address=10.0.0.2 list="CounterStrike"', lines[2])

    def test_committed_mikrotik_output_matches_json(self):
        result = json.loads(Path("ips.json").read_text(encoding="utf-8"))
        contents = Path("list.rsc").read_text(encoding="utf-8")
        for address in result["ips"]:
            self.assertIn(f"address={address} ", contents)
        self.assertEqual(contents.count("/ip firewall address-list add "), result["count"])

    def test_cli_end_to_end_with_local_http_server(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config.json").write_text(json.dumps(self.config), encoding="utf-8")
            output = root / "result.json"
            mikrotik_output = root / "result.rsc"
            server_code = (
                "import http.server, os; "
                f"os.chdir({directory!r}); "
                "server=http.server.ThreadingHTTPServer(('127.0.0.1', 0), "
                "http.server.SimpleHTTPRequestHandler); "
                "print(server.server_port, flush=True); server.serve_forever()"
            )
            process = subprocess.Popen(
                [sys.executable, "-c", server_code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                port = process.stdout.readline().strip()
                env = {**os.environ, "STEAM_API_URL": f"http://127.0.0.1:{port}/config.json"}
                completed = subprocess.run(
                    [
                        sys.executable,
                        "scripts/update_ips.py",
                        "--output",
                        str(output),
                        "--mikrotik-output",
                        str(mikrotik_output),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    env=env,
                )
            finally:
                process.terminate()
                process.communicate(timeout=5)
            result = json.loads(output.read_text(encoding="utf-8"))
            mikrotik_contents = mikrotik_output.read_text(encoding="utf-8")
        self.assertEqual(result["count"], 2)
        self.assertIn("address=10.0.0.1", mikrotik_contents)
        self.assertIn("Wrote 2 relay IPs", completed.stdout)


if __name__ == "__main__":
    unittest.main()
