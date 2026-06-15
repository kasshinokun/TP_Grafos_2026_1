# Interface Gráfica CustomTkinter para o Projeto Delta v4c — REV B
# Novidades:
#   - Spinner (+/-) para "Anos de histórico" limitado de 1 a 5.
#   - Seletor de tema: Light / Dark / System.
#   - Menu suspenso no topo para navegar entre as telas:
#       1) Início     — fluxo de mineração (original)
#       2) Sobre      — informações do projeto + QR code do repositório
#       3) Grafos     — visualizador de arquivos .gexf em ./work/ (+ uploader)
# Release: 2026-06-15

import os
import sys
import json
import queue
import logging
import threading
import subprocess
from typing import List, Optional

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
except ImportError as e:
    raise SystemExit(
        "customtkinter não está instalado. Rode: pip install customtkinter pillow pyzbar qrcode networkx matplotlib"
    ) from e

# Dependências opcionais (apenas para telas auxiliares)
try:
    import qrcode
    from PIL import Image
except Exception:
    qrcode = None
    Image = None

try:
    import networkx as nx
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except Exception:
    nx = None
    plt = None
    FigureCanvasTkAgg = None

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

# Runner de grafos (integração opcional)
try:
    from grafos_runner import run_graphs
except Exception:
    run_graphs = None

# Validador de grafos (carregamento sob demanda)
try:
    from grafos.validate_loader import GraphValidateLoader
except Exception:
    try:
        from graph_validate_loader import GraphValidateLoader  # fallback
    except Exception:
        GraphValidateLoader = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_QR = os.path.join(APP_DIR, "meu_qrcode.png")
DEFAULT_JSON = os.path.join(APP_DIR, "data.json")
JSON_DIR = os.path.join(APP_DIR, "json")
WORK_DIR = os.path.join(APP_DIR, "work")
TEST_RUNNER = os.path.join(APP_DIR, "tests", "run_all.py")

# Metadados do projeto (tela "Sobre")
PROJECT_META = {
    "projeto": "Projeto Delta v4c — Mineração Híbrida GitHub",
    "faculdade": "Universidade XYZ — Faculdade de Computação",
    "graduacao": "Bacharelado em Ciência da Computação",
    "turma": "Engenharia de Software — Turma A",
    "semestre": "2026/1",
    "professor": "Prof. Dr. Fulano de Tal",
    "alunos": [
        "Aluno 1 — RA 00001",
        "Aluno 2 — RA 00002",
        "Aluno 3 — RA 00003",
        "Aluno 4 — RA 00004",
    ],
    "repo_url": "https://github.com/seu-usuario/projeto-delta",
}


# ==============================================================================
# Handler de logging que injeta mensagens numa queue thread-safe
# ==============================================================================
class QueueLogHandler(logging.Handler):
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord):
        try:
            self.log_queue.put_nowait(self.format(record))
        except queue.Full:
            pass


# ==============================================================================
# Janela principal
# ==============================================================================
class DeltaGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Projeto Delta v4c — Minerador GitHub (rev B)")
        self.geometry("1240x800")
        self.minsize(1000, 660)

        self.log_queue: queue.Queue = queue.Queue(maxsize=5000)
        self.notification_queue: queue.Queue = queue.Queue(maxsize=1000)
        self.worker_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        self._orchestrator_ref: Optional[Orchestrator] = None
        self._real_tokens: List[str] = []

        # Containers das telas (mostradas/escondidas pelo menu superior)
        self._views = {}
        self._current_view: Optional[str] = None
        # Referência ao canvas matplotlib na tela de grafos
        self._graph_canvas = None

        self._install_log_handler()
        self._build_topbar()
        self._build_views()
        self._show_view("inicio")
        self._poll_queues()

    # ---------------- logging ----------------
    def _install_log_handler(self):
        handler = QueueLogHandler(self.log_queue)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(threadName)s: %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)

    # ==========================================================================
    # TOPBAR — menu de navegação + tema
    # ==========================================================================
    def _build_topbar(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        topbar = ctk.CTkFrame(self, height=52, corner_radius=0)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(
            topbar, text="⛏ Projeto Delta",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=(16, 12), pady=10, sticky="w")

        # Dropdown de navegação entre telas
        self.nav_var = ctk.StringVar(value="Início")
        self.nav_menu = ctk.CTkOptionMenu(
            topbar,
            values=["Início", "Sobre", "Grafos"],
            variable=self.nav_var,
            width=160,
            command=self._on_nav_change,
        )
        self.nav_menu.grid(row=0, column=1, padx=(0, 12), pady=10, sticky="w")

        # Seletor de tema
        ctk.CTkLabel(topbar, text="Tema:").grid(row=0, column=3, padx=(0, 6), pady=10, sticky="e")
        self.theme_var = ctk.StringVar(value="System")
        self.theme_menu = ctk.CTkOptionMenu(
            topbar,
            values=["Light", "Dark", "System"],
            variable=self.theme_var,
            width=110,
            command=self._on_theme_change,
        )
        self.theme_menu.grid(row=0, column=4, padx=(0, 16), pady=10, sticky="e")

    def _on_nav_change(self, label: str):
        mapping = {"Início": "inicio", "Sobre": "sobre", "Grafos": "grafos"}
        key = mapping.get(label, "inicio")
        self._show_view(key)

    def _on_theme_change(self, mode: str):
        # CustomTkinter aceita "Light", "Dark", "System"
        ctk.set_appearance_mode(mode)
        self._notify(f"🎨 Tema alterado para: {mode}")

    def _show_view(self, name: str):
        for k, frame in self._views.items():
            frame.grid_remove()
        if name in self._views:
            self._views[name].grid(row=1, column=0, sticky="nsew")
            self._current_view = name
            if name == "grafos":
                self._refresh_graph_list()

    # ==========================================================================
    # Construção das três telas
    # ==========================================================================
    def _build_views(self):
        self._views["inicio"] = self._build_view_inicio()
        self._views["sobre"] = self._build_view_sobre()
        self._views["grafos"] = self._build_view_grafos()

    # --------------------------------------------------------------------------
    # TELA: INÍCIO (mineração)
    # --------------------------------------------------------------------------
    def _build_view_inicio(self) -> ctk.CTkFrame:
        container = ctk.CTkFrame(self, corner_radius=0)
        container.grid_columnconfigure(0, weight=0)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # Sidebar
        side = ctk.CTkScrollableFrame(container, width=380, corner_radius=0)
        side.grid(row=0, column=0, sticky="nsw")

        ctk.CTkLabel(
            side, text="Mineração híbrida GitHub",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(14, 14), padx=16, anchor="w")

        # --- Grupo: Alvo ---
        frame_target = ctk.CTkFrame(side, fg_color=("gray85", "gray15"))
        frame_target.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkLabel(frame_target, text="🎯 Alvo da Mineração",
                     font=ctk.CTkFont(weight="bold")).pack(padx=16, pady=(12, 8), anchor="w")

        ctk.CTkLabel(frame_target, text="Target user").pack(padx=16, pady=(0, 2), anchor="w")
        self.entry_user = ctk.CTkEntry(frame_target, placeholder_text="ex: torvalds")
        self.entry_user.pack(padx=16, pady=(0, 8), fill="x")

        ctk.CTkLabel(frame_target, text="Target repo").pack(padx=16, pady=(0, 2), anchor="w")
        self.entry_repo = ctk.CTkEntry(frame_target, placeholder_text="ex: linux")
        self.entry_repo.pack(padx=16, pady=(0, 8), fill="x")

        # ---- Anos de histórico: spinner 1..5 ----
        ctk.CTkLabel(frame_target, text="Anos de histórico (1–5)").pack(
            padx=16, pady=(0, 2), anchor="w"
        )
        years_row = ctk.CTkFrame(frame_target, fg_color="transparent")
        years_row.pack(padx=16, pady=(0, 12), fill="x")

        self.years_var = ctk.IntVar(value=5)
        ctk.CTkButton(
            years_row, text="−", width=40,
            command=lambda: self._step_years(-1),
        ).pack(side="left")

        self.entry_years = ctk.CTkEntry(
            years_row, width=70, justify="center",
        )
        self.entry_years.insert(0, "5")
        self.entry_years.configure(state="disabled")  # alterado apenas pelos botões
        self.entry_years.pack(side="left", padx=8)

        ctk.CTkButton(
            years_row, text="+", width=40,
            command=lambda: self._step_years(+1),
        ).pack(side="left")

        # --- Grupo: Tokens ---
        frame_tokens = ctk.CTkFrame(side, fg_color=("gray85", "gray15"))
        frame_tokens.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkLabel(frame_tokens, text="🔑 Tokens GitHub",
                     font=ctk.CTkFont(weight="bold")).pack(padx=16, pady=(12, 8), anchor="w")

        self.token_display = ctk.CTkTextbox(
            frame_tokens, height=90,
            font=ctk.CTkFont(family="Courier New", size=11), state="disabled",
        )
        self.token_display.pack(padx=16, pady=(0, 8), fill="x")

        token_input_row = ctk.CTkFrame(frame_tokens, fg_color="transparent")
        token_input_row.pack(padx=16, pady=(0, 12), fill="x")

        self.entry_new_token = ctk.CTkEntry(
            token_input_row, placeholder_text="Cole o token aqui (ghp_...)"
        )
        self.entry_new_token.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            token_input_row, text="➕ Add", width=60,
            fg_color="#16a34a", hover_color="#15803d",
            command=self._on_add_token,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            token_input_row, text="🗑️", width=40,
            fg_color="#dc2626", hover_color="#b91c1c",
            command=self._clear_tokens,
        ).pack(side="left")

        self.use_tokens_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            frame_tokens, text="Usar tokens (mineração rápida)",
            variable=self.use_tokens_var,
        ).pack(padx=16, pady=(0, 12), anchor="w")

        self.run_lapidador_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            frame_tokens, text="Rodar Lapidador ao terminar",
            variable=self.run_lapidador_var,
        ).pack(padx=16, pady=(0, 12), anchor="w")

        # --- Grupo: Arquivos ---
        frame_files = ctk.CTkFrame(side, fg_color="transparent")
        frame_files.pack(fill="x", padx=16, pady=(0, 16))

        row1 = ctk.CTkFrame(frame_files, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(row1, text="📂 Carregar QR", width=130,
                      command=self.on_load_qr).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row1, text="📂 Carregar JSON", width=130,
                      command=self.on_load_json).pack(side="left")

        row2 = ctk.CTkFrame(frame_files, fg_color="transparent")
        row2.pack(fill="x")
        ctk.CTkButton(row2, text="💾 Salvar JSON", width=130,
                      command=self.on_save_json).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row2, text="📱 Gerar QR", width=130,
                      command=self.on_generate_qr).pack(side="left")

        # --- Grupo: Ações principais ---
        frame_actions = ctk.CTkFrame(side, fg_color="transparent")
        frame_actions.pack(fill="x", padx=16, pady=(0, 16))

        self.btn_start = ctk.CTkButton(
            frame_actions, text="▶ Iniciar mineração",
            fg_color="#16a34a", hover_color="#15803d",
            font=ctk.CTkFont(weight="bold"),
            command=self.on_start, height=40,
        )
        self.btn_start.pack(fill="x", pady=(0, 8))

        self.btn_stop = ctk.CTkButton(
            frame_actions, text="■ Parar",
            fg_color="#dc2626", hover_color="#b91c1c",
            font=ctk.CTkFont(weight="bold"),
            state="disabled", command=self.on_stop, height=40,
        )
        self.btn_stop.pack(fill="x", pady=(0, 16))

        self.btn_post = ctk.CTkButton(
            frame_actions, text="📊 Pós-processar (Lapidador + Grafos)",
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=self.on_post_process,
        )
        self.btn_post.pack(fill="x", pady=(0, 8))

        self.btn_tests = ctk.CTkButton(
            frame_actions, text="🧪 Rodar Testes Unitários",
            fg_color="#7c3aed", hover_color="#6d28d9",
            command=self.on_run_tests,
        )
        self.btn_tests.pack(fill="x")

        self.status_lbl = ctk.CTkLabel(
            side, text="Status: ocioso",
            font=ctk.CTkFont(weight="bold"), text_color="gray",
        )
        self.status_lbl.pack(padx=16, pady=(20, 16), anchor="w")

        # ----- Área principal -----
        main = ctk.CTkFrame(container, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(0, weight=3)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        log_box = ctk.CTkFrame(main)
        log_box.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))
        log_box.grid_rowconfigure(1, weight=1)
        log_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(log_box, text="📜 Log da aplicação",
                     font=ctk.CTkFont(weight="bold", size=14)).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4))
        self.log_text = ctk.CTkTextbox(
            log_box, wrap="word", font=ctk.CTkFont(family="Courier New", size=12))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        notif_box = ctk.CTkFrame(main, fg_color=("gray85", "gray15"))
        notif_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))
        notif_box.grid_rowconfigure(1, weight=1)
        notif_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(notif_box, text="🔔 Notificações",
                     font=ctk.CTkFont(weight="bold", size=14)).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4))
        self.notif_text = ctk.CTkTextbox(
            notif_box, wrap="word",
            font=ctk.CTkFont(family="Courier New", size=12),
            fg_color=("gray80", "gray10"))
        self.notif_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        return container

    def _step_years(self, delta: int):
        """Incrementa/decrementa o campo de anos respeitando o intervalo [1, 5]."""
        try:
            current = int(self.entry_years.get())
        except ValueError:
            current = 5
        new = max(1, min(5, current + delta))
        self.entry_years.configure(state="normal")
        self.entry_years.delete(0, "end")
        self.entry_years.insert(0, str(new))
        self.entry_years.configure(state="disabled")
        self.years_var.set(new)

    # --------------------------------------------------------------------------
    # TELA: SOBRE
    # --------------------------------------------------------------------------
    def _build_view_sobre(self) -> ctk.CTkFrame:
        container = ctk.CTkScrollableFrame(self, corner_radius=0)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=0)

        # Coluna 1 — Informações
        info = ctk.CTkFrame(container, fg_color="transparent")
        info.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)

        ctk.CTkLabel(
            info, text="Sobre o Projeto",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w", pady=(0, 12))

        def field(label, value):
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", pady=4, anchor="w")
            ctk.CTkLabel(row, text=label, width=140, anchor="w",
                         font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(row, text=value, anchor="w", justify="left",
                         wraplength=560).pack(side="left", fill="x", expand=True)

        field("Projeto:", PROJECT_META["projeto"])
        field("Faculdade:", PROJECT_META["faculdade"])
        field("Graduação:", PROJECT_META["graduacao"])
        field("Turma:", PROJECT_META["turma"])
        field("Semestre:", PROJECT_META["semestre"])
        field("Professor:", PROJECT_META["professor"])

        ctk.CTkLabel(info, text="Alunos do grupo:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(12, 4))
        for a in PROJECT_META["alunos"]:
            ctk.CTkLabel(info, text=f"  • {a}", anchor="w").pack(anchor="w")

        ctk.CTkLabel(info, text="Repositório:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(12, 4))
        ctk.CTkLabel(info, text=PROJECT_META["repo_url"],
                     text_color="#3b82f6", anchor="w").pack(anchor="w")

        # Coluna 2 — QR code do repositório
        qr_frame = ctk.CTkFrame(container, fg_color=("gray85", "gray15"))
        qr_frame.grid(row=0, column=1, sticky="ne", padx=24, pady=24)

        ctk.CTkLabel(qr_frame, text="QR — Repositório",
                     font=ctk.CTkFont(weight="bold")).pack(padx=16, pady=(16, 8))

        qr_label = ctk.CTkLabel(qr_frame, text="")
        qr_label.pack(padx=16, pady=(0, 16))
        self._render_repo_qr(qr_label)

        return container

    def _render_repo_qr(self, label_widget):
        """Gera e exibe o QR code da URL do repositório."""
        if qrcode is None or Image is None:
            label_widget.configure(text="(instale 'qrcode' e 'pillow' para ver o QR)")
            return
        try:
            img = qrcode.make(PROJECT_META["repo_url"]).convert("RGB")
            img = img.resize((240, 240), Image.NEAREST)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(240, 240))
            label_widget.configure(image=ctk_img, text="")
            label_widget.image = ctk_img  # evita garbage collection
        except Exception as e:
            label_widget.configure(text=f"(falha ao gerar QR: {e})")

    # --------------------------------------------------------------------------
    # TELA: GRAFOS
    # --------------------------------------------------------------------------
    def _build_view_grafos(self) -> ctk.CTkFrame:
        container = ctk.CTkFrame(self, corner_radius=0)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(2, weight=1)

        # --- Linha 1: combobox + botão Carregar ---
        topo = ctk.CTkFrame(container, fg_color=("gray85", "gray15"))
        topo.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        topo.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(topo, text="Grafos em ./work/:",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=(12, 8), pady=12, sticky="w")

        self.gexf_combobox = ctk.CTkComboBox(topo, values=[], width=420)
        self.gexf_combobox.grid(row=0, column=1, padx=(0, 8), pady=12, sticky="ew")

        ctk.CTkButton(topo, text="🔄 Atualizar lista", width=140,
                      command=self._refresh_graph_list).grid(
            row=0, column=2, padx=4, pady=12)
        ctk.CTkButton(topo, text="📈 Carregar",
                      fg_color="#16a34a", hover_color="#15803d", width=120,
                      command=self._load_selected_gexf).grid(
            row=0, column=3, padx=(4, 12), pady=12)

        # --- Linha 2: file uploader manual ---
        upload = ctk.CTkFrame(container, fg_color=("gray85", "gray15"))
        upload.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        upload.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(upload, text="Arquivo .gexf:",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=(12, 8), pady=12, sticky="w")

        self.gexf_path_entry = ctk.CTkEntry(
            upload, placeholder_text="Caminho para um arquivo .gexf…")
        self.gexf_path_entry.grid(row=0, column=1, padx=(0, 8), pady=12, sticky="ew")

        ctk.CTkButton(upload, text="📂 Procurar…", width=140,
                      command=self._browse_gexf).grid(
            row=0, column=2, padx=4, pady=12)
        ctk.CTkButton(upload, text="📈 Carregar",
                      fg_color="#2563eb", hover_color="#1d4ed8", width=120,
                      command=self._load_uploaded_gexf).grid(
            row=0, column=3, padx=(4, 12), pady=12)

        # --- Linha 3: canvas do grafo ---
        self.graph_area = ctk.CTkFrame(container)
        self.graph_area.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.graph_area.grid_columnconfigure(0, weight=1)
        self.graph_area.grid_rowconfigure(0, weight=1)

        self.graph_status = ctk.CTkLabel(
            self.graph_area,
            text="Selecione um grafo na combobox ou envie um arquivo .gexf.",
            text_color="gray",
        )
        self.graph_status.grid(row=0, column=0, sticky="nsew")

        return container

    def _refresh_graph_list(self):
        files = []
        try:
            if os.path.isdir(WORK_DIR):
                files = sorted(
                    f for f in os.listdir(WORK_DIR) if f.lower().endswith(".gexf"))
        except Exception as e:
            logging.warning(f"Falha ao listar {WORK_DIR}: {e}")
        values = files if files else ["(nenhum .gexf encontrado em ./work/)"]
        self.gexf_combobox.configure(values=values)
        self.gexf_combobox.set(values[0])

    def _browse_gexf(self):
        path = filedialog.askopenfilename(
            title="Selecionar arquivo .gexf",
            initialdir=APP_DIR,
            filetypes=[("Graph Exchange XML", "*.gexf"), ("Todos", "*.*")],
        )
        if path:
            self.gexf_path_entry.delete(0, "end")
            self.gexf_path_entry.insert(0, path)

    def _load_selected_gexf(self):
        name = self.gexf_combobox.get().strip()
        if not name or name.startswith("("):
            messagebox.showinfo("Grafos", "Nenhum arquivo selecionado.")
            return
        path = os.path.join(WORK_DIR, name)
        self._render_gexf(path, validate=False)

    def _load_uploaded_gexf(self):
        path = self.gexf_path_entry.get().strip()
        if not path:
            messagebox.showinfo("Grafos", "Informe um caminho de arquivo .gexf.")
            return
        if not os.path.isfile(path):
            messagebox.showerror("Grafos", f"Arquivo inexistente:\n{path}")
            return
        self._render_gexf(path, validate=True)

    def _render_gexf(self, path: str, validate: bool):
        """Renderiza o .gexf no canvas embutido. Quando validate=True, usa GraphValidateLoader."""
        if nx is None or plt is None or FigureCanvasTkAgg is None:
            self.graph_status.configure(
                text="Instale 'networkx' e 'matplotlib' para visualizar grafos.")
            return
        try:
            if validate:
                if GraphValidateLoader is None:
                    self._notify("⚠ GraphValidateLoader indisponível — carregando sem validação.")
                    graph = nx.read_gexf(path)
                else:
                    loader = GraphValidateLoader(path)
                    graph = loader.load()  # contrato esperado: retorna grafo networkx
                    self._notify(f"✔ Grafo validado por GraphValidateLoader: {os.path.basename(path)}")
            else:
                graph = nx.read_gexf(path)

            # Limpa canvas anterior
            for w in self.graph_area.winfo_children():
                w.destroy()
            self._graph_canvas = None

            fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
            if graph.number_of_nodes() == 0:
                ax.text(0.5, 0.5, "Grafo vazio", ha="center", va="center")
            else:
                pos = nx.spring_layout(graph, seed=42)
                nx.draw_networkx_nodes(graph, pos, ax=ax, node_size=120,
                                       node_color="#3b82f6", alpha=0.85)
                nx.draw_networkx_edges(graph, pos, ax=ax, edge_color="#64748b",
                                       alpha=0.5, width=0.8)
                if graph.number_of_nodes() <= 80:
                    nx.draw_networkx_labels(graph, pos, ax=ax, font_size=8)
            ax.set_axis_off()
            ax.set_title(
                f"{os.path.basename(path)}  "
                f"(|V|={graph.number_of_nodes()}, |E|={graph.number_of_edges()})",
                fontsize=11)

            canvas = FigureCanvasTkAgg(fig, master=self.graph_area)
            canvas.draw()
            widget = canvas.get_tk_widget()
            widget.grid(row=0, column=0, sticky="nsew")
            self._graph_canvas = canvas
            self._notify(f"📈 Grafo carregado: {os.path.basename(path)}")
        except Exception as e:
            logging.error(f"Falha ao carregar grafo: {e}", exc_info=True)
            messagebox.showerror("Grafos", f"Falha ao carregar/validar o grafo:\n{e}")

    # ==========================================================================
    # Token Management
    # ==========================================================================
    def _mask_token(self, token: str) -> str:
        clean_token = token.strip()
        if len(clean_token) >= 4:
            return f"|---------------> Token ...{clean_token[-4:]}"
        return f"|---------------> Token ...{clean_token}"

    def _update_token_display(self):
        self.token_display.configure(state="normal")
        self.token_display.delete("1.0", "end")
        for t in self._real_tokens:
            self.token_display.insert("end", self._mask_token(t) + "\n")
        self.token_display.configure(state="disabled")

    def _on_add_token(self):
        raw_input = self.entry_new_token.get().strip()
        if not raw_input:
            return
        new_tokens = [t.strip() for t in raw_input.replace(',', '\n').split() if t.strip()]
        added_count = 0
        for t in new_tokens:
            if t not in self._real_tokens:
                self._real_tokens.append(t)
                added_count += 1
        self.entry_new_token.delete(0, "end")
        self._update_token_display()
        if added_count > 0:
            self._notify(f"✅ {added_count} token(s) adicionado(s).")
        else:
            self._notify("ℹ️ Tokens já existentes ou inválidos.")

    def _clear_tokens(self):
        self._real_tokens.clear()
        self._update_token_display()
        self._notify("🗑️ Lista de tokens limpa.")

    # ==========================================================================
    # Handlers de arquivos / execução
    # ==========================================================================
    def on_load_qr(self):
        path = filedialog.askopenfilename(
            title="Selecionar QR Code", initialdir=APP_DIR,
            filetypes=[("Imagens", "*.png *.jpg *.jpeg"), ("Todos", "*.*")])
        if not path:
            return
        try:
            data = QRCodeJSONHandler.ler_qr_code(path) or {}
            self._apply_config(data)
            self._notify(f"QR Code carregado: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Erro QR", str(e))

    def on_load_json(self):
        path = filedialog.askopenfilename(
            title="Selecionar data.json", initialdir=APP_DIR,
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._apply_config(data)
            self._notify(f"JSON carregado: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Erro JSON", str(e))

    def on_save_json(self):
        data = self._collect_config()
        path = filedialog.asksaveasfilename(
            title="Salvar configuração", initialdir=APP_DIR,
            defaultextension=".json", initialfile="data.json",
            filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._notify(f"JSON salvo em {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    def on_generate_qr(self):
        data = self._collect_config()
        path = filedialog.asksaveasfilename(
            title="Gerar QR Code", initialdir=APP_DIR,
            defaultextension=".png", initialfile="meu_qrcode.png",
            filetypes=[("PNG", "*.png")])
        if not path:
            return
        try:
            QRCodeJSONHandler.gerar_qr_code(data, path)
            self._notify(f"QR Code gerado em {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Erro QR", str(e))

    def on_start(self):
        cfg = self._collect_config()
        if not cfg["target_user"] or not cfg["target_repo"]:
            messagebox.showerror("Erro", "Informe target_user e target_repo.")
            return
        try:
            years = int(self.entry_years.get().strip() or "5")
            if not (1 <= years <= 5):
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Anos deve estar entre 1 e 5.")
            return

        use_tokens = self.use_tokens_var.get()
        tokens = cfg["token"] if use_tokens else []

        self.shutdown_event.clear()
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.status_lbl.configure(text="Status: minerando…", text_color="#16a34a")

        self.worker_thread = threading.Thread(
            target=self._run_mining,
            args=(tokens, cfg["target_user"], cfg["target_repo"], years, use_tokens),
            daemon=True, name="GUI-MiningWorker")
        self.worker_thread.start()

    def on_stop(self):
        if self._orchestrator_ref is not None:
            try:
                self._orchestrator_ref.shutdown_mgr.request_shutdown()
            except Exception:
                pass
        self.shutdown_event.set()
        self._notify("⏹ Parada solicitada — aguardando finalização.")
        self.status_lbl.configure(text="Status: parando…", text_color="#f59e0b")

    def on_post_process(self):
        if not os.path.isdir(JSON_DIR):
            messagebox.showwarning(
                "Sem dados",
                f"Pasta ./json/ não encontrada em:\n{JSON_DIR}")
            return
        self.btn_post.configure(state="disabled")
        self.status_lbl.configure(text="Status: pós-processando…", text_color="#2563eb")
        threading.Thread(target=self._run_post_process, daemon=True,
                         name="GUI-PostProc").start()

    def on_run_tests(self):
        if not os.path.isfile(TEST_RUNNER):
            messagebox.showwarning("Suíte não encontrada",
                                   f"Arquivo não localizado:\n{TEST_RUNNER}")
            return
        self.btn_tests.configure(state="disabled")
        self.status_lbl.configure(text="Status: testando…", text_color="#7c3aed")
        threading.Thread(target=self._run_tests_subprocess, daemon=True,
                         name="GUI-Tests").start()

    # ==========================================================================
    # Workers
    # ==========================================================================
    def _run_mining(self, tokens, user, repo, years, use_tokens):
        try:
            if use_tokens:
                if not tokens:
                    self._notify("⚠ Sem tokens — alternando para SEM TOKEN.")
                    untokenized_runner(target_user=user, target_repo=repo, years_back=years)
                else:
                    valid = TokenCertifier.validate_tokens(tokens)
                    if not valid:
                        self._notify("⚠ Nenhum token válido — alternando para SEM TOKEN.")
                        untokenized_runner(target_user=user, target_repo=repo, years_back=years)
                    else:
                        app = Orchestrator(tokens=valid, target_user=user,
                                           target_repo=repo, years_back=years)
                        self._orchestrator_ref = app
                        app.start()
            else:
                untokenized_runner(target_user=user, target_repo=repo, years_back=years)
            self._notify("✅ Mineração finalizada.")
        except Exception as e:
            logging.error(f"Erro na mineração: {e}", exc_info=True)
            self._notify(f"❌ Erro: {e}")
        finally:
            self._orchestrator_ref = None
            if self.run_lapidador_var.get():
                self._safe_run_lapidador()
                self._safe_run_graphs()
            self.after(0, self._reset_buttons)

    def _run_post_process(self):
        try:
            self._notify("📊 Iniciando pós-processamento de ./json/ …")
            self._safe_run_lapidador()
            self._safe_run_graphs()
            self._notify("✅ Pós-processamento concluído.")
        except Exception as e:
            logging.error(f"Erro no pós-processamento: {e}", exc_info=True)
            self._notify(f"❌ Erro pós-processamento: {e}")
        finally:
            self.after(0, lambda: (
                self.btn_post.configure(state="normal"),
                self.status_lbl.configure(text="Status: ocioso", text_color="gray")))

    def _safe_run_lapidador(self):
        if init_lapidador is None:
            self._notify("ℹ Lapidador não disponível — pulando.")
            return
        try:
            self._notify("🪨 Executando Lapidador…")
            init_lapidador()
            self._notify("🪨 Lapidador finalizado.")
        except Exception as e:
            logging.error(f"Lapidador falhou: {e}", exc_info=True)
            self._notify(f"❌ Lapidador falhou: {e}")

    def _safe_run_graphs(self):
        if run_graphs is None:
            self._notify("ℹ grafos_runner não disponível — pulando.")
            return
        try:
            self._notify("🕸 Construindo grafos a partir de ./json/ …")
            summary = run_graphs(JSON_DIR)
            self._notify(f"🕸 Grafos: {summary}")
        except Exception as e:
            logging.error(f"grafos_runner falhou: {e}", exc_info=True)
            self._notify(f"❌ Grafos falhou: {e}")

    def _run_tests_subprocess(self):
        try:
            self._notify(f"🧪 Executando suíte: {TEST_RUNNER}")
            proc = subprocess.Popen(
                [sys.executable, TEST_RUNNER], cwd=APP_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1)
            assert proc.stdout is not None
            for line in proc.stdout:
                logging.info(line.rstrip())
            rc = proc.wait()
            self._notify(f"🧪 Testes finalizados (exit={rc}).")
        except Exception as e:
            logging.error(f"Erro ao rodar testes: {e}", exc_info=True)
            self._notify(f"❌ Erro nos testes: {e}")
        finally:
            self.after(0, lambda: (
                self.btn_tests.configure(state="normal"),
                self.status_lbl.configure(text="Status: ocioso", text_color="gray")))

    def _reset_buttons(self):
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_lbl.configure(text="Status: ocioso", text_color="gray")

    # ==========================================================================
    # Helpers
    # ==========================================================================
    def _collect_config(self) -> dict:
        return {
            "token": self._real_tokens,
            "target_user": self.entry_user.get().strip(),
            "target_repo": self.entry_repo.get().strip(),
        }

    def _apply_config(self, data: dict):
        tokens = data.get("token", [])
        if isinstance(tokens, str):
            tokens = [tokens]
        self._real_tokens = [str(t).strip() for t in tokens if str(t).strip()]
        self._update_token_display()
        self.entry_user.delete(0, "end")
        self.entry_user.insert(0, data.get("target_user", ""))
        self.entry_repo.delete(0, "end")
        self.entry_repo.insert(0, data.get("target_repo", ""))

    def _notify(self, msg: str):
        try:
            self.notification_queue.put_nowait(msg)
        except queue.Full:
            pass

    # ==========================================================================
    # Polling
    # ==========================================================================
    def _poll_queues(self):
        drained = 0
        while drained < 200:
            try:
                msg = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            if "COOLDOWN" in msg or "MINING_COMPLETE" in msg or "cooldown" in msg.lower():
                self._notify(msg)
            drained += 1

        drained = 0
        while drained < 100:
            try:
                note = self.notification_queue.get_nowait()
            except queue.Empty:
                break
            self.notif_text.insert("end", note + "\n")
            self.notif_text.see("end")
            drained += 1

        self.after(120, self._poll_queues)


def main():
    app = DeltaGUI()
    try:
        if os.path.exists(DEFAULT_QR):
            data = QRCodeJSONHandler.ler_qr_code(DEFAULT_QR) or {}
            if data:
                app._apply_config(data)
        elif os.path.exists(DEFAULT_JSON):
            with open(DEFAULT_JSON, "r", encoding="utf-8") as f:
                app._apply_config(json.load(f))
    except Exception as e:
        logging.warning(f"Falha ao pré-carregar config: {e}")
    app.mainloop()


if __name__ == "__main__":
    main()
