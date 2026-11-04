import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from application_ledger import Ledger
from eligibility import screen
from standard_form_adapters import (SENDER_VERSIONS, attempt_blocker, provider_statuses,
                                    prepare_native, open_howoge_form, HOWOGE_NOTICES)

class DispatchPolicyTests(unittest.TestCase):
    def test_unknown_old_apartment_does_not_block_other_apartment_after_restart(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"ledger.json"
            old="https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/old"
            new="https://www.gewobag.de/fuer-mietinteressentinnen/mietangebote/other"
            ledger=Ledger(remote=False,path=path)
            ledger.reserve(old,adapter_version=SENDER_VERSIONS["gewobag"])
            ledger.finish(old,"submission_unverified")
            restarted=Ledger(remote=False,path=path)
            self.assertEqual(attempt_blocker("gewobag",old,restarted,set()),"already_reserved_or_submitted")
            self.assertIsNone(attempt_blocker("gewobag",new,restarted,set()))
            self.assertEqual(attempt_blocker("gewobag",new,restarted,{"gewobag"}),"provider_uncertain_submission_this_run")
            self.assertIsNone(attempt_blocker("howoge","https://howoge.de/other",restarted,{"gewobag"}))
    def test_four_reported_providers_do_not_mean_four_validated_senders(self):
        ledger=Mock()
        ledger.validated.return_value=False
        with patch.dict(os.environ,{"APPLICANT_WBM_DATA_CONSENT":""}):
            states=provider_statuses(ledger,True)
        self.assertEqual(set(states),{"gewobag","howoge","gesobau","wbm"})
        self.assertFalse(states["gesobau"]["sender_implemented"])
        self.assertFalse(states["wbm"]["automatic_attempts_enabled"])
        self.assertTrue(states["howoge"]["automatic_attempts_enabled"])
        self.assertFalse(any(s["submission_confirmed"] for s in states.values()))

class NativeFormGuards(unittest.IsolatedAsyncioTestCase):
    async def test_wbm_additional_consent_is_required_before_any_personal_data(self):
        page=Mock()
        with patch.dict(os.environ,{"APPLICANT_WBM_DATA_CONSENT":""}),patch("standard_form_adapters.visible_challenge",new=AsyncMock(return_value=False)):
            ready,reason=await prepare_native("wbm",page,{}, {})
        self.assertFalse(ready)
        self.assertEqual(reason,"wbm_additional_data_processing_consent_required")
        page.locator.assert_not_called()
    async def test_changed_howoge_attestation_cannot_be_acknowledged(self):
        page=Mock()
        page.locator.return_value.inner_text=AsyncMock(return_value="Bestätigen Sie, dass Ihr Einkommen ausreicht.")
        ready,reason=await open_howoge_form(page)
        self.assertFalse(ready)
        self.assertEqual(reason,"howoge_notice_changed_requires_review")
        page.get_by_role.assert_not_called()
    async def test_howoge_notices_do_not_fill_contact_data(self):
        page=Mock()
        page.locator.return_value.inner_text=AsyncMock(return_value=" ".join(n[2] for n in HOWOGE_NOTICES))
        page.locator.return_value.wait_for=AsyncMock()
        page.get_by_role.return_value.click=AsyncMock()
        controls=[]
        for _,label,_ in HOWOGE_NOTICES:
            c=Mock(evaluate=AsyncMock(return_value=label),check=AsyncMock())
            controls.append(c)
        with patch("standard_form_adapters.one",new=AsyncMock(side_effect=controls)):
            self.assertEqual(await open_howoge_form(page),(True,"form_profile_mapping_required"))
        for c in controls:
            c.check.assert_awaited_once()
            c.fill.assert_not_called()

class ProviderDetailFormats(unittest.TestCase):
    def test_wbm_eur_rooms_area_and_negative_wbs(self):
        value=screen("Warmmiete 499,00 EUR Anzahl der Zimmer: 1 Größe: ca. 35.77 m² WBS erforderlich: Nein Bezugsfertig ab: 16.11.2026 Bezirk/Ortsteil: Mitte / Anbieter-Angebotskarte",provider_verified=True)
        self.assertTrue(value["eligible"])
        self.assertEqual(value["area_sqm"],"35.77")
        self.assertEqual(value["wbs"],"not_required")
    def test_howoge_explicit_berlin_buch_address_maps_to_pankow(self):
        value=screen("Adresse: Beispiel 1, 13125 Berlin, Buch Warmmiete: 499,00 € Zimmer: 1 Wohnfläche 32,5 Quadratmeter Bezugsfrei ab: ab sofort kein WBS erforderlich",provider_verified=True)
        self.assertTrue(value["eligible"])
        self.assertEqual(value["district"],"pankow")
        self.assertIsNone(screen("Warmmiete 499,00 € Lage: Ausflug nach Buch möglich")["district"])

if __name__=="__main__": unittest.main()
