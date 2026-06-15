# Interface Gráfica CustomTkinter para o Projeto Delta v4c — REV B (Multitela + Grafos)
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
        "customtkinter não está instalado. Rode: pip install customtkinter pillow pyzbar qrcode"
    ) from e

# Bibliotecas para exibição de grafos
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
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

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_QR = os.path.join(APP_DIR, "meu_qrcode.png")
DEFAULT_JSON = os.path.join(APP_DIR, "data.json")
JSON_DIR = os.path.join(APP_DIR, "json")
TEST_RUNNER = os.path.join(APP_DIR, "test_cli", "run_all.py")
WORK_DIR = os.path.join(APP_DIR, "work")          # pasta onde ficam os .gexf
REPO_URL = "https://github.com/seu-usuario/projeto-delta"   # URL do repositório (substituir pela real)


# ==============================================================================
# Classe para validação de arquivos .gexf
# ==============================================================================
class GraphValidateLoader:
    """Valida e carrega um grafo a partir de um arquivo .gexf."""

    @staticmethod
    def validate(file_path: str) -> Optional[nx.Graph]:
        """Retorna o grafo se válido, None em caso de erro."""
        if not os.path.isfile(file_path):
            return None
        try:
            if nx is None:
                raise ImportError("NetworkX não instalado.")
            G = nx.read_gexf(file_path)
            return G
        except Exception as e:
            logging.error(f"Erro ao validar/carregar {file_path}: {e}")
            return None


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
# Tela de Mineração (conteúdo original)
# ==============================================================================
class MiningFrame(ctk.CTkFrame):
    def __init__(self, parent, log_queue: queue.Queue, notif_queue: queue.Queue):
        super().__init__(parent)
        self.log_queue = log_queue
        self.notification_queue = notif_queue
        self.worker_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        self._orchestrator_ref: Optional[Orchestrator] = None
        self._real_tokens: List[str] = []

        self._build_layout()
        self._poll_queues()

    # ------------------ Layout ------------------
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar com rolagem
        side = ctk.CTkScrollableFrame(self, width=360, corner_radius=0)
        side.grid(row=0, column=0, sticky="nsw")

        ctk.CTkLabel(
            side, text="⛏ Projeto Delta",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(16, 4), padx=16, anchor="w")
        ctk.CTkLabel(side, text="Mineração híbrida GitHub", text_color="gray").pack(
            padx=16, pady=(0, 20), anchor="w"
        )

        # --- Alvo ---
        frame_target = ctk.CTkFrame(side, fg_color=("gray20", "gray15"))
        frame_target.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(frame_target, text="🎯 Alvo da Mineração", font=ctk.CTkFont(weight="bold")).pack(
            padx=16, pady=(12, 8), anchor="w"
        )
        ctk.CTkLabel(frame_target, text="Target user").pack(padx=16, pady=(0, 2), anchor="w")
        self.entry_user = ctk.CTkEntry(frame_target, placeholder_text="ex: torvalds")
        self.entry_user.pack(padx=16, pady=(0, 8), fill="x")

        ctk.CTkLabel(frame_target, text="Target repo").pack(padx=16, pady=(0, 2), anchor="w")
        self.entry_repo = ctk.CTkEntry(frame_target, placeholder_text="ex: linux")
        self.entry_repo.pack(padx=16, pady=(0, 8), fill="x")

        # Campo de anos com botões +1 / -1
        frame_years = ctk.CTkFrame(frame_target, fg_color="transparent")
        frame_years.pack(padx=16, pady=(0, 12), fill="x")
        ctk.CTkLabel(frame_years, text="Anos de histórico", anchor="w").pack(side="left", padx=(0, 10))
        self.entry_years = ctk.CTkEntry(frame_years, width=70)
        self.entry_years.insert(0, "5")
        self.entry_years.pack(side="left", padx=(0, 8))
        self.btn_year_minus = ctk.CTkButton(frame_years, text="-1", width=30, command=self._dec_years)
        self.btn_year_minus.pack(side="left", padx=2)
        self.btn_year_plus = ctk.CTkButton(frame_years, text="+1", width=30, command=self._inc_years)
        self.btn_year_plus.pack(side="left", padx=2)

        # --- Tokens ---
        frame_tokens = ctk.CTkFrame(side, fg_color=("gray20", "gray15"))
        frame_tokens.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(frame_tokens, text="🔑 Tokens GitHub", font=ctk.CTkFont(weight="bold")).pack(
            padx=16, pady=(12, 8), anchor="w"
        )
        self.token_display = ctk.CTkTextbox(
            frame_tokens, height=90, font=ctk.CTkFont(family="Courier New", size=11), state="disabled"
        )
        self.token_display.pack(padx=16, pady=(0, 8), fill="x")

        token_input_row = ctk.CTkFrame(frame_tokens, fg_color="transparent")
        token_input_row.pack(padx=16, pady=(0, 12), fill="x")
        self.entry_new_token = ctk.CTkEntry(token_input_row, placeholder_text="Cole o token aqui (ghp_...)")
        self.entry_new_token.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(token_input_row, text="➕ Add", width=60, fg_color="#16a34a",
                      command=self._on_add_token).pack(side="left", padx=(0, 4))
        ctk.CTkButton(token_input_row, text="🗑️", width=40, fg_color="#dc2626",
                      command=self._clear_tokens).pack(side="left")

        self.use_tokens_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(frame_tokens, text="Usar tokens (mineração rápida)",
                        variable=self.use_tokens_var).pack(padx=16, pady=(0, 12), anchor="w")
        self.run_lapidador_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(frame_tokens, text="Rodar Lapidador ao terminar",
                        variable=self.run_lapidador_var).pack(padx=16, pady=(0, 12), anchor="w")

        # --- Arquivos ---
        frame_files = ctk.CTkFrame(side, fg_color="transparent")
        frame_files.pack(fill="x", padx=16, pady=(0, 16))
        row1 = ctk.CTkFrame(frame_files, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(row1, text="📂 Carregar QR", width=110, command=self.on_load_qr).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row1, text="📂 Carregar JSON", width=110, command=self.on_load_json).pack(side="left")
        row2 = ctk.CTkFrame(frame_files, fg_color="transparent")
        row2.pack(fill="x")
        ctk.CTkButton(row2, text="💾 Salvar JSON", width=110, command=self.on_save_json).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row2, text="📱 Gerar QR", width=110, command=self.on_generate_qr).pack(side="left")

        # --- Ações ---
        frame_actions = ctk.CTkFrame(side, fg_color="transparent")
        frame_actions.pack(fill="x", padx=16, pady=(0, 16))
        self.btn_start = ctk.CTkButton(frame_actions, text="▶ Iniciar mineração", fg_color="#16a34a",
                                       command=self.on_start, height=40)
        self.btn_start.pack(fill="x", pady=(0, 8))
        self.btn_stop = ctk.CTkButton(frame_actions, text="■ Parar", fg_color="#dc2626", state="disabled",
                                      command=self.on_stop, height=40)
        self.btn_stop.pack(fill="x", pady=(0, 16))
        self.btn_post = ctk.CTkButton(frame_actions, text="📊 Pós-processar (Lapidador + Grafos)",
                                      fg_color="#2563eb", command=self.on_post_process)
        self.btn_post.pack(fill="x", pady=(0, 8))
        self.btn_tests = ctk.CTkButton(frame_actions, text="🧪 Rodar Testes Unitários", fg_color="#7c3aed",
                                       command=self.on_run_tests)
        self.btn_tests.pack(fill="x")

        self.status_lbl = ctk.CTkLabel(side, text="Status: ocioso", font=ctk.CTkFont(weight="bold"), text_color="gray")
        self.status_lbl.pack(padx=16, pady=(20, 16), anchor="w")

        # --- Área principal (Log e Notificações) ---
        main = ctk.CTkFrame(self, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(0, weight=3)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        log_box = ctk.CTkFrame(main)
        log_box.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))
        log_box.grid_rowconfigure(1, weight=1)
        log_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(log_box, text="📜 Log da aplicação", font=ctk.CTkFont(weight="bold", size=14)).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )
        self.log_text = ctk.CTkTextbox(log_box, wrap="word", font=ctk.CTkFont(family="Courier New", size=12))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        notif_box = ctk.CTkFrame(main, fg_color=("gray20", "gray15"))
        notif_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))
        notif_box.grid_rowconfigure(1, weight=1)
        notif_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(notif_box, text="🔔 Notificações", font=ctk.CTkFont(weight="bold", size=14)).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )
        self.notif_text = ctk.CTkTextbox(notif_box, wrap="word", font=ctk.CTkFont(family="Courier New", size=12),
                                         fg_color=("gray10", "gray5"))
        self.notif_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    # ------------------ Anos (+1 / -1) ------------------
    def _inc_years(self):
        try:
            val = int(self.entry_years.get())
        except:
            val = 3
        new_val = min(5, val + 1)
        self.entry_years.delete(0, "end")
        self.entry_years.insert(0, str(new_val))

    def _dec_years(self):
        try:
            val = int(self.entry_years.get())
        except:
            val = 3
        new_val = max(1, val - 1)
        self.entry_years.delete(0, "end")
        self.entry_years.insert(0, str(new_val))

    # ------------------ Token Management ------------------
    def _mask_token(self, token: str) -> str:
        clean = token.strip()
        if len(clean) >= 4:
            return f"|---------------> Token ...{clean[-4:]}"
        return f"|---------------> Token ...{clean}"

    def _update_token_display(self):
        self.token_display.configure(state="normal")
        self.token_display.delete("1.0", "end")
        for t in self._real_tokens:
            self.token_display.insert("end", self._mask_token(t) + "\n")
        self.token_display.configure(state="disabled")

    def _on_add_token(self):
        raw = self.entry_new_token.get().strip()
        if not raw:
            return
        new_tokens = [t.strip() for t in raw.replace(',', '\n').split() if t.strip()]
        added = 0
        for t in new_tokens:
            if t not in self._real_tokens:
                self._real_tokens.append(t)
                added += 1
        self.entry_new_token.delete(0, "end")
        self._update_token_display()
        self._notify(f"✅ {added} token(s) adicionado(s).")

    def _clear_tokens(self):
        self._real_tokens.clear()
        self._update_token_display()
        self._notify("🗑️ Lista de tokens limpa.")

    # ------------------ Handlers ------------------
    def on_load_qr(self):
        path = filedialog.askopenfilename(title="Selecionar QR Code", initialdir=APP_DIR,
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
        path = filedialog.askopenfilename(title="Selecionar data.json", initialdir=APP_DIR,
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
        path = filedialog.asksaveasfilename(title="Salvar configuração", initialdir=APP_DIR,
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
        path = filedialog.asksaveasfilename(title="Gerar QR Code", initialdir=APP_DIR,
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
            messagebox.showerror("Erro", "Anos deve ser inteiro entre 1 e 5.")
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
            daemon=True, name="GUI-MiningWorker",
        )
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
            messagebox.showwarning("Sem dados", f"Pasta ./json/ não encontrada em:\n{JSON_DIR}")
            return
        self.btn_post.configure(state="disabled")
        self.status_lbl.configure(text="Status: pós-processando…", text_color="#2563eb")
        threading.Thread(target=self._run_post_process, daemon=True, name="GUI-PostProc").start()

    def on_run_tests(self):
        if not os.path.isfile(TEST_RUNNER):
            messagebox.showwarning("Suíte não encontrada", f"Arquivo não localizado:\n{TEST_RUNNER}")
            return
        self.btn_tests.configure(state="disabled")
        self.status_lbl.configure(text="Status: testando…", text_color="#7c3aed")
        threading.Thread(target=self._run_tests_subprocess, daemon=True, name="GUI-Tests").start()

    # ------------------ Workers ------------------
    def _run_mining(self, tokens, user, repo, years, use_tokens):
        try:
            if use_tokens:
                if not tokens:
                    self._notify("⚠ Sem tokens — alternando para modo SEM TOKEN.")
                    untokenized_runner(target_user=user, target_repo=repo, years_back=years)
                else:
                    valid = TokenCertifier.validate_tokens(tokens)
                    if not valid:
                        self._notify("⚠ Nenhum token válido — alternando para SEM TOKEN.")
                        untokenized_runner(target_user=user, target_repo=repo, years_back=years)
                    else:
                        app = Orchestrator(tokens=valid, target_user=user, target_repo=repo, years_back=years)
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
                self.status_lbl.configure(text="Status: ocioso", text_color="gray")
            ))

    def _safe_run_lapidador(self):
        if init_lapidador is None:
            self._notify("ℹ Lapidador (main_rebuild) não disponível — pulando.")
            return
        try:
            self._notify("🪨 Executando Lapidador (main_rebuild.main) …")
            init_lapidador()
            self._notify("🪨 Lapidador finalizado.")
        except Exception as e:
            logging.error(f"Lapidador falhou: {e}", exc_info=True)
            self._notify(f"❌ Lapidador falhou: {e}")

    def _safe_run_graphs(self):
        if run_graphs is None:
            self._notify("ℹ grafos_runner não disponível — pulando módulo de grafos.")
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
                [sys.executable, TEST_RUNNER],
                cwd=APP_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
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
                self.status_lbl.configure(text="Status: ocioso", text_color="gray")
            ))

    def _reset_buttons(self):
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_lbl.configure(text="Status: ocioso", text_color="gray")

    # ------------------ Helpers e polling ------------------
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


# ==============================================================================
# Tela Sobre
# ==============================================================================
class AboutFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._build_layout()

    def _build_layout(self):
        # Dados institucionais
        info = (
            "Projeto Delta v4c\n\n"
            "Faculdade: Exemplo de Faculdade\n"
            "Alunos: Aluno A, Aluno B, Aluno C\n"
            "Professor: Prof. Orientador\n"
            "Turma: Engenharia de Software\n"
            "Graduação: Ciência da Computação\n"
            "Semestre: 2026/1\n"
        )
        lbl_info = ctk.CTkLabel(self, text=info, justify="left", font=ctk.CTkFont(size=14))
        lbl_info.pack(pady=(30, 20), padx=40, anchor="w")

        # QR Code com a URL do repositório
        qr_img = None
        try:
            qr_img = QRCodeJSONHandler.gerar_qr_code(REPO_URL, None)  # retorna imagem PIL
            if qr_img:
                from PIL import ImageTk
                qr_tk = ImageTk.PhotoImage(qr_img)
                lbl_qr = ctk.CTkLabel(self, image=qr_tk, text="")
                lbl_qr.image = qr_tk
                lbl_qr.pack(pady=20)
        except Exception as e:
            lbl_err = ctk.CTkLabel(self, text=f"Falha ao gerar QR Code:\n{e}", text_color="red")
            lbl_err.pack(pady=20)

        ctk.CTkLabel(self, text=f"Repositório: {REPO_URL}", wraplength=500).pack(pady=10)


# ==============================================================================
# Tela de Visualização de Grafos
# ==============================================================================
class GraphFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.current_graph = None
        self.canvas = None   # matplotlib canvas
        self._build_layout()
        self._refresh_gexf_list()

    def _build_layout(self):
        # Topo: seleção de arquivo da pasta work
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(top_frame, text="Grafos disponíveis (work/):").pack(side="left", padx=(0, 10))
        self.combo_gexf = ctk.CTkComboBox(top_frame, values=[], width=300)
        self.combo_gexf.pack(side="left", padx=(0, 10))
        btn_load_combo = ctk.CTkButton(top_frame, text="Carregar", width=80, command=self._load_selected_gexf)
        btn_load_combo.pack(side="left")

        # Upload personalizado
        upload_frame = ctk.CTkFrame(self, fg_color="transparent")
        upload_frame.pack(fill="x", padx=20, pady=(10, 20))
        ctk.CTkLabel(upload_frame, text="Ou escolha um arquivo .gexf:").pack(side="left", padx=(0, 10))
        self.entry_custom = ctk.CTkEntry(upload_frame, placeholder_text="Caminho do arquivo .gexf", width=400)
        self.entry_custom.pack(side="left", padx=(0, 10))
        btn_browse = ctk.CTkButton(upload_frame, text="📂 Procurar", width=80, command=self._browse_gexf)
        btn_browse.pack(side="left", padx=(0, 10))
        btn_load_custom = ctk.CTkButton(upload_frame, text="Carregar", width=80, command=self._load_custom_gexf)
        btn_load_custom.pack(side="left")

        # Área para exibir o grafo (matplotlib)
        self.graph_container = ctk.CTkFrame(self)
        self.graph_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self, text="Nenhum grafo carregado.", text_color="gray")
        self.status_label.pack(pady=10)

    def _refresh_gexf_list(self):
        """Atualiza combobox com arquivos .gexf encontrados em WORK_DIR."""
        if not os.path.isdir(WORK_DIR):
            self.combo_gexf.configure(values=["Pasta work/ não encontrada"])
            return
        files = [f for f in os.listdir(WORK_DIR) if f.endswith('.gexf')]
        if not files:
            self.combo_gexf.configure(values=["Nenhum .gexf encontrado"])
        else:
            self.combo_gexf.configure(values=files)

    def _browse_gexf(self):
        path = filedialog.askopenfilename(title="Selecionar arquivo .gexf",
                                          filetypes=[("GEXF", "*.gexf"), ("Todos", "*.*")])
        if path:
            self.entry_custom.delete(0, "end")
            self.entry_custom.insert(0, path)

    def _load_selected_gexf(self):
        selected = self.combo_gexf.get()
        if not selected or selected.startswith("Nenhum") or selected.startswith("Pasta"):
            self.status_label.configure(text="Nenhum arquivo válido selecionado.", text_color="orange")
            return
        full_path = os.path.join(WORK_DIR, selected)
        self._load_graph(full_path)

    def _load_custom_gexf(self):
        path = self.entry_custom.get().strip()
        if not path:
            self.status_label.configure(text="Informe o caminho do arquivo .gexf", text_color="orange")
            return
        self._load_graph(path)

    def _load_graph(self, file_path: str):
        if not MATPLOTLIB_AVAILABLE:
            self.status_label.configure(text="Matplotlib ou NetworkX não instalados. Instale com: pip install matplotlib networkx", text_color="red")
            return
        G = GraphValidateLoader.validate(file_path)
        if G is None:
            self.status_label.configure(text=f"Falha ao carregar/validar: {file_path}", text_color="red")
            return
        self.current_graph = G
        self.status_label.configure(text=f"Grafo carregado: {os.path.basename(file_path)} | Nós: {G.number_of_nodes()} | Arestas: {G.number_of_edges()}", text_color="green")
        self._display_graph(G)

    def _display_graph(self, G: nx.Graph):
        # Limpa container anterior
        for widget in self.graph_container.winfo_children():
            widget.destroy()

        # Cria figura matplotlib
        fig, ax = plt.subplots(figsize=(6, 5), dpi=100)
        pos = nx.spring_layout(G, seed=42, k=0.3)   # layout para visualização
        nx.draw(G, pos, ax=ax, with_labels=False, node_size=30, font_size=8, alpha=0.7)
        # Se o grafo for pequeno, mostra rótulos
        if G.number_of_nodes() < 50:
            nx.draw_networkx_labels(G, pos, ax=ax, font_size=8)
        ax.set_title(f"Grafo - {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")

        # Embed no tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.graph_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas = canvas


# ==============================================================================
# Janela principal com menu superior e troca de telas
# ==============================================================================
class DeltaGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Projeto Delta v4c — Minerador GitHub (rev B)")
        self.geometry("1180x760")
        self.minsize(960, 620)

        # Filas de logging (compartilhadas)
        self.log_queue: queue.Queue = queue.Queue(maxsize=5000)
        self.notification_queue: queue.Queue = queue.Queue(maxsize=1000)
        self._install_log_handler()

        # Top bar com seletor de tema e navegação
        top_bar = ctk.CTkFrame(self, height=50, corner_radius=0)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        # Dropdown de tema
        theme_var = ctk.StringVar(value="System")
        theme_menu = ctk.CTkOptionMenu(top_bar, values=["System", "Dark", "Light"],
                                       variable=theme_var, command=self._change_theme,
                                       width=120)
        theme_menu.pack(side="right", padx=20)

        # Seletor de telas (Mineração, Sobre, Grafos)
        self.view_selector = ctk.CTkSegmentedButton(top_bar, values=["Mineração", "Sobre", "Grafos"],
                                                    command=self._show_frame)
        self.view_selector.pack(side="left", padx=20, pady=10)

        # Container para os frames dinâmicos
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True)

        # Cria as três telas
        self.mining_frame = MiningFrame(self.content_frame, self.log_queue, self.notification_queue)
        self.about_frame = AboutFrame(self.content_frame)
        self.graph_frame = GraphFrame(self.content_frame)

        # Empilha todos (mesmo que invisíveis)
        self.mining_frame.place(relwidth=1, relheight=1)
        self.about_frame.place(relwidth=1, relheight=1)
        self.graph_frame.place(relwidth=1, relheight=1)

        # Exibe a tela inicial (Mineração)
        self._show_frame("Mineração")

        # Pré-carrega configuração se houver QR/JSON padrão
        self._preload_config()

    def _install_log_handler(self):
        handler = QueueLogHandler(self.log_queue)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(threadName)s: %(message)s", datefmt="%H:%M:%S"
        ))
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)

    def _change_theme(self, choice: str):
        ctk.set_appearance_mode(choice)

    def _show_frame(self, frame_name: str):
        """Levanta o frame selecionado e ajusta o estado do seletor."""
        self.view_selector.set(frame_name)
        if frame_name == "Mineração":
            self.mining_frame.tkraise()
        elif frame_name == "Sobre":
            self.about_frame.tkraise()
        elif frame_name == "Grafos":
            # Atualiza lista de .gexf sempre que a tela for mostrada
            self.graph_frame._refresh_gexf_list()
            self.graph_frame.tkraise()

    def _preload_config(self):
        """Carrega QR/JSON padrão na tela de mineração, se existir."""
        try:
            if os.path.exists(DEFAULT_QR):
                data = QRCodeJSONHandler.ler_qr_code(DEFAULT_QR) or {}
                if data:
                    self.mining_frame._apply_config(data)
            elif os.path.exists(DEFAULT_JSON):
                with open(DEFAULT_JSON, "r", encoding="utf-8") as f:
                    self.mining_frame._apply_config(json.load(f))
        except Exception as e:
            logging.warning(f"Falha ao pré-carregar config: {e}")


def main():
    app = DeltaGUI()
    app.mainloop()


if __name__ == "__main__":
    main()