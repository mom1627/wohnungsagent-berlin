import unittest
from unittest.mock import Mock, AsyncMock, patch
from gewobag_adapter import SubmissionTransport, submit_prepared

class TransportTests(unittest.TestCase):
    def request(self,url="https://app.wohnungshelden.de/submit?private-token",origin="https://app.wohnungshelden.de/public/listings/example/application",method="POST"):
        return Mock(url=url,frame=Mock(url=origin),method=method,resource_type="xhr")

    def test_only_trusted_provider_posts_are_observed_and_no_values_are_saved(self):
        transport = SubmissionTransport(Mock())
        accepted = self.request()
        transport.request(accepted)
        transport.response(Mock(request=accepted,status=422))
        for request in (self.request(url="https://example.org/steal"),
                        self.request(origin="https://example.org/iframe"),
                        self.request(method="GET"),self.request(url="http://app.wohnungshelden.de/plain")):
            transport.request(request)
        self.assertEqual(transport.report(),{"provider_post_observed":True,"provider_post_count":1,
            "provider_http_statuses":[422],"provider_request_failed":False})
        self.assertNotIn("private-token",str(transport.report()))

    def test_failure_status_and_vendor_host_are_diagnostics_only(self):
        transport = SubmissionTransport(Mock())
        request = self.request(url="https://api.wohnungshelden.de/request")
        transport.request(request)
        transport.requestfailed(request)
        transport.response(Mock(request=request,status=200))
        self.assertTrue(transport.report()["provider_request_failed"])
        self.assertNotIn("confirmed",transport.report())

class NoFalseSuccess(unittest.IsolatedAsyncioTestCase):
    async def test_http_200_without_visible_receipt_is_not_confirmed_or_retried(self):
        frame = Mock(url="https://app.wohnungshelden.de/public/listings/test/application")
        frame.is_detached.return_value=False
        frame.locator.return_value.inner_text=AsyncMock(return_value="Anfrageformular Vorname")
        button = Mock(count=AsyncMock(return_value=1),is_enabled=AsyncMock(return_value=True))
        frame.get_by_role.return_value=button
        page = Mock(main_frame=frame,frames=[frame],wait_for_timeout=AsyncMock())
        page.context.pages=[page]
        handlers={}
        page.on.side_effect=lambda event,handler:handlers.update({event:handler})
        async def native_submit(*args,**kwargs):
            request=Mock(method="POST",resource_type="xhr",frame=frame,url="https://app.wohnungshelden.de/application?secret")
            handlers["request"](request)
            handlers["response"](Mock(request=request,status=200))
        button.press=AsyncMock(side_effect=native_submit)
        ledger=Mock(remote=True)
        with patch("gewobag_adapter.visible_challenge",new=AsyncMock(return_value=False)):
            result=await submit_prepared(page,frame,"https://www.gewobag.de/example",ledger,enabled=True)
        self.assertFalse(result["confirmed"])
        self.assertEqual(result["transport_diagnostics"]["provider_http_statuses"],[200])
        button.press.assert_awaited_once()
        self.assertEqual(page.remove_listener.call_count,3)
        ledger.finish.assert_called_once_with("https://www.gewobag.de/example","submission_unverified",confirmation=False)
