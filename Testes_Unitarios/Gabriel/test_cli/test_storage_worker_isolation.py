# Testa que BufferedStorageWorker não consome a notification_queue.
import os, sys, time, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from orchestrator_hibrido_alpha0e import EventBus, BufferedStorageWorker, ShutdownManager


class TestStorageWorkerIsolation(unittest.TestCase):
    def test_worker_nao_drena_notificacoes(self):
        bus = EventBus()
        shutdown = ShutdownManager()
        bus.publish_notification({"type": "TOKEN_COOLDOWN", "token": "x"})
        worker = BufferedStorageWorker(bus, shutdown)
        worker.start()
        time.sleep(0.5)
        shutdown.request_shutdown()
        worker.join(timeout=3)

        note = bus.consume_notification(timeout=0.3)
        self.assertIsNotNone(note)
        self.assertEqual(note["type"], "TOKEN_COOLDOWN")


if __name__ == "__main__":
    unittest.main()
