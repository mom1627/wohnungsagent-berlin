import os
import unittest
from unittest.mock import patch
from application_profile import load_profile

class ProfileTests(unittest.TestCase):
    def test_missing_secrets(self):
        with patch.dict(os.environ, {}, clear=True):
            result = load_profile()
        self.assertFalse(result["ready"])
        self.assertEqual(len(result["missing_secrets"]), 3)
    def test_complete_profile(self):
        with patch.dict(os.environ, {"APPLICANT_NAME":"Test Person",
                                     "APPLICANT_EMAIL":"test@example.com",
                                     "APPLICANT_PHONE":"012345"}, clear=True):
            result = load_profile()
        self.assertTrue(result["ready"])
        self.assertIn("Studium", result["note"])

if __name__ == "__main__":
    unittest.main()
