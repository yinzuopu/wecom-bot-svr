import sys
import types
import unittest
from pathlib import Path

wx_crypt_stub = types.ModuleType("wx_crypt")
wx_crypt_stub.WXBizMsgCrypt = object
wx_crypt_stub.WxChannel_Wecom = object()
sys.modules.setdefault("wx_crypt", wx_crypt_stub)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wecom_bot_svr import WecomBotServer


class HealthCheckTest(unittest.TestCase):
    def test_get_runtime_status(self):
        server = WecomBotServer("test_bot", "127.0.0.1", 5001, path="/wecom_bot")

        status = server.get_runtime_status()

        self.assertEqual(status["status"], "ok")
        self.assertEqual(status["name"], "test_bot")
        self.assertEqual(status["host"], "127.0.0.1")
        self.assertEqual(status["port"], 5001)
        self.assertEqual(status["callback_path"], "/wecom_bot")
        self.assertEqual(status["active_msg_path"], "/active_send")
        self.assertEqual(status["health_check_path"], "/health")
        self.assertIn("log_level", status)
        self.assertIn("version", status)
        self.assertIn("started_at", status)
        self.assertGreaterEqual(status["uptime_seconds"], 0)

    def test_configurable_log_level(self):
        server = WecomBotServer("test_bot", "127.0.0.1", 5001, path="/wecom_bot", log_level="debug")

        status = server.get_runtime_status()

        self.assertEqual(status["log_level"], "DEBUG")

    def test_invalid_log_level(self):
        with self.assertRaises(ValueError):
            WecomBotServer("test_bot", "127.0.0.1", 5001, path="/wecom_bot", log_level="verbose")

    def test_health_check_route(self):
        server = WecomBotServer(
            "test_bot",
            "127.0.0.1",
            5001,
            path="/wecom_bot",
            health_check_path="/status",
        )
        server.set_message_handler(lambda msg: None)
        server.set_event_handler(lambda msg: None)
        server._app.run = lambda *args, **kwargs: None

        server.run()
        response = server._app.test_client().get("/status")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["health_check_path"], "/status")
        self.assertEqual(data["callback_path"], "/wecom_bot")


if __name__ == "__main__":
    unittest.main()
