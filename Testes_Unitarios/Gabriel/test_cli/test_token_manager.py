# Testa TokenManager: aquisição, liberação, cooldown global.
import os, sys, time, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from orchestrator_hibrido_alpha0e import TokenManager


class TestTokenManager(unittest.TestCase):
    def test_get_release(self):
        mgr = TokenManager(["a", "b"])
        t = mgr.get_available_token()
        self.assertIn(t, ["a", "b"])
        mgr.release_token(t)

    def test_cooldown_block(self):
        mgr = TokenManager(["a"])
        mgr.set_cooldown("a", int(time.time()) + 300)
        self.assertTrue(mgr.all_in_cooldown())
        # após simulação de expiração
        mgr.set_cooldown("a", int(time.time()) - 10)
        self.assertFalse(mgr.all_in_cooldown())

    def test_next_reset_time(self):
        mgr = TokenManager(["a", "b"])
        now = int(time.time())
        mgr.set_cooldown("a", now + 100)
        mgr.set_cooldown("b", now + 50)
        nxt = mgr.get_next_reset_time()
        self.assertAlmostEqual(nxt, now + 50, delta=2)


if __name__ == "__main__":
    unittest.main()
