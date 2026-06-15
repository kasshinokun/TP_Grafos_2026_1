from grafo.core.application import Application
from grafo.cli.cli import CLI

def main():
    app = Application()
    cli = CLI(app)
    cli.run()

if __name__ == "__main__":
    main()
