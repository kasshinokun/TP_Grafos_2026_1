# Interface Gráfica CustomTkinter para o Projeto Delta v4c — REV A
# Release: 2026-06-15
#
# Mudanças desta revisão (rev_a):
#   [FEATURE] Checkbox "Rodar Lapidador ao terminar" — dispara init_lapidador()
#             ao final de _run_mining(), inclusive após parada graciosa.
#   [FEATURE] Botão "📊 Pós-processar (Lapidador + Grafos)" — varre ./json/
#             e roda os pipelines sem precisar minerar.
#   [FEATURE] Botão "🧪 Rodar Testes Unitários" — invoca a suíte test_cli/run_all.py
#             em subprocess, com saída transmitida ao painel de Log.
#   [FEATURE] Integra módulo de grafos via grafos_runner.run_graphs().
#
# Uso: python gui_ctk.py
#      ou: python orchestrator_hibrido_alpha0e.py --gui

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
    init_lapidador = None  # tolerado em ambientes sem o módulo

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

        self.title("Projeto Delta v4c — Minerador GitHub (rev A)")
        self.geometry("1180x760")
        self.minsize(960, 620)

        self.log_queue: queue.Queue = queue.Queue(maxsize=5000)
        self.notification_queue: queue.Queue = queue.Queue(maxsize=1000)
        self.worker_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        self._orchestrator_ref: Optional[Orchestrator] = None

        self._install_log_handler()
        self._build_layout()
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

    # ---------------- layout ----------------
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        side = ctk.CTkFrame(self, width=340, corner_radius=0)
        side.grid(row=0, column=0, sticky="nsw")
        side.grid_propagate(False)

        ctk.CTkLabel(
            side, text="⛏  Projeto Delta",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(16, 4), padx=16, anchor="w")
        ctk.CTkLabel(side, text="Mineração híbrida GitHub", text_color="gray").pack(
            padx=16, anchor="w"
        )

        ctk.CTkLabel(side, text="Target user").pack(padx=16, pady=(20, 2), anchor="w")
        self.entry_user = ctk.CTkEntry(side, placeholder_text="ex: torvalds")
        self.entry_user.pack(padx=16, fill="x")

        ctk.CTkLabel(side, text="Target repo").pack(padx=16, pady=(10, 2), anchor="w")
        self.entry_repo = ctk.CTkEntry(side, placeholder_text="ex: linux")
        self.entry_repo.pack(padx=16, fill="x")

        ctk.CTkLabel(side, text="Anos de histórico").pack(padx=16, pady=(10, 2), anchor="w")
        self.entry_years = ctk.CTkEntry(side)
        self.entry_years.insert(0, "5")
        self.entry_years.pack(padx=16, fill="x")

        ctk.CTkLabel(side, text="Tokens GitHub (um por linha)").pack(
            padx=16, pady=(14, 2), anchor="w"
        )
        self.txt_tokens = ctk.CTkTextbox(side, height=110)
        self.txt_tokens.pack(padx=16, fill="x")

        self.use_tokens_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            side, text="Usar tokens (mineração rápida)",
            variable=self.use_tokens_var,
        ).pack(padx=16, pady=(12, 2), anchor="w")

        # >>> NOVO: checkbox para rodar lapidador automaticamente
        self.run_lapidador_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            side, text="Rodar Lapidador ao terminar",
            variable=self.run_lapidador_var,
        ).pack(padx=16, pady=(2, 8), anchor="w")

        row = ctk.CTkFrame(side, fg_color="transparent")
        row.pack(padx=16, pady=(8, 4), fill="x")
        ctk.CTkButton(row, text="Carregar QR", width=90, command=self.on_load_qr).pack(
            side="left", padx=(0, 4)
        )
        ctk.CTkButton(row, text="Carregar JSON", width=110, command=self.on_load_json).pack(
            side="left", padx=4
        )

        row2 = ctk.CTkFrame(side, fg_color="transparent")
        row2.pack(padx=16, pady=(4, 12), fill="x")
        ctk.CTkButton(row2, text="Salvar JSON", width=110, command=self.on_save_json).pack(
            side="left", padx=(0, 4)
        )
        ctk.CTkButton(row2, text="Gerar QR", width=90, command=self.on_generate_qr).pack(
            side="left", padx=4
        )

        # Ações principais
        self.btn_start = ctk.CTkButton(
            side, text="▶  Iniciar mineração",
            fg_color="#16a34a", hover_color="#15803d", command=self.on_start,
        )
        self.btn_start.pack(padx=16, pady=(16, 6), fill="x")

        self.btn_stop = ctk.CTkButton(
            side, text="■  Parar",
            fg_color="#dc2626", hover_color="#b91c1c",
            state="disabled", command=self.on_stop,
        )
        self.btn_stop.pack(padx=16, pady=(0, 10), fill="x")

        # >>> NOVO: pós-processar e testes
        self.btn_post = ctk.CTkButton(
            side, text="📊 Pós-processar (Lapidador + Grafos)",
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=self.on_post_process,
        )
        self.btn_post.pack(padx=16, pady=(4, 6), fill="x")

        self.btn_tests = ctk.CTkButton(
            side, text="🧪 Rodar Testes Unitários",
            fg_color="#7c3aed", hover_color="#6d28d9",
            command=self.on_run_tests,
        )
        self.btn_tests.pack(padx=16, pady=(0, 14), fill="x")

        self.status_lbl = ctk.CTkLabel(side, text="Status: ocioso", text_color="gray")
        self.status_lbl.pack(padx=16, anchor="w")

        # ----- Área principal -----
        main = ctk.CTkFrame(self, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(0, weight=3)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        log_box = ctk.CTkFrame(main)
        log_box.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))
        log_box.grid_rowconfigure(1, weight=1)
        log_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            log_box, text="Log da aplicação", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))
        self.log_text = ctk.CTkTextbox(
            log_box, wrap="word", font=ctk.CTkFont(family="Courier New", size=12)
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        notif_box = ctk.CTkFrame(main)
        notif_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))
        notif_box.grid_rowconfigure(1, weight=1)
        notif_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            notif_box,
            text="Notificações (cooldown / fim de mineração / testes)",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))
        self.notif_text = ctk.CTkTextbox(
            notif_box, wrap="word", font=ctk.CTkFont(family="Courier New", size=12)
        )
        self.notif_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    # ---------------- handlers ----------------
    def on_load_qr(self):
        path = filedialog.askopenfilename(
            title="Selecionar QR Code", initialdir=APP_DIR,
            filetypes=[("Imagens", "*.png *.jpg *.jpeg"), ("Todos", "*.*")],
        )
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
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
        )
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
            filetypes=[("JSON", "*.json")],
        )
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
            filetypes=[("PNG", "*.png")],
        )
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
            if years < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Anos deve ser inteiro >= 1.")
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
        """Pós-processa JSONs existentes em ./json/ sem precisar minerar."""
        if not os.path.isdir(JSON_DIR):
            messagebox.showwarning(
                "Sem dados",
                f"Pasta ./json/ não encontrada em:\n{JSON_DIR}\n\n"
                "Rode uma mineração antes ou crie a pasta com os JSONs.",
            )
            return
        self.btn_post.configure(state="disabled")
        self.status_lbl.configure(text="Status: pós-processando…", text_color="#2563eb")
        threading.Thread(
            target=self._run_post_process, daemon=True, name="GUI-PostProc"
        ).start()

    def on_run_tests(self):
        if not os.path.isfile(TEST_RUNNER):
            messagebox.showwarning(
                "Suíte não encontrada",
                f"Arquivo não localizado:\n{TEST_RUNNER}",
            )
            return
        self.btn_tests.configure(state="disabled")
        self.status_lbl.configure(text="Status: testando…", text_color="#7c3aed")
        threading.Thread(
            target=self._run_tests_subprocess, daemon=True, name="GUI-Tests"
        ).start()

    # ---------------- workers ----------------
    def _run_mining(self, tokens: List[str], user: str, repo: str, years: int, use_tokens: bool):
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
                        app = Orchestrator(
                            tokens=valid, target_user=user,
                            target_repo=repo, years_back=years,
                        )
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
            # >>> Executa Lapidador (e Grafos) ao terminar, inclusive após parada graciosa
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
                self.status_lbl.configure(text="Status: ocioso", text_color="gray"),
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
                self.status_lbl.configure(text="Status: ocioso", text_color="gray"),
            ))

    def _reset_buttons(self):
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_lbl.configure(text="Status: ocioso", text_color="gray")

    # ---------------- helpers ----------------
    def _collect_config(self) -> dict:
        tokens_raw = self.txt_tokens.get("1.0", "end").strip()
        tokens = [t.strip() for t in tokens_raw.splitlines() if t.strip()]
        return {
            "token": tokens,
            "target_user": self.entry_user.get().strip(),
            "target_repo": self.entry_repo.get().strip(),
        }

    def _apply_config(self, data: dict):
        tokens = data.get("token", [])
        if isinstance(tokens, str):
            tokens = [tokens]
        self.txt_tokens.delete("1.0", "end")
        self.txt_tokens.insert("1.0", "\n".join(tokens))
        self.entry_user.delete(0, "end")
        self.entry_user.insert(0, data.get("target_user", ""))
        self.entry_repo.delete(0, "end")
        self.entry_repo.insert(0, data.get("target_repo", ""))

    def _notify(self, msg: str):
        try:
            self.notification_queue.put_nowait(msg)
        except queue.Full:
            pass

    # ---------------- polling ----------------
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
