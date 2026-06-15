# Validação por simulação das otimizações do orchestrator_hibrido_alpha0e.
# Não requer rede: usa mocks para EventBus, TokenManager, BufferedStorageWorker.
# Roda: python debug/validacao_simulacao.py
import os, sys, time, threading, queue, logging, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator_hibrido_alpha0e import (
    EventBus, TokenManager, BufferedStorageWorker, ShutdownManager,
)

logging.disable(logging.CRITICAL)


class SimulacaoFilasSeparadas(unittest.TestCase):
    """Garante que cooldown vai para notification_queue e dados vão para data_queue."""

    def test_cooldown_nao_polui_data_queue(self):
        bus = EventBus()
        bus.publish_notification({"type": "TOKEN_COOLDOWN", "token": "abc"})
        bus.publish_data({"type": "DATA_EXTRACTED", "items": [1, 2, 3]})

        note = bus.consume_notification(timeout=0.5)
        data = bus.consume_data(timeout=0.5)

        self.assertEqual(note["type"], "TOKEN_COOLDOWN")
        self.assertEqual(data["type"], "DATA_EXTRACTED")

    def test_storage_worker_consome_apenas_data(self):
        bus = EventBus()
        shutdown = ShutdownManager()
        # injeta apenas notificação; storage worker NÃO deve consumi-la
        bus.publish_notification({"type": "TOKEN_COOLDOWN", "token": "x"})
        worker = BufferedStorageWorker(bus, shutdown)
        worker.start()
        time.sleep(0.4)
        shutdown.request_shutdown()
        worker.join(timeout=3)

        note = bus.consume_notification(timeout=0.2)
        self.assertIsNotNone(note, "Cooldown não pode ser drenado pelo BufferedStorageWorker")
        self.assertEqual(note["type"], "TOKEN_COOLDOWN")


class SimulacaoCooldownGlobal(unittest.TestCase):
    """Quando todos os tokens entram em cooldown, all_in_cooldown() = True."""

    def test_all_in_cooldown(self):
        mgr = TokenManager(["t1", "t2"])
        future = int(time.time()) + 600
        mgr.set_cooldown("t1", future)
        mgr.set_cooldown("t2", future)
        self.assertTrue(mgr.all_in_cooldown())
        self.assertGreater(mgr.get_next_reset_time(), time.time())

    def test_partial_cooldown(self):
        mgr = TokenManager(["t1", "t2"])
        mgr.set_cooldown("t1", int(time.time()) + 600)
        self.assertFalse(mgr.all_in_cooldown())


class SimulacaoMiningComplete(unittest.TestCase):
    def test_evento_mining_complete(self):
        bus = EventBus()
        bus.publish_notification({"type": "MINING_COMPLETE"})
        note = bus.consume_notification(timeout=0.5)
        self.assertEqual(note["type"], "MINING_COMPLETE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
