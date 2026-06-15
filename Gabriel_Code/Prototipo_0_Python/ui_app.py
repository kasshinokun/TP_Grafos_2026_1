import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt
from core.base_app import MicroApp

class UIMicroApp(QMainWindow, MicroApp):
    def __init__(self):
        # Inicialização múltipla (PyQt e MicroApp)
        QMainWindow.__init__(self)
        MicroApp.__init__(self, "UIApp")
        
        self.setWindowTitle("GraphAnalyzer - Engenharia de Software")
        self.resize(800, 600)
        
        # Layout Principal
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Cabeçalho
        self.header = QLabel("Painel de Controle de Grafos (EDA Architecture)")
        self.header.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        self.layout.addWidget(self.header)
        
        # Tabela de Alunos
        self.student_table = QTableWidget(0, 2)
        self.student_table.setHorizontalHeaderLabels(["Nome do Aluno", "Papel"])
        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.student_table)
        
        # Botões de Ação
        self.btn_layout = QHBoxLayout()
        self.btn_fetch = QPushButton("GET /students (Carregar Alunos)")
        self.btn_fetch.clicked.connect(lambda: self.send_request("GET", "STUDENTS"))
        
        self.btn_create_graph = QPushButton("POST /create_graph (Inicializar Grafo)")
        self.btn_create_graph.clicked.connect(self.request_graph_creation)
        
        self.btn_stats = QPushButton("GET /graph_stats (Ver Estatísticas)")
        self.btn_stats.clicked.connect(lambda: self.send_request("GET", "GRAPH_STATS"))
        
        self.btn_layout.addWidget(self.btn_fetch)
        self.btn_layout.addWidget(self.btn_create_graph)
        self.btn_layout.addWidget(self.btn_stats)
        self.layout.addLayout(self.btn_layout)
        
        # Status Bar
        self.status_label = QLabel("Pronto")
        self.layout.addWidget(self.status_label)

    def request_graph_creation(self):
        count = self.student_table.rowCount()
        if count == 0:
            QMessageBox.warning(self, "Aviso", "Carregue os alunos primeiro!")
            return
        self.send_request("POST", "CREATE_GRAPH", {"num_nodes": count})

    def _handle_event(self, event_type: str, payload: dict):
        """
        Processa as respostas das outras micro-aplicações.
        """
        if event_type == "RESPONSE_GET_STUDENTS":
            students = payload.get("students", [])
            self.student_table.setRowCount(0)
            for s in students:
                row = self.student_table.rowCount()
                self.student_table.insertRow(row)
                self.student_table.setItem(row, 0, QTableWidgetItem(s["name"]))
                self.student_table.setItem(row, 1, QTableWidgetItem(s["role"]))
            self.status_label.setText(f"Carregados {len(students)} alunos.")

        elif event_type == "RESPONSE_POST_CREATE_GRAPH":
            status = payload.get("status")
            self.status_label.setText(f"Grafo criado com sucesso: {status}")
            QMessageBox.information(self, "Sucesso", "Grafo inicializado para os alunos.")

        elif event_type == "RESPONSE_GET_GRAPH_STATS":
            if "error" in payload:
                QMessageBox.critical(self, "Erro", payload["error"])
            else:
                vertices = payload.get("vertices")
                edges = payload.get("edges")
                self.status_label.setText(f"Grafo: {vertices} vértices, {edges} arestas.")
                QMessageBox.information(self, "Estatísticas", f"Vértices: {vertices}\nArestas: {edges}")
