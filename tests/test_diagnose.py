import unittest
from diagnose_inberlinwohnen import Links

class DiagnosticTests(unittest.TestCase):
    def test_extract_anchor(self):
        parser = Links()
        parser.feed('<a href="/wohnungsfinder">Wohnungen</a>')
        self.assertEqual(parser.links, ["/wohnungsfinder"])

if __name__ == "__main__":
    unittest.main()
