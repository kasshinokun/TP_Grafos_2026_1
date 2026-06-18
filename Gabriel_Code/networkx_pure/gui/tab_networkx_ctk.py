"""
Aba CustomTkinter — PureNetworkX & Validação.
Adiciona ao GUI principal três blocos:
1. Execução da suíte de testes unitários (`unittest`) com saída no console.
2. Demonstração interativa de cada uma das 11 categorias.
3. Carregamento de arquivos `.gexf` (importação em qualquer ID).
"""
from __future__ import annotations
import io
import threading
import unittest
from pathlib import Path
from pprint import pformat
from tkinter import filedialog, messagebox
import customtkinter as ctk

from grafo.graph.abstract_graph import AbstractGraph
from grafo.networkx_pure import (
    CATEGORY_NAMES,
    read_gexf,
    run_category_demo,
    write_gexf,
)

class NetworkXTabCTk:
    """Encapsula a aba 'PureNetworkX' do GUI principal (versão CTk)."""

    def __init__(self, parent: ctk.CTkFrame, app_core, print_to_console) -> None:
        self.app_core = app_core
        self.print = print_to_console
        self.frame = ctk.CTkFrame(parent)
        self._build()

    def _build(self) -> None:
        # ---- bloco 1: testes unitários
        f_tests = ctk.CTkFrame(self.frame, border_width=2, border_color="gray")
        f_tests.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(f_tests, text="Suíte de Testes Unitários (PureNetworkX)", 
                     font=("Helvetica", 14, "bold")).pack(pady=(10, 5))
        
        btn_frame = ctk.CTkFrame(f_tests, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="Rodar todos os testes", 
                      command=self._run_tests).pack(side="left", padx=10)
        ctk.CTkLabel(btn_frame, text="Executa `unittest` sobre todos os algoritmos das 11 categorias.", 
                     text_color="gray").pack(side="left", padx=10)

        # ---- bloco 2: demo das 11 categorias
        f_cat = ctk.CTkFrame(self.frame, border_width=2, border_color="gray")
        f_cat.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(f_cat, text="Demonstração das 11 Categorias", 
                     font=("Helvetica", 14, "bold")).pack(pady=(10, 5))

        grid_frame = ctk.CTkFrame(f_cat, fg_color="transparent")
        grid_frame.pack(fill="x", padx=10, pady=10)
        grid_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(grid_frame, text="Categoria:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cat_combo = ctk.CTkComboBox(grid_frame, values=CATEGORY_NAMES, state="readonly", width=300)
        if CATEGORY_NAMES:
            self.cat_combo.set(CATEGORY_NAMES[1] if len(CATEGORY_NAMES) > 1 else CATEGORY_NAMES[0])
        self.cat_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(grid_frame, text="ID do grafo:").grid(row=0, column=2, padx=5, pady=5)
        self.ent_gid = ctk.CTkEntry(grid_frame, width=80)
        self.ent_gid.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkButton(grid_frame, text="Executar categoria", 
                      command=self._run_category).grid(row=0, column=4, padx=10, pady=5)
        ctk.CTkButton(grid_frame, text="Executar TODAS (0..11)", 
                      command=self._run_all_categories).grid(row=0, column=5, padx=5, pady=5)

        # ---- bloco 3: GEXF I/O
        f_io = ctk.CTkFrame(self.frame, border_width=2, border_color="gray")
        f_io.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(f_io, text="Importar / Exportar .gexf", 
                     font=("Helvetica", 14, "bold")).pack(pady=(10, 5))
        
        io_frame = ctk.CTkFrame(f_io, fg_color="transparent")
        io_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(io_frame, text="ID a usar:").pack(side="left", padx=5)
        self.ent_iogid = ctk.CTkEntry(io_frame, width=80)
        self.ent_iogid.pack(side="left", padx=5)
        ctk.CTkButton(io_frame, text="Carregar .gexf", 
                      command=self._load_gexf).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(io_frame, text="Salvar .gexf do grafo ativo", 
                      command=self._save_gexf).pack(side="left", padx=10, pady=10)

        # ---- saída local
        f_out = ctk.CTkFrame(self.frame, border_width=2, border_color="gray")
        f_out.pack(fill="both", expand=True, padx=15, pady=10)
        ctk.CTkLabel(f_out, text="Resultado da execução", 
                     font=("Helvetica", 14, "bold")).pack(pady=(10, 5))
        
        self.txt = ctk.CTkTextbox(f_out, fg_color="#0d1117", text_color="#c9d1d9", 
                                  font=("Consolas", 12), wrap="word")
        self.txt.pack(fill="both", expand=True, padx=5, pady=5)

    # ---------------------------------------------------------- helpers
    def _emit(self, text: str) -> None:
        self.txt.insert("end", text + "\n")
        # Rola para o final (CTkTextbox não tem .see() direto, acessamos o textbox interno)
        self.txt._textbox.see("end")
        self.print(text)

    def _resolve_graph(self, gid: str) -> AbstractGraph | None:
        if self.app_core is None:
            messagebox.showerror("Erro", "Application core não inicializado.")
            return None
        reg = getattr(self.app_core, "registry", None) or getattr(self.app_core, "graph_registry", None)
        if reg is None:
            messagebox.showerror("Erro", "GraphRegistry não encontrado na Application.")
            return None
        try:
            getter = getattr(reg, "get", None) or getattr(reg, "get_graph", None)
            g = getter(gid) if getter else None
        except Exception as exc:
            messagebox.showerror("Erro", f"Falha ao obter grafo '{gid}': {exc}")
            return None
        if g is None:
            messagebox.showwarning("Aviso", f"Grafo '{gid}' não encontrado no registry.")
        return g

    def _register_graph(self, gid: str, graph: AbstractGraph) -> bool:
        reg = getattr(self.app_core, "registry", None) or getattr(self.app_core, "graph_registry", None)
        if reg is None:
            return False
        for name in ("add", "register", "set", "put"):
            fn = getattr(reg, name, None)
            if callable(fn):
                try:
                    fn(gid, graph)
                    return True
                except TypeError:
                    continue
        try:
            reg[gid] = graph
            return True
        except Exception:
            return False

    # ---------------------------------------------------------- handlers
    def _run_tests(self) -> None:
        def task() -> None:
            self._emit("\n>>> Executando suíte de testes PureNetworkX...")
            buf = io.StringIO()
            try:
                loader = unittest.TestLoader()
                suite = loader.discover(
                    start_dir=str(Path(__file__).resolve().parents[2]),
                    pattern="test_pure_networkx.py",
                )
                runner = unittest.TextTestRunner(stream=buf, verbosity=2)
                result = runner.run(suite)
                self._emit(buf.getvalue())
                self._emit(f"--> Testes: {result.testsRun} | "
                           f"falhas: {len(result.failures)} | erros: {len(result.errors)}")
            except Exception as exc:
                self._emit(f"❌ Erro ao rodar testes: {exc}")
        threading.Thread(target=task, daemon=True).start()

    def _run_category(self) -> None:
        gid = self.ent_gid.get().strip()
        if not gid:
            messagebox.showwarning("Aviso", "Informe o ID do grafo.")
            return
        
        try:
            idx = CATEGORY_NAMES.index(self.cat_combo.get())
        except ValueError:
            idx = -1
            
        if idx < 0:
            return
        g = self._resolve_graph(gid)
        if g is None:
            return
        self._emit(f"\n=== {CATEGORY_NAMES[idx]} (grafo '{gid}') ===")
        try:
            result = run_category_demo(idx, g)
            self._emit(pformat(result, sort_dicts=False, compact=False, width=110))
        except Exception as exc:
            self._emit(f"❌ {type(exc).__name__}: {exc}")

    def _run_all_categories(self) -> None:
        gid = self.ent_gid.get().strip()
        if not gid:
            messagebox.showwarning("Aviso", "Informe o ID do grafo.")
            return
        g = self._resolve_graph(gid)
        if g is None:
            return
        for idx, name in enumerate(CATEGORY_NAMES):
            self._emit(f"\n=== {name} ===")
            try:
                self._emit(pformat(run_category_demo(idx, g),
                                   sort_dicts=False, compact=False, width=110))
            except Exception as exc:
                self._emit(f"❌ {type(exc).__name__}: {exc}")

    def _load_gexf(self) -> None:
        gid = self.ent_iogid.get().strip()
        if not gid:
            messagebox.showwarning("Aviso", "Informe o ID a atribuir.")
            return
        path = filedialog.askopenfilename(filetypes=[("Gephi GEXF", "*.gexf")])
        if not path:
            return
        try:
            graph, directed = read_gexf(path)
        except Exception as exc:
            messagebox.showerror("GEXF", f"Falha ao ler: {exc}")
            return
        if not self._register_graph(gid, graph):
            messagebox.showerror("Registry", "Não consegui registrar o grafo na Application.")
            return
        self._emit(f"✓ GEXF carregado em '{gid}' "
                   f"({graph.get_vertex_count()} vértices, {graph.get_edge_count()} arestas, "
                   f"{'direcionado' if directed else 'não-direcionado'}).")

    def _save_gexf(self) -> None:
        gid = self.ent_iogid.get().strip()
        if not gid:
            messagebox.showwarning("Aviso", "Informe o ID do grafo.")
            return
        g = self._resolve_graph(gid)
        if g is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".gexf",
                                            filetypes=[("Gephi GEXF", "*.gexf")])
        if not path:
            return
        try:
            write_gexf(g, path, directed=True)
            self._emit(f"✓ Grafo '{gid}' salvo em {path}")
        except Exception as exc:
            messagebox.showerror("GEXF", f"Falha ao salvar: {exc}")