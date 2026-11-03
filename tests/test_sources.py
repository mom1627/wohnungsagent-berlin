import os
import unittest
from unittest.mock import patch
from sources import load_feed

class SourceTests(unittest.TestCase):
    def test_http_rejected(self):
        with self.assertRaises(ValueError):
            load_feed("http://example.org/feed.json")
    def test_unapproved_host_rejected(self):
        with patch.dict(os.environ, {"FEED_ALLOWED_HOSTS": "approved.example"}):
            with self.assertRaises(ValueError):
                load_feed("https://other.example/feed.json")

if __name__ == "__main__":
    unittest.main()
