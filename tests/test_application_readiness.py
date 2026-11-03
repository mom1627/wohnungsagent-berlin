import unittest
from application_readiness import evaluate

class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.match={"url":"https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/example","basic_criteria_match":True,"special_wbs_condition_detected":False,"wbs_mentioned_in_offer":False}
        self.evidence={"status":"readable_unverified","http_status":200,"evidence":{"wbs_mentions":[]}}
    def test_no_form_blocks(self):
        self.assertEqual(evaluate(self.match,self.evidence)[1],"application_form_not_verified")
    def test_wbs_category_unknown_blocks(self):
        self.match["wbs_mentioned_in_offer"]=True
        self.assertEqual(evaluate(self.match,self.evidence,True)[1],"wbs_category_not_verified")
    def test_special_wbs_blocks(self):
        self.evidence["evidence"]["wbs_mentions"]=["WBS 160"]
        self.assertEqual(evaluate(self.match,self.evidence,True)[1],"potentially_incompatible_eligibility")
    def test_unknown_provider_blocks(self):
        self.match["url"]="https://example.org/offer"
        self.assertEqual(evaluate(self.match,self.evidence,True)[1],"provider_not_supported")
    def test_verified_non_wbs_candidate(self):
        self.assertEqual(evaluate(self.match,self.evidence,True),(True,"ready"))

if __name__=="__main__":
    unittest.main()
