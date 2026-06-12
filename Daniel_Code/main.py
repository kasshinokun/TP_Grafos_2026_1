# main.py
import sys
import os

# Adiciona o diretório atual ao path para garantir que as importações funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.event_bus import EventBus
from apps.miner_app import MinerApp
from apps.graph_app import GraphApp

def main():
    print("===================================================")
    print("Iniciando GraphAnalyzer - Etapa 1 (Minerador)")
    print("===================================================\n")

    # Inicializa o EventBus (Singleton)
    bus = EventBus()

    # Instancia as micro-aplicações. Elas se inscrevem sozinhas no EventBus
    miner = MinerApp()
    graph_logic = GraphApp()

    # Dispara o evento inicial para começar o processo
    # O repositório já está configurado para TheAlgorithms/Java
    bus.publish("START_MINING", {"repo": "TheAlgorithms/Java"})

if __name__ == "__main__":
    main()