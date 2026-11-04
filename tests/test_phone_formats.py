import unittest
from gewobag_adapter import phone_formats

class PhoneFormattingTests(unittest.TestCase):
    def test_separators(self):
        self.assertEqual(phone_formats("+1 (202) 555-0100"),["+12025550100"])
    def test_german_equivalent_representations(self):
        self.assertEqual(phone_formats("+49 (0) 170 00000000"),["+4917000000000","017000000000"])
    def test_no_number_is_invented_from_words(self):
        self.assertEqual(phone_formats("APPLICANT_PHONE"),[])
    def test_international_access_prefix(self):
        self.assertEqual(phone_formats("0012025550100"),["+12025550100"])
