import json
import tempfile
import unittest
from pathlib import Path

from scripts.update_ips import extract_ips, write_result


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

    def test_extracts_unique_numerically_sorted_addresses(self):
        self.assertEqual(extract_ips(self.config), ["10.0.0.1", "10.0.0.2"])

    def test_writes_expected_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "ips.json"
            write_result(output, self.config)
            data = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(data["revision"], 42)
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["ips"], ["10.0.0.1", "10.0.0.2"])


if __name__ == "__main__":
    unittest.main()
