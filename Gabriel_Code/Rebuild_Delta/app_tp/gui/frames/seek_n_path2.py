import os
import customtkinter as ctk
from tkinter import messagebox

from filemanager import PATH_D_GEXF
from grafo.utils.gexf_parser import load_gexf
from grafo.networkx_pure.transversal import bfs, dfs


class SearchPathsFrame(ctk.CTkFrame):
    """Frame para o módulo de Busca & Caminhos."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.current_graph = None  # grafo .gexf carregado (AdjacencyListGraph)

        # Configuração do layout: duas colunas (sidebar e conteúdo)
        self.grid_columnconfigure(0, weight=0)   # sidebar não expande
        self.grid_columnconfigure(1, weight=1)   # conteúdo expande
        self.grid_rowconfigure(0, weight=1)

        # ==================== SIDEBAR ====================
        self.sidebar = ctk.CTkFrame(self, width=300)
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
        self.sidebar.grid_propagate(False)  # mantém largura fixa

        # Título da sidebar
        self.title_label = ctk.CTkLabel(
            self.sidebar,
            text="Busca & Caminhos",
            font=("Helvetica", 20, "bold")
        )
        self.title_label.pack(pady=(20, 10))

        # ==================== SELETOR DE GRAFO (.gexf) ====================
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

        # Instrução para categoria
        self.cat_label = ctk.CTkLabel(
            self.sidebar,
            text="Categoria:",
            font=("Helvetica", 14, "bold")
        )
        self.cat_label.pack(pady=(10, 0))

        # ComboBox de categorias
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

        # Instrução para algoritmo
        self.algo_label = ctk.CTkLabel(
            self.sidebar,
            text="Algoritmo:",
            font=("Helvetica", 14, "bold")
        )
        self.algo_label.pack(pady=(10, 0))

        # ComboBox de algoritmos (será preenchida dinamicamente)
        self.algorithms = []  # placeholder
        self.algorithm_combo = ctk.CTkComboBox(
            self.sidebar,
            values=[],
            width=250,
            state="readonly",
            command=self._on_algorithm_change
        )
        self.algorithm_combo.pack(pady=(5, 15))

        # Mapeamento categoria -> lista de algoritmos
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

        # ==================== ÁREA DE CONTEÚDO ====================
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Placeholder genérico
        self.placeholder_label = ctk.CTkLabel(
            self.content,
            text="Conteúdo do algoritmo selecionado aparecerá aqui.",
            font=("Helvetica", 16)
        )

        # Painel específico de BFS/DFS (busca em grafos direcionados)
        self.search_panel = self._build_search_panel(self.content)

        # Exibe o placeholder por padrão
        self.placeholder_label.grid(row=0, column=0, sticky="nsew")

        # Atualiza a combo de algoritmos com a primeira categoria
        self._update_algorithms(self.categories[0])

        # Carrega automaticamente o primeiro grafo .gexf da lista (se houver)
        if self.graph_files:
            self._load_selected_graph(self.graph_files[0])

    # ------------------------------------------------------------------
    # Seleção e carregamento de grafos .gexf
    # ------------------------------------------------------------------

    @staticmethod
    def _list_gexf_files():
        try:
            return sorted(
                f for f in os.listdir(PATH_D_GEXF) if f.endswith(".gexf")
            )
        except OSError:
            return []

    def _on_graph_change(self, choice: str):
        self._load_selected_graph(choice)

    def _load_selected_graph(self, filename: str):
        """Carrega o arquivo .gexf escolhido e atualiza a listagem de vértices."""
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
            self.graph_status_label.configure(
                text=f"✅ {filename}\n{n} nós, {e} arestas."
            )
            # Atualiza a listagem de vértices no painel
            self._update_vertex_list()
            # Limpa as entradas de origem/destino
            self.source_entry.delete(0, "end")
            self.target_entry.delete(0, "end")
        except Exception as ex:
            self.current_graph = None
            self.graph_status_label.configure(
                text=f"❌ Erro ao carregar {filename}: {ex}"
            )
            self._update_vertex_list()

        # Reexecuta o algoritmo atualmente selecionado (se for BFS/DFS, exibe o painel)
        self._on_algorithm_change(self.algorithm_combo.get())

    def _update_vertex_list(self):
        """Preenche o self.names_vertex_box com a lista de vértices do grafo atual."""
        self.names_vertex_box.configure(state="normal")
        self.names_vertex_box.delete("1.0", "end")

        if self.current_graph is None:
            self.names_vertex_box.insert("1.0", "Nenhum grafo carregado.")
        else:
            n = self.current_graph.get_vertex_count()
            labels = self.current_graph.vertex_labels
            # Mostra cada vértice no formato: "índice: rótulo"
            for i in range(n):
                label = labels.get(i, i)
                self.names_vertex_box.insert("end", f"{i}: {label}\n")

        self.names_vertex_box.configure(state="disabled")

    def _update_algorithms(self, category):
        """Atualiza a ComboBox de algoritmos com base na categoria escolhida."""
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
        """Exibe o painel adequado conforme o algoritmo selecionado."""
        if choice and self.algorithm_combo.get() != choice:
            self.algorithm_combo.set(choice)

        if choice in ("BFS", "DFS"):
            self.search_panel.grid(row=0, column=0, sticky="nsew")
            self.placeholder_label.grid_forget()
        else:
            self.placeholder_label.grid(row=0, column=0, sticky="nsew")
            self.search_panel.grid_forget()
            if choice:
                self.placeholder_label.configure(
                    text=f"Algoritmo selecionado: {choice}\n(Área em desenvolvimento)"
                )
            else:
                self.placeholder_label.configure(text="Selecione um algoritmo.")

    # ------------------------------------------------------------------
    # Painel de execução de BFS/DFS
    # ------------------------------------------------------------------

    def _build_search_panel(self, parent) -> ctk.CTkFrame:
        """Monta o painel com campos de entrada para origem/destino,
        botão Executar, área de resultados e listagem de vértices."""
        panel = ctk.CTkFrame(parent, fg_color="transparent")
        panel.grid_columnconfigure(0, weight=1)

        controls = ctk.CTkFrame(panel, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 10))

        # Origem
        ctk.CTkLabel(
            controls, text="Vértice de origem (índice):", font=("Helvetica", 13)
        ).pack(side="left", padx=(0, 8))

        self.source_entry = ctk.CTkEntry(controls,
                                        placeholder_text="Digite apenas números",
                                         width=100)
        self.source_entry.pack(side="left", padx=(0, 8))

        # Destino (opcional)
        ctk.CTkLabel(
            controls, text="Destino (índice, opcional):", font=("Helvetica", 13)
        ).pack(side="left", padx=(8, 8))

        self.target_entry = ctk.CTkEntry(controls,
                                        placeholder_text="Digite apenas números",
                                         width=100)
        self.target_entry.pack(side="left", padx=(0, 8))

        # Botão Executar
        self.run_button = ctk.CTkButton(
            controls, text="▶ Executar", width=110, command=self._run_search
        )
        self.run_button.pack(side="left", padx=(8, 0))

        self.view_algorithm_combo = ctk.CTkComboBox(
            controls,
            values=["Console","Grafico"],
            width=170,
            state="readonly"
        )
        self.view_algorithm_combo.pack(side="left", padx=(0, 8))
        
        # Área de resultados (ocupa espaço restante)
        self.search_result_box = ctk.CTkTextbox(panel, height=320, wrap="word")
        self.search_result_box.pack(side="left", fill="both", expand=True)
        self.search_result_box.configure(state="disabled")

        # Listagem de vértices (largura fixa)
        self.names_vertex_box = ctk.CTkTextbox(panel, width=220, height=320, wrap="word")
        self.names_vertex_box.pack(side="left", fill="y", expand=False)
        self.names_vertex_box.configure(state="disabled")

        return panel

    def _set_result_text(self, text: str):
        self.search_result_box.configure(state="normal")
        self.search_result_box.delete("1.0", "end")
        self.search_result_box.insert("1.0", text)
        self.search_result_box.configure(state="disabled")

    def _run_search(self):
        """Executa BFS ou DFS a partir do índice digitado na origem."""
        if self.current_graph is None:
            messagebox.showwarning("Aviso", "Nenhum grafo carregado.")
            return

        # Lê e valida a origem
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

        # Lê e valida o destino (opcional)
        target_text = self.target_entry.get().strip()
        target = None
        if target_text:
            try:
                target = int(target_text)
            except ValueError:
                messagebox.showerror("Erro", "Destino deve ser um número inteiro (índice) ou vazio.")
                return
            if target < 0 or target >= self.current_graph.get_vertex_count():
                messagebox.showerror("Erro", f"Índice {target} fora do intervalo.")
                return

        algorithm = self.algorithm_combo.get()
        try:
            if algorithm == "BFS":
                result = bfs(self.current_graph, source)
            elif algorithm == "DFS":
                result = dfs(self.current_graph, source)
            else:
                return  # não deveria ocorrer
        except IndexError as ex:
            messagebox.showerror("Erro", str(ex))
            return

        label_of = self.current_graph.vertex_labels.get

        lines = [
            f"Algoritmo: {algorithm}",
            f"Origem: {label_of(source, source)} ({source})",
            "",
            f"Ordem de visita ({len(result.order)} de "
            f"{self.current_graph.get_vertex_count()} vértices alcançados):",
        ]
        lines.append(
            ", ".join(f"{label_of(v, v)} ({v})" for v in result.order)
        )

        if target is not None:
            path = result.path_to(target)
            lines.append("")
            if path is None:
                lines.append(
                    f"Destino {label_of(target, target)} ({target}) não é "
                    f"alcançável a partir da origem (grafo direcionado)."
                )
            else:
                path_str = " → ".join(f"{label_of(v, v)} ({v})" for v in path)
                lines.append(f"Caminho até o destino:\n{path_str}")

        self._set_result_text("\n".join(lines))
