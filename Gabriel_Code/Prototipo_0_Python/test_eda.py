import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.data_app import DataMicroApp
from apps.graph_app import GraphMicroApp
from core.event_bus import EventBus

def test_flow():
    app = QApplication(sys.argv)
    bus = EventBus.instance()
    
    data_app = DataMicroApp()
    graph_app = GraphMicroApp()
    
    # Manter referências para evitar coleta de lixo
    _apps = [data_app, graph_app]
    
    results = {"students_received": False, "graph_created": False}

    def on_event(event_type, payload):
        print(f"[TEST] Capturado: {event_type}")
        if event_type == "RESPONSE_GET_STUDENTS":
            results["students_received"] = True
            print(f"[TEST] Alunos recebidos: {len(payload['students'])}")
            # Próximo passo: Criar grafo
            bus.publish("API_POST_CREATE_GRAPH", {"num_nodes": len(payload['students'])})
            
        elif event_type == "RESPONSE_POST_CREATE_GRAPH":
            results["graph_created"] = True
            print("[TEST] Grafo criado com sucesso.")
            # Finalizar teste
            if results["students_received"] and results["graph_created"]:
                print("\n--- TODOS OS TESTES PASSARAM ---")
                app.quit()

    bus.subscribe(on_event)
    
    # Inicia o fluxo simulando um request da UI
    print("--- Iniciando Teste de Integração EDA ---")
    QTimer.singleShot(100, lambda: bus.publish("API_GET_STUDENTS"))
    
    # Timeout de segurança
    QTimer.singleShot(2000, lambda: (print("Erro: Timeout no teste"), app.quit()))
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_flow()
