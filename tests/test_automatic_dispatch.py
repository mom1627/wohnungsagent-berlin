import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from application_ledger import Ledger
from eligibility import screen
from housing_profile import load_housing_profile
from gewobag_adapter import VERSION, offer_blockers, prepare, submit_prepared, visible_challenge

FIXTURE = {"salutation":"Herr","household_size":1,"apply_for_self":True,"wbs_type":"100",
           "wbs_valid_until":"2099-12-31","wbs_max_area_sqm":50,"wbs_special_need":False,
           "wofg9_certificate":False,"enrolled":False,"immomio_account":True}
TEXT = "Gesamtmiete 500,00 Euro Anzahl Zimmer 1 Fläche in m² 36,50 m² Bezirk/Ortsteil Pankow / Test Frei ab 01.12.2030 Für die Anmietung ist ein bereits vorhandener WBS Voraussetzung"

class HousingProfileTests(unittest.TestCase):
    def test_protected_profile_required(self):
        with patch.dict(os.environ,{},clear=True): self.assertFalse(load_housing_profile()["ready"])
    def test_valid_profile(self):
        with patch.dict(os.environ,{"APPLICANT_HOUSING_PROFILE":json.dumps(FIXTURE)},clear=True):
            self.assertTrue(load_housing_profile()["ready"])
    def test_strings_do_not_become_truthy_booleans(self):
        value = {**FIXTURE,"enrolled":"false"}
        with patch.dict(os.environ,{"APPLICANT_HOUSING_PROFILE":json.dumps(value)},clear=True):
            self.assertFalse(load_housing_profile()["ready"])
    def test_expired_certificate(self):
        value = {**FIXTURE,"wbs_valid_until":"2000-01-01"}
        with patch.dict(os.environ,{"APPLICANT_HOUSING_PROFILE":json.dumps(value)},clear=True):
            self.assertEqual(load_housing_profile()["reason"],"housing_profile_wbs_expired")
    def test_corrupt_profile_does_not_echo_secret(self):
        with patch.dict(os.environ,{"APPLICANT_HOUSING_PROFILE":"not-json-private-value"},clear=True):
            self.assertEqual(load_housing_profile(),{"ready":False,"reason":"invalid_protected_housing_profile"})
    def test_area_and_generic_wbs_eligibility(self):
        decision = screen(TEXT,provider_verified=True)
        self.assertEqual(decision["area_sqm"],"36.50")
        self.assertEqual(offer_blockers(decision,{"ready":True,**FIXTURE}),[])
        decision = screen(TEXT.replace("36,50","50,01"),provider_verified=True)
        self.assertIn("offer_exceeds_wbs_area",offer_blockers(decision,{"ready":True,**FIXTURE}))
    def test_special_need_not_inferred_from_wbs(self):
        decision = screen(TEXT+" nur mit besonderem Wohnbedarf",provider_verified=True)
        self.assertIn("special_eligibility_requires_review",offer_blockers(decision,{"ready":True,**FIXTURE}))
    def test_availability_after_wbs_expiry(self):
        decision = screen(TEXT,provider_verified=True)
        with patch("gewobag_adapter.today",return_value=date(2029,1,1)):
            result = offer_blockers(decision,{"ready":True,**FIXTURE,"wbs_valid_until":"2030-06-01"})
        self.assertIn("wbs_expires_before_availability",result)

class FormGuardTests(unittest.IsolatedAsyncioTestCase):
    async def test_unknown_dynamic_required_field_is_blocked(self):
        frame = Mock()
        with patch("gewobag_adapter.fields",new=AsyncMock(return_value=[{"id":"new_income_attestation","required":True,"type":"text"}])),patch("gewobag_adapter.visible_challenge",new=AsyncMock(return_value=False)):
            self.assertEqual(await prepare(Mock(),frame,{},FIXTURE),(False,"unknown_required_field"))
        frame.locator.assert_not_called()
    async def test_no_certificate_answer_is_not_false_attestation(self):
        field = {"id":"formly_14_radio_gewobag_paragraph_9_bescheinigung_vorhanden_0-Ja","required":True,"type":"radio"}
        with patch("gewobag_adapter.fields",new=AsyncMock(return_value=[field])),patch("gewobag_adapter.visible_challenge",new=AsyncMock(return_value=False)):
            result = await prepare(Mock(),Mock(),{},FIXTURE)
        self.assertEqual(result,(False,"required_wofg9_certificate_not_available"))
    async def test_no_enrollment_answer_is_not_false_attestation(self):
        field = {"id":"gewobag_immatrikulationsbescheinigung_vorhanden-Ja","required":True,"type":"radio"}
        with patch("gewobag_adapter.fields",new=AsyncMock(return_value=[field])),patch("gewobag_adapter.visible_challenge",new=AsyncMock(return_value=False)):
            result = await prepare(Mock(),Mock(),{},FIXTURE)
        self.assertEqual(result,(False,"required_enrollment_certificate_not_available"))
    async def test_invisible_badge_is_not_a_challenge(self):
        frame = Mock(url="https://www.google.com/recaptcha/api2/anchor?size=invisible")
        owner = Mock()
        owner.is_visible = AsyncMock(return_value=True)
        frame.frame_element = AsyncMock(return_value=owner)
        self.assertFalse(await visible_challenge(Mock(frames=[frame])))
    async def test_visible_challenge_frame_is_blocked(self):
        frame = Mock(url="https://www.google.com/recaptcha/api2/bframe?k=public-key")
        owner = Mock()
        owner.is_visible = AsyncMock(return_value=True)
        owner.bounding_box = AsyncMock(return_value={"height":400,"width":400})
        frame.frame_element = AsyncMock(return_value=owner)
        self.assertTrue(await visible_challenge(Mock(frames=[frame])))

class SubmissionTests(unittest.IsolatedAsyncioTestCase):
    def setup_request(self,texts):
        frame,button,body,page = Mock(),Mock(),Mock(),Mock()
        button.count = AsyncMock(return_value=1)
        button.is_enabled = AsyncMock(return_value=True)
        button.press = AsyncMock()
        body.inner_text = AsyncMock(side_effect=texts)
        frame.get_by_role.return_value = button
        frame.locator.return_value = body
        page.wait_for_timeout = AsyncMock()
        return page,frame,button
    async def test_remote_reservation_precedes_click_and_success_is_persisted(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=Ledger(remote=False,path=Path(d)/"ledger.json")
            ledger.remote=True
            ledger.read=Mock()
            ledger.save=Mock()
            page,frame,button=self.setup_request(["Anfrageformular","Ihre Anfrage wurde erfolgreich versendet."])
            async def click(*args,**kwargs):
                self.assertTrue(ledger.contains("https://gewobag.de/test"))
                self.assertFalse(ledger.validated(VERSION))
            button.press.side_effect=click
            with patch("gewobag_adapter.visible_challenge",new=AsyncMock(return_value=False)):
                result=await submit_prepared(page,frame,"https://gewobag.de/test",ledger,enabled=True)
            self.assertTrue(result["confirmed"])
            self.assertTrue(ledger.validated(VERSION))
            self.assertFalse(ledger.adapter_uncertain(VERSION))
    async def test_reservation_failure_never_clicks(self):
        page,frame,button=self.setup_request(["Anfrageformular"])
        ledger=Mock(remote=True)
        ledger.reserve.side_effect=RuntimeError("storage failure")
        with patch("gewobag_adapter.visible_challenge",new=AsyncMock(return_value=False)):
            with self.assertRaises(RuntimeError): await submit_prepared(page,frame,"https://gewobag.de/test",ledger,enabled=True)
        button.press.assert_not_called()
    async def test_click_timeout_is_an_uncertain_submission(self):
        page,frame,button=self.setup_request(["Anfrageformular"])
        button.press.side_effect=TimeoutError()
        ledger=Mock(remote=True)
        ledger.reserve.return_value=True
        with patch("gewobag_adapter.visible_challenge",new=AsyncMock(return_value=False)):
            result=await submit_prepared(page,frame,"https://gewobag.de/test",ledger,enabled=True)
        self.assertEqual(result["status"],"submission_unverified")
        ledger.finish.assert_called_once_with("https://gewobag.de/test","submission_unverified",confirmation=False)
    async def test_preexisting_confirmation_is_not_a_new_success(self):
        page,frame,button=self.setup_request(["Ihre Anfrage wurde erfolgreich versendet."])
        ledger=Mock(remote=True)
        with patch("gewobag_adapter.visible_challenge",new=AsyncMock(return_value=False)):
            result=await submit_prepared(page,frame,"https://gewobag.de/test",ledger,enabled=True)
        self.assertFalse(result["confirmed"])
        ledger.reserve.assert_not_called()
    async def test_challenge_after_click_does_not_get_solved_or_retried(self):
        page,frame,button=self.setup_request(["Anfrageformular"])
        ledger=Mock(remote=True)
        ledger.reserve.return_value=True
        with patch("gewobag_adapter.visible_challenge",new=AsyncMock(side_effect=[False,True])):
            result=await submit_prepared(page,frame,"https://gewobag.de/test",ledger,enabled=True)
        self.assertEqual(result["reason"],"visible_captcha_after_submit_requires_manual_action")
        self.assertFalse(result["confirmed"])
        button.press.assert_awaited_once()
    async def test_failed_finish_does_not_create_a_false_validation(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=Ledger(remote=False,path=Path(d)/"ledger.json")
            ledger.reserve("https://gewobag.de/test",adapter_version=VERSION)
            with patch.object(ledger,"save",side_effect=RuntimeError("storage failure")):
                with self.assertRaises(RuntimeError): ledger.finish("https://gewobag.de/test","submitted_confirmed",True)
            self.assertFalse(ledger.validated(VERSION))
            self.assertTrue(ledger.adapter_uncertain(VERSION))
