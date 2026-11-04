import os
import unittest
from datetime import date
from unittest.mock import Mock, AsyncMock, patch
from stadtundland_adapter import (requested_date,income_answer,readiness_blocker,
    prepare_stadtundland,known_control,INCOME_LABEL,PRIVACY)
from eligibility import screen

class ProtectedInputs(unittest.TestCase):
    def test_missing_date_is_not_invented(self):
        for value in ("","sofort vielleicht","2027-02-30"):
            with patch.dict(os.environ,{"APPLICANT_EARLIEST_MOVE_IN":value}):
                self.assertIsNone(requested_date())
                self.assertEqual(readiness_blocker(),"stadtundland_user_move_in_date_required")

    def test_explicit_asap_and_future_date(self):
        with patch("stadtundland_adapter.today",return_value=date(2030,1,10)):
            with patch.dict(os.environ,{"APPLICANT_EARLIEST_MOVE_IN":"ASAP"}):
                self.assertEqual(requested_date(),date(2030,1,10))
            with patch.dict(os.environ,{"APPLICANT_EARLIEST_MOVE_IN":"2030-02-01"}):
                self.assertEqual(requested_date(),date(2030,2,1))

    def test_income_question_is_answered_truthfully_at_exact_boundary(self):
        with patch.dict(os.environ,{"APPLICANT_MONTHLY_NET_INCOME":"1000"}):
            self.assertEqual(income_answer("350.00"),"Ja")
            self.assertEqual(income_answer("350.01"),"Nein")
        for value in ("","NaN","Infinity","-1"):
            with patch.dict(os.environ,{"APPLICANT_MONTHLY_NET_INCOME":value}):
                self.assertIsNone(income_answer("350"))

    def test_unknown_or_changed_attestation_is_rejected(self):
        field={"id":"formly_radio_stadt_und_land_monatliche_warmmiete_hoechstens_35%_monatliches_netto_haushaltseinkommen_0-input",
               "type":"radio","tag":"input","label":"Nein","group":INCOME_LABEL}
        self.assertTrue(known_control(field))
        self.assertFalse(known_control({**field,"group":"Ich bestätige eine Jobcenter-Kostenübernahme"}))
        self.assertFalse(known_control({"id":"mat-input-77","type":"text","tag":"input","label":"Ausweisnummer"}))
        self.assertFalse(known_control({"id":"stadt_und_land_bestaetigung_datenschutzhinweis","type":"checkbox","tag":"input","label":PRIVACY+" Ich akzeptiere kostenpflichtige Leistungen."}))

    def test_combined_area_label_does_not_use_utility_area(self):
        decision=screen("Wohnfläche / Nutzfläche 40,00 m² / 80 m²")
        self.assertEqual(decision["area_sqm"],"40.00")

class BeforeTransmission(unittest.IsolatedAsyncioTestCase):
    async def test_missing_date_stops_before_any_form_access(self):
        page,frame=Mock(),Mock()
        with patch.dict(os.environ,{"APPLICANT_EARLIEST_MOVE_IN":""}):
            ready,reason=await prepare_stadtundland(page,frame,{}, {}, {})
        self.assertFalse(ready)
        self.assertEqual(reason,"stadtundland_user_move_in_date_required")
        frame.locator.assert_not_called()

    async def test_new_question_after_income_answer_stops_before_contact_data(self):
        page,frame=Mock(),Mock()
        radio=frame.get_by_role.return_value
        radio.count=AsyncMock(return_value=1)
        radio.get_by_role.return_value.check=AsyncMock()
        known={"id":"mat-input-1","type":"text","tag":"input","label":"Vorname"}
        unknown={"id":"new_cost_approval","type":"checkbox","tag":"input","label":"Kostenübernahme vorhanden"}
        with patch.dict(os.environ,{"APPLICANT_EARLIEST_MOVE_IN":"ASAP","APPLICANT_MONTHLY_NET_INCOME":"1000"}),\
             patch("stadtundland_adapter.visible_challenge",new=AsyncMock(return_value=False)),\
             patch("stadtundland_adapter.inspect_controls",new=AsyncMock(side_effect=[[known],[known,unknown]])):
            ready,reason=await prepare_stadtundland(page,frame,{}, {"household_size":1,"apply_for_self":True},{"total_rent_eur":"500"})
        self.assertFalse(ready)
        self.assertEqual(reason,"stadtundland_new_conditional_question_requires_review")
        frame.get_by_label.assert_not_called()
        radio.get_by_role.return_value.check.assert_awaited_once()
