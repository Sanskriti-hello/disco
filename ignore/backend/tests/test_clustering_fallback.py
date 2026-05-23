import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from services.llm_router import deterministic_cluster_tabs


class ClusterFallbackTest(unittest.TestCase):
    def test_deterministic_cluster_tabs(self):
        tabs = [
            {"title": "Buy laptop on Amazon", "url": "https://amazon.com", "content": "price comparison"},
            {"title": "Arxiv ML Paper", "url": "https://arxiv.org", "content": "study deep learning"},
            {"title": "Stack Overflow bug fix", "url": "https://stackoverflow.com", "content": "code issue"},
        ]
        clusters = deterministic_cluster_tabs(tabs)
        self.assertGreaterEqual(len(clusters), 1)
        total = sum(len(c['tabs']) for c in clusters)
        self.assertEqual(total, len(tabs))


if __name__ == '__main__':
    unittest.main()
