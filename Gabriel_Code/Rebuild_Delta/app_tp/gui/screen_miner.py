"""Tela de mineração de repositórios GitHub com suporte a QR Code e múltiplos tokens."""
import customtkinter as ctk
import threading
import queue
import csv
from datetime import datetime
from tkinter import scrolledtext, messagebox, filedialog
from typing import Optional, Callable, List, Dict
import os

from gui.screen_base import BaseScreen
from miner.common_miner import CommonMiner
from miner.scrap_graphql_miner import ScrapGraphQL
from miner.qr_handler import decode_github_qr, mask_token
from miner import graph_builder
from grafo.networkx_pure.adapter import GraphAdapter
from filemanager import PATH_D_QR, PATH_D_CSV, PATH_D_GEXF


class MinerScreen(BaseScreen):
    """Tela para configurar e executar a mineração com suporte a múltiplos tokens via QR Code."""

    def __init__(self, master,
                 on_back: Optional[Callable] = None,
                 on_graph_ready: Optional[Callable] = None,
                 **kwargs):
        self.on_graph_ready = on_graph_ready
        self._miner = None
        self._result_queue = queue.Queue()
        self.tokens: List[str] = []
        
        # --- ATRIBUTOS PARA CONTROLE DE TEMPO ---
        self.start_time = None
        self.end_time = None
        # ----------------------------------------
        
        super().__init__(
            master,
            title="⛏️ Minerador GitHub Pro",
            subtitle="Extração paralela com escalonamento de tokens e leitura de QR Code",
            on_back=on_back,
            **kwargs
        )
        self._poll_results()

    def _build_content(self):
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=16, pady=12)

        # Coluna Esquerda: Configuração
        left = ctk.CTkFrame(outer, width=350)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Configuração de Acesso", font=("Arial", 13, "bold")).pack(anchor="w", pady=(10, 6), padx=10)

        # Botão QR Code
        self.btn_qr = ctk.CTkButton(left, text="📷 Carregar QR Code (Tokens)", 
                                   command=self._load_qr, fg_color="#4F46E5", hover_color="#4338CA")
        self.btn_qr.pack(fill="x", padx=10, pady=5)

        fields = ctk.CTkFrame(left, fg_color="transparent")
        fields.pack(fill="x", padx=10)

        ctk.CTkLabel(fields, text="Tokens Ativos:", font=("Arial", 11)).pack(anchor="w", pady=(6, 0))
        self.txt_tokens_display = ctk.CTkTextbox(fields, height=80, font=("Consolas", 10))
        self.txt_tokens_display.pack(fill="x", pady=2)
        self.txt_tokens_display.insert("0.0", "Nenhum token carregado.\nUse o QR Code ou insira manualmente no campo abaixo.")
        self.txt_tokens_display.configure(state="disabled")

        self.entry_manual_token = ctk.CTkEntry(fields, placeholder_text="Adicionar token manual...", show="*")
        self.entry_manual_token.pack(fill="x", pady=2)
        ctk.CTkButton(fields, text="Adicionar", width=60, height=24, command=self._add_manual_token).pack(anchor="e", pady=2)

        self.entry_owner = ctk.CTkEntry(fields, placeholder_text="Proprietário (ex: vuejs)")
        self.entry_owner.pack(fill="x", pady=(10, 2))

        repo_row = ctk.CTkFrame(fields, fg_color="transparent")
        repo_row.pack(fill="x", pady=2)
        self.entry_repo = ctk.CTkEntry(repo_row, placeholder_text="Repositório (ex: core)")
        self.entry_repo.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_stats = ctk.CTkButton(repo_row, text="📊", width=40, command=self._fetch_repo_stats)
        self.btn_stats.pack(side="left")

        # Botões de Ação
        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=14)

        self.btn_start = ctk.CTkButton(btn_row, text="▶ Iniciar Mineração", fg_color="#16A34A", command=self._start_mining)
        self.btn_start.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.btn_cancel = ctk.CTkButton(btn_row, text="⏹ Parar", fg_color="#DC2626", state="disabled", command=self._cancel_mining)
        self.btn_cancel.pack(side="left", expand=True, fill="x")

        # Progresso
        self.lbl_progress = ctk.CTkLabel(left, text="Pronto para iniciar", text_color="#888", font=("Arial", 10))
        self.lbl_progress.pack(anchor="w", padx=10, pady=(10, 0))
        self.bar = ctk.CTkProgressBar(left)
        self.bar.pack(fill="x", padx=10, pady=4)
        self.bar.set(0)

        # Coluna Direita: Log
        right = ctk.CTkFrame(outer)
        right.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(right, text="Log de Operações", font=("Arial", 13, "bold")).pack(anchor="w", padx=10, pady=(10, 4))
        self.log = scrolledtext.ScrolledText(right, font=("Consolas", 9), bg="#1E1E1E", fg="#D4D4D4", relief="flat")
        self.log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _load_qr(self):
        path = filedialog.askopenfilename(initialdir=PATH_D_QR,  # root_path/qr_tokens
                                          initialfile="meu_qrcode.png", # nome predefinido
                                          title="Selecionar QR Code", filetypes=[("Imagens", "*.png *.jpg *.jpeg"), ("Todos", "*.*")])
        if not path: return
        try:
            data = decode_github_qr(path)
            new_tokens = data.get("token", [])
            if isinstance(new_tokens, list):
                self.tokens = list(set(self.tokens + new_tokens))
                self.entry_owner.delete(0, "end")
                self.entry_owner.insert(0, data.get("target_user", ""))
                self.entry_repo.delete(0, "end")
                self.entry_repo.insert(0, data.get("target_repo", ""))
                self._update_token_display()
                self._log(f"✅ QR Code lido: {len(new_tokens)} tokens adicionados.")
        except Exception as e:
            messagebox.showerror("Erro QR Code", str(e))

    def _add_manual_token(self):
        t = self.entry_manual_token.get().strip()
        if t:
            if t not in self.tokens:
                self.tokens.append(t)
                self._update_token_display()
                self.entry_manual_token.delete(0, "end")
                self._log("➕ Token manual adicionado.")
            else:
                messagebox.showinfo("Info", "Token já existe na lista.")

    def _update_token_display(self):
        self.txt_tokens_display.configure(state="normal")
        self.txt_tokens_display.delete("0.0", "end")
        if not self.tokens:
            self.txt_tokens_display.insert("0.0", "Nenhum token carregado.")
        else:
            for t in self.tokens:
                self.txt_tokens_display.insert("end", f"• {mask_token(t)}\n")
        self.txt_tokens_display.configure(state="disabled")

    def _start_mining(self):
        owner = self.entry_owner.get().strip()
        repo = self.entry_repo.get().strip()
        if not owner or not repo:
            messagebox.showwarning("Aviso", "Informe o Proprietário e o Repositório.")
            return
        if not self.tokens:
            messagebox.showwarning("Aviso", "Carregue pelo menos um token via QR Code ou manualmente.")
            return

        self.btn_start.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")  # só habilita após a mineração iniciar de fato
        self.bar.set(0)
        self._log(f"📊 Apurando status via GraphQL antes de minerar {owner}/{repo}...")

        def preflight_worker():
            try:
                scraper = ScrapGraphQL(self.tokens, owner, repo)
                status = scraper.check_status()
                self._result_queue.put(('preflight_ok', owner, repo, status))
            except Exception as ex:
                self._result_queue.put(('preflight_fail', owner, repo, str(ex)))

        threading.Thread(target=preflight_worker, daemon=True).start()

    def _launch_mining(self, owner: str, repo: str):
        """Inicia de fato a mineração REST, após o status GraphQL ter sido
        verificado com sucesso (token válido, repositório existe)."""
        self.btn_cancel.configure(state="normal")

        # --- REGISTRA O INÍCIO DA MINERAÇÃO ---
        self.start_time = datetime.now()
        self._log(f"⏱️ Início da mineração: {self.start_time.strftime('%H:%M:%S')}")
        self._log(f"🚀 Iniciando mineração paralela em {owner}/{repo}...")

        # --- FUNÇÃO DE PROGRESSO COM TEMPO DECORRIDO ---
        def on_progress(pct: float, msg: str):
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                total_sec = elapsed.total_seconds()
                time_str = f"{int(total_sec//60)}m {int(total_sec%60)}s"
                full_msg = f"⏱️ {time_str} → {msg}"
            else:
                full_msg = msg
            self._result_queue.put(('progress', pct, full_msg))

        self._miner = CommonMiner(owner, repo, self.tokens, on_progress=on_progress)

        def worker():
            try:
                graph = self._miner.run()
                stats = self._miner.get_stats()
                interactions = list(self._miner.interactions)
                self._result_queue.put(('done', graph, interactions, stats, None))
            except Exception as ex:
                self._result_queue.put(('done', None, [], {}, str(ex)))

        threading.Thread(target=worker, daemon=True).start()

    def _cancel_mining(self):
        if self._miner:
            self._miner.cancel()
            self._log("⏹ Cancelamento solicitado...")
            # --- REGISTRA O TEMPO PARCIAL EM CASO DE CANCELAMENTO ---
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                self._log(f"⏱️ Cancelado após {elapsed.total_seconds():.2f} segundos")

    def _poll_results(self):
        try:
            while True:
                msg = self._result_queue.get_nowait()
                if msg[0] == 'progress':
                    _, pct, text = msg
                    self.bar.set(pct)
                    self.lbl_progress.configure(text=f"{pct*100:.0f}% - {text}")
                    self._log(text)
                elif msg[0] == 'preflight_ok':
                    _, owner, repo, status = msg
                    login = status.get("viewer_login") or "?"
                    remaining = status.get("remaining")
                    limit = status.get("limit")
                    issues_n = status.get("total_issues")
                    prs_n = status.get("total_prs")
                    self._log(f"✅ Status OK — token autenticado como '{login}'.")
                    self._log(f"📈 Quota GraphQL: {remaining}/{limit} requisições restantes.")
                    self._log(f"📦 Repositório encontrado: {issues_n} issues, {prs_n} PRs (histórico total).")
                    self._launch_mining(owner, repo)
                elif msg[0] == 'preflight_fail':
                    _, owner, repo, error = msg
                    self._log(f"❌ Falha na apuração de status (GraphQL): {error}")
                    messagebox.showerror(
                        "Status indisponível",
                        f"Não foi possível verificar o status de {owner}/{repo} antes de minerar:\n{error}")
                    self.btn_start.configure(state="normal")
                    self.btn_cancel.configure(state="disabled")
                elif msg[0] == 'stats':
                    _, stats, error = msg
                    self.btn_stats.configure(state="normal")
                    if error:
                        self._log(f"❌ Erro ao obter estatísticas: {error}")
                        messagebox.showerror("Erro", error)
                    else:
                        login = stats.get("viewer_login") or "?"
                        rl = stats.get("rate_limit") or {}
                        self._log(f"📊 Token autenticado como '{login}'. "
                                  f"Quota: {rl.get('remaining')}/{rl.get('limit')}.")
                        self._log(f"📊 Estatísticas: {stats['total_items']} itens, "
                                  f"{stats['max_years']} ano(s) de histórico disponível.")
                        messagebox.showinfo(
                            "Estatísticas",
                            f"Token: {login}\n"
                            f"Quota GraphQL restante: {rl.get('remaining')}/{rl.get('limit')}\n"
                            f"Total de registros: {stats['total_items']}\n"
                            f"Idade máxima: {stats['max_years']} anos")
                elif msg[0] == 'done':
                    _, graph, interactions, stats, error = msg
                    self.btn_start.configure(state="normal")
                    self.btn_cancel.configure(state="disabled")
                    
                    if error:
                        self._log(f"❌ Erro: {error}")
                        messagebox.showerror("Erro", error)
                    else:
                        # --- REGISTRA O TÉRMINO E A DURAÇÃO TOTAL ---
                        self.end_time = datetime.now()
                        if self.start_time:
                            duration = self.end_time - self.start_time
                            self._log(f"⏱️ Término da mineração: {self.end_time.strftime('%H:%M:%S')}")
                            self._log(f"⏱️ Duração total: {duration.total_seconds():.2f} segundos")
                        else:
                            self._log("⏱️ Término da mineração (sem registro de início)")

                        self._log(f"✅ Concluído! {graph.get_vertex_count()} nós encontrados.")

                        csv_path = self._export_result_csv(interactions)
                        if csv_path:
                            self._log(f"💾 Resultado bruto da mineração salvo em: {csv_path}")

                        gexf_paths = self._export_typed_graphs(interactions)
                        for label, p in gexf_paths.items():
                            self._log(f"💾 {label} exportado em: {p}")

                        if self.on_graph_ready:
                            self.on_graph_ready(GraphAdapter(graph))
        except queue.Empty:
            pass
        self.after(150, self._poll_results)

    def _log(self, msg: str):
        self.log.insert("end", f"[{os.getpid()}] {msg}\n")
        self.log.see("end")

    def _export_result_csv(self, interactions) -> Optional[str]:
        """Salva o resultado bruto (provisório) da mineração em
        root_path/csv-provisorio, no formato actor,target,type — uma linha
        por interação, antes de ser dividida nos 4 grafos da Etapa 1."""
        try:
            owner = self.entry_owner.get().strip() or "repo"
            repo = self.entry_repo.get().strip() or "mineracao"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{owner}_{repo}_{timestamp}.csv"
            path = os.path.join(PATH_D_CSV, filename)

            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["actor", "target", "type"])
                for inter in interactions:
                    actor = inter.get("author")
                    itype = inter.get("type", "")
                    for target in inter.get("mentions", []):
                        if actor and target and actor != target:
                            writer.writerow([actor, target, itype])
            return path
        except Exception as ex:
            self._log(f"⚠️ Não foi possível salvar o CSV do resultado: {ex}")
            return None

    def _export_typed_graphs(self, interactions) -> Dict[str, str]:
        """Constrói (Etapa 1 do PDF) e exporta para root_path/gexf os 4
        grafos da mineração: Grafo 1 (comentários), Grafo 2 (fechamentos),
        Grafo 3 (revisões/merges) e o Grafo integrado (ponderado)."""
        owner = self.entry_owner.get().strip() or "repo"
        repo = self.entry_repo.get().strip() or "mineracao"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            graphs = graph_builder.build_all_graphs(interactions)
        except Exception as ex:
            self._log(f"⚠️ Não foi possível separar os 4 grafos: {ex}")
            return {}

        names = {
            "graph1": ("Grafo 1 (comentários)", "graph1"),
            "graph2": ("Grafo 2 (fechamentos)", "graph2"),
            "graph3": ("Grafo 3 (revisões/merges)", "graph3"),
            "graph_integrado": ("Grafo integrado (ponderado)", "graph_integrado"),
        }

        exported: Dict[str, str] = {}
        for key, (label, slug) in names.items():
            g = graphs.get(key)
            if g is None:
                continue
            filename = f"{slug}_{owner}_{repo}_{timestamp}.gexf"
            path = os.path.join(PATH_D_GEXF, filename)
            try:
                g.export_to_gephi(path)
                exported[label] = path
            except Exception as ex:
                self._log(f"⚠️ Falha ao exportar {label}: {ex}")
        return exported
    # ===============================================================
    def _fetch_repo_stats(self):
        """Consulta GraphQL (em segundo plano) para obter status/limites do repositório."""
        owner = self.entry_owner.get().strip()
        repo = self.entry_repo.get().strip()
        if not owner or not repo:
            messagebox.showwarning("Aviso", "Preencha Proprietário e Repositório.")
            return
        if not self.tokens:
            messagebox.showwarning("Aviso", "Carregue pelo menos um token via QR Code ou manualmente.")
            return

        self.btn_stats.configure(state="disabled")
        self._log("📊 Consultando status via GraphQL...")

        def worker():
            try:
                scraper = ScrapGraphQL(self.tokens, owner, repo)
                stats = scraper.compute_limits()
                self._result_queue.put(('stats', stats, None))
            except Exception as ex:
                self._result_queue.put(('stats', None, str(ex)))

        threading.Thread(target=worker, daemon=True).start()
    # ===============================================================
