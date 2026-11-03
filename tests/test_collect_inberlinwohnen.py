import unittest
from unittest.mock import patch
from collect_inberlinwohnen import AnchorParser

class CollectorTests(unittest.TestCase):
    def test_anchor_extraction(self):
        p = AnchorParser()
        p.feed('<a href="https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/abc">x</a>')
        self.assertEqual(len(p.links), 1)

if __name__ == "__main__":
    unittest.main()
