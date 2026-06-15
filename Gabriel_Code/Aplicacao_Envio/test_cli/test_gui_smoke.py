# Testa GUI: carrega módulo sem mainloop (smoke test).
import os, sys, unittest, importlib.util


class TestGUIImport(unittest.TestCase):
    def test_modulo_gui_importavel(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, root)
        spec = importlib.util.find_spec("gui_ctk")
        self.assertIsNotNone(spec, "gui_ctk.py deve existir na raiz")


if __name__ == "__main__":
    unittest.main()
