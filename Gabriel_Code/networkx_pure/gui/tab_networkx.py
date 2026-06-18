"""
Nova aba Tkinter — PureNetworkX & Validação.

Adiciona ao GUI principal três blocos:
    1. Execução da suíte de testes unitários (`unittest`) com saída no console.
    2. Demonstração interativa de cada uma das 11 categorias.
    3. Carregamento de arquivos `.gexf` (importação em qualquer ID).
"""
from __future__ import annotations

import io
import threading
import tkinter as tk
import unittest
from pathlib import Path
from pprint import pformat
from tkinter import filedialog, messagebox, ttk

from grafo.graph.abstract_graph import AbstractGraph
from grafo.graph.adjacency_list_graph import AdjacencyListGraph
from grafo.graph.adjacency_matrix_graph import AdjacencyMatrixGraph
from grafo.networkx_pure import (
    CATEGORY_NAMES,
    read_gexf,
    run_category_demo,
    write_gexf,
)


class NetworkXTab:
    """Encapsula a aba 'PureNetworkX' do GUI principal."""

    def __init__(self, notebook: ttk.Notebook, app_core, print_to_console) -> None:
        self.app_core = app_core
        self.print = print_to_console
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text=" 🧪 6. PureNetworkX & Testes ")
        self._build()

    # --------------------------------------------------------------- layout
    def _build(self) -> None:
        # ---- bloco 1: testes unitários
        f_tests = ttk.LabelFrame(self.frame, text=" Suíte de Testes Unitários (PureNetworkX) ")
        f_tests.pack(fill="x", padx=15, pady=10)
        ttk.Button(f_tests, text="Rodar todos os testes",
                   command=self._run_tests).pack(side="left", padx=10, pady=10)
        ttk.Label(f_tests, text="Executa `unittest` sobre todos os algoritmos das 11 categorias.",
                  foreground="#555").pack(side="left", padx=10)

        # ---- bloco 2: demo das 11 categorias
        f_cat = ttk.LabelFrame(self.frame, text=" Demonstração das 11 Categorias ")
        f_cat.pack(fill="x", padx=15, pady=10)

        ttk.Label(f_cat, text="Categoria:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cat_combo = ttk.Combobox(f_cat, values=CATEGORY_NAMES, state="readonly", width=55)
        self.cat_combo.current(1)
        self.cat_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(f_cat, text="ID do grafo:").grid(row=0, column=2, padx=5, pady=5)
        self.ent_gid = ttk.Entry(f_cat, width=8)
        self.ent_gid.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(f_cat, text="Executar categoria",
                   command=self._run_category).grid(row=0, column=4, padx=10, pady=5)
        ttk.Button(f_cat, text="Executar TODAS (0..11)",
                   command=self._run_all_categories).grid(row=0, column=5, padx=5, pady=5)
        f_cat.columnconfigure(1, weight=1)

        # ---- bloco 3: GEXF I/O
        f_io = ttk.LabelFrame(self.frame, text=" Importar / Exportar .gexf ")
        f_io.pack(fill="x", padx=15, pady=10)

        ttk.Label(f_io, text="ID a usar:").pack(side="left", padx=5)
        self.ent_iogid = ttk.Entry(f_io, width=8)
        self.ent_iogid.pack(side="left", padx=5)
        ttk.Button(f_io, text="Carregar .gexf",
                   command=self._load_gexf).pack(side="left", padx=10, pady=10)
        ttk.Button(f_io, text="Salvar .gexf do grafo ativo",
                   command=self._save_gexf).pack(side="left", padx=10, pady=10)

        # ---- saída local
        f_out = ttk.LabelFrame(self.frame, text=" Resultado da execução ")
        f_out.pack(fill="both", expand=True, padx=15, pady=10)
        self.txt = tk.Text(f_out, bg="#0d1117", fg="#c9d1d9",
                           font=("Consolas", 10), wrap="word")
        self.txt.pack(fill="both", expand=True, padx=5, pady=5)

    # ---------------------------------------------------------- helpers
    def _emit(self, text: str) -> None:
        self.txt.insert("end", text + "\n")
        self.txt.see("end")
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
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erro", f"Falha ao obter grafo '{gid}': {exc}")
            return None
        if g is None:
            messagebox.showwarning("Aviso", f"Grafo '{gid}' não encontrado no registry.")
        return g

    def _register_graph(self, gid: str, graph: AbstractGraph) -> bool:
        reg = getattr(self.app_core, "registry", None) or getattr(self.app_core, "graph_registry", None)
        if reg is None:
            return False
        # tenta o método mais comum
        for name in ("add", "register", "set", "put"):
            fn = getattr(reg, name, None)
            if callable(fn):
                try:
                    fn(gid, graph)
                    return True
                except TypeError:
                    continue
        # fallback: dict-like
        try:
            reg[gid] = graph  # type: ignore[index]
            return True
        except Exception:  # noqa: BLE001
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
            except Exception as exc:  # noqa: BLE001
                self._emit(f"❌ Erro ao rodar testes: {exc}")
        threading.Thread(target=task, daemon=True).start()

    def _run_category(self) -> None:
        gid = self.ent_gid.get().strip()
        if not gid:
            messagebox.showwarning("Aviso", "Informe o ID do grafo.")
            return
        idx = self.cat_combo.current()
        if idx < 0:
            return
        g = self._resolve_graph(gid)
        if g is None:
            return
        self._emit(f"\n=== {CATEGORY_NAMES[idx]} (grafo '{gid}') ===")
        try:
            result = run_category_demo(idx, g)
            self._emit(pformat(result, sort_dicts=False, compact=False, width=110))
        except Exception as exc:  # noqa: BLE001
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
            except Exception as exc:  # noqa: BLE001
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
        except Exception as exc:  # noqa: BLE001
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
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("GEXF", f"Falha ao salvar: {exc}")
