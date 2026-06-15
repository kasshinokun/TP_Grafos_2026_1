#!/usr/bin/env python3
# delta_gui_pyqt6.py — Interface PyQt6 para o Projeto Delta v4c (REV A)
# com ofuscação de tokens nos logs.

import os
import sys
import json
import logging
import threading
import subprocess
import re
from typing import List, Optional

from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QObject, QTimer, QSettings
)
from PyQt6.QtGui import QFont, QTextCursor, QPalette, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QTextEdit, QCheckBox,
    QPushButton, QFileDialog, QMessageBox, QProgressBar,
    QSplitter, QComboBox, QStatusBar, QFrame
)

# Módulos originais do projeto
from orchestrator_hibrido_alpha0e import (
    QRCodeJSONHandler,
    JsonWorker,
    Orchestrator,
    untokenized_runner,
    TokenCertifier,
    THREADS_PER_TYPE,
    MAX_ASYNC_CONCURRENCY_PER_THREAD,
)

# Lapidador (pós-processamento) – opcional
try:
    from main_rebuild import main as init_lapidador
except ImportError:
    init_lapidador = None

# Runner de grafos – opcional
try:
    from grafos_runner import run_graphs
except ImportError:
    run_graphs = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_QR = os.path.join(APP_DIR, "meu_qrcode.png")
DEFAULT_JSON = os.path.join(APP_DIR, "data.json")
JSON_DIR = os.path.join(APP_DIR, "json")
TEST_RUNNER = os.path.join(APP_DIR, "test_cli", "run_all.py")


# =============================================================================
# Handler de logging que emite sinais para a interface (thread‑safe)
# =============================================================================
class LogEmitter(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._handler = None

    def install(self):
        handler = _SignalLogHandler(self.log_signal)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(threadName)s: %(message)s",
            datefmt="%H:%M:%S"
        ))
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(handler)
        self._handler = handler


class _SignalLogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg)


# =============================================================================
# Workers (executam tarefas pesadas em threads separadas)
# =============================================================================
class MiningWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    notification = pyqtSignal(str)

    def __init__(self, tokens, user, repo, years, use_tokens, run_lapidador_after):
        super().__init__()
        self.tokens = tokens
        self.user = user
        self.repo = repo
        self.years = years
        self.use_tokens = use_tokens
        self.run_lapidador_after = run_lapidador_after
        self.orchestrator_ref = None
        self._shutdown = threading.Event()

    def request_stop(self):
        self._shutdown.set()
        if self.orchestrator_ref:
            try:
                self.orchestrator_ref.shutdown_mgr.request_shutdown()
            except Exception:
                pass

    def run(self):
        try:
            if self.use_tokens and self.tokens:
                valid = TokenCertifier.validate_tokens(self.tokens)
                if valid:
                    app = Orchestrator(
                        tokens=valid,
                        target_user=self.user,
                        target_repo=self.repo,
                        years_back=self.years,
                    )
                    self.orchestrator_ref = app
                    app.start()
                else:
                    self.notification.emit("⚠ Nenhum token válido — usando modo SEM TOKEN.")
                    untokenized_runner(self.user, self.repo, self.years)
            else:
                untokenized_runner(self.user, self.repo, self.years)

            self.notification.emit("✅ Mineração finalizada.")

            if self.run_lapidador_after:
                self._safe_run_lapidador()
                self._safe_run_graphs()

        except Exception as e:
            logging.error(f"Erro na mineração: {e}", exc_info=True)
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def _safe_run_lapidador(self):
        if init_lapidador is None:
            self.notification.emit("ℹ Lapidador (main_rebuild) não disponível — pulando.")
            return
        try:
            self.notification.emit("🪨 Executando Lapidador (main_rebuild.main) …")
            init_lapidador()
            self.notification.emit("🪨 Lapidador finalizado.")
        except Exception as e:
            logging.error(f"Lapidador falhou: {e}", exc_info=True)
            self.notification.emit(f"❌ Lapidador falhou: {e}")

    def _safe_run_graphs(self):
        if run_graphs is None:
            self.notification.emit("ℹ grafos_runner não disponível — pulando módulo de grafos.")
            return
        try:
            self.notification.emit("🕸 Construindo grafos a partir de ./json/ …")
            summary = run_graphs(JSON_DIR)
            self.notification.emit(f"🕸 Grafos: {summary}")
        except Exception as e:
            logging.error(f"grafos_runner falhou: {e}", exc_info=True)
            self.notification.emit(f"❌ Grafos falhou: {e}")


class PostProcessWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    notification = pyqtSignal(str)

    def run(self):
        try:
            self.notification.emit("📊 Iniciando pós-processamento de ./json/ …")
            if init_lapidador:
                self.notification.emit("🪨 Executando Lapidador …")
                init_lapidador()
                self.notification.emit("🪨 Lapidador finalizado.")
            else:
                self.notification.emit("ℹ Lapidador não disponível.")
            if run_graphs:
                self.notification.emit("🕸 Construindo grafos …")
                summary = run_graphs(JSON_DIR)
                self.notification.emit(f"🕸 Grafos: {summary}")
            else:
                self.notification.emit("ℹ grafos_runner não disponível.")
            self.notification.emit("✅ Pós-processamento concluído.")
        except Exception as e:
            logging.error(f"Erro no pós-processamento: {e}", exc_info=True)
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class TestsWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    notification = pyqtSignal(str)

    def run(self):
        try:
            self.notification.emit(f"🧪 Executando suíte: {TEST_RUNNER}")
            proc = subprocess.Popen(
                [sys.executable, TEST_RUNNER],
                cwd=APP_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in iter(proc.stdout.readline, ''):
                if line:
                    logging.info(line.rstrip())
            rc = proc.wait()
            self.notification.emit(f"🧪 Testes finalizados (exit={rc}).")
        except Exception as e:
            logging.error(f"Erro ao rodar testes: {e}", exc_info=True)
            self.error.emit(str(e))
        finally:
            self.finished.emit()


# =============================================================================
# Janela principal (PyQt6)
# =============================================================================
class DeltaGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projeto Delta v4c — Minerador GitHub (PyQt6)")
        self.setMinimumSize(1024, 700)
        self.resize(1200, 800)

        # Configuração de tema e estado
        self.settings = QSettings("DeltaProject", "DeltaGUI")
        self._restore_theme()

        # Widgets e workers
        self.mining_worker = None
        self.post_worker = None
        self.tests_worker = None
        self.orchestrator_ref = None

        # Monta a interface
        self._setup_ui()
        self._install_logging()
        self._connect_signals()
        self._load_initial_config()

    # -------------------------------------------------------------------------
    # [MASK] Função para ofuscar tokens
    # -------------------------------------------------------------------------
    def _mask_token(self, token: str) -> str:
        """Retorna token no formato: |---------------> Token ...abcd"""
        if not isinstance(token, str):
            return token
        if len(token) > 4:
            return f"|---------------> Token ...{token[-4:]}"
        else:
            return "|---------------> Token [curto demais]"

    def _mask_tokens_in_text(self, text: str) -> str:
        """Substitui qualquer token GitHub (ou string longa) no texto pela versão mascarada."""
        # Detecta padrões comuns de token GitHub (ghp_, gho_, ghu_, ghs_, glpat_)
        # Também detecta qualquer sequência alfanumérica com mais de 20 caracteres
        pattern = r'\b(gh[pous]_[A-Za-z0-9]{36,}|glpat-[A-Za-z0-9\-]{20,}|[A-Za-z0-9]{25,})\b'
        
        def replacer(match):
            full_token = match.group(0)
            return self._mask_token(full_token)
        
        return re.sub(pattern, replacer, text)

    # -------------------------------------------------------------------------
    # Interface
    # -------------------------------------------------------------------------
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # ---- Painel esquerdo (controles) ----
        left_panel = QWidget()
        left_panel.setMaximumWidth(380)
        left_layout = QVBoxLayout(left_panel)

        title = QLabel("⛏ Projeto Delta")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        left_layout.addWidget(title)
        left_layout.addWidget(QLabel("Mineração híbrida GitHub"))
        left_layout.addSpacing(12)

        # Grupo: Alvo
        target_group = QGroupBox("Repositório alvo")
        target_layout = QVBoxLayout(target_group)
        self.entry_user = QLineEdit()
        self.entry_user.setPlaceholderText("ex: torvalds")
        self.entry_repo = QLineEdit()
        self.entry_repo.setPlaceholderText("ex: linux")
        self.entry_years = QLineEdit("5")
        target_layout.addWidget(QLabel("Usuário:"))
        target_layout.addWidget(self.entry_user)
        target_layout.addWidget(QLabel("Repositório:"))
        target_layout.addWidget(self.entry_repo)
        target_layout.addWidget(QLabel("Anos de histórico:"))
        target_layout.addWidget(self.entry_years)
        left_layout.addWidget(target_group)

        # Grupo: Tokens (com aviso de segurança)
        token_group = QGroupBox("Tokens GitHub")
        token_layout = QVBoxLayout(token_group)
        self.txt_tokens = QTextEdit()
        self.txt_tokens.setPlaceholderText("Um token por linha")
        self.txt_tokens.setMaximumHeight(120)
        self.use_tokens_cb = QCheckBox("Usar tokens (mineração rápida)")
        self.use_tokens_cb.setChecked(True)
        token_layout.addWidget(self.txt_tokens)
        token_layout.addWidget(self.use_tokens_cb)
        security_warning = QLabel("⚠ Os tokens são mostrados em claro aqui para edição, mas NUNCA aparecem completos nos logs.")
        security_warning.setWordWrap(True)
        security_warning.setStyleSheet("color: #f59e0b; font-size: 10px;")
        token_layout.addWidget(security_warning)
        left_layout.addWidget(token_group)

        # Checkbox pós-mineração
        self.run_lapidador_cb = QCheckBox("Rodar Lapidador ao terminar")
        self.run_lapidador_cb.setChecked(True)
        left_layout.addWidget(self.run_lapidador_cb)

        # Botões de arquivo
        file_buttons = QHBoxLayout()
        btn_load_qr = QPushButton("Carregar QR")
        btn_load_json = QPushButton("Carregar JSON")
        btn_save_json = QPushButton("Salvar JSON")
        btn_gen_qr = QPushButton("Gerar QR")
        file_buttons.addWidget(btn_load_qr)
        file_buttons.addWidget(btn_load_json)
        file_buttons.addWidget(btn_save_json)
        file_buttons.addWidget(btn_gen_qr)
        left_layout.addLayout(file_buttons)

        # Botões principais
        self.btn_start = QPushButton("▶ Iniciar mineração")
        self.btn_start.setStyleSheet("background-color: #16a34a; color: white; font-weight: bold;")
        self.btn_stop = QPushButton("■ Parar")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("background-color: #dc2626; color: white;")
        self.btn_post = QPushButton("📊 Pós-processar (Lapidador + Grafos)")
        self.btn_tests = QPushButton("🧪 Rodar Testes Unitários")

        left_layout.addWidget(self.btn_start)
        left_layout.addWidget(self.btn_stop)
        left_layout.addWidget(self.btn_post)
        left_layout.addWidget(self.btn_tests)

        # Tema e status
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Tema:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Escuro", "Sistema"])
        theme_layout.addWidget(self.theme_combo)
        left_layout.addLayout(theme_layout)

        self.status_label = QLabel("Status: ocioso")
        self.status_label.setStyleSheet("color: gray;")
        left_layout.addWidget(self.status_label)
        left_layout.addStretch()

        # ---- Painel direito (logs) ----
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 10))
        right_layout.addWidget(QLabel("📄 Log da aplicação"))
        right_layout.addWidget(self.log_text)

        self.notif_text = QTextEdit()
        self.notif_text.setReadOnly(True)
        self.notif_text.setFont(QFont("Courier New", 10))
        self.notif_text.setMaximumHeight(200)
        right_layout.addWidget(QLabel("🔔 Notificações"))
        right_layout.addWidget(self.notif_text)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        self.statusBar().addPermanentWidget(self.progress_bar)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 850])

        # Tooltips
        btn_load_qr.setToolTip("Carrega configuração a partir de uma imagem QR Code")
        btn_load_json.setToolTip("Carrega configuração de um arquivo JSON")
        btn_save_json.setToolTip("Salva configuração atual em JSON")
        btn_gen_qr.setToolTip("Gera QR Code com a configuração atual")
        self.btn_start.setToolTip("Inicia a mineração do repositório GitHub")
        self.btn_stop.setToolTip("Solicita parada graciosa da mineração")
        self.btn_post.setToolTip("Processa todos os JSONs da pasta ./json/ sem minerar")
        self.btn_tests.setToolTip("Executa a suíte de testes unitários (subprocesso)")
        self.theme_combo.setToolTip("Altera o tema da interface (claro/escuro/sistema)")

        # Guardar referências para conexão posterior
        self.btn_load_qr = btn_load_qr
        self.btn_load_json = btn_load_json
        self.btn_save_json = btn_save_json
        self.btn_gen_qr = btn_gen_qr

    def _install_logging(self):
        self.log_emitter = LogEmitter()
        self.log_emitter.log_signal.connect(self._append_log)
        self.log_emitter.install()

    def _connect_signals(self):
        self.btn_start.clicked.connect(self.on_start)
        self.btn_stop.clicked.connect(self.on_stop)
        self.btn_post.clicked.connect(self.on_post_process)
        self.btn_tests.clicked.connect(self.on_run_tests)
        self.theme_combo.currentTextChanged.connect(self._change_theme)

        self.btn_load_qr.clicked.connect(self.on_load_qr)
        self.btn_load_json.clicked.connect(self.on_load_json)
        self.btn_save_json.clicked.connect(self.on_save_json)
        self.btn_gen_qr.clicked.connect(self.on_generate_qr)

    # -------------------------------------------------------------------------
    # Ações
    # -------------------------------------------------------------------------
    def on_load_qr(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar QR Code", APP_DIR,
            "Imagens (*.png *.jpg *.jpeg);;Todos (*.*)"
        )
        if not path:
            return
        try:
            data = QRCodeJSONHandler.ler_qr_code(path) or {}
            self._apply_config(data)
            # Notifica de forma ofuscada
            tokens = data.get("token", [])
            if tokens:
                masked_list = [self._mask_token(t) for t in (tokens if isinstance(tokens, list) else [tokens])]
                self._notify(f"QR Code carregado: {os.path.basename(path)} | Tokens: {', '.join(masked_list)}")
            else:
                self._notify(f"QR Code carregado: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro QR", str(e))

    def on_load_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar JSON", APP_DIR,
            "JSON (*.json);;Todos (*.*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._apply_config(data)
            tokens = data.get("token", [])
            if tokens:
                masked_list = [self._mask_token(t) for t in (tokens if isinstance(tokens, list) else [tokens])]
                self._notify(f"JSON carregado: {os.path.basename(path)} | Tokens: {', '.join(masked_list)}")
            else:
                self._notify(f"JSON carregado: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro JSON", str(e))

    def on_save_json(self):
        data = self._collect_config()
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar configuração", APP_DIR,
            "JSON (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._notify(f"JSON salvo em {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", str(e))

    def on_generate_qr(self):
        data = self._collect_config()
        path, _ = QFileDialog.getSaveFileName(
            self, "Gerar QR Code", APP_DIR,
            "PNG (*.png)"
        )
        if not path:
            return
        try:
            QRCodeJSONHandler.gerar_qr_code(data, path)
            self._notify(f"QR Code gerado em {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro QR", str(e))

    def on_start(self):
        cfg = self._collect_config()
        if not cfg["target_user"] or not cfg["target_repo"]:
            QMessageBox.warning(self, "Campos incompletos", "Informe target_user e target_repo.")
            return
        try:
            years = int(self.entry_years.text().strip() or "5")
            if years < 1:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Erro", "Anos deve ser inteiro >= 1.")
            return

        use_tokens = self.use_tokens_cb.isChecked()
        tokens = cfg["token"] if use_tokens else []

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_post.setEnabled(False)
        self.btn_tests.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Status: minerando…")
        self.status_label.setStyleSheet("color: #16a34a;")

        self.mining_worker = MiningWorker(
            tokens, cfg["target_user"], cfg["target_repo"],
            years, use_tokens, self.run_lapidador_cb.isChecked()
        )
        self.mining_worker.finished.connect(self._on_mining_finished)
        self.mining_worker.error.connect(self._on_mining_error)
        self.mining_worker.notification.connect(self._notify)
        self.mining_worker.start()

    def on_stop(self):
        if self.mining_worker:
            self.mining_worker.request_stop()
        self._notify("⏹ Parada solicitada — aguardando finalização.")
        self.status_label.setText("Status: parando…")
        self.status_label.setStyleSheet("color: #f59e0b;")

    def on_post_process(self):
        if not os.path.isdir(JSON_DIR):
            QMessageBox.warning(
                self, "Sem dados",
                f"Pasta ./json/ não encontrada em:\n{JSON_DIR}\n\n"
                "Rode uma mineração antes ou crie a pasta com os JSONs."
            )
            return

        self.btn_post.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.btn_tests.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Status: pós-processando…")
        self.status_label.setStyleSheet("color: #2563eb;")

        self.post_worker = PostProcessWorker()
        self.post_worker.finished.connect(self._on_post_finished)
        self.post_worker.error.connect(self._on_post_error)
        self.post_worker.notification.connect(self._notify)
        self.post_worker.start()

    def on_run_tests(self):
        if not os.path.isfile(TEST_RUNNER):
            QMessageBox.warning(
                self, "Suíte não encontrada",
                f"Arquivo não localizado:\n{TEST_RUNNER}"
            )
            return

        self.btn_tests.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.btn_post.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Status: testando…")
        self.status_label.setStyleSheet("color: #7c3aed;")

        self.tests_worker = TestsWorker()
        self.tests_worker.finished.connect(self._on_tests_finished)
        self.tests_worker.error.connect(self._on_tests_error)
        self.tests_worker.notification.connect(self._notify)
        self.tests_worker.start()

    # -------------------------------------------------------------------------
    # Callbacks dos workers
    # -------------------------------------------------------------------------
    def _on_mining_finished(self):
        self._reset_ui_after_task()
        self._notify("Mineração encerrada.")

    def _on_mining_error(self, err_msg):
        self._reset_ui_after_task()
        self._notify(f"❌ Erro na mineração: {err_msg}")

    def _on_post_finished(self):
        self._reset_ui_after_task()
        self._notify("Pós-processamento concluído.")

    def _on_post_error(self, err_msg):
        self._reset_ui_after_task()
        self._notify(f"❌ Erro no pós-processamento: {err_msg}")

    def _on_tests_finished(self):
        self._reset_ui_after_task()
        self._notify("Testes finalizados.")

    def _on_tests_error(self, err_msg):
        self._reset_ui_after_task()
        self._notify(f"❌ Erro nos testes: {err_msg}")

    def _reset_ui_after_task(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_post.setEnabled(True)
        self.btn_tests.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Status: ocioso")
        self.status_label.setStyleSheet("color: gray;")
        self.mining_worker = None

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _collect_config(self) -> dict:
        tokens = [t.strip() for t in self.txt_tokens.toPlainText().splitlines() if t.strip()]
        return {
            "token": tokens,
            "target_user": self.entry_user.text().strip(),
            "target_repo": self.entry_repo.text().strip(),
        }

    def _apply_config(self, data: dict):
        tokens = data.get("token", [])
        if isinstance(tokens, str):
            tokens = [tokens]
        self.txt_tokens.setPlainText("\n".join(tokens))  # mantém texto claro para edição
        self.entry_user.setText(data.get("target_user", ""))
        self.entry_repo.setText(data.get("target_repo", ""))

    def _notify(self, msg: str):
        """Adiciona mensagem ofuscada à área de notificações."""
        import time
        timestamp = time.strftime("%H:%M:%S")
        masked_msg = self._mask_tokens_in_text(msg)
        self.notif_text.append(f"[{timestamp}] {masked_msg}")
        self.notif_text.moveCursor(QTextCursor.MoveOperation.End)

    def _append_log(self, msg: str):
        """Adiciona mensagem ofuscada ao log principal."""
        masked_msg = self._mask_tokens_in_text(msg)
        self.log_text.append(masked_msg)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)
        # Se a mensagem contiver palavras-chave, também notifica
        if any(k in masked_msg.lower() for k in ["cooldown", "mining_complete", "erro", "falhou"]):
            self._notify(masked_msg)

    def _load_initial_config(self):
        try:
            if os.path.exists(DEFAULT_QR):
                data = QRCodeJSONHandler.ler_qr_code(DEFAULT_QR) or {}
                if data:
                    self._apply_config(data)
            elif os.path.exists(DEFAULT_JSON):
                with open(DEFAULT_JSON, "r", encoding="utf-8") as f:
                    self._apply_config(json.load(f))
        except Exception as e:
            logging.warning(f"Falha ao pré-carregar config: {e}")

    # -------------------------------------------------------------------------
    # Tema
    # -------------------------------------------------------------------------
    def _restore_theme(self):
        theme = self.settings.value("theme", "Sistema")
        index = self.theme_combo.findText(theme) if hasattr(self, 'theme_combo') else -1
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        else:
            self._apply_theme(theme)

    def _change_theme(self, theme_name: str):
        self._apply_theme(theme_name)
        self.settings.setValue("theme", theme_name)

    def _apply_theme(self, theme_name: str):
        app = QApplication.instance()
        if theme_name == "Escuro":
            app.setStyle("Fusion")
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Highlight, QColor(142, 45, 197))
            palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
            app.setPalette(palette)
        elif theme_name == "Claro":
            app.setStyle("Fusion")
            app.setPalette(app.style().standardPalette())
        else:  # Sistema
            app.setStyle("Fusion")
            app.setPalette(app.style().standardPalette())


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DeltaGUI")
    app.setOrganizationName("DeltaProject")
    window = DeltaGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
