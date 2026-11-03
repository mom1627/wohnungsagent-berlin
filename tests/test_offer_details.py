import unittest
from inspect_offer_details import DetailParser, inspect_url

class OfferDetailsTests(unittest.TestCase):
    def test_parser(self):
        p = DetailParser()
        p.feed('<div>Warmmiete 490 Euro</div><script type="application/ld+json">{"name":"Test"}</script>')
        self.assertIn("Warmmiete", " ".join(p.text))
        self.assertEqual(p.jsonld[0]["name"], "Test")
    def test_unapproved_domain(self):
        r = inspect_url("https://example.org/listing", {})
        self.assertEqual(r["status"], "unverified")
        self.assertIn("error", r)

if __name__ == "__main__":
    unittest.main()
