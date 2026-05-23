import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from schemas.dashboard_schema import normalize_dashboard_payload


class DashboardSchemaTest(unittest.TestCase):
    def test_normalized_schema_keys(self):
        data = normalize_dashboard_payload({"title": "T", "summary": "S"}, "generic")
        expected = {"theme", "layout", "sections", "metadata"}
        self.assertTrue(expected.issubset(set(data.keys())))


if __name__ == '__main__':
    unittest.main()
