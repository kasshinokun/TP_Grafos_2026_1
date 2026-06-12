import sys
import os

# Adiciona o diretório atual ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from apps.ui_app import UIMicroApp
from apps.data_app import DataMicroApp
from apps.graph_app import GraphMicroApp

def main():
    app = QApplication(sys.argv)
    
    # Inicializa as micro-aplicações (Backend e Lógica)
    # Elas rodam no mesmo loop de eventos do Qt, mas são logicamente separadas
    data_backend = DataMicroApp()
    graph_logic = GraphMicroApp()
    
    # Inicializa a Interface (Frontend)
    ui_frontend = UIMicroApp()
    ui_frontend.show()
    
    print("--- Aplicação GraphAnalyzer Iniciada (EDA Architecture) ---")
    print("Micro-apps ativas: DataApp, GraphApp, UIApp")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
