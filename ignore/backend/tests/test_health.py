import os
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from main import app
from fastapi.testclient import TestClient


class HealthTest(unittest.TestCase):
    def test_health_endpoint(self):
        client = TestClient(app)
        resp = client.get('/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('status'), 'ok')
        self.assertIn('providers', data)


if __name__ == '__main__':
    unittest.main()
