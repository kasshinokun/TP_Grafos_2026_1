# Testa EventBus: filas separadas para tasks, dados e notificações.
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from orchestrator_hibrido_alpha0e import EventBus


class TestEventBus(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()

    def test_task_roundtrip(self):
        self.bus.publish_task({"type": "FETCH", "url": "x"})
        t = self.bus.consume_task(timeout=0.5)
        self.assertEqual(t["type"], "FETCH")

    def test_data_roundtrip(self):
        self.bus.publish_data({"type": "DATA_EXTRACTED", "items": []})
        d = self.bus.consume_data(timeout=0.5)
        self.assertEqual(d["type"], "DATA_EXTRACTED")

    def test_notification_roundtrip(self):
        self.bus.publish_notification({"type": "TOKEN_COOLDOWN"})
        n = self.bus.consume_notification(timeout=0.5)
        self.assertEqual(n["type"], "TOKEN_COOLDOWN")

    def test_isolamento_entre_filas(self):
        self.bus.publish_notification({"type": "X"})
        self.assertIsNone(self.bus.consume_data(timeout=0.1))
        self.assertIsNone(self.bus.consume_task(timeout=0.1))


if __name__ == "__main__":
    unittest.main()
