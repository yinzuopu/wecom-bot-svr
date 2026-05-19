import unittest
import sys
import types


wx_crypt = types.ModuleType("wx_crypt")
wx_crypt.WXBizMsgCrypt = object
wx_crypt.WxChannel_Wecom = object()
sys.modules.setdefault("wx_crypt", wx_crypt)

from wecom_bot_svr import RspTextMsg, WecomBotServer
import wecom_bot_svr.app as app_module


def message_handler(_req_msg):
    return RspTextMsg()


def event_handler(_req_msg):
    return RspTextMsg()


class StatusEndpointTest(unittest.TestCase):
    def test_status_endpoint_returns_runtime_info(self):
        server = WecomBotServer(
            "test-bot",
            "127.0.0.1",
            5001,
            path="/wecom_bot",
            token="token",
            aes_key="a" * 43,
            bot_key="bot-key",
        )
        server.set_message_handler(message_handler)
        server.set_event_handler(event_handler)
        server._register_routes()

        response = server._app.test_client().get("/status")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["name"], "test-bot")
        self.assertEqual(payload["paths"]["callback"], "/wecom_bot")
        self.assertEqual(payload["paths"]["active_send"], "/active_send")
        self.assertEqual(payload["paths"]["status"], "/status")
        self.assertTrue(payload["handlers"]["message"])
        self.assertTrue(payload["handlers"]["event"])
        self.assertFalse(payload["handlers"]["error"])
        self.assertTrue(payload["config"]["token"])
        self.assertTrue(payload["config"]["aes_key"])
        self.assertFalse(payload["config"]["corp_id"])
        self.assertTrue(payload["config"]["bot_key"])
        self.assertEqual(payload["config_errors"], [])
        self.assertTrue(payload["ready"])
        self.assertIsInstance(payload["uptime_seconds"], int)
        self.assertIn("version", payload)

    def test_status_endpoint_reports_missing_required_config(self):
        server = WecomBotServer(
            "test-bot",
            "127.0.0.1",
            5001,
            path="/wecom_bot",
            token=None,
            aes_key=None,
        )
        server._register_routes()

        response = server._app.test_client().get("/status")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertFalse(payload["config"]["token"])
        self.assertFalse(payload["config"]["aes_key"])
        self.assertEqual(payload["config_errors"], ["token", "aes_key"])
        self.assertFalse(payload["ready"])

    def test_status_endpoint_can_be_customized(self):
        server = WecomBotServer("test-bot", "127.0.0.1", 5001, path="/wecom_bot", status_path="/healthz")
        server._register_routes()

        client = server._app.test_client()
        self.assertEqual(client.get("/healthz").status_code, 200)
        self.assertEqual(client.get("/status").status_code, 404)

    def test_post_decrypt_failure_logs_and_returns_empty_response(self):
        class FailingCrypto:
            def __init__(self, *_args, **_kwargs):
                pass

            def DecryptMsg(self, *_args):
                return 40001, None

        original_crypto = app_module.WXBizMsgCrypt
        app_module.WXBizMsgCrypt = FailingCrypto
        error_codes = []
        try:
            server = WecomBotServer("test-bot", "127.0.0.1", 5001, path="/wecom_bot", token="token", aes_key="a" * 43)
            server.set_error_handler(error_codes.append)
            server._register_routes()

            with self.assertLogs(level="WARNING") as logs:
                response = server._app.test_client().post(
                    "/wecom_bot?msg_signature=bad&timestamp=1&nonce=2",
                    data=b"<xml></xml>",
                )
        finally:
            app_module.WXBizMsgCrypt = original_crypto

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"")
        self.assertEqual(error_codes, [40001])
        self.assertIn("decrypt message failed: ret=40001", "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
