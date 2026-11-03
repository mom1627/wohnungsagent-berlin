import unittest
from public_pages import extract_jsonld

class PublicPagesTests(unittest.TestCase):
    def test_extract_jsonld(self):
        html = '<script type="application/ld+json">{"@type":"Apartment","name":"Demo"}</script>'
        self.assertEqual(extract_jsonld(html)[0]["@type"], "Apartment")
    def test_ignore_invalid(self):
        self.assertEqual(extract_jsonld('<script type="application/ld+json">{bad}</script>'), [])

if __name__ == "__main__":
    unittest.main()
