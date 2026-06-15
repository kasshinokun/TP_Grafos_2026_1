"""Runner agregado da suíte unitária do Projeto Delta v4c.
Descobre e executa todos os test_*.py do diretório atual usando unittest.
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
APP  = os.path.normpath(os.path.join(HERE, "..", "app"))
sys.path.insert(0, APP)
sys.path.insert(0, HERE)

def main() -> int:
    loader = unittest.TestLoader()
    suite  = loader.discover(start_dir=HERE, pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    raise SystemExit(main())
