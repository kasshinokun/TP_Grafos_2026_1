import os
import customtkinter as ctk
from tkinter import messagebox

from filemanager import PATH_D_GEXF
from grafo.utils.gexf_parser import load_gexf
from grafo.networkx_pure.adapter import GraphAdapter
from grafo.networkx_pure.transversal import (
    bfs, dfs,
    connected_components,
    kosaraju_scc, tarjan_scc,
    kruskal, prim,
    dijkstra, bellman_ford, floyd_warshall,
    ford_fulkerson, edmonds_karp,
    topological_sort,
)
from gui.graph_canvas import GraphCanvas


class SearchPathsFrame(ctk.CTkFrame):
    """Frame para o módulo de Busca & Caminhos."""

    VIEW_MODE_CONSOLE = "Console"
    VIEW_MODE_GRAFICO = "Gráfico"

    PALETTE = ["#4A90E2", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6", "#1ABC9C"]
    COLOR_DEFAULT = "#4A90E2"
    COLOR_SOURCE  = "#E74C3C"
    COLOR_TARGET  = "#F39C12"
    COLOR_PATH    = "#2ECC71"

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.current_graph = None

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ==================== SIDEBAR ====================
        self.sidebar = ctk.CTkFrame(self, width=300)
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
        self.sidebar.grid_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.sidebar,
            text="Busca & Caminhos",
            font=("Helvetica", 20, "bold")
        )
        self.title_label.pack(pady=(20, 10))

        self.graph_label = ctk.CTkLabel(
            self.sidebar,
            text="Grafo (./gexf):",
            font=("Helvetica", 14, "bold")
        )
        self.graph_label.pack(pady=(10, 0))

        self.graph_files = self._list_gexf_files()
        self.graph_combo = ctk.CTkComboBox(
            self.sidebar,
            values=self.graph_files if self.graph_files else ["(nenhum .gexf encontrado)"],
            width=250,
            state="readonly",
            command=self._on_graph_change
        )
        self.graph_combo.pack(pady=(5, 5))

        self.graph_status_label = ctk.CTkLabel(
            self.sidebar,
            text="Nenhum grafo carregado.",
            font=("Helvetica", 11),
            wraplength=250,
        )
        self.graph_status_label.pack(pady=(0, 15))

        if self.graph_files:
            self.graph_combo.set(self.graph_files[0])
        else:
            self.graph_combo.set("(nenhum .gexf encontrado)")

        self.cat_label = ctk.CTkLabel(
            self.sidebar,
            text="Categoria:",
            font=("Helvetica", 14, "bold")
        )
        self.cat_label.pack(pady=(10, 0))

        self.categories = [
            "Buscas",
            "Conectividade em grafos",
            "SSC's",
            "Árvore e árvore geradoras",
            "Caminhos mínimos",
            "Fluxo em rede",
            "Topologia",
            "Planaridade"
        ]

        self.category_combo = ctk.CTkComboBox(
            self.sidebar,
            values=self.categories,
            width=250,
            state="readonly",
            command=self._on_category_change
        )
        self.category_combo.pack(pady=(5, 15))
        self.category_combo.set(self.categories[0])

        self.algo_label = ctk.CTkLabel(
            self.sidebar,
            text="Algoritmo:",
            font=("Helvetica", 14, "bold")
        )
        self.algo_label.pack(pady=(10, 0))

        self.algorithm_combo = ctk.CTkComboBox(
            self.sidebar,
            values=[],
            width=250,
            state="readonly",
            command=self._on_algorithm_change
        )
        self.algorithm_combo.pack(pady=(5, 15))

        self.category_algorithms = {
            "Buscas": ["BFS", "DFS"],
            "Conectividade em grafos": ["Componentes conexos", "Pontes", "Articulações"],
            "SSC's": ["Kosaraju", "Tarjan"],
            "Árvore e árvore geradoras": ["Kruskal", "Prim"],
            "Caminhos mínimos": ["Dijkstra", "Bellman-Ford", "Floyd-Warshall"],
            "Fluxo em rede": ["Ford-Fulkerson", "Edmonds-Karp"],
            "Topologia": ["Ordenação topológica"],
            "Planaridade": ["Teste de planaridade"]
        }

        self.algorithms_need_source = {
            "BFS", "DFS", "Dijkstra", "Bellman-Ford", "Prim",
        }
        self.algorithms_need_source_target = {
            "Ford-Fulkerson", "Edmonds-Karp",
        }
        self.algorithms_not_implemented = {
            "Pontes", "Articulações", "Teste de planaridade",
        }

        # ==================== ÁREA DE CONTEÚDO ====================
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.search_panel = self._build_search_panel(self.content)
        self.search_panel.grid(row=0, column=0, sticky="nsew")

        self._update_algorithms(self.categories[0])

        if self.graph_files:
            self._load_selected_graph(self.graph_files[0])

    # ------------------------------------------------------------------
    # Seleção e carregamento de grafos
    # ------------------------------------------------------------------

    @staticmethod
    def _list_gexf_files():
        try:
            return sorted(f for f in os.listdir(PATH_D_GEXF) if f.endswith(".gexf"))
        except OSError:
            return []

    def _on_graph_change(self, choice: str):
        self._load_selected_graph(choice)

    def _load_selected_graph(self, filename: str):
        if not filename or filename == "(nenhum .gexf encontrado)":
            self.current_graph = None
            self.graph_status_label.configure(text="Nenhum grafo carregado.")
            self._update_vertex_list()
            return

        path = os.path.join(PATH_D_GEXF, filename)
        try:
            self.current_graph = load_gexf(path)
            n = self.current_graph.get_vertex_count()
            e = self.current_graph.get_edge_count()
            self.graph_status_label.configure(text=f"✅ {filename}\n{n} nós, {e} arestas.")
            self.source_entry.delete(0, "end")
            self.target_entry.delete(0, "end")
            self._update_vertex_list()
        except Exception as ex:
            self.current_graph = None
            self.graph_status_label.configure(text=f"❌ Erro ao carregar {filename}: {ex}")
            self._update_vertex_list()

        self._on_algorithm_change(self.algorithm_combo.get())

    def _update_vertex_list(self):
        """Atualiza a lista de vértices exibida na coluna direita."""
        self.names_vertex_box.configure(state="normal")
        self.names_vertex_box.delete("1.0", "end")
        if self.current_graph is None:
            self.names_vertex_box.insert("1.0", "Nenhum grafo carregado.")
        else:
            n = self.current_graph.get_vertex_count()
            labels = self.current_graph.vertex_labels
            for i in range(n):
                label = labels.get(i, i)
                self.names_vertex_box.insert("end", f"{i}: {label}\n")
        self.names_vertex_box.configure(state="disabled")

    def _update_algorithms(self, category):
        algo_list = self.category_algorithms.get(category, [])
        if algo_list:
            self.algorithm_combo.configure(values=algo_list)
            self.algorithm_combo.set(algo_list[0])
        else:
            self.algorithm_combo.configure(values=[])
            self.algorithm_combo.set("")
        self._on_algorithm_change(self.algorithm_combo.get())

    def _on_category_change(self, choice):
        self._update_algorithms(choice)

    def _on_algorithm_change(self, choice):
        if choice and self.algorithm_combo.get() != choice:
            self.algorithm_combo.set(choice)

        need_source = choice in self.algorithms_need_source
        need_target = choice in self.algorithms_need_source_target

        if need_source or need_target:
            self.source_label.pack(side="left", padx=(0, 8))
            self.source_entry.pack(side="left", padx=(0, 8))
            self.target_label.configure(
                text="Destino (índice):" if need_target else "Destino (índice, opcional):"
            )
            self.target_label.pack(side="left", padx=(8, 8))
            self.target_entry.pack(side="left", padx=(0, 8))
        else:
            self.source_label.pack_forget()
            self.source_entry.pack_forget()
            self.target_label.pack_forget()
            self.target_entry.pack_forget()

        if self.current_graph is None:
            self.run_button.configure(state="disabled")
        else:
            self.run_button.configure(state="normal")

        self._refresh_output_panel(choice)

    def _on_view_mode_change(self, _choice=None):
        self._refresh_output_panel(self.algorithm_combo.get())

    def _refresh_output_panel(self, choice):
        view_mode = self.view_algorithm_combo.get() if hasattr(self, "view_algorithm_combo") else self.VIEW_MODE_CONSOLE
        if view_mode == self.VIEW_MODE_GRAFICO:
            self._show_graphic()
            if self.current_graph is not None:
                self._ensure_canvas_loaded()
                self.graph_canvas.set_node_colors({})
            self.canvas_note_label.configure(text=f"Algoritmo selecionado: {choice}. Clique em Executar.")
        else:
            self._show_console()
            self._set_result_text(f"Algoritmo selecionado: {choice}\nClique em Executar.")

    # ------------------------------------------------------------------
    # Painel de controle (sempre visível)
    # ------------------------------------------------------------------

    def _build_search_panel(self, parent) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(parent, fg_color="transparent")
        panel.grid_columnconfigure(0, weight=1)   # coluna do canvas/console
        panel.grid_columnconfigure(1, weight=0)   # coluna da lista de vértices (largura fixa)
        panel.grid_rowconfigure(2, weight=1)      # área principal expande

        # ---- Linha 0: controles principais (origem, destino, executar, modo) ----
        controls = ctk.CTkFrame(panel, fg_color="transparent")
        controls.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        self.source_label = ctk.CTkLabel(
            controls, text="Vértice de origem (índice):", font=("Helvetica", 13)
        )
        self.source_label.pack(side="left", padx=(0, 8))
        self.source_entry = ctk.CTkEntry(controls, placeholder_text="Digite apenas números", width=100)
        self.source_entry.pack(side="left", padx=(0, 8))

        self.target_label = ctk.CTkLabel(
            controls, text="Destino (índice, opcional):", font=("Helvetica", 13)
        )
        self.target_label.pack(side="left", padx=(8, 8))
        self.target_entry = ctk.CTkEntry(controls, placeholder_text="Digite apenas números", width=100)
        self.target_entry.pack(side="left", padx=(0, 8))

        self.run_button = ctk.CTkButton(
            controls, text="▶ Executar", width=110, command=self._run_search
        )
        self.run_button.pack(side="left", padx=(8, 0))

        mode_view_execute = [self.VIEW_MODE_CONSOLE, self.VIEW_MODE_GRAFICO]
        self.view_algorithm_combo = ctk.CTkComboBox(
            controls,
            values=mode_view_execute,
            width=170,
            state="readonly",
            command=self._on_view_mode_change,
        )
        self.view_algorithm_combo.pack(side="left", padx=(8, 0))
        self.view_algorithm_combo.set(mode_view_execute[0])

        # ---- Linha 1: zoom + botão "Recalcular Layout" (apenas modo Gráfico) ----
        self.zoom_controls = ctk.CTkFrame(panel, fg_color="transparent")
        self.zoom_controls.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        self.zoom_controls.grid_remove()  # oculto inicialmente

        # Botão placeholder "Recalcular Layout"
        self.recalc_button = ctk.CTkButton(
            self.zoom_controls,
            text="Recalcular Layout",
            width=140,
            command=self._on_recalculate_layout_click,
        )
        self.recalc_button.pack(side="left", padx=(0, 10))

        self.zoom_label = ctk.CTkLabel(
            self.zoom_controls, text="🔍 Zoom", font=("Helvetica", 12)
        )
        self.zoom_label.pack(side="left", padx=(0, 8))

        self.zoom_slider = ctk.CTkSlider(
            self.zoom_controls, from_=0.2, to=4.0, number_of_steps=38, width=180,
            command=self._on_zoom_slider,
        )
        self.zoom_slider.pack(side="left", padx=(0, 0))
        self.zoom_slider.set(1.0)

        # ---- Linha 2: área de saída (esquerda) e lista de vértices (direita) ----
        # Container para console e canvas (ocupam a mesma posição, alternados)
        self.output_container = ctk.CTkFrame(panel, fg_color="transparent")
        self.output_container.grid(row=2, column=0, sticky="nsew")
        self.output_container.grid_columnconfigure(0, weight=1)
        self.output_container.grid_rowconfigure(0, weight=1)
        self.output_container.grid_rowconfigure(1, weight=0)  # linha para nota

        # Console (texto)
        self.search_result_box = ctk.CTkTextbox(self.output_container, wrap="word")
        self.search_result_box.configure(state="disabled")
        self.search_result_box.grid(row=0, column=0, sticky="nsew")

        # Canvas (gráfico)
        self.graph_canvas_container, self.graph_canvas = GraphCanvas.with_scrollbars(
            self.output_container, adapter=None,
            on_zoom_change=self._sync_zoom_slider,
            bg="#F5F5F5", highlightthickness=0,
        )
        self.graph_canvas_container.grid(row=0, column=0, sticky="nsew")
        self.graph_canvas_container.grid_remove()  # oculto inicialmente

        # Nota/legenda abaixo do canvas
        self.canvas_note_label = ctk.CTkLabel(
            self.output_container, text="", font=("Helvetica", 11),
            text_color="#666", wraplength=500, justify="left",
        )
        self.canvas_note_label.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        self.canvas_note_label.grid_remove()

        self._graph_canvas_loaded_for = None

        # Lista de vértices (sempre visível)
        self.names_vertex_box = ctk.CTkTextbox(panel, width=220, wrap="word")
        self.names_vertex_box.grid(row=2, column=1, sticky="nswe", padx=(10, 0))
        self.names_vertex_box.configure(state="disabled")

        # Oculta os campos de origem/destino inicialmente
        self.source_label.pack_forget()
        self.source_entry.pack_forget()
        self.target_label.pack_forget()
        self.target_entry.pack_forget()

        return panel

    def _set_result_text(self, text: str):
        self.search_result_box.configure(state="normal")
        self.search_result_box.delete("1.0", "end")
        self.search_result_box.insert("1.0", text)
        self.search_result_box.configure(state="disabled")

    # ------------------------------------------------------------------
    # Placeholder para "Recalcular Layout"
    # ------------------------------------------------------------------

    def _on_recalculate_layout_click(self):
        """Placeholder: apenas exibe uma mensagem no console."""
        self._console_log("Função 'Recalcular Layout' não implementada.")
        messagebox.showinfo(
            "Funcionalidade em desenvolvimento",
            "A recalcular layout ainda não foi implementado.\n"
            "Em breve estará disponível."
        )

    def _console_log(self, text: str):
        """Exibe uma mensagem no console (modo texto)."""
        # Se estiver no modo console, adiciona ao texto existente; senão, apenas mostra.
        # Por simplicidade, vamos substituir o conteúdo ou adicionar no final?
        # Vamos adicionar no final, mantendo o histórico.
        self.search_result_box.configure(state="normal")
        self.search_result_box.insert("end", f"\n[INFO] {text}")
        self.search_result_box.configure(state="disabled")
        self.search_result_box.see("end")

    # ------------------------------------------------------------------
    # Execução do algoritmo
    # ------------------------------------------------------------------

    def _run_search(self):
        if self.current_graph is None:
            messagebox.showwarning("Aviso", "Nenhum grafo carregado.")
            return

        algorithm = self.algorithm_combo.get()
        if not algorithm:
            messagebox.showwarning("Aviso", "Selecione um algoritmo.")
            return

        view_mode = self.view_algorithm_combo.get()
        if view_mode not in (self.VIEW_MODE_CONSOLE, self.VIEW_MODE_GRAFICO):
            messagebox.showerror("Erro", f"Modo de visualização desconhecido: '{view_mode}'.")
            return

        if algorithm in self.algorithms_not_implemented:
            self._show_console()
            self._set_result_text(
                f"Algoritmo '{algorithm}' ainda não implementado no backend.\n"
                "Em breve estará disponível."
            )
            return

        need_source = algorithm in self.algorithms_need_source
        need_target = algorithm in self.algorithms_need_source_target

        source = None
        target = None

        if need_source or need_target:
            source_text = self.source_entry.get().strip()
            if not source_text:
                messagebox.showwarning("Aviso", "Digite o índice do vértice de origem.")
                return
            try:
                source = int(source_text)
            except ValueError:
                messagebox.showerror("Erro", "Origem deve ser um número inteiro (índice).")
                return
            if source < 0 or source >= self.current_graph.get_vertex_count():
                messagebox.showerror("Erro", f"Índice {source} fora do intervalo (0 a {self.current_graph.get_vertex_count()-1}).")
                return

            target_text = self.target_entry.get().strip()
            if need_target and not target_text:
                messagebox.showwarning("Aviso", "Digite o índice do vértice de destino.")
                return
            if target_text:
                try:
                    target = int(target_text)
                except ValueError:
                    messagebox.showerror("Erro", "Destino deve ser um número inteiro (índice) ou vazio.")
                    return
                if target < 0 or target >= self.current_graph.get_vertex_count():
                    messagebox.showerror("Erro", f"Índice {target} fora do intervalo.")
                    return

        if view_mode == self.VIEW_MODE_CONSOLE:
            self._run_console(algorithm, source, target)
        else:
            self._run_graphic(algorithm, source, target)

    def _run_console(self, algorithm, source, target):
        self._show_console()
        try:
            result_text = self._execute_algorithm(algorithm, source, target)
        except Exception as ex:
            messagebox.showerror("Erro", f"Falha ao executar '{algorithm}': {ex}")
            return
        self._set_result_text(result_text)

    def _run_graphic(self, algorithm, source, target):
        self._show_graphic()
        try:
            colors, note = self._compute_node_colors(algorithm, source, target)
        except Exception as ex:
            messagebox.showerror("Erro", f"Falha ao executar '{algorithm}': {ex}")
            return

        self._ensure_canvas_loaded()
        self.graph_canvas.set_node_colors(colors)
        if note:
            self.canvas_note_label.configure(text=note)

    # ------------------------------------------------------------------
    # Alternância de modo de exibição (Console x Gráfico)
    # ------------------------------------------------------------------

    def _show_console(self):
        # Mostra o console, oculta o canvas e a nota
        self.search_result_box.grid()
        self.graph_canvas_container.grid_remove()
        self.canvas_note_label.grid_remove()
        self.zoom_controls.grid_remove()  # esconde zoom e recalc

    def _show_graphic(self):
        # Mostra o canvas e a nota, oculta o console
        self.search_result_box.grid_remove()
        self.graph_canvas_container.grid()
        self.canvas_note_label.grid()
        self.zoom_controls.grid()  # mostra zoom e recalc

    def _ensure_canvas_loaded(self):
        if self._graph_canvas_loaded_for is not self.current_graph:
            adapter = GraphAdapter(self.current_graph)
            self.graph_canvas.load_adapter(adapter)
            self._graph_canvas_loaded_for = self.current_graph
            self.zoom_slider.set(1.0)

    def _on_zoom_slider(self, value):
        if self.graph_canvas:
            self.graph_canvas.set_zoom_level(float(value))

    def _sync_zoom_slider(self, zoom_level: float):
        if hasattr(self, "zoom_slider"):
            self.zoom_slider.set(zoom_level)

    # ------------------------------------------------------------------
    # Dispatcher: executa o algoritmo escolhido e formata o resultado
    # ------------------------------------------------------------------

    def _execute_algorithm(self, algorithm: str, source: int, target: int) -> str:
        g = self.current_graph
        label_of = g.vertex_labels.get

        def fmt_vertex(v: int) -> str:
            return f"{label_of(v, v)} ({v})"

        # ---------------- Buscas (BFS / DFS) ----------------
        if algorithm in ("BFS", "DFS"):
            result = bfs(g, source) if algorithm == "BFS" else dfs(g, source)
            lines = [
                f"Algoritmo: {algorithm}",
                f"Origem: {fmt_vertex(source)}",
                "",
                f"Ordem de visita ({len(result.order)} de "
                f"{g.get_vertex_count()} vértices alcançados):",
                ", ".join(fmt_vertex(v) for v in result.order),
            ]
            if target is not None:
                path = result.path_to(target)
                lines.append("")
                if path is None:
                    lines.append(
                        f"Destino {fmt_vertex(target)} não é alcançável "
                        f"a partir da origem (grafo direcionado)."
                    )
                else:
                    lines.append(
                        "Caminho até o destino:\n" + " → ".join(fmt_vertex(v) for v in path)
                    )
            return "\n".join(lines)

        # ---------------- Conectividade ----------------
        if algorithm == "Componentes conexos":
            comps = connected_components(g)
            lines = [
                f"Algoritmo: {algorithm}",
                f"Total de componentes: {len(comps)}",
                "",
            ]
            for i, comp in enumerate(comps, start=1):
                lines.append(f"Componente {i} ({len(comp)} vértices):")
                lines.append(", ".join(fmt_vertex(v) for v in comp))
                lines.append("")
            return "\n".join(lines).rstrip()

        # ---------------- SCC's ----------------
        if algorithm in ("Kosaraju", "Tarjan"):
            sccs = kosaraju_scc(g) if algorithm == "Kosaraju" else tarjan_scc(g)
            lines = [
                f"Algoritmo: {algorithm}",
                f"Total de componentes fortemente conexos: {len(sccs)}",
                "",
            ]
            for i, comp in enumerate(sccs, start=1):
                lines.append(f"SCC {i} ({len(comp)} vértices):")
                lines.append(", ".join(fmt_vertex(v) for v in comp))
                lines.append("")
            return "\n".join(lines).rstrip()

        # ---------------- Árvore geradora mínima ----------------
        if algorithm in ("Kruskal", "Prim"):
            mst = kruskal(g) if algorithm == "Kruskal" else prim(g, source or 0)
            lines = [
                f"Algoritmo: {algorithm}",
                f"Arestas na MST: {mst.get_edge_count()}",
                "",
            ]
            total_weight = 0.0
            for u in range(mst.get_vertex_count()):
                for v, w in mst.adj[u].items():
                    if u < v:  # cada aresta uma única vez (MST é não direcionada)
                        lines.append(f"{fmt_vertex(u)} — {fmt_vertex(v)}  (peso {w})")
                        total_weight += w
            lines.append("")
            lines.append(f"Peso total da MST: {total_weight}")
            return "\n".join(lines)

        # ---------------- Caminhos mínimos ----------------
        if algorithm in ("Dijkstra", "Bellman-Ford"):
            if algorithm == "Dijkstra":
                dist, pred = dijkstra(g, source)
                neg_cycle_note = None
            else:
                dist, pred, no_neg_cycle = bellman_ford(g, source)
                neg_cycle_note = None if no_neg_cycle else "⚠ Ciclo de peso negativo detectado no grafo."

            lines = [f"Algoritmo: {algorithm}", f"Origem: {fmt_vertex(source)}", ""]
            if neg_cycle_note:
                lines.append(neg_cycle_note)
                lines.append("")
            lines.append("Distâncias a partir da origem:")
            for v in range(g.get_vertex_count()):
                d = dist[v]
                d_str = "∞" if d == float("inf") else str(d)
                lines.append(f"  {fmt_vertex(v)}: {d_str}")

            if target is not None:
                lines.append("")
                d = dist[target]
                if d == float("inf"):
                    lines.append(f"Destino {fmt_vertex(target)} não é alcançável a partir da origem.")
                else:
                    # Reconstrói o caminho a partir do vetor de predecessores
                    path = [target]
                    v = target
                    while pred[v] is not None:
                        v = pred[v]
                        path.append(v)
                    path.reverse()
                    lines.append(f"Distância até o destino: {d}")
                    lines.append("Caminho: " + " → ".join(fmt_vertex(v) for v in path))
            return "\n".join(lines)

        if algorithm == "Floyd-Warshall":
            dist, pred = floyd_warshall(g)
            n = g.get_vertex_count()
            lines = [f"Algoritmo: {algorithm}", f"Matriz de distâncias ({n}x{n}):", ""]
            for i in range(n):
                row = []
                for j in range(n):
                    d = dist[i][j]
                    row.append("∞" if d == float("inf") else str(d))
                lines.append(f"{fmt_vertex(i)}: " + ", ".join(row))
            return "\n".join(lines)

        # ---------------- Fluxo em rede ----------------
        if algorithm in ("Ford-Fulkerson", "Edmonds-Karp"):
            flow_fn = ford_fulkerson if algorithm == "Ford-Fulkerson" else edmonds_karp
            max_flow, flow_graph = flow_fn(g, source, target)
            lines = [
                f"Algoritmo: {algorithm}",
                f"Origem: {fmt_vertex(source)}  |  Destino: {fmt_vertex(target)}",
                "",
                f"Fluxo máximo: {max_flow}",
                "",
                "Arestas com fluxo:",
            ]
            for u in range(flow_graph.get_vertex_count()):
                for v, w in flow_graph.adj[u].items():
                    lines.append(f"  {fmt_vertex(u)} → {fmt_vertex(v)}: {w}")
            return "\n".join(lines)

        # ---------------- Topologia ----------------
        if algorithm == "Ordenação topológica":
            order = topological_sort(g)
            lines = [f"Algoritmo: {algorithm}", ""]
            if order is None:
                lines.append("O grafo possui ciclo — não é um DAG, ordenação topológica não existe.")
            else:
                lines.append("Ordem topológica:")
                lines.append(", ".join(fmt_vertex(v) for v in order))
            return "\n".join(lines)

        return f"Algoritmo '{algorithm}' ainda não implementado."

    # ------------------------------------------------------------------
    # Dispatcher para cores (modo Gráfico)
    # ------------------------------------------------------------------

    def _palette_cycle(self, groups):
        colors = {}
        for i, group in enumerate(groups):
            color = self.PALETTE[i % len(self.PALETTE)]
            for v in group:
                colors[v] = color
        return colors

    def _compute_node_colors(self, algorithm: str, source: int, target: int):
        g = self.current_graph

        # ---------------- Buscas (BFS / DFS) ----------------
        if algorithm in ("BFS", "DFS"):
            result = bfs(g, source) if algorithm == "BFS" else dfs(g, source)
            colors = {v: self.COLOR_DEFAULT for v in result.order}
            if target is not None:
                path = result.path_to(target)
                if path:
                    for v in path:
                        colors[v] = self.COLOR_PATH
            colors[source] = self.COLOR_SOURCE
            note = (
                f"{algorithm} a partir de {g.vertex_labels.get(source, source)} — "
                f"vermelho: origem · azul: visitados" +
                (" · verde: caminho até o destino" if target is not None else "")
            )
            return colors, note

        # ---------------- Conectividade ----------------
        if algorithm == "Componentes conexos":
            comps = connected_components(g)
            colors = self._palette_cycle(comps)
            return colors, f"{len(comps)} componente(s) conexo(s) — cada cor é um componente"

        # ---------------- SCC's ----------------
        if algorithm in ("Kosaraju", "Tarjan"):
            sccs = kosaraju_scc(g) if algorithm == "Kosaraju" else tarjan_scc(g)
            colors = self._palette_cycle(sccs)
            return colors, f"{len(sccs)} componente(s) fortemente conexo(s) — cada cor é um SCC"

        # ---------------- Árvore geradora mínima ----------------
        if algorithm in ("Kruskal", "Prim"):
            mst = kruskal(g) if algorithm == "Kruskal" else prim(g, source or 0)
            in_mst = {v for u in range(mst.get_vertex_count()) for v in mst.adj[u]}
            in_mst |= {u for u in range(mst.get_vertex_count()) if mst.adj[u]}
            colors = {v: self.COLOR_PATH for v in in_mst}
            note = (
                f"{algorithm} — verde: vértices conectados pela MST "
                f"({mst.get_edge_count()} arestas). Obs.: a coloração de arestas "
                f"ainda não é suportada pelo canvas; veja o modo Console para a lista completa."
            )
            return colors, note

        # ---------------- Caminhos mínimos ----------------
        if algorithm in ("Dijkstra", "Bellman-Ford"):
            if algorithm == "Dijkstra":
                dist, pred = dijkstra(g, source)
            else:
                dist, pred, _no_neg_cycle = bellman_ford(g, source)

            colors = {
                v: self.COLOR_DEFAULT
                for v in range(g.get_vertex_count())
                if dist[v] != float("inf")
            }
            colors[source] = self.COLOR_SOURCE
            note = f"{algorithm} a partir de {g.vertex_labels.get(source, source)} — azul: alcançáveis"

            if target is not None and dist[target] != float("inf"):
                v = target
                while v is not None:
                    colors[v] = self.COLOR_PATH
                    v = pred[v]
                colors[source] = self.COLOR_SOURCE
                note += " · verde: caminho mínimo até o destino"
            return colors, note

        if algorithm == "Floyd-Warshall":
            colors = {}
            note = (
                "Floyd-Warshall calcula distâncias entre todos os pares de vértices — "
                "não há um destaque único por nó. Veja o modo Console para a matriz completa."
            )
            return colors, note

        # ---------------- Fluxo em rede ----------------
        if algorithm in ("Ford-Fulkerson", "Edmonds-Karp"):
            flow_fn = ford_fulkerson if algorithm == "Ford-Fulkerson" else edmonds_karp
            max_flow, flow_graph = flow_fn(g, source, target)
            touched = {u for u in range(flow_graph.get_vertex_count()) if flow_graph.adj[u]}
            touched |= {v for u in range(flow_graph.get_vertex_count()) for v in flow_graph.adj[u]}
            colors = {v: self.COLOR_DEFAULT for v in touched}
            colors[source] = self.COLOR_SOURCE
            colors[target] = self.COLOR_TARGET
            note = (
                f"{algorithm} — fluxo máximo {max_flow}. Vermelho: origem · laranja: destino · "
                f"azul: vértices na rede residual com fluxo. Veja o Console para as arestas."
            )
            return colors, note

        # ---------------- Topologia ----------------
        if algorithm == "Ordenação topológica":
            order = topological_sort(g)
            if order is None:
                return {}, "O grafo possui ciclo — não é um DAG, ordenação topológica não existe."
            colors = {v: self.PALETTE[i % len(self.PALETTE)] for i, v in enumerate(order)}
            return colors, "Cores em sequência cíclica conforme a ordem topológica"

        return {}, f"Algoritmo '{algorithm}' ainda não implementado."
