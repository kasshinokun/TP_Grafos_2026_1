# Interface Gráfica PyQt6 para o Projeto Delta v4c — REV E (QR via buffer de bytes)
# Release: 2026-06-15

import os
import sys
import json
import queue
import logging
import threading
import subprocess
import io
from typing import List, Optional, Dict, Any

# PyQt6
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QListWidget, QListWidgetItem,
    QComboBox, QTabWidget, QStackedWidget, QToolBar, QFileDialog,
    QMessageBox, QSpinBox, QCheckBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPalette, QColor, QPixmap

# Bibliotecas para QR Code em memória
import qrcode
from PIL import Image

# Importações do projeto original
from orchestrator_hibrido_alpha0e import (
    QRCodeJSONHandler,
    JsonWorker,
    Orchestrator,
    untokenized_runner,
    TokenCertifier,
    THREADS_PER_TYPE,
    MAX_ASYNC_CONCURRENCY_PER_THREAD,
)

# Lapidador (pós-processamento)
try:
    from main_rebuild import main as init_lapidador
except Exception:
    init_lapidador = None

# Runner de grafos
try:
    from grafos_runner import run_graphs
except Exception:
    run_graphs = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_QR = os.path.join(APP_DIR, "meu_qrcode.png")
DEFAULT_JSON = os.path.join(APP_DIR, "data.json")
JSON_DIR = os.path.join(APP_DIR, "json")
TEST_RUNNER = os.path.join(APP_DIR, "test_cli", "run_all.py")
WORK_DIR = os.path.join(APP_DIR, "work")
REPO_URL = "https://github.com/kasshinokun/TP_Grafos_2026_1"


# ==============================================================================
# Classes auxiliares (parser GEXF)
# ==============================================================================
class GraphValidateLoader:
    """Valida e carrega um grafo a partir de um arquivo .gexf usando parser XML manual."""
    @staticmethod
    def validate(file_path: str):
        if not os.path.isfile(file_path):
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logging.error(f"Erro ao ler arquivo {file_path}: {e}")
            return None

        directed = False
        graph_tag = GraphValidateLoader._find_tag(content, 'graph')
        if graph_tag:
            attrs = GraphValidateLoader._parse_attributes(graph_tag)
            if attrs.get('defaultedgetype') == 'directed' or attrs.get('mode') == 'directed':
                directed = True

        nodes = []
        node_tags = GraphValidateLoader._find_all_tags(content, 'node')
        for tag in node_tags:
            attrs = GraphValidateLoader._parse_attributes(tag)
            node_id = attrs.get('id')
            if node_id:
                nodes.append(node_id)

        edges = []
        edge_tags = GraphValidateLoader._find_all_tags(content, 'edge')
        for tag in edge_tags:
            attrs = GraphValidateLoader._parse_attributes(tag)
            source = attrs.get('source')
            target = attrs.get('target')
            if source and target:
                edges.append((source, target))

        return {
            'nodes': nodes,
            'edges': edges,
            'node_count': len(nodes),
            'edge_count': len(edges),
            'directed': directed
        }

    @staticmethod
    def _find_tag(text: str, tag_name: str) -> str:
        start = text.find(f'<{tag_name}')
        if start == -1:
            return ''
        end = GraphValidateLoader._find_tag_end(text, start)
        if end == -1:
            return ''
        return text[start:end+1]

    @staticmethod
    def _find_all_tags(text: str, tag_name: str):
        tags = []
        pos = 0
        while True:
            start = text.find(f'<{tag_name}', pos)
            if start == -1:
                break
            end = GraphValidateLoader._find_tag_end(text, start)
            if end == -1:
                break
            tags.append(text[start:end+1])
            pos = end + 1
        return tags

    @staticmethod
    def _find_tag_end(text: str, start: int) -> int:
        i = start
        in_quote = False
        quote_char = ''
        while i < len(text):
            ch = text[i]
            if ch == '"' or ch == "'":
                if not in_quote:
                    in_quote = True
                    quote_char = ch
                elif ch == quote_char:
                    in_quote = False
            elif ch == '>' and not in_quote:
                return i
            elif ch == '/' and i+1 < len(text) and text[i+1] == '>' and not in_quote:
                return i+1
            i += 1
        return -1

    @staticmethod
    def _parse_attributes(tag: str) -> dict:
        attrs = {}
        first_space = tag.find(' ')
        if first_space == -1:
            return attrs
        attr_part = tag[first_space:].rstrip('/>').strip()
        i = 0
        length = len(attr_part)
        while i < length:
            while i < length and attr_part[i].isspace():
                i += 1
            if i >= length:
                break
            j = i
            while j < length and attr_part[j] != '=' and not attr_part[j].isspace():
                j += 1
            if j >= length or attr_part[j] != '=':
                i = j + 1
                continue
            attr_name = attr_part[i:j].strip()
            i = j + 1
            while i < length and attr_part[i].isspace():
                i += 1
            if i >= length:
                break
            if attr_part[i] not in ('"', "'"):
                j = i
                while j < length and not attr_part[j].isspace():
                    j += 1
                attr_value = attr_part[i:j]
                attrs[attr_name] = attr_value
                i = j
                continue
            quote = attr_part[i]
            i += 1
            j = i
            while j < length and attr_part[j] != quote:
                j += 1
            if j >= length:
                break
            attr_value = attr_part[i:j]
            attrs[attr_name] = attr_value
            i = j + 1
        return attrs


# ==============================================================================
# Thread para mineração (executa em segundo plano)
# ==============================================================================
class MiningThread(QThread):
    log_signal = pyqtSignal(str)
    notify_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, tokens, user, repo, years, use_tokens, run_lapidador):
        super().__init__()
        self.tokens = tokens
        self.user = user
        self.repo = repo
        self.years = years
        self.use_tokens = use_tokens
        self.run_lapidador = run_lapidador
        self.orchestrator = None

    def run(self):
        try:
            if self.use_tokens:
                if not self.tokens:
                    self.notify_signal.emit("⚠ Sem tokens — alternando para modo SEM TOKEN.")
                    untokenized_runner(target_user=self.user, target_repo=self.repo, years_back=self.years)
                else:
                    valid = TokenCertifier.validate_tokens(self.tokens)
                    if not valid:
                        self.notify_signal.emit("⚠ Nenhum token válido — alternando para SEM TOKEN.")
                        untokenized_runner(target_user=self.user, target_repo=self.repo, years_back=self.years)
                    else:
                        app = Orchestrator(tokens=valid, target_user=self.user, target_repo=self.repo, years_back=self.years)
                        self.orchestrator = app
                        app.start()
            else:
                untokenized_runner(target_user=self.user, target_repo=self.repo, years_back=self.years)
            self.notify_signal.emit("✅ Mineração finalizada.")
        except Exception as e:
            logging.error(f"Erro na mineração: {e}", exc_info=True)
            self.notify_signal.emit(f"❌ Erro: {e}")
        finally:
            if self.run_lapidador:
                self._run_lapidador()
                self._run_graphs()
            self.finished_signal.emit()

    def _run_lapidador(self):
        if init_lapidador is None:
            self.notify_signal.emit("ℹ Lapidador (main_rebuild) não disponível — pulando.")
            return
        try:
            self.notify_signal.emit("🪨 Executando Lapidador (main_rebuild.main) …")
            init_lapidador()
            self.notify_signal.emit("🪨 Lapidador finalizado.")
        except Exception as e:
            logging.error(f"Lapidador falhou: {e}", exc_info=True)
            self.notify_signal.emit(f"❌ Lapidador falhou: {e}")

    def _run_graphs(self):
        if run_graphs is None:
            self.notify_signal.emit("ℹ grafos_runner não disponível — pulando módulo de grafos.")
            return
        try:
            self.notify_signal.emit("🕸 Construindo grafos a partir de ./json/ …")
            summary = run_graphs(JSON_DIR)
            self.notify_signal.emit(f"🕸 Grafos: {summary}")
        except Exception as e:
            logging.error(f"grafos_runner falhou: {e}", exc_info=True)
            self.notify_signal.emit(f"❌ Grafos falhou: {e}")

    def stop(self):
        if self.orchestrator:
            try:
                self.orchestrator.shutdown_mgr.request_shutdown()
            except Exception:
                pass


# ==============================================================================
# Tela de Mineração
# ==============================================================================
class MiningWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.real_tokens: List[str] = []
        self.mining_thread: Optional[MiningThread] = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Sidebar (painel esquerdo)
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("⛏ Projeto Delta")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        sidebar_layout.addWidget(title)

        subtitle = QLabel("Mineração híbrida GitHub")
        subtitle.setStyleSheet("color: gray;")
        sidebar_layout.addWidget(subtitle)

        # Alvo
        group_target = QFrame()
        group_target.setFrameShape(QFrame.Shape.Box)
        group_target_layout = QVBoxLayout(group_target)
        group_target_layout.addWidget(QLabel("🎯 Alvo da Mineração"))
        group_target_layout.addWidget(QLabel("Target user"))
        self.entry_user = QLineEdit()
        self.entry_user.setPlaceholderText("ex: torvalds")
        group_target_layout.addWidget(self.entry_user)
        group_target_layout.addWidget(QLabel("Target repo"))
        self.entry_repo = QLineEdit()
        self.entry_repo.setPlaceholderText("ex: linux")
        group_target_layout.addWidget(self.entry_repo)
        group_target_layout.addWidget(QLabel("Anos de histórico"))
        years_layout = QHBoxLayout()
        self.spin_years = QSpinBox()
        self.spin_years.setRange(1, 5)
        self.spin_years.setValue(5)
        btn_minus = QPushButton("-1")
        btn_plus = QPushButton("+1")
        btn_minus.clicked.connect(lambda: self.spin_years.setValue(self.spin_years.value() - 1))
        btn_plus.clicked.connect(lambda: self.spin_years.setValue(self.spin_years.value() + 1))
        years_layout.addWidget(self.spin_years)
        years_layout.addWidget(btn_minus)
        years_layout.addWidget(btn_plus)
        group_target_layout.addLayout(years_layout)
        sidebar_layout.addWidget(group_target)

        # Tokens
        group_tokens = QFrame()
        group_tokens.setFrameShape(QFrame.Shape.Box)
        group_tokens_layout = QVBoxLayout(group_tokens)
        group_tokens_layout.addWidget(QLabel("🔑 Tokens GitHub"))
        self.token_list = QListWidget()
        self.token_list.setMaximumHeight(100)
        group_tokens_layout.addWidget(self.token_list)

        token_input_layout = QHBoxLayout()
        self.entry_new_token = QLineEdit()
        self.entry_new_token.setPlaceholderText("Cole o token aqui (ghp_...)")
        btn_add = QPushButton("➕ Add")
        btn_add.clicked.connect(self.add_token)
        btn_clear = QPushButton("🗑️")
        btn_clear.clicked.connect(self.clear_tokens)
        token_input_layout.addWidget(self.entry_new_token)
        token_input_layout.addWidget(btn_add)
        token_input_layout.addWidget(btn_clear)
        group_tokens_layout.addLayout(token_input_layout)

        self.use_tokens_cb = QCheckBox("Usar tokens (mineração rápida)")
        self.use_tokens_cb.setChecked(True)
        group_tokens_layout.addWidget(self.use_tokens_cb)
        self.run_lapidador_cb = QCheckBox("Rodar Lapidador ao terminar")
        self.run_lapidador_cb.setChecked(True)
        group_tokens_layout.addWidget(self.run_lapidador_cb)
        sidebar_layout.addWidget(group_tokens)


        # --- Container horizontal para Arquivos e Ações ---
        actions_horizontal = QWidget()
        actions_horizontal_layout = QHBoxLayout(actions_horizontal)
        actions_horizontal_layout.setContentsMargins(0, 0, 0, 0)
        
        # Arquivos
        group_files = QFrame()
        group_files.setFrameShape(QFrame.Shape.Box)
        group_files_layout = QVBoxLayout(group_files)
        btn_load_qr = QPushButton("📂 Carregar QR")
        btn_load_qr.clicked.connect(self.load_qr)
        btn_load_json = QPushButton("📂 Carregar JSON")
        btn_load_json.clicked.connect(self.load_json)
        btn_save_json = QPushButton("💾 Salvar JSON")
        btn_save_json.clicked.connect(self.save_json)
        btn_gen_qr = QPushButton("📱 Gerar QR")
        btn_gen_qr.clicked.connect(self.generate_qr)
        group_files_layout.addWidget(btn_load_qr)
        group_files_layout.addWidget(btn_load_json)
        group_files_layout.addWidget(btn_save_json)
        group_files_layout.addWidget(btn_gen_qr)

        # Ações
        group_actions = QFrame()
        group_actions.setFrameShape(QFrame.Shape.Box)
        group_actions_layout = QVBoxLayout(group_actions)
        self.btn_start = QPushButton("▶ Iniciar mineração")
        self.btn_start.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold;")
        self.btn_start.clicked.connect(self.start_mining)
        self.btn_stop = QPushButton("■ Parar")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold;")
        self.btn_stop.clicked.connect(self.stop_mining)
        self.btn_post = QPushButton("📊 Pós-processar (Lapidador + Grafos)")
        self.btn_post.clicked.connect(self.post_process)
        self.btn_tests = QPushButton("🧪 Rodar Testes Unitários")
        self.btn_tests.clicked.connect(self.run_tests)
        group_actions_layout.addWidget(self.btn_start)
        group_actions_layout.addWidget(self.btn_stop)
        group_actions_layout.addWidget(self.btn_post)
        group_actions_layout.addWidget(self.btn_tests)

        # Adiciona os dois frames ao layout horizontal
        actions_horizontal_layout.addWidget(group_files)
        actions_horizontal_layout.addWidget(group_actions)

        # Adiciona o container horizontal à sidebar
        sidebar_layout.addWidget(actions_horizontal)
        
        # Satus do Processo
        self.status_label = QLabel("Status: ocioso")
        self.status_label.setStyleSheet("font-weight: bold; color: gray;")
        sidebar_layout.addWidget(self.status_label)
        sidebar_layout.addStretch()

        # Área principal (log e notificações)
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(QLabel("📜 Log da aplicação"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFontFamily("Courier New")
        main_layout.addWidget(self.log_text)
        main_layout.addWidget(QLabel("🔔 Notificações"))
        self.notif_text = QTextEdit()
        self.notif_text.setReadOnly(True)
        self.notif_text.setFontFamily("Courier New")
        main_layout.addWidget(self.notif_text)

        splitter = QHBoxLayout()
        splitter.addWidget(sidebar, 1)
        splitter.addWidget(main_widget, 2)
        layout.addLayout(splitter)

        self.preload_config()

    # --- Token management ---
    def mask_token(self, token: str) -> str:
        clean = token.strip()
        if len(clean) >= 4:
            return f"|---------------> Token ...{clean[-4:]}"
        return f"|---------------> Token ...{clean}"

    def update_token_display(self):
        self.token_list.clear()
        for t in self.real_tokens:
            self.token_list.addItem(self.mask_token(t))

    def add_token(self):
        raw = self.entry_new_token.text().strip()
        if not raw:
            return
        new_tokens = [t.strip() for t in raw.replace(',', '\n').split() if t.strip()]
        added = 0
        for t in new_tokens:
            if t not in self.real_tokens:
                self.real_tokens.append(t)
                added += 1
        self.entry_new_token.clear()
        self.update_token_display()
        self.notify(f"✅ {added} token(s) adicionado(s).")

    def clear_tokens(self):
        self.real_tokens.clear()
        self.update_token_display()
        self.notify("🗑️ Lista de tokens limpa.")

    # --- Handlers de arquivos ---
    def load_qr(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar QR Code", APP_DIR, "Imagens (*.png *.jpg *.jpeg);;Todos (*.*)")
        if not path:
            return
        try:
            data = QRCodeJSONHandler.ler_qr_code(path) or {}
            self.apply_config(data)
            self.notify(f"QR Code carregado: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro QR", str(e))

    def load_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar data.json", APP_DIR, "JSON (*.json);;Todos (*.*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.apply_config(data)
            self.notify(f"JSON carregado: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro JSON", str(e))

    def save_json(self):
        data = self.collect_config()
        path, _ = QFileDialog.getSaveFileName(self, "Salvar configuração", os.path.join(APP_DIR, "data.json"), "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.notify(f"JSON salvo em {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", str(e))

    def generate_qr(self):
        data = self.collect_config()
        path, _ = QFileDialog.getSaveFileName(self, "Gerar QR Code", os.path.join(APP_DIR, "meu_qrcode.png"), "PNG (*.png)")
        if not path:
            return
        try:
            QRCodeJSONHandler.gerar_qr_code(data, path)
            self.notify(f"QR Code gerado em {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro QR", str(e))

    # --- Ações principais ---
    def start_mining(self):
        cfg = self.collect_config()
        if not cfg["target_user"] or not cfg["target_repo"]:
            QMessageBox.critical(self, "Erro", "Informe target_user e target_repo.")
            return
        years = self.spin_years.value()
        use_tokens = self.use_tokens_cb.isChecked()
        tokens = cfg["token"] if use_tokens else []

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.status_label.setText("Status: minerando…")
        self.status_label.setStyleSheet("color: #16a34a; font-weight: bold;")

        self.mining_thread = MiningThread(tokens, cfg["target_user"], cfg["target_repo"], years, use_tokens, self.run_lapidador_cb.isChecked())
        self.mining_thread.log_signal.connect(self.append_log)
        self.mining_thread.notify_signal.connect(self.notify)
        self.mining_thread.finished_signal.connect(self.mining_finished)
        self.mining_thread.start()

    def stop_mining(self):
        if self.mining_thread:
            self.mining_thread.stop()
            self.notify("⏹ Parada solicitada — aguardando finalização.")
            self.status_label.setText("Status: parando…")
            self.status_label.setStyleSheet("color: #f59e0b; font-weight: bold;")

    def mining_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status_label.setText("Status: ocioso")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")

    def post_process(self):
        if not os.path.isdir(JSON_DIR):
            QMessageBox.warning(self, "Sem dados", f"Pasta ./json/ não encontrada em:\n{JSON_DIR}")
            return
        self.btn_post.setEnabled(False)
        self.status_label.setText("Status: pós-processando…")
        self.status_label.setStyleSheet("color: #2563eb; font-weight: bold;")
        def run():
            try:
                self.notify("📊 Iniciando pós-processamento de ./json/ …")
                if init_lapidador:
                    self.notify("🪨 Executando Lapidador …")
                    init_lapidador()
                if run_graphs:
                    self.notify("🕸 Construindo grafos …")
                    summary = run_graphs(JSON_DIR)
                    self.notify(f"🕸 Grafos: {summary}")
                self.notify("✅ Pós-processamento concluído.")
            except Exception as e:
                self.notify(f"❌ Erro pós-processamento: {e}")
            finally:
                self.btn_post.setEnabled(True)
                self.status_label.setText("Status: ocioso")
                self.status_label.setStyleSheet("color: gray; font-weight: bold;")
        threading.Thread(target=run, daemon=True).start()

    def run_tests(self):
        if not os.path.isfile(TEST_RUNNER):
            QMessageBox.warning(self, "Suíte não encontrada", f"Arquivo não localizado:\n{TEST_RUNNER}")
            return
        self.btn_tests.setEnabled(False)
        self.status_label.setText("Status: testando…")
        self.status_label.setStyleSheet("color: #7c3aed; font-weight: bold;")
        def run():
            try:
                self.notify(f"🧪 Executando suíte: {TEST_RUNNER}")
                proc = subprocess.Popen(
                    [sys.executable, TEST_RUNNER],
                    cwd=APP_DIR,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                )
                assert proc.stdout is not None
                for line in proc.stdout:
                    self.append_log(line.rstrip())
                rc = proc.wait()
                self.notify(f"🧪 Testes finalizados (exit={rc}).")
            except Exception as e:
                self.notify(f"❌ Erro nos testes: {e}")
            finally:
                self.btn_tests.setEnabled(True)
                self.status_label.setText("Status: ocioso")
                self.status_label.setStyleSheet("color: gray; font-weight: bold;")
        threading.Thread(target=run, daemon=True).start()

    # --- Helpers ---
    def collect_config(self) -> dict:
        return {
            "token": self.real_tokens,
            "target_user": self.entry_user.text().strip(),
            "target_repo": self.entry_repo.text().strip(),
        }

    def apply_config(self, data: dict):
        tokens = data.get("token", [])
        if isinstance(tokens, str):
            tokens = [tokens]
        self.real_tokens = [str(t).strip() for t in tokens if str(t).strip()]
        self.update_token_display()
        self.entry_user.setText(data.get("target_user", ""))
        self.entry_repo.setText(data.get("target_repo", ""))

    def preload_config(self):
        try:
            if os.path.exists(DEFAULT_QR):
                data = QRCodeJSONHandler.ler_qr_code(DEFAULT_QR) or {}
                if data:
                    self.apply_config(data)
            elif os.path.exists(DEFAULT_JSON):
                with open(DEFAULT_JSON, "r", encoding="utf-8") as f:
                    self.apply_config(json.load(f))
        except Exception as e:
            logging.warning(f"Falha ao pré-carregar config: {e}")

    def append_log(self, msg: str):
        self.log_text.append(msg)
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def notify(self, msg: str):
        self.notif_text.append(msg)
        cursor = self.notif_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.notif_text.setTextCursor(cursor)


# ==============================================================================
# Tela Sobre (agora recebe QPixmap gerado via buffer de bytes)
# ==============================================================================
class AboutWidget(QWidget):
    def __init__(self, qr_pixmap: QPixmap = None):
        super().__init__()
        self.qr_pixmap = qr_pixmap
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        info_text = (
            "🏫 Projeto Trabalho Prático de Teoria de Grafos\n"
            "e Computabilidade\n\n"
            "🏛️ Faculdade: Pontifícia Universidade Católica de Minas Gerais - PUC MINAS\n"
            "📍 Campus: Coração Eucarístico\n"
            "👥 Alunos:\n"
            "   • Daniel Lucas Soares Madureira\n"
            "   • Gabriel da Silva Cassino\n"
            "   • Paulo Henrique Rodrigues Neves\n"
            "   • Vinicius Cezar Pereira Menezes\n"
            "👨‍🏫 Professor: Prof. Leonardo Vilela Cardoso\n"
            "📚 Turma: 31.32.101\n"
            "🎓 Graduação: Engenharia de Computação\n"
            "📅 Semestre: 2026/1\n"
        )
        lbl_info = QLabel(info_text)
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(lbl_info)

        if self.qr_pixmap and not self.qr_pixmap.isNull():
            lbl_qr = QLabel()
            lbl_qr.setPixmap(self.qr_pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
            lbl_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_qr)

        lbl_url = QLabel(f"Repositório: {REPO_URL}")
        lbl_url.setWordWrap(True)
        layout.addWidget(lbl_url)
        layout.addStretch()


# ==============================================================================
# Tela de Visualização de Grafos
# ==============================================================================
class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_graph_data: Optional[Dict[str, Any]] = None
        self.init_ui()
        self.refresh_gexf_list()

    def init_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Grafos disponíveis (work/):"))
        self.combo_gexf = QComboBox()
        self.combo_gexf.setMinimumWidth(300)
        top_layout.addWidget(self.combo_gexf)
        btn_load_combo = QPushButton("Carregar")
        btn_load_combo.clicked.connect(self.load_selected_gexf)
        top_layout.addWidget(btn_load_combo)
        layout.addLayout(top_layout)

        upload_layout = QHBoxLayout()
        upload_layout.addWidget(QLabel("Ou escolha um arquivo .gexf:"))
        self.entry_custom = QLineEdit()
        self.entry_custom.setPlaceholderText("Caminho do arquivo .gexf")
        self.entry_custom.setMinimumWidth(400)
        upload_layout.addWidget(self.entry_custom)
        btn_browse = QPushButton("📂 Procurar")
        btn_browse.clicked.connect(self.browse_gexf)
        upload_layout.addWidget(btn_browse)
        btn_load_custom = QPushButton("Carregar")
        btn_load_custom.clicked.connect(self.load_custom_gexf)
        upload_layout.addWidget(btn_load_custom)
        layout.addLayout(upload_layout)

        self.tabview = QTabWidget()
        self.tab_stats = QTextEdit()
        self.tab_stats.setReadOnly(True)
        self.tab_stats.setFontFamily("Courier New")
        self.tab_nodes = QTextEdit()
        self.tab_nodes.setReadOnly(True)
        self.tab_nodes.setFontFamily("Courier New")
        self.tab_edges = QTextEdit()
        self.tab_edges.setReadOnly(True)
        self.tab_edges.setFontFamily("Courier New")
        self.tabview.addTab(self.tab_stats, "Estatísticas")
        self.tabview.addTab(self.tab_nodes, "Nós")
        self.tabview.addTab(self.tab_edges, "Arestas")
        layout.addWidget(self.tabview)

        self.status_label = QLabel("Nenhum grafo carregado.")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

    def refresh_gexf_list(self):
        if not os.path.isdir(WORK_DIR):
            self.combo_gexf.addItem("Pasta work/ não encontrada")
            return
        files = [f for f in os.listdir(WORK_DIR) if f.endswith('.gexf')]
        self.combo_gexf.clear()
        if not files:
            self.combo_gexf.addItem("Nenhum .gexf encontrado")
        else:
            self.combo_gexf.addItems(files)

    def browse_gexf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo .gexf", "", "GEXF (*.gexf);;Todos (*.*)")
        if path:
            self.entry_custom.setText(path)

    def load_selected_gexf(self):
        selected = self.combo_gexf.currentText()
        if not selected or selected.startswith("Nenhum") or selected.startswith("Pasta"):
            self.status_label.setText("Nenhum arquivo válido selecionado.")
            self.status_label.setStyleSheet("color: orange;")
            return
        full_path = os.path.join(WORK_DIR, selected)
        self.load_graph(full_path)

    def load_custom_gexf(self):
        path = self.entry_custom.text().strip()
        if not path:
            self.status_label.setText("Informe o caminho do arquivo .gexf")
            self.status_label.setStyleSheet("color: orange;")
            return
        self.load_graph(path)

    def load_graph(self, file_path: str):
        data = GraphValidateLoader.validate(file_path)
        if data is None:
            self.status_label.setText(f"Falha ao carregar/validar: {file_path}")
            self.status_label.setStyleSheet("color: red;")
            return
        self.current_graph_data = data
        self.display_graph_data(data, file_path)

    def display_graph_data(self, data: Dict[str, Any], file_path: str):
        stats = (
            f"Arquivo: {os.path.basename(file_path)}\n"
            f"Direcionado: {'Sim' if data['directed'] else 'Não'}\n"
            f"Número de nós: {data['node_count']}\n"
            f"Número de arestas: {data['edge_count']}\n"
        )
        if data['node_count'] > 0:
            stats += f"Grau médio: {(2 * data['edge_count']) / data['node_count']:.2f}\n"
        self.tab_stats.setText(stats)

        nodes_str = "\n".join(data['nodes'])
        self.tab_nodes.setText(nodes_str)

        edges_str = "\n".join([f"{s} -> {t}" for s, t in data['edges']])
        self.tab_edges.setText(edges_str)

        self.status_label.setText(f"Grafo carregado: {os.path.basename(file_path)} | Nós: {data['node_count']} | Arestas: {data['edge_count']}")
        self.status_label.setStyleSheet("color: green;")


# ==============================================================================
# Janela Principal
# ==============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projeto Delta v4c — Minerador GitHub (PyQt6)")
        self.setGeometry(100, 100, 1180, 760)
        self.setMinimumSize(960, 620)

        # Gera QR Code do repositório diretamente em memória (buffer de bytes)
        qr_pixmap = self.generate_qr_from_memory()

        # Cria o stack de telas
        self.stack = QStackedWidget()
        self.mining_widget = MiningWidget()
        self.about_widget = AboutWidget(qr_pixmap)
        self.graph_widget = GraphWidget()
        self.stack.addWidget(self.mining_widget)
        self.stack.addWidget(self.about_widget)
        self.stack.addWidget(self.graph_widget)

        # Barra de ferramentas
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        theme_combo = QComboBox()
        theme_combo.addItems(["System", "Dark", "Light"])
        theme_combo.currentTextChanged.connect(self.change_theme)
        toolbar.addWidget(QLabel(" Tema: "))
        toolbar.addWidget(theme_combo)
        toolbar.addSeparator()

        btn_mining = QPushButton("Mineração")
        btn_mining.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_about = QPushButton("Sobre")
        btn_about.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_graph = QPushButton("Grafos")
        btn_graph.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        toolbar.addWidget(btn_mining)
        toolbar.addWidget(btn_about)
        toolbar.addWidget(btn_graph)

        self.setCentralWidget(self.stack)
        self.stack.setCurrentIndex(0)

    def generate_qr_from_memory(self) -> Optional[QPixmap]:
        """Gera QR Code em buffer de bytes e retorna QPixmap sem tocar em disco."""
        try:
            # Cria QR Code
            qr = qrcode.QRCode(box_size=8, border=2)
            qr.add_data(REPO_URL)
            qr.make(fit=True)
            img_pil = qr.make_image(fill_color="black", back_color="white")
            # Redimensiona para um tamanho razoável
            img_pil = img_pil.resize((200, 200), Image.Resampling.LANCZOS)

            # Converte PIL Image para bytes (PNG) em memória
            buffer = io.BytesIO()
            img_pil.save(buffer, format="PNG")
            buffer.seek(0)
            data = buffer.read()

            # Carrega QPixmap a partir dos bytes
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            return pixmap
        except Exception as e:
            logging.warning(f"Falha ao gerar QR Code em memória: {e}")
            return None

    def change_theme(self, theme: str):
        app = QApplication.instance()
        if theme == "Dark":
            app.setStyle("Fusion")
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
            app.setPalette(dark_palette)
        elif theme == "Light":
            app.setStyle("Fusion")
            app.setPalette(app.style().standardPalette())
        else:  # System
            app.setStyle("Fusion")
            app.setPalette(app.style().standardPalette())

    def closeEvent(self, event):
        """Nenhum arquivo temporário para limpar, apenas aceita o fechamento."""
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
